"""Testes da F4 · Inscrição e etapas (specs/F4-inscricao/)."""
from datetime import timedelta

from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.utils import timezone

from empreendimentos.models import Empreendimento
from usuarios.models import Usuario

from .models import Inscricao, Trilha

ANTES_DA_0009 = ('trilhas', '0008_remover_tipo_pre_incubacao')


def criar_par():
    """Um empreendimento e uma trilha personalizada, prontos para inscrever."""
    professor = Usuario.objects.create_user('prof@escola.com', 'Prof', 'senha-forte-123',
                                            papel=Usuario.Papel.PROFESSOR)
    empreendedor = Usuario.objects.create_user('joao@atelie.com', 'João', 'senha-forte-123',
                                               papel=Usuario.Papel.EMPREENDEDOR)
    empreendimento = Empreendimento.objects.create(nome='Ateliê', tipo='Artesanato',
                                                   representante=empreendedor)
    trilha = Trilha.objects.create(titulo='Precificação', usuario_criador=professor,
                                   status=Trilha.Status.PUBLICADA)
    return empreendimento, trilha


class RestricaoDeInscricaoTests(TestCase):
    """INS-07 e A-03, no nível do banco: só uma inscrição ativa ou pausada por par."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()

    def inscrever(self, status=Inscricao.Status.ATIVA):
        return Inscricao.objects.create(empreendimento=self.empreendimento, trilha=self.trilha,
                                        status=status)

    def test_a03_banco_recusa_duplicada_ativa_ou_pausada(self):
        for em_andamento in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            for nova in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
                with self.subTest(existente=em_andamento, nova=nova):
                    primeira = self.inscrever(em_andamento)
                    with self.assertRaises(IntegrityError), transaction.atomic():
                        self.inscrever(nova)
                    primeira.status = Inscricao.Status.CANCELADA
                    primeira.save()

    def test_a03_aceita_nova_apos_concluida_ou_cancelada(self):
        for encerrada in (Inscricao.Status.CONCLUIDA, Inscricao.Status.CANCELADA):
            with self.subTest(status=encerrada):
                inscricao = self.inscrever()
                inscricao.status = encerrada
                inscricao.save()
                self.inscrever().delete()  # a nova é aceita; sai para o próximo caso

        # Várias encerradas no mesmo par convivem com uma em andamento.
        self.inscrever(Inscricao.Status.CONCLUIDA)
        self.inscrever(Inscricao.Status.CONCLUIDA)
        self.inscrever()
        self.assertEqual(Inscricao.objects.filter(empreendimento=self.empreendimento,
                                                  trilha=self.trilha).count(), 5)


class MigracaoF4Tests(TransactionTestCase):
    """Migração 0009 (plano da F4, seção 3), rodada de verdade para trás."""

    serialized_rollback = True

    def setUp(self):
        self.addCleanup(self.voltar_ao_estado_atual)  # roda mesmo se o teste falhar

    def voltar_ao_estado_atual(self):
        executor = MigrationExecutor(connection)
        executor.migrate(executor.loader.graph.leaf_nodes())

    def test_migracao_reversa_converte_concluidas_em_canceladas(self):
        empreendimento, trilha = criar_par()
        concluida_em = timezone.now() - timedelta(days=3)
        concluidas = [
            Inscricao.objects.create(empreendimento=empreendimento, trilha=trilha,
                                     status=Inscricao.Status.CONCLUIDA,
                                     concluido_em=concluida_em - timedelta(days=dias))
            for dias in (0, 10)
        ]
        ativa = Inscricao.objects.create(empreendimento=empreendimento, trilha=trilha)

        MigrationExecutor(connection).migrate([ANTES_DA_0009])

        Antiga = MigrationExecutor(connection).loader.project_state(ANTES_DA_0009).apps \
            .get_model('trilhas', 'Inscricao')
        for original in concluidas:
            convertida = Antiga.objects.get(pk=original.pk)
            self.assertEqual(convertida.status, 'cancelada')
            self.assertEqual(convertida.cancelado_em, original.concluido_em)
        self.assertEqual(Antiga.objects.get(pk=ativa.pk).status, 'ativa')
        self.assertEqual(Antiga.objects.filter(empreendimento_id=empreendimento.pk,
                                               trilha_id=trilha.pk).count(), 3)
