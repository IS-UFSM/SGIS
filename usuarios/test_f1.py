"""Testes da F1 · Acesso e contas (specs/F1-acesso/)."""
import importlib
import os
from io import StringIO
from unittest import mock

from django.core.management import call_command
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

from .models import Usuario

ANTES = ('usuarios', '0003_papel_empreendedor')
DEPOIS = ('usuarios', '0004_troca_de_senha_e_criado_em')


def entrar(client, email, senha):
    return client.post(reverse('login'), {'email': email, 'senha': senha})


class EmailEmMinusculasTests(TestCase):
    """ACE-01: o e-mail vale com ou sem maiúsculas e é guardado em minúsculas."""

    def test_a01_entra_com_email_em_maiusculas(self):
        Usuario.objects.create_user('maria@x.com', 'Maria', 'senha-forte-123',
                                    papel=Usuario.Papel.PROFESSOR)

        resposta = entrar(self.client, 'Maria@X.com', 'senha-forte-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

    def test_a01_conta_criada_com_maiusculas_fica_em_minusculas(self):
        conta = Usuario.objects.create_user('Joao@X.com', 'João', 'senha-forte-123',
                                            papel=Usuario.Papel.PROFESSOR)
        conta.refresh_from_db()
        self.assertEqual(conta.email, 'joao@x.com')


class SenhaFracaTests(TestCase):
    """ACE-12: senha com os validadores do Django e mínimo de 10 caracteres."""

    SENHAS_FRACAS = [
        ('9 caracteres', 'Trilha#12'),
        ('comum', 'qwertyuiop'),
        ('só números', '83920571946'),
        ('parecida com o e-mail', 'mariadastrilhas'),
    ]

    def setUp(self):
        self.is_ = Usuario.objects.create_user('is-teste@sgis.com', 'Incubadora',
                                               'senha-forte-123', papel=Usuario.Papel.IS)

    def test_a09_senha_fraca_recusada_na_criacao_redefinicao_e_troca(self):
        # A redefinição pela IS chega na F1 · T5; aqui, os caminhos que já existem.
        self.client.force_login(self.is_)
        for motivo, senha in self.SENHAS_FRACAS:
            with self.subTest(caminho='criação', motivo=motivo):
                resposta = self.client.post(reverse('criar_usuario'), {
                    'nome': 'Maria das Trilhas', 'email': 'mariadastrilhas@escola.com',
                    'papel': Usuario.Papel.PROFESSOR, 'senha': senha,
                })
                self.assertTrue(resposta.context['form'].has_error('senha'))
                self.assertFalse(
                    Usuario.objects.filter(email='mariadastrilhas@escola.com').exists())

        conta = Usuario.objects.create_user('mariadastrilhas@escola.com', 'Maria das Trilhas',
                                            'senha-antiga-123', papel=Usuario.Papel.PROFESSOR)
        self.client.force_login(conta)
        for motivo, senha in self.SENHAS_FRACAS:
            with self.subTest(caminho='troca', motivo=motivo):
                resposta = self.client.post(reverse('trocar_senha'), {
                    'senha_atual': 'senha-antiga-123',
                    'nova_senha': senha, 'confirmar_nova_senha': senha,
                })
                self.assertTrue(resposta.context['form'].has_error('nova_senha'))
                conta.refresh_from_db()
                self.assertTrue(conta.check_password('senha-antiga-123'))


class CreateSuperuserTests(TestCase):
    """ACE-13: o primeiro admin é criado por comando e consegue entrar."""

    def test_createsuperuser_cria_conta_que_entra(self):
        with mock.patch.dict(os.environ, {'DJANGO_SUPERUSER_PASSWORD': 'senha-do-admin-123'}):
            call_command('createsuperuser', interactive=False, email='Admin@SGIS.com',
                         nome='Administrador', stdout=StringIO())

        conta = Usuario.objects.get(email='admin@sgis.com')
        self.assertEqual(conta.papel, Usuario.Papel.ADMIN)
        resposta = entrar(self.client, 'admin@sgis.com', 'senha-do-admin-123')
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)


class MigracaoTests(TransactionTestCase):
    """Migração 0004 (plano da F1, seção 3), rodada de verdade a partir da 0003."""

    serialized_rollback = True

    def setUp(self):
        self.addCleanup(self.voltar_ao_estado_atual)  # roda mesmo se o setUp falhar
        self.executor = MigrationExecutor(connection)
        self.executor.migrate([ANTES])
        self.apps_antes = self.executor.loader.project_state(ANTES).apps

    def voltar_ao_estado_atual(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def migrar_para_a_0004(self):
        executor = MigrationExecutor(connection)
        executor.migrate([DEPOIS])

    def test_migracao_marca_contas_is_e_normaliza_emails(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.create(email='Outra.IS@SGIS.com', nome='IS', papel='is', password='!')
        Antigo.objects.create(email='Prof@Escola.com', nome='Prof', papel='professor',
                              password='!')

        self.migrar_para_a_0004()

        self.assertTrue(Usuario.objects.get(email='outra.is@sgis.com').deve_trocar_senha)
        professor = Usuario.objects.get(email='prof@escola.com')
        self.assertFalse(professor.deve_trocar_senha)
        self.assertIsNotNone(professor.criado_em)

    def test_a20_conta_inicial_da_is_em_minusculas_com_troca_obrigatoria(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.filter(papel='is').delete()
        conta_inicial = importlib.import_module(
            'usuarios.migrations.0002_criar_usuario_is_padrao')
        ambiente = {'IS_EMAIL': 'Nova.IS@SGIS.com', 'IS_SENHA_INICIAL': 'senha-inicial-123'}
        with mock.patch.dict(os.environ, ambiente):
            conta_inicial.criar_usuario_is_padrao(self.apps_antes, None)

        self.migrar_para_a_0004()

        conta = Usuario.objects.get(papel=Usuario.Papel.IS)
        self.assertEqual(conta.email, 'nova.is@sgis.com')
        self.assertTrue(conta.deve_trocar_senha)
        self.assertTrue(conta.check_password('senha-inicial-123'))

    def test_migracao_para_com_emails_que_ficariam_iguais(self):
        Antigo = self.apps_antes.get_model('usuarios', 'Usuario')
        Antigo.objects.create(email='Ana@X.com', nome='Ana', papel='professor', password='!')
        Antigo.objects.create(email='ana@x.com', nome='Ana 2', papel='professor', password='!')

        with self.assertRaises(RuntimeError):
            self.migrar_para_a_0004()

        emails = set(Antigo.objects.values_list('email', flat=True))
        self.assertTrue({'Ana@X.com', 'ana@x.com'} <= emails)  # nada foi alterado
        Antigo.objects.filter(email='Ana@X.com').delete()
