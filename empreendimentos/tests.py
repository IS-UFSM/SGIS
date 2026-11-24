from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from trilhas import regras as regras_trilhas
from trilhas.models import Inscricao, Trilha
from usuarios import regras as regras_usuarios
from usuarios.models import Usuario

from .models import Empreendimento


def criar_conta(email, papel=Usuario.Papel.EMPREENDEDOR):
    return Usuario.objects.create_user(email, 'Pessoa', 'senha-forte-123', papel=papel)


class RepresentanteTests(TestCase):
    """F2 · T1: EMP-02, RN-01 e RN-02 (spec 3.2)."""

    dados = {'nome': 'Ateliê', 'tipo': Empreendimento.Tipo.COLETIVO}

    def test_a04_empreendedor_nao_representa_dois(self):
        conta = criar_conta('joao@atelie.com')
        regras_usuarios.vincular_empreendimento(conta, self.dados)

        with self.assertRaises(ValidationError) as erro:
            regras_usuarios.vincular_empreendimento(conta, {**self.dados, 'nome': 'Horta'})
        self.assertIn('representante', erro.exception.error_dict)

        # O banco também recusa, mesmo por fora das regras.
        with self.assertRaises(IntegrityError):
            Empreendimento.objects.create(nome='Horta', tipo='outro', representante=conta)

    def test_a04_so_empreendedor_e_representante(self):
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.IS, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                conta = criar_conta(f'{papel}@ufsm.br', papel=papel)
                with self.assertRaises(ValidationError) as erro:
                    regras_usuarios.vincular_empreendimento(conta, self.dados)
                self.assertEqual(erro.exception.error_dict['representante'][0].code, 'papel_invalido')
                self.assertFalse(Empreendimento.objects.filter(representante=conta).exists())


class MigracaoDoTipoTests(TransactionTestCase):
    """F2 · T1: a 0005 converte o tipo em texto livre, e a reversa o devolve (decisão 7.1)."""

    # A migração trilhas/0005 cria as trilhas de etapa no banco de testes; sem isto,
    # a limpeza do TransactionTestCase as apagaria para os testes seguintes.
    serialized_rollback = True

    antes = [('empreendimentos', '0004_email_telefone_contato')]
    depois = [('empreendimentos', '0005_converter_tipo')]

    def migrar(self, alvo):
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(alvo)
        return executor.loader.project_state(alvo).apps

    def tearDown(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_converte_tipo_e_reversa_restaura(self):
        apps = self.migrar(self.antes)
        EmpreendimentoAntigo = apps.get_model('empreendimentos', 'Empreendimento')
        # A tabela de usuários continua no esquema atual: as contas usam o model de hoje.
        criar = lambda email, **campos: EmpreendimentoAntigo.objects.create(
            representante_id=criar_conta(email).pk, **campos,
        )
        livre = criar('a@a.com', nome='Ateliê', tipo='Artesanato / Textil', descricao='Peças à mão.')
        sem_descricao = criar('b@b.com', nome='Horta', tipo='alimentos', descricao='')
        valido = criar('c@c.com', nome='MEI do Zé', tipo='mei', descricao='Já na lista.')

        apps = self.migrar(self.depois)
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        livre_novo = Empreendimento.objects.get(pk=livre.pk)
        self.assertEqual(livre_novo.tipo, 'outro')
        self.assertEqual(livre_novo.descricao, 'Peças à mão.\n\nTipo anterior: Artesanato / Textil')
        sem_descricao_novo = Empreendimento.objects.get(pk=sem_descricao.pk)
        self.assertEqual(
            (sem_descricao_novo.tipo, sem_descricao_novo.descricao),
            ('outro', 'Tipo anterior: alimentos'),
        )
        self.assertEqual(Empreendimento.objects.get(pk=valido.pk).tipo, 'mei')

        apps = self.migrar(self.antes)
        Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
        for original in (livre, sem_descricao, valido):
            restaurado = Empreendimento.objects.get(pk=original.pk)
            self.assertEqual(
                (restaurado.tipo, restaurado.descricao), (original.tipo, original.descricao),
            )


class ListaTests(TestCase):
    """F2 · T2: EMP-03 (spec 3.4), a lista da IS com filtros e etapa calculada."""

    url = reverse('empreendimentos:lista')

    def setUp(self):
        # Todo empreendimento novo entra na Pré-incubação (signal da F4).
        Trilha.objects.exclude(etapa='').update(status=Trilha.Status.PUBLICADA)
        self.is_user = criar_conta('is@ufsm.br', papel=Usuario.Papel.IS)
        self.pre = self.criar('Ateliê', 'a@a.com')
        self.incubado = self.criar('Brechó', 'b@b.com')
        regras_trilhas.avancar_etapa(self.incubado, self.is_user, Trilha.Etapa.PRE_INCUBACAO)
        self.desativado = self.criar('Cozinha', 'c@c.com')
        self.desativado.desativado_em = timezone.now()
        self.desativado.save()
        self.sem_etapa = self.criar('Doceria', 'd@d.com')
        self.sem_etapa.inscricoes.update(status=Inscricao.Status.CANCELADA)
        self.client.force_login(self.is_user)

    def criar(self, nome, email):
        return Empreendimento.objects.create(
            nome=nome, tipo=Empreendimento.Tipo.COLETIVO, representante=criar_conta(email),
        )

    def listados(self, **filtros):
        resposta = self.client.get(self.url, filtros)
        self.assertEqual(resposta.status_code, 200)
        return [e.nome for e in resposta.context['empreendimentos']]

    def test_a06_filtros_se_combinam(self):
        self.assertEqual(self.listados(), ['Ateliê', 'Brechó', 'Cozinha', 'Doceria'])
        self.assertEqual(self.listados(situacao='desativados'), ['Cozinha'])
        self.assertEqual(self.listados(situacao='ativos'), ['Ateliê', 'Brechó', 'Doceria'])
        self.assertEqual(self.listados(etapa=Trilha.Etapa.PRE_INCUBACAO), ['Ateliê', 'Cozinha'])
        self.assertEqual(self.listados(etapa=Trilha.Etapa.INCUBACAO), ['Brechó'])
        self.assertEqual(self.listados(etapa='sem'), ['Doceria'])
        self.assertEqual(
            self.listados(situacao='ativos', etapa=Trilha.Etapa.PRE_INCUBACAO), ['Ateliê'],
        )
        self.assertEqual(self.listados(situacao='desativados', etapa='sem'), [])
        # Filtro desconhecido é ignorado, como na lista de trilhas.
        self.assertEqual(len(self.listados(situacao='x', etapa='y')), 4)

    def test_a07_lista_mostra_etapa_calculada(self):
        resposta = self.client.get(self.url)
        etapas = {e.nome: e.etapa_rotulo for e in resposta.context['empreendimentos']}
        self.assertEqual(etapas, {
            'Ateliê': 'Pré-incubação', 'Brechó': 'Incubação',
            'Cozinha': 'Pré-incubação', 'Doceria': 'Sem etapa',
        })
        self.assertContains(resposta, 'Incubação')
        self.assertContains(resposta, reverse('trilhas:etapa', args=[self.incubado.pk]))
        # Nada de etapa gravada no empreendimento (INS-05).
        campos = {campo.name for campo in Empreendimento._meta.get_fields()}
        self.assertFalse(any('etapa' in nome for nome in campos))

    def test_a07_etapa_nao_custa_uma_consulta_por_linha(self):
        """Plano, seção 4: o número de consultas não cresce com o número de empreendimentos."""
        with CaptureQueriesContext(connection) as antes:
            self.client.get(self.url)
        for numero in range(3):
            self.criar(f'Extra {numero}', f'extra{numero}@e.com')
        with CaptureQueriesContext(connection) as depois:
            resposta = self.client.get(self.url)
        self.assertEqual(len(resposta.context['empreendimentos']), 7)
        self.assertEqual(len(depois), len(antes))

    def test_lista_so_para_a_is(self):
        """EMP-03: professor, conta do empreendimento e admin recebem 403."""
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                self.client.force_login(criar_conta(f'outro-{papel}@ufsm.br', papel=papel))
                self.assertEqual(self.client.get(self.url).status_code, 403)

    def test_cabecalho_da_is_tem_link_para_a_lista(self):
        self.assertContains(self.client.get(reverse('home')), f'href="{self.url}"')


class PerfilTests(TestCase):
    """F2 · T3: EMP-04 e EMP-05 (spec 3.5), o perfil e quem o vê."""

    def setUp(self):
        self.is_user = criar_conta('is@ufsm.br', papel=Usuario.Papel.IS)
        self.professor = criar_conta('x@ufsm.br', papel=Usuario.Papel.PROFESSOR)
        self.conta_a = criar_conta('conta@atelie.com')
        self.a = Empreendimento.objects.create(
            nome='Ateliê', tipo=Empreendimento.Tipo.COLETIVO, descricao='Peças feitas à mão.',
            email_contato='oi@atelie.com', telefone_contato='55 3220-0000',
            representante=self.conta_a,
        )
        self.b = Empreendimento.objects.create(
            nome='Horta', tipo=Empreendimento.Tipo.MEI, representante=criar_conta('conta@horta.com'),
        )
        # A esteve numa trilha do professor X; a inscrição já foi encerrada (A-09).
        self.trilha = Trilha.objects.create(
            titulo='Precificação', usuario_criador=self.professor, status=Trilha.Status.PUBLICADA,
        )
        Inscricao.objects.create(
            empreendimento=self.a, trilha=self.trilha, status=Inscricao.Status.CANCELADA,
        )

    def url(self, empreendimento):
        return reverse('empreendimentos:perfil', args=[empreendimento.pk])

    def abrir(self, usuario, empreendimento):
        self.client.force_login(usuario)
        return self.client.get(self.url(empreendimento))

    def test_a08_perfil_mostra_dados_contatos_etapa_e_inscricoes(self):
        """Os contatos entram no perfil na T7 (EMP-07)."""
        resposta = self.abrir(self.is_user, self.a)
        self.assertEqual(resposta.status_code, 200)
        for texto in (
            'Ateliê', 'Coletivo', 'Peças feitas à mão.', 'oi@atelie.com', '55 3220-0000',
            'Conta do empreendimento', 'conta@atelie.com',
        ):
            self.assertContains(resposta, texto)
        self.assertEqual(resposta.context['etapa_atual'], 'Pré-incubação')
        status = {i.trilha.titulo: i.status for i in resposta.context['inscricoes']}
        self.assertEqual(status, {
            'Pré-incubação': Inscricao.Status.ATIVA,
            'Precificação': Inscricao.Status.CANCELADA,
        })
        self.assertContains(resposta, 'Cancelada')
        self.assertContains(resposta, reverse('trilhas:etapa', args=[self.a.pk]))
        self.assertContains(resposta, reverse('trilhas:detalhe', args=[self.trilha.pk]))

    def test_a09_professor_ve_quem_atendeu_e_outro_recebe_403(self):
        resposta = self.abrir(self.professor, self.a)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, reverse('trilhas:detalhe', args=[self.trilha.pk]))
        self.assertNotContains(resposta, reverse('trilhas:etapa', args=[self.a.pk]))  # só a IS

        self.assertEqual(self.abrir(self.professor, self.b).status_code, 403)
        outro = criar_conta('z@ufsm.br', papel=Usuario.Papel.PROFESSOR)
        self.assertEqual(self.abrir(outro, self.a).status_code, 403)

    def test_a10_representante_ve_o_proprio_e_admin_recebe_403(self):
        resposta = self.abrir(self.conta_a, self.a)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, f'href="{self.url(self.a)}"')  # "Meu empreendimento"
        # A tela de etapa é só da IS.
        self.assertNotContains(resposta, reverse('trilhas:etapa', args=[self.a.pk]))
        self.assertEqual(self.abrir(self.conta_a, self.b).status_code, 403)

        admin = criar_conta('admin@ufsm.br', papel=Usuario.Papel.ADMIN)
        for empreendimento in (self.a, self.b):
            with self.subTest(empreendimento=empreendimento.nome):
                self.assertEqual(self.abrir(admin, empreendimento).status_code, 403)

    def test_perfil_exige_login(self):
        resposta = self.client.get(self.url(self.a))
        self.assertEqual(resposta.status_code, 302)
        self.assertIn(reverse('login'), resposta['Location'])

    def test_lista_tem_link_para_o_perfil(self):
        self.client.force_login(self.is_user)
        resposta = self.client.get(reverse('empreendimentos:lista'))
        self.assertContains(resposta, f'href="{self.url(self.a)}"')
        self.assertContains(resposta, f'href="{self.url(self.b)}"')
