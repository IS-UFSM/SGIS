"""Testes da F4 · Inscrição e etapas (specs/F4-inscricao/)."""
from datetime import timedelta
from unittest import mock

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, connection, transaction
from django.db.migrations.executor import MigrationExecutor
from django.test import TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from empreendimentos.models import Empreendimento
from sgis.excecoes import RegraViolada
from usuarios.models import Usuario

from . import regras
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


class InscricaoPersonalizadaTests(TestCase):
    """INS-01, INS-07 e 3.2.1: inscrição à mão pela IS (T3)."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.url = reverse('trilhas:inscricoes')

    def inscricoes(self, trilha=None):
        return Inscricao.objects.filter(empreendimento=self.empreendimento,
                                        trilha=trilha or self.trilha)

    def postar(self, trilha=None):
        self.client.force_login(self.is_user)
        return self.client.post(self.url, {'empreendimento': self.empreendimento.pk,
                                           'trilha': (trilha or self.trilha).pk})

    def test_a01_inscrito_ve_a_trilha_e_outro_nao(self):
        outro = Usuario.objects.create_user('maria@horta.com', 'Maria', 'senha-forte-123',
                                            papel=Usuario.Papel.EMPREENDEDOR)
        Empreendimento.objects.create(nome='Horta', tipo='Agricultura', representante=outro)

        self.assertRedirects(self.postar(), self.url)
        inscricao = self.inscricoes().get()
        self.assertEqual(inscricao.inscrito_por, self.is_user)  # 3.1.4
        self.assertIsNotNone(inscricao.inscrito_em)

        detalhe = reverse('trilhas:detalhe', args=[self.trilha.pk])
        self.client.force_login(self.empreendimento.representante)
        self.assertContains(self.client.get(reverse('trilhas:inscritas')), 'Precificação')
        self.assertEqual(self.client.get(detalhe).status_code, 200)

        self.client.force_login(outro)
        self.assertNotContains(self.client.get(reverse('trilhas:inscritas')), 'Precificação')
        self.assertEqual(self.client.get(detalhe).status_code, 403)

    def test_a03_recusa_duplicada_ativa_ou_pausada(self):
        inscricao = regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        for status in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            with self.subTest(status=status):
                inscricao.status = status
                inscricao.save()

                with self.assertRaises(RegraViolada):
                    regras.inscrever(self.empreendimento, self.trilha, self.is_user)

                resposta = self.postar()
                self.assertEqual(resposta.status_code, 200)
                self.assertTrue(resposta.context['form'].has_error('__all__'))
                self.assertEqual(self.inscricoes().count(), 1)

    def test_a13_formulario_nao_aceita_trilha_de_etapa_publicada(self):
        # Publicada no teste: sem isso a recusa viria do rascunho (plano, seção 9).
        Trilha.objects.exclude(etapa='').update(status=Trilha.Status.PUBLICADA)

        self.client.force_login(self.is_user)
        opcoes = self.client.get(self.url).context['form'].fields['trilha'].queryset
        self.assertFalse(opcoes.exclude(etapa='').exists())

        for etapa in (Trilha.Etapa.INCUBACAO, Trilha.Etapa.DESINCUBACAO):
            with self.subTest(etapa=etapa):
                trilha = Trilha.objects.get(etapa=etapa)
                resposta = self.postar(trilha)
                self.assertTrue(resposta.context['form'].has_error('trilha', 'invalid_choice'))
                with self.assertRaises(RegraViolada):
                    regras.inscrever(self.empreendimento, trilha, self.is_user)
                self.assertFalse(self.inscricoes(trilha).exists())

    def test_inscrever_nega_outros_papeis(self):
        """INS-01 e A-04, na regra: a view já é coberta por `test_apenas_is_acessa`."""
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'senha-forte-123',
                                                      papel=papel)
                with self.assertRaises(PermissionDenied):
                    regras.inscrever(self.empreendimento, self.trilha, usuario)
        self.assertFalse(self.inscricoes().exists())


class StatusDaInscricaoTests(TestCase):
    """INS-06 (spec 3.5): pausar, reativar, cancelar e concluir (T3)."""

    def setUp(self):
        self.empreendimento, self.trilha = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.inscricao = regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        self.client.force_login(self.is_user)

    def acao(self, acao, inscricao=None, **dados):
        inscricao = inscricao or self.inscricao
        resposta = self.client.post(
            reverse('trilhas:alterar_inscricao', args=[inscricao.pk, acao]), dados,
        )
        inscricao.refresh_from_db()
        return resposta

    def test_a13c_is_conclui_personalizada_e_pode_reinscrever(self):
        self.assertRedirects(self.acao('concluir'), reverse('trilhas:inscricoes'))
        self.assertEqual(self.inscricao.status, Inscricao.Status.CONCLUIDA)
        self.assertIsNotNone(self.inscricao.concluido_em)

        # Selo com texto (RNF-05) e nenhuma ação na inscrição concluída.
        pagina = self.client.get(reverse('trilhas:inscricoes'))
        self.assertContains(pagina, 'Concluída')
        self.assertNotContains(
            pagina, reverse('trilhas:alterar_inscricao', args=[self.inscricao.pk, 'cancelar']),
        )

        nova =regras.inscrever(self.empreendimento, self.trilha, self.is_user)
        self.assertEqual(nova.status, Inscricao.Status.ATIVA)
        self.assertEqual(Inscricao.objects.filter(trilha=self.trilha).count(), 2)

    def test_a13c_concluir_trilha_de_etapa_e_recusado(self):
        pre = self.empreendimento.inscricoes.get(trilha__etapa=Trilha.Etapa.PRE_INCUBACAO)
        self.assertEqual(pre.status, Inscricao.Status.ATIVA)

        self.acao('concluir', pre)
        self.assertEqual(pre.status, Inscricao.Status.ATIVA)
        self.assertIsNone(pre.concluido_em)
        with self.assertRaises(RegraViolada):
            regras.alterar_status(pre, self.is_user, 'concluir')

    def test_a14_pausar_reativar_cancelar_gravam_status_data_e_motivo(self):
        horarios = [timezone.now() + timedelta(hours=hora) for hora in range(4)]
        # Troca só o `timezone` visto por regras.py; o do Django segue para sessões e afins.
        with mock.patch('trilhas.regras.timezone') as relogio:
            relogio.now.side_effect = horarios
            self.acao('pausar', motivo='  Férias coletivas  ')
            self.assertEqual(self.inscricao.status, Inscricao.Status.PAUSADA)
            self.assertEqual(self.inscricao.pausado_em, horarios[0])
            self.assertEqual(self.inscricao.motivo, 'Férias coletivas')

            self.acao('reativar', motivo='não é guardado')
            self.assertEqual(self.inscricao.status, Inscricao.Status.ATIVA)
            self.assertEqual(self.inscricao.reativado_em, horarios[1])
            self.assertEqual(self.inscricao.motivo, 'Férias coletivas')

            # 3.5.4: pausar de novo substitui a data, e o motivo novo substitui o anterior.
            self.acao('pausar', motivo='Obra no ateliê')
            self.assertEqual(self.inscricao.pausado_em, horarios[2])
            self.assertEqual(self.inscricao.motivo, 'Obra no ateliê')

            self.acao('cancelar')
            self.assertEqual(self.inscricao.status, Inscricao.Status.CANCELADA)
            self.assertEqual(self.inscricao.cancelado_em, horarios[3])
            self.assertEqual(self.inscricao.motivo, 'Obra no ateliê')  # sem motivo, fica o anterior
        self.assertTrue(Inscricao.objects.filter(pk=self.inscricao.pk).exists())  # 3.5.2

    def test_a15_concluida_ou_cancelada_nao_volta(self):
        for encerrar in ('concluir', 'cancelar'):
            inscricao = (self.inscricao if encerrar == 'concluir'
                         else regras.inscrever(self.empreendimento, self.trilha, self.is_user))
            regras.alterar_status(inscricao, self.is_user, encerrar)
            encerrada = inscricao.status
            for acao in regras.TRANSICOES_INSCRICAO:
                with self.subTest(status=encerrada, acao=acao):
                    self.acao(acao, inscricao)
                    self.assertEqual(inscricao.status, encerrada)
                    with self.assertRaises(RegraViolada):
                        regras.alterar_status(inscricao, self.is_user, acao)
            if encerrar == 'concluir':
                self.assertIsNone(inscricao.reativado_em)

    def test_concluir_nega_outros_papeis(self):
        """INS-06: só a IS muda o status, na view e na regra."""
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            with self.subTest(papel=papel):
                usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'senha-forte-123',
                                                      papel=papel)
                self.client.force_login(usuario)
                self.assertEqual(self.acao('concluir').status_code, 403)
                with self.assertRaises(PermissionDenied):
                    regras.alterar_status(self.inscricao, usuario, 'concluir')
                self.assertEqual(self.inscricao.status, Inscricao.Status.ATIVA)


class EtapaAtualTests(TestCase):
    """INS-05 e INS-11: a etapa é calculada a partir das inscrições (T3)."""

    def setUp(self):
        self.empreendimento, _ = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.pre = self.empreendimento.inscricoes.get(trilha__etapa=Trilha.Etapa.PRE_INCUBACAO)

    def test_a16_sem_inscricao_de_etapa_e_sem_etapa(self):
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.PRE_INCUBACAO)

        regras.alterar_status(self.pre, self.is_user, 'pausar')  # pausada conta como etapa
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.PRE_INCUBACAO)

        regras.alterar_status(self.pre, self.is_user, 'cancelar')  # 3.5.3
        self.assertIsNone(regras.inscricao_de_etapa(self.empreendimento))
        self.assertIsNone(regras.etapa_atual(self.empreendimento))
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        # Nenhuma tabela guarda a etapa do empreendimento.
        for modelo in (Empreendimento, Inscricao):
            with self.subTest(modelo=modelo.__name__):
                campos = {campo.name for campo in modelo._meta.get_fields()}
                self.assertFalse(campos & {'etapa', 'etapa_atual'})

    def test_incubacao_concluida_so_depois_da_desincubacao(self):
        """INS-11 (3.4.6). O avançar é da T5; aqui a conclusão é gravada direto."""
        desincubacao = Trilha.objects.get(etapa=Trilha.Etapa.DESINCUBACAO)
        self.pre.status = Inscricao.Status.CONCLUIDA
        self.pre.save()
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        ultima = Inscricao.objects.create(empreendimento=self.empreendimento, trilha=desincubacao)
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.DESINCUBACAO)
        self.assertFalse(regras.incubacao_concluida(self.empreendimento))

        ultima.status = Inscricao.Status.CONCLUIDA
        ultima.save()
        self.assertIsNone(regras.etapa_atual(self.empreendimento))
        self.assertTrue(regras.incubacao_concluida(self.empreendimento))

    def test_proxima_etapa_segue_a_ordem(self):
        """3.4.2: Pré-incubação → Incubação → Desincubação."""
        self.assertEqual(regras.proxima_etapa(Trilha.Etapa.PRE_INCUBACAO), Trilha.Etapa.INCUBACAO)
        self.assertEqual(regras.proxima_etapa(Trilha.Etapa.INCUBACAO), Trilha.Etapa.DESINCUBACAO)
        self.assertIsNone(regras.proxima_etapa(Trilha.Etapa.DESINCUBACAO))


def publicar_etapas(*etapas):
    """As migrações deixam Incubação e Desincubação em rascunho (plano, seção 9)."""
    Trilha.objects.filter(etapa__in=etapas or regras.ETAPAS_EM_ORDEM) \
        .update(status=Trilha.Status.PUBLICADA)


class EtapasTests(TestCase):
    """INS-03, INS-04, INS-11, RN-09 e 3.5a: avançar e definir etapa (T5)."""

    def setUp(self):
        self.empreendimento, _ = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.pre = self.empreendimento.inscricoes.get(trilha__etapa=Trilha.Etapa.PRE_INCUBACAO)
        self.client.force_login(self.is_user)

    def url(self, nome=''):
        return reverse(f'trilhas:etapa{nome}', args=[self.empreendimento.pk])

    def avancar(self, etapa_esperada=None):
        if etapa_esperada is None:
            etapa_esperada = regras.etapa_atual(self.empreendimento) or ''
        return self.client.post(self.url('_avancar'), {'etapa_esperada': etapa_esperada})

    def definir(self, etapa):
        return self.client.post(self.url('_definir'), {'etapa': etapa})

    def de_etapa(self):
        return self.empreendimento.inscricoes.exclude(trilha__etapa='')

    def em_andamento(self):
        return self.de_etapa().filter(status__in=regras.STATUS_EM_ANDAMENTO)

    def retrato(self):
        """Tudo o que uma recusa não pode mudar."""
        return list(self.de_etapa().order_by('pk').values_list(
            'pk', 'status', 'concluido_em', 'trilha__etapa'))

    def test_a08_avancar_conclui_e_inscreve_na_proxima(self):
        publicar_etapas(Trilha.Etapa.INCUBACAO)
        self.assertRedirects(self.avancar(), self.url())

        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, Inscricao.Status.CONCLUIDA)
        self.assertIsNotNone(self.pre.concluido_em)
        nova = self.em_andamento().get()
        self.assertEqual(nova.trilha.etapa, Trilha.Etapa.INCUBACAO)
        self.assertEqual(nova.status, Inscricao.Status.ATIVA)
        self.assertEqual(nova.inscrito_por, self.is_user)
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.INCUBACAO)

    def test_a09_sequencia_de_acoes_nunca_gera_duas_etapas(self):
        publicar_etapas()
        incubacao = Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO)
        acoes = [
            lambda: self.avancar(),
            lambda: self.avancar(Trilha.Etapa.PRE_INCUBACAO),  # clique repetido
            lambda: self.definir(Trilha.Etapa.DESINCUBACAO),
            lambda: self.client.post(reverse('trilhas:inscricoes'), {
                'empreendimento': self.empreendimento.pk, 'trilha': incubacao.pk}),
            lambda: regras.alterar_status(self.em_andamento().get(), self.is_user, 'pausar'),
            lambda: self.avancar(),
            lambda: regras.alterar_status(self.em_andamento().get(), self.is_user, 'reativar'),
            lambda: regras.alterar_status(self.em_andamento().get(), self.is_user, 'cancelar'),
            lambda: self.definir(Trilha.Etapa.PRE_INCUBACAO),
            lambda: self.definir(Trilha.Etapa.INCUBACAO),
            lambda: self.avancar(),
        ]
        for passo, acao in enumerate(acoes):
            with self.subTest(passo=passo):
                acao()
                self.assertLessEqual(self.em_andamento().count(), 1)
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.INCUBACAO)

    def test_a10_proxima_etapa_em_rascunho_recusa_e_nada_muda(self):
        antes = self.retrato()
        with self.assertRaises(RegraViolada) as recusa:
            regras.avancar_etapa(self.empreendimento, self.is_user, Trilha.Etapa.PRE_INCUBACAO)
        self.assertIn('Incubação', str(recusa.exception))  # diz qual trilha falta publicar

        self.avancar()
        self.assertEqual(self.retrato(), antes)
        self.assertNotContains(self.client.get(self.url()), self.url('_avancar'))

    def test_a11_inscricao_pausada_nao_avanca(self):
        publicar_etapas()
        regras.alterar_status(self.pre, self.is_user, 'pausar')
        antes = self.retrato()

        self.avancar()
        with self.assertRaises(RegraViolada):
            regras.avancar_etapa(self.empreendimento, self.is_user, Trilha.Etapa.PRE_INCUBACAO)
        self.assertEqual(self.retrato(), antes)

    def test_a12_avancar_da_desincubacao_encerra_a_incubacao(self):
        publicar_etapas()
        self.avancar()
        self.avancar()
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.DESINCUBACAO)

        self.assertContains(self.client.get(self.url()), 'Encerrar a incubação')
        self.avancar()
        self.assertFalse(self.em_andamento().exists())
        self.assertEqual(self.de_etapa().filter(status=Inscricao.Status.CONCLUIDA).count(), 3)
        self.assertIsNone(regras.etapa_atual(self.empreendimento))
        self.assertTrue(regras.incubacao_concluida(self.empreendimento))
        self.assertContains(self.client.get(self.url()), 'Incubação concluída')

    def test_a12b_empreendimento_desativado_nao_avanca_nem_define_etapa(self):
        publicar_etapas()
        self.empreendimento.desativado_em = timezone.now()
        self.empreendimento.save()

        antes = self.retrato()
        self.avancar()
        with self.assertRaises(RegraViolada):
            regras.avancar_etapa(self.empreendimento, self.is_user, Trilha.Etapa.PRE_INCUBACAO)
        self.assertEqual(self.retrato(), antes)

        # Nem a partir da Desincubação (decisão 7.6), nem definindo a etapa.
        self.pre.status = Inscricao.Status.CONCLUIDA
        self.pre.save()
        Inscricao.objects.create(empreendimento=self.empreendimento,
                                 trilha=Trilha.objects.get(etapa=Trilha.Etapa.DESINCUBACAO))
        antes = self.retrato()
        with self.assertRaises(RegraViolada):
            regras.avancar_etapa(self.empreendimento, self.is_user, Trilha.Etapa.DESINCUBACAO)
        self.assertEqual(self.retrato(), antes)
        regras.alterar_status(self.em_andamento().get(), self.is_user, 'cancelar')
        antes = self.retrato()
        self.definir(Trilha.Etapa.INCUBACAO)
        with self.assertRaises(RegraViolada):
            regras.definir_etapa(self.empreendimento, Trilha.Etapa.INCUBACAO, self.is_user)
        self.assertEqual(self.retrato(), antes)
        pagina = self.client.get(self.url())
        self.assertNotContains(pagina, self.url('_avancar'))
        self.assertNotContains(pagina, self.url('_definir'))

    def test_a13b_define_etapa_sem_etapa_ativa(self):
        regras.alterar_status(self.pre, self.is_user, 'cancelar')
        self.assertContains(self.client.get(self.url()), 'Sem etapa')

        # 3.5a.1: a trilha da etapa escolhida precisa estar publicada.
        self.definir(Trilha.Etapa.INCUBACAO)
        self.assertFalse(self.em_andamento().exists())

        publicar_etapas(Trilha.Etapa.INCUBACAO)
        self.assertRedirects(self.definir(Trilha.Etapa.INCUBACAO), self.url())
        nova = self.em_andamento().get()
        self.assertEqual(nova.trilha.etapa, Trilha.Etapa.INCUBACAO)
        self.assertEqual(nova.status, Inscricao.Status.ATIVA)
        self.assertEqual(nova.inscrito_por, self.is_user)  # 3.5a.2

    def test_a13b_definir_forjado_com_etapa_ativa_e_recusado(self):
        publicar_etapas()
        for status in (Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA):
            with self.subTest(status=status):
                self.pre.status = status
                self.pre.save()
                pagina = self.client.get(self.url())
                self.assertIsNone(pagina.context['form'])
                self.assertNotContains(pagina, self.url('_definir'))

                antes = self.retrato()
                self.definir(Trilha.Etapa.INCUBACAO)
                with self.assertRaises(RegraViolada):
                    regras.definir_etapa(self.empreendimento, Trilha.Etapa.INCUBACAO, self.is_user)
                self.assertEqual(self.retrato(), antes)

    def test_avancar_com_etapa_esperada_antiga_e_recusado(self):
        """Plano, seção 4: um clique duplo não avança duas etapas."""
        publicar_etapas()
        self.avancar(Trilha.Etapa.PRE_INCUBACAO)
        antes = self.retrato()
        self.avancar(Trilha.Etapa.PRE_INCUBACAO)
        self.assertEqual(self.retrato(), antes)
        self.assertEqual(regras.etapa_atual(self.empreendimento), Trilha.Etapa.INCUBACAO)

    def test_rotas_de_etapa_e_lote_negam_outros_papeis(self):
        """Rotas de etapa e de lote (INS-10): só a IS, em GET e em POST."""
        publicar_etapas()
        antes = self.retrato()
        personalizada = Trilha.objects.get(titulo='Precificação')
        lote = reverse('trilhas:inscricoes_lote')
        for papel in (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDEDOR, Usuario.Papel.ADMIN):
            usuario = Usuario.objects.create_user(f'{papel}@ufsm.br', papel, 'senha-forte-123',
                                                  papel=papel)
            self.client.force_login(usuario)
            with self.subTest(papel=papel):
                self.assertEqual(self.client.get(self.url()).status_code, 403)
                self.assertEqual(self.avancar(Trilha.Etapa.PRE_INCUBACAO).status_code, 403)
                self.assertEqual(self.definir(Trilha.Etapa.INCUBACAO).status_code, 403)
                self.assertEqual(self.client.get(lote).status_code, 403)
                resposta = self.client.post(lote, {'trilha': personalizada.pk,
                                                   'empreendimentos': [self.empreendimento.pk]})
                self.assertEqual(resposta.status_code, 403)
                for funcao, argumentos in (
                    (regras.avancar_etapa, (usuario, Trilha.Etapa.PRE_INCUBACAO)),
                    (regras.definir_etapa, (Trilha.Etapa.INCUBACAO, usuario)),
                ):
                    with self.assertRaises(PermissionDenied):
                        funcao(self.empreendimento, *argumentos)
                with self.assertRaises(PermissionDenied):
                    regras.inscrever_em_lote(personalizada, [self.empreendimento], usuario)
        self.assertEqual(self.retrato(), antes)
        self.assertFalse(personalizada.inscricoes.exists())

        self.client.force_login(self.is_user)
        self.assertEqual(self.client.get(self.url('_avancar')).status_code, 405)

    def test_j3_etapas_de_ponta_a_ponta(self):
        """J-3: da Pré-incubação à Incubação pela tela, sem nunca estar em duas etapas."""
        publicar_etapas(Trilha.Etapa.INCUBACAO)
        pagina = self.client.get(reverse('trilhas:inscricoes'))
        self.assertContains(pagina, self.url())  # entrada pela tela de inscrições (7.9)

        pagina = self.client.get(self.url())
        self.assertContains(pagina, 'Pré-incubação')
        self.assertContains(pagina, 'Avançar para Incubação')

        pagina = self.client.post(self.url('_avancar'),
                                  {'etapa_esperada': Trilha.Etapa.PRE_INCUBACAO}, follow=True)
        self.assertContains(pagina, 'avançou para')
        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, Inscricao.Status.CONCLUIDA)
        self.assertEqual(self.em_andamento().get().trilha.etapa, Trilha.Etapa.INCUBACAO)


class PreIncubacaoTests(TestCase):
    """INS-02 e 3.3: entrada automática na Pré-incubação (T4)."""

    def setUp(self):
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        self.pre = Trilha.objects.get(etapa=Trilha.Etapa.PRE_INCUBACAO)  # criada pela migração
        self.contador = 0

    def criar_empreendimento(self, nome='Ateliê'):
        self.contador += 1
        dono = Usuario.objects.create_user(f'dono{self.contador}@atelie.com', nome,
                                           'senha-forte-123', papel=Usuario.Papel.EMPREENDEDOR)
        return Empreendimento.objects.create(nome=nome, tipo=Empreendimento.Tipo.COLETIVO,
                                             representante=dono)

    def pre_em_rascunho(self):
        Trilha.objects.filter(pk=self.pre.pk).update(status=Trilha.Status.RASCUNHO,
                                                     publicada_em=None)
        self.pre.refresh_from_db()
        if not self.pre.atividades.filter(arquivada_em__isnull=True).exists():
            regras.acrescentar_atividade(self.pre, self.is_user,
                                         {'titulo': 'Boas-vindas', 'tipo': 'leitura'})

    def publicar_pre(self):
        regras.publicar(self.pre, self.is_user)

    def na_pre(self, empreendimento):
        return empreendimento.inscricoes.filter(trilha=self.pre)

    def test_a05_empreendimento_novo_entra_na_pre_incubacao_sem_autor(self):
        empreendimento = self.criar_empreendimento()
        inscricao = self.na_pre(empreendimento).get()
        self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)
        self.assertIsNone(inscricao.inscrito_por)
        self.assertEqual(regras.etapa_atual(empreendimento), Trilha.Etapa.PRE_INCUBACAO)
        self.assertIsNone(regras.aviso_pre_incubacao())

    def test_a06_pre_em_rascunho_fica_sem_etapa_e_avisa_is(self):
        self.pre_em_rascunho()
        empreendimento = self.criar_empreendimento()
        self.assertFalse(empreendimento.inscricoes.exists())
        self.assertIsNone(regras.etapa_atual(empreendimento))

        # A IS vê o aviso ao criar o empreendedor pela tela.
        self.client.force_login(self.is_user)
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Horta', 'email': 'horta@coletivo.com', 'papel': Usuario.Papel.EMPREENDEDOR,
            'senha': 'senha-super-segura',
            'empreendimento-nome': 'Horta', 'empreendimento-tipo': Empreendimento.Tipo.COLETIVO,
        }, follow=True)
        avisos = [m for m in resposta.context['messages'] if m.level_tag == 'warning']
        self.assertEqual(len(avisos), 1)
        self.assertIn(self.pre.titulo, str(avisos[0]))
        self.assertFalse(Empreendimento.objects.get(nome='Horta').inscricoes.exists())

    def test_a06_sem_aviso_ao_criar_com_pre_publicada(self):
        self.client.force_login(self.is_user)
        resposta = self.client.post(reverse('criar_usuario'), {
            'nome': 'Horta', 'email': 'horta@coletivo.com', 'papel': Usuario.Papel.EMPREENDEDOR,
            'senha': 'senha-super-segura',
            'empreendimento-nome': 'Horta', 'empreendimento-tipo': Empreendimento.Tipo.COLETIVO,
        }, follow=True)
        self.assertFalse([m for m in resposta.context['messages'] if m.level_tag == 'warning'])

    def test_a06_publicar_pre_inscreve_pendentes(self):
        self.pre_em_rascunho()
        pendentes = [self.criar_empreendimento('Ateliê'), self.criar_empreendimento('Horta')]
        desativado = self.criar_empreendimento('Fechado')
        desativado.desativado_em = timezone.now()
        desativado.save(update_fields=['desativado_em'])

        self.publicar_pre()

        for empreendimento in pendentes:
            with self.subTest(empreendimento=empreendimento.nome):
                inscricao = self.na_pre(empreendimento).get()
                self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)
                self.assertIsNone(inscricao.inscrito_por)
        self.assertFalse(desativado.inscricoes.exists())

    def test_a06_publicar_pela_tela_inscreve_pendentes(self):
        self.pre_em_rascunho()
        empreendimento = self.criar_empreendimento()
        self.client.force_login(self.is_user)
        self.client.post(reverse('trilhas:acao', args=[self.pre.pk, 'publicar']))
        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, Trilha.Status.PUBLICADA)
        self.assertTrue(self.na_pre(empreendimento).exists())

    def test_a06_publicar_e_atomico(self):
        self.pre_em_rascunho()
        self.criar_empreendimento()
        with mock.patch.object(regras, 'inscrever_pendentes_na_pre_incubacao',
                               side_effect=RuntimeError):
            with self.assertRaises(RuntimeError):
                self.publicar_pre()
        self.pre.refresh_from_db()
        self.assertEqual(self.pre.status, Trilha.Status.RASCUNHO)

    def test_a07_quem_concluiu_nao_e_reinscrito(self):
        publicar_etapas()
        concluiu = self.criar_empreendimento('Ateliê')
        for etapa in regras.ETAPAS_EM_ORDEM:
            regras.avancar_etapa(concluiu, self.is_user, etapa)
        self.assertTrue(regras.incubacao_concluida(concluiu))
        cancelado = self.criar_empreendimento('Horta')  # passou pela Pré-incubação e saiu
        regras.alterar_status(self.na_pre(cancelado).get(), self.is_user, 'cancelar')
        antes = Inscricao.objects.count()

        # A Pré-incubação recebe atividade nova e é publicada de novo.
        regras.acrescentar_atividade(self.pre, self.is_user,
                                     {'titulo': 'Nova leitura', 'tipo': 'leitura'})
        self.pre_em_rascunho()
        self.publicar_pre()

        self.assertEqual(Inscricao.objects.count(), antes)
        self.assertEqual(self.na_pre(concluiu).count(), 1)
        self.assertEqual(self.na_pre(cancelado).count(), 1)
        self.assertTrue(regras.incubacao_concluida(concluiu))


class InscricaoEmLoteTests(TestCase):
    """INS-10 (spec 3.8): inscrição em lote pela IS (T7)."""

    def setUp(self):
        self.ja_inscrito, self.trilha = criar_par()
        self.is_user = Usuario.objects.create_user('is@ufsm.br', 'IS', 'senha-forte-123',
                                                   papel=Usuario.Papel.IS)
        dono = Usuario.objects.create_user('ana@horta.com', 'Ana', 'senha-forte-123',
                                           papel=Usuario.Papel.EMPREENDEDOR)
        self.novo = Empreendimento.objects.create(nome='Horta', tipo='Agricultura',
                                                  representante=dono)
        # RN-01 (F2): cada empreendimento tem a sua conta.
        dona_brecho = Usuario.objects.create_user('bia@brecho.com', 'Bia', 'senha-forte-123',
                                                  papel=Usuario.Papel.EMPREENDEDOR)
        self.desativado = Empreendimento.objects.create(nome='Brechó', tipo='Moda',
                                                        representante=dona_brecho,
                                                        desativado_em=timezone.now())
        regras.inscrever(self.ja_inscrito, self.trilha, self.is_user)
        self.url = reverse('trilhas:inscricoes_lote')
        self.client.force_login(self.is_user)

    def postar(self, *empreendimentos, trilha=None):
        return self.client.post(self.url, {
            'trilha': (trilha or self.trilha).pk,
            'empreendimentos': [e.pk for e in empreendimentos],
        }, follow=True)

    def test_a19_lote_inscreve_um_e_ignora_dois(self):
        pagina = self.client.get(self.url)
        self.assertContains(pagina, 'Horta')
        self.assertNotContains(pagina, 'Brechó')  # a tela lista só os ativos

        # O desativado vem forjado pelo POST: é ignorado, sem invalidar o lote.
        resposta = self.postar(self.ja_inscrito, self.novo, self.desativado)
        self.assertContains(resposta, '1 inscrito, 2 ignorados')

        inscricao = self.trilha.inscricoes.get(empreendimento=self.novo)
        self.assertEqual(inscricao.status, Inscricao.Status.ATIVA)
        self.assertEqual(inscricao.inscrito_por, self.is_user)
        self.assertEqual(self.trilha.inscricoes.filter(empreendimento=self.ja_inscrito).count(), 1)
        self.assertFalse(self.trilha.inscricoes.filter(empreendimento=self.desativado).exists())

    def test_lote_aceita_quem_concluiu_e_ignora_pausado(self):
        """3.8.2 e 3.1.3: só ativa e pausada contam como já inscrito."""
        inscricao = self.trilha.inscricoes.get(empreendimento=self.ja_inscrito)
        regras.alterar_status(inscricao, self.is_user, 'pausar')
        inscritos, ignorados = regras.inscrever_em_lote(
            self.trilha, [self.ja_inscrito, self.novo], self.is_user)
        self.assertEqual((len(inscritos), ignorados), (1, [self.ja_inscrito]))

        regras.alterar_status(inscricao, self.is_user, 'cancelar')
        regras.alterar_status(inscritos[0], self.is_user, 'concluir')
        inscritos, ignorados = regras.inscrever_em_lote(
            self.trilha, [self.ja_inscrito, self.novo], self.is_user)
        self.assertEqual((len(inscritos), len(ignorados)), (2, 0))

    def test_lote_so_em_trilha_personalizada_publicada(self):
        """3.8.1: trilha de etapa ou em rascunho é recusada e ninguém é inscrito."""
        publicar_etapas()
        rascunho = Trilha.objects.create(titulo='Rascunho', usuario_criador=self.is_user)
        for trilha in (Trilha.objects.get(etapa=Trilha.Etapa.INCUBACAO), rascunho):
            with self.subTest(trilha=trilha.titulo):
                resposta = self.postar(self.novo, trilha=trilha)
                self.assertTrue(resposta.context['form'].has_error('trilha', 'invalid_choice'))
                with self.assertRaises(RegraViolada):
                    regras.inscrever_em_lote(trilha, [self.novo], self.is_user)
                self.assertFalse(trilha.inscricoes.filter(empreendimento=self.novo).exists())

    def test_lote_sem_empreendimento_marcado_e_recusado(self):
        resposta = self.postar()
        self.assertTrue(resposta.context['form'].has_error('empreendimentos', 'required'))
        self.assertEqual(self.trilha.inscricoes.count(), 1)

    def test_tela_de_inscricoes_leva_ao_lote(self):
        self.assertContains(self.client.get(reverse('trilhas:inscricoes')), self.url)


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
