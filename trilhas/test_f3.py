"""Testes da F3 · Trilhas (specs/F3-trilhas/spec.md). Cada teste cita o critério que cobre."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase

from .models import Trilha

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
