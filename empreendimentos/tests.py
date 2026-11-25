from django.core.exceptions import ValidationError
from django.db import IntegrityError, connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase, override_settings
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


class EdicaoTests(TestCase):
    """F2 · T4: EMP-01 e spec 3.3, só a IS edita, sem trocar a conta do empreendimento."""

    def setUp(self):
        self.is_user = criar_conta('is@ufsm.br', papel=Usuario.Papel.IS)
        self.conta = criar_conta('conta@atelie.com')
        self.empreendimento = Empreendimento.objects.create(
            nome='Ateliê', tipo=Empreendimento.Tipo.COLETIVO, representante=self.conta,
        )
        self.url = reverse('empreendimentos:editar', args=[self.empreendimento.pk])
        self.dados = {
            'nome': 'Ateliê da Praça', 'tipo': Empreendimento.Tipo.ASSOCIACAO,
            'descricao': 'Peças feitas à mão.', 'email_contato': 'oi@atelie.com',
            'telefone_contato': '55 3220-0000',
        }

    def retrato(self):
        self.empreendimento.refresh_from_db()
        return (
            self.empreendimento.nome, self.empreendimento.tipo, self.empreendimento.descricao,
            self.empreendimento.email_contato, self.empreendimento.telefone_contato,
            self.empreendimento.representante_id,
        )

    def test_a03_is_edita(self):
        self.client.force_login(self.is_user)
        self.assertEqual(self.client.get(self.url).status_code, 200)
        resposta = self.client.post(self.url, self.dados)
        self.assertRedirects(
            resposta, reverse('empreendimentos:perfil', args=[self.empreendimento.pk]),
        )
        self.assertEqual(self.retrato(), (*self.dados.values(), self.conta.pk))

    def test_a03_dado_invalido_nao_salva(self):
        self.client.force_login(self.is_user)
        antes = self.retrato()
        for campo, valor in (('nome', ''), ('tipo', 'alimentos'), ('email_contato', 'nao-e-email')):
            with self.subTest(campo=campo):
                resposta = self.client.post(self.url, {**self.dados, campo: valor})
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error(campo))
                self.assertEqual(self.retrato(), antes)

    def test_a03_professor_e_representante_nao_editam(self):
        professor = criar_conta('x@ufsm.br', papel=Usuario.Papel.PROFESSOR)
        Inscricao.objects.create(  # mesmo atendendo o empreendimento, o professor só lê
            empreendimento=self.empreendimento,
            trilha=Trilha.objects.create(titulo='Precificação', usuario_criador=professor),
        )
        admin = criar_conta('admin@ufsm.br', papel=Usuario.Papel.ADMIN)
        antes = self.retrato()
        for usuario in (professor, self.conta, admin):
            with self.subTest(papel=usuario.papel):
                self.client.force_login(usuario)
                self.assertEqual(self.client.get(self.url).status_code, 403)
                self.assertEqual(self.client.post(self.url, self.dados).status_code, 403)
                perfil = self.client.get(
                    reverse('empreendimentos:perfil', args=[self.empreendimento.pk]),
                )
                self.assertNotContains(perfil, self.url, status_code=perfil.status_code)
        self.assertEqual(self.retrato(), antes)

    def test_a05_representante_forjado_e_ignorado(self):
        outra = criar_conta('outra@horta.com')
        self.client.force_login(self.is_user)
        self.client.post(self.url, {**self.dados, 'representante': outra.pk})
        self.assertEqual(self.retrato()[-1], self.conta.pk)
        self.assertEqual(self.retrato()[0], 'Ateliê da Praça')  # o resto foi salvo

    def test_perfil_da_is_tem_botao_editar(self):
        self.client.force_login(self.is_user)
        perfil = self.client.get(reverse('empreendimentos:perfil', args=[self.empreendimento.pk]))
        self.assertContains(perfil, f'href="{self.url}"')


@override_settings(STORAGES={  # o /admin/ usa arquivos estáticos, como nos testes da F1
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
})
class CriacaoTests(TestCase):
    """F2 · T5: EMP-01, o formulário da F1 pede todos os dados do empreendimento."""

    dados_empreendimento = {
        'empreendimento-nome': 'Ateliê da Praça',
        'empreendimento-tipo': Empreendimento.Tipo.ASSOCIACAO,
        'empreendimento-descricao': 'Peças feitas à mão.',
        'empreendimento-email_contato': 'contato@atelie.com',
        'empreendimento-telefone_contato': '(55) 3220-0000',
    }
    esperado = ('Ateliê da Praça', 'associacao', 'Peças feitas à mão.',
                'contato@atelie.com', '(55) 3220-0000')

    def setUp(self):
        self.is_user = criar_conta('is@ufsm.br', papel=Usuario.Papel.IS)
        self.admin = Usuario.objects.create_superuser('admin@ufsm.br', 'Admin', 'senha-forte-123')

    def criar_pela_is(self, email='joao@atelie.com', **extra):
        self.client.force_login(self.is_user)
        return self.client.post(reverse('criar_usuario'), {
            'nome': 'João do Ateliê', 'email': email, 'papel': Usuario.Papel.EMPREENDEDOR,
            'senha': 'senha-inicial-123', **self.dados_empreendimento, **extra,
        })

    def criar_pelo_admin(self, email='joao@atelie.com', **extra):
        self.client.force_login(self.admin)
        return self.client.post(reverse('admin:usuarios_usuario_add'), {
            'nome': 'João do Ateliê', 'email': email, 'papel': Usuario.Papel.EMPREENDEDOR,
            'password1': 'senha-inicial-123', 'password2': 'senha-inicial-123',
            **self.dados_empreendimento, **extra,
        })

    def salvo(self, email='joao@atelie.com'):
        e = Empreendimento.objects.get(representante__email=email)
        return (e.nome, e.tipo, e.descricao, e.email_contato, e.telefone_contato)

    def test_a01_criar_empreendedor_salva_todos_os_campos(self):
        for criar, email in ((self.criar_pela_is, 'is@atelie.com'),
                             (self.criar_pelo_admin, 'admin@atelie.com')):
            with self.subTest(tela=criar.__name__):
                resposta = criar(email=email)
                self.assertEqual(resposta.status_code, 302)
                self.assertEqual(self.salvo(email), self.esperado)

    def test_a01_formulario_da_is_mostra_os_campos_novos(self):
        self.client.force_login(self.is_user)
        resposta = self.client.get(reverse('criar_usuario'))
        for campo in ('email_contato', 'telefone_contato'):
            self.assertContains(resposta, f'name="empreendimento-{campo}"')

    def test_a01_email_e_telefone_sao_opcionais(self):
        self.criar_pela_is(**{
            'empreendimento-email_contato': '', 'empreendimento-telefone_contato': '',
        })
        self.assertEqual(self.salvo()[3:], ('', ''))

    def test_a02_tipo_ou_email_invalido_nao_cria_nada(self):
        invalidos = (('tipo', 'alimentos'), ('tipo', ''), ('email_contato', 'nao-e-email'))
        for criar in (self.criar_pela_is, self.criar_pelo_admin):
            for campo, valor in invalidos:
                with self.subTest(tela=criar.__name__, campo=campo, valor=valor):
                    resposta = criar(**{f'empreendimento-{campo}': valor})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertFalse(Usuario.objects.filter(email='joao@atelie.com').exists())
                    self.assertFalse(Empreendimento.objects.filter(nome='Ateliê da Praça').exists())
