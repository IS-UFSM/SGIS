"""Testes da F3 · Trilhas (specs/F3-trilhas/spec.md). Cada teste cita o critério que cobre."""

from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from empreendimentos.models import Empreendimento
from usuarios.models import Usuario

from . import regras
from .models import AtividadeTrilha, Inscricao, Trilha
from .regras import RegraViolada

ANTES_DA_F3 = [('trilhas', '0005_criar_trilha_pre_incubacao')]
DEPOIS_DA_F3 = [('trilhas', '0008_remover_tipo_pre_incubacao')]
# Estado dos outros apps no momento do teste (já com o campo `representante`).
OUTROS_APPS = [
    ('usuarios', '0003_papel_empreendedor'),
    ('empreendimentos', '0003_renomeia_representante'),
]


class TrilhasDeEtapaTests(TestCase):
    def test_a02_existem_tres_trilhas_de_etapa(self):
        """A-02 (TRL-01, TRL-03): o sistema instalado tem uma trilha para cada etapa."""
        etapas = list(Trilha.objects.exclude(etapa='').values_list('etapa', flat=True))
        self.assertCountEqual(etapas, Trilha.Etapa.values)


class MigracaoF3Tests(TransactionTestCase):
    """Spec F3, seção 6: conversão de tipo/pre_incubacao para etapa/status (plan.md, seção 3)."""

    # Restaura no fim os dados criados pelas migrações (usuário IS, trilhas de etapa),
    # dos quais os outros testes dependem.
    serialized_rollback = True

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(ANTES_DA_F3)  # também exercita a reversa de 0006 a 0008
        apps = executor.loader.project_state(ANTES_DA_F3 + OUTROS_APPS).apps

        Usuario = apps.get_model('usuarios', 'Usuario')
        Trilha = apps.get_model('trilhas', 'Trilha')
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        Inscricao = apps.get_model('trilhas', 'Inscricao')

        empreendedor = Usuario.objects.create(email='e@ufsm.br', nome='Emp', papel='empreendedor')
        professor = Usuario.objects.create(email='p@ufsm.br', nome='Prof', papel='professor')
        empreendimento = Empreendimento.objects.create(
            nome='Padaria', tipo='alimentos', representante=empreendedor,
        )
        self.pre_pk = Trilha.objects.get(pre_incubacao=True).pk
        self.inscricao_pk = Inscricao.objects.create(
            empreendimento=empreendimento, trilha_id=self.pre_pk, status='ativa',
        ).pk
        self.personalizada_pk = Trilha.objects.create(
            titulo='Precificação', tipo='custom', usuario_criador=professor,
        ).pk
        self.professor_pk = professor.pk

        executor = MigrationExecutor(connection)
        executor.migrate(DEPOIS_DA_F3)
        self.apps = executor.loader.project_state(DEPOIS_DA_F3 + OUTROS_APPS).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_pre_incubacao_vira_etapa_publicada_sem_perder_inscricoes(self):
        Trilha = self.apps.get_model('trilhas', 'Trilha')
        Inscricao = self.apps.get_model('trilhas', 'Inscricao')

        pre = Trilha.objects.get(pk=self.pre_pk)
        self.assertEqual(pre.etapa, 'pre_incubacao')
        self.assertEqual(pre.status, 'publicada')
        self.assertIsNone(pre.usuario_criador_id)
        self.assertEqual(Inscricao.objects.get(pk=self.inscricao_pk).trilha_id, self.pre_pk)

        personalizada = Trilha.objects.get(pk=self.personalizada_pk)
        self.assertEqual(personalizada.etapa, '')
        self.assertEqual(personalizada.status, 'publicada')
        self.assertEqual(personalizada.usuario_criador_id, self.professor_pk)

        for etapa in ('incubacao', 'desincubacao'):
            with self.subTest(etapa=etapa):
                trilha = Trilha.objects.get(etapa=etapa)
                self.assertEqual(trilha.status, 'rascunho')
                self.assertIsNone(trilha.usuario_criador_id)


def criar_usuario(email, papel):
    return Usuario.objects.create_user(email, email.split('@')[0], 'x', papel=papel)


class RegrasBaseTests(TestCase):
    """Cenário comum: IS, professores X, Y e Z, um empreendedor com empreendimento e o admin."""

    def setUp(self):
        self.is_user = criar_usuario('is@ufsm.br', Usuario.Papel.IS)
        self.prof_x = criar_usuario('x@ufsm.br', Usuario.Papel.PROFESSOR)
        self.prof_y = criar_usuario('y@ufsm.br', Usuario.Papel.PROFESSOR)
        self.prof_z = criar_usuario('z@ufsm.br', Usuario.Papel.PROFESSOR)
        self.empreendedor = criar_usuario('e@ufsm.br', Usuario.Papel.EMPREENDEDOR)
        self.admin = criar_usuario('admin@ufsm.br', Usuario.Papel.ADMIN)
        self.empreendimento = Empreendimento.objects.create(
            nome='Padaria', tipo='alimentos', representante=self.empreendedor,
        )
        self.etapa = Trilha.objects.get(etapa=Trilha.Etapa.PRE_INCUBACAO)  # criada pela migração
        self.trilha_x = Trilha.objects.create(titulo='Do X', usuario_criador=self.prof_x)

    def dono_de(self, trilha):
        return self.is_user if trilha.e_de_etapa else trilha.usuario_criador

    def atividade(self, trilha, titulo='Ler o guia', **extra):
        dados = {'titulo': titulo, 'tipo': AtividadeTrilha.Tipo.LEITURA, **extra}
        return regras.acrescentar_atividade(trilha, self.dono_de(trilha), dados)

    def publicada(self, trilha):
        self.atividade(trilha)
        regras.publicar(trilha, self.dono_de(trilha))
        trilha.refresh_from_db()
        return trilha

    def inscrever(self, trilha, status=Inscricao.Status.ATIVA):
        return Inscricao.objects.create(
            empreendimento=self.empreendimento, trilha=trilha, status=status,
        )


class EstadosDaTrilhaTests(RegrasBaseTests):
    def test_a03_trilha_de_etapa_nao_pode_ser_arquivada(self):
        """A-03 (RN-08): nem a IS arquiva uma trilha de etapa."""
        self.assertEqual(self.etapa.status, Trilha.Status.PUBLICADA)
        with self.assertRaises(RegraViolada):
            regras.arquivar(self.etapa, self.is_user)
        self.etapa.refresh_from_db()
        self.assertEqual(self.etapa.status, Trilha.Status.PUBLICADA)

    def test_a09_publicar_exige_atividade_ativa(self):
        """A-09 (TRL-05): sem atividade ativa não publica; com uma, publica."""
        with self.assertRaises(RegraViolada):
            regras.publicar(self.trilha_x, self.prof_x)

        arquivada = self.atividade(self.trilha_x)
        regras.arquivar_atividade(arquivada, self.prof_x)
        with self.assertRaises(RegraViolada):
            regras.publicar(self.trilha_x, self.prof_x)

        self.atividade(self.trilha_x, 'Outra')
        regras.publicar(self.trilha_x, self.prof_x)
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.status, Trilha.Status.PUBLICADA)
        self.assertIsNotNone(self.trilha_x.publicada_em)

    def test_a10_publicada_nao_volta_a_rascunho(self):
        """A-10 (TRL-05): não há transição de volta; publicar de novo é recusado."""
        trilha = self.publicada(self.trilha_x)
        with self.assertRaises(RegraViolada):
            regras.publicar(trilha, self.prof_x)
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.PUBLICADA)

    def test_a14_trilha_arquivada_nao_e_editavel(self):
        """A-14 (TRL-05): nenhuma alteração em trilha arquivada."""
        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        regras.arquivar(trilha, self.prof_x)
        trilha.refresh_from_db()
        atividade.refresh_from_db()

        self.assertEqual(regras.campos_editaveis(trilha), ())
        acoes = {
            'publicar': lambda: regras.publicar(trilha, self.prof_x),
            'arquivar': lambda: regras.arquivar(trilha, self.prof_x),
            'acrescentar': lambda: regras.acrescentar_atividade(
                trilha, self.prof_x, {'titulo': 'X', 'tipo': AtividadeTrilha.Tipo.TAREFA},
            ),
            'apagar atividade': lambda: regras.apagar_atividade(atividade, self.prof_x),
            'arquivar atividade': lambda: regras.arquivar_atividade(atividade, self.prof_x),
            'mover atividade': lambda: regras.mover_atividade(atividade, self.prof_x, 'cima'),
            'IS publicar': lambda: regras.publicar(trilha, self.is_user),
        }
        for nome, acao in acoes.items():
            with self.subTest(acao=nome), self.assertRaises(RegraViolada):
                acao()

    def test_a15_nao_arquiva_trilha_com_inscricao_ativa_ou_pausada(self):
        """A-15 (TRL-05, decisão 7.3): só arquiva depois de concluir ou cancelar as inscrições."""
        trilha = self.publicada(self.trilha_x)
        inscricao = self.inscrever(trilha)
        for status in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            with self.subTest(status=status):
                Inscricao.objects.filter(pk=inscricao.pk).update(status=status)
                with self.assertRaises(RegraViolada):
                    regras.arquivar(trilha, self.prof_x)

        Inscricao.objects.filter(pk=inscricao.pk).update(status=Inscricao.Status.CANCELADA)
        regras.arquivar(trilha, self.prof_x)
        trilha.refresh_from_db()
        self.assertEqual(trilha.status, Trilha.Status.ARQUIVADA)
        self.assertIsNotNone(trilha.arquivada_em)


class AtividadesTests(RegrasBaseTests):
    def test_a08_atividade_nova_entra_no_fim(self):
        """A-08 (TRL-04): cada atividade nova fica por último."""
        primeira = self.atividade(self.trilha_x, 'Primeira')
        segunda = self.atividade(self.trilha_x, 'Segunda')
        self.assertLess(primeira.ordem, segunda.ordem)
        self.assertEqual(list(self.trilha_x.atividades.all()), [primeira, segunda])

    def test_a11_campos_editaveis_por_estado(self):
        """A-11 (TRL-06): depois de publicada, só os textos da atividade mudam."""
        self.assertIn('prazo_fixo', regras.campos_editaveis(self.trilha_x))
        trilha = self.publicada(self.trilha_x)
        self.assertEqual(set(regras.campos_editaveis(trilha)), {'titulo', 'descricao', 'endereco'})

    def test_a13_atividade_de_publicada_nao_e_apagada_so_arquivada(self):
        """A-13 (RN-10): em rascunho apaga; publicada, só arquiva."""
        rascunho = self.atividade(self.trilha_x, 'Some')
        regras.apagar_atividade(rascunho, self.prof_x)
        self.assertFalse(AtividadeTrilha.objects.filter(pk=rascunho.pk).exists())

        trilha = self.publicada(self.trilha_x)
        atividade = trilha.atividades.get()
        with self.assertRaises(RegraViolada):
            regras.apagar_atividade(atividade, self.prof_x)
        regras.arquivar_atividade(atividade, self.prof_x)
        atividade.refresh_from_db()
        self.assertIsNotNone(atividade.arquivada_em)

    def test_a23_mover_so_em_rascunho(self):
        """A-23 (TRL-08): troca de lugar com a vizinha; em publicada é recusado."""
        primeira = self.atividade(self.trilha_x, 'Primeira')
        segunda = self.atividade(self.trilha_x, 'Segunda')
        regras.mover_atividade(segunda, self.prof_x, 'cima')
        self.assertEqual(list(self.trilha_x.atividades.all()), [segunda, primeira])

        regras.publicar(self.trilha_x, self.prof_x)
        segunda.refresh_from_db()
        with self.assertRaises(RegraViolada):
            regras.mover_atividade(segunda, self.prof_x, 'baixo')


class QuemEditaTests(RegrasBaseTests):
    def test_a16_professor_nao_altera_trilha_de_outro(self):
        """A-16 (TRL-07): o professor Y não edita, publica nem arquiva a trilha do X."""
        self.assertFalse(regras.pode_editar(self.prof_y, self.trilha_x))
        self.atividade(self.trilha_x)
        with self.assertRaises(PermissionDenied):
            regras.publicar(self.trilha_x, self.prof_y)
        regras.publicar(self.trilha_x, self.prof_x)
        with self.assertRaises(PermissionDenied):
            regras.arquivar(self.trilha_x, self.prof_y)

    def test_a17_professor_nao_edita_trilha_de_etapa_nem_da_is(self):
        """A-17 (TRL-07)."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        for trilha in (self.etapa, da_is):
            with self.subTest(trilha=trilha.titulo):
                self.assertFalse(regras.pode_editar(self.prof_x, trilha))
                with self.assertRaises(PermissionDenied):
                    regras.acrescentar_atividade(
                        trilha, self.prof_x, {'titulo': 'X', 'tipo': AtividadeTrilha.Tipo.TAREFA},
                    )

    def test_a19_empreendedor_e_admin_nao_editam(self):
        """A-19 (TRL-07)."""
        for usuario in (self.empreendedor, self.admin):
            for trilha in (self.etapa, self.trilha_x):
                with self.subTest(usuario=usuario.papel, trilha=trilha.titulo):
                    self.assertFalse(regras.pode_editar(usuario, trilha))

    def test_dono_e_is_editam(self):
        """TRL-07 (spec 3.3.5): o dono edita a sua; a IS edita qualquer uma."""
        self.assertTrue(regras.pode_editar(self.prof_x, self.trilha_x))
        self.assertTrue(regras.pode_editar(self.is_user, self.trilha_x))
        self.assertTrue(regras.pode_editar(self.is_user, self.etapa))

    def test_a18_confirmacao_so_quando_is_altera_trilha_de_professor(self):
        """A-18 (decisão 7.7): só a IS, e só em trilha de professor, precisa confirmar."""
        da_is = Trilha.objects.create(titulo='Da IS', usuario_criador=self.is_user)
        self.assertTrue(regras.exige_confirmacao(self.is_user, self.trilha_x))
        self.assertFalse(regras.exige_confirmacao(self.is_user, self.etapa))
        self.assertFalse(regras.exige_confirmacao(self.is_user, da_is))
        self.assertFalse(regras.exige_confirmacao(self.prof_x, self.trilha_x))

    def test_a18b_is_altera_mas_professor_continua_dono(self):
        """A-18b (RN-04): a IS publica a trilha do professor; o dono não muda."""
        self.atividade(self.trilha_x)
        regras.publicar(self.trilha_x, self.is_user)
        self.trilha_x.refresh_from_db()
        self.assertEqual(self.trilha_x.usuario_criador, self.prof_x)
        self.assertTrue(regras.e_dono(self.prof_x, self.trilha_x))
        self.assertFalse(regras.e_dono(self.is_user, self.trilha_x))


class QuemVeTests(RegrasBaseTests):
    def test_a20_rascunho_visivel_so_para_dono_e_is(self):
        """A-20 (TRL-10)."""
        self.assertTrue(regras.pode_ver(self.prof_x, self.trilha_x))
        self.assertTrue(regras.pode_ver(self.is_user, self.trilha_x))
        for usuario in (self.prof_y, self.empreendedor, self.admin):
            with self.subTest(usuario=usuario.email):
                self.assertFalse(regras.pode_ver(usuario, self.trilha_x))

    def test_a21_professor_ve_trilha_de_outro_so_se_atende_o_empreendimento(self):
        """A-21 (TRL-10): X atende o empreendimento (inscrito na trilha dele) e vê a do Y; Z não."""
        trilha_y = self.publicada(Trilha.objects.create(titulo='Do Y', usuario_criador=self.prof_y))
        self.inscrever(self.publicada(self.trilha_x))
        self.inscrever(trilha_y)

        self.assertTrue(regras.pode_ver(self.prof_x, trilha_y))
        self.assertFalse(regras.pode_ver(self.prof_z, trilha_y))

        # Continua vendo depois que a inscrição na trilha dele termina (PRO-03).
        Inscricao.objects.filter(trilha=self.trilha_x).update(status=Inscricao.Status.CANCELADA)
        self.assertTrue(regras.pode_ver(self.prof_x, trilha_y))

    def test_professor_ve_trilhas_de_etapa(self):
        """TRL-10: o professor vê as trilhas de etapa, em leitura."""
        rascunho = Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO)
        self.assertTrue(regras.pode_ver(self.prof_z, self.etapa))
        self.assertTrue(regras.pode_ver(self.prof_z, rascunho))

    def test_a22_empreendedor_nao_ve_trilha_sem_inscricao(self):
        """A-22 (TRL-10): vê só as trilhas em que o empreendimento está ou esteve inscrito."""
        trilha = self.publicada(self.trilha_x)
        self.assertTrue(regras.pode_ver(self.empreendedor, self.etapa))  # inscrição automática
        self.assertFalse(regras.pode_ver(self.empreendedor, trilha))

        inscricao = self.inscrever(trilha)
        self.assertTrue(regras.pode_ver(self.empreendedor, trilha))
        Inscricao.objects.filter(pk=inscricao.pk).update(status=Inscricao.Status.CANCELADA)
        self.assertTrue(regras.pode_ver(self.empreendedor, trilha))

    def test_admin_nao_ve_trilhas(self):
        """RN-16: o admin não acessa dados de negócio."""
        self.assertFalse(regras.trilhas_visiveis(self.admin).exists())
