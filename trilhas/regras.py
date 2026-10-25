"""Regras da F3 · Trilhas: quem pode e quando pode (specs/F3-trilhas/spec.md, seção 3).

As views só chamam estas funções. Falta de permissão (quem) levanta `PermissionDenied`,
que vira 403; condição de estado não atendida (quando) levanta `RegraViolada`, cuja
mensagem é mostrada ao usuário.
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from empreendimentos.models import Empreendimento
from usuarios.models import Usuario

from .models import AtividadeTrilha, Inscricao, Trilha

# Campos de atividade que podem mudar em cada estado da trilha (spec 3.5).
CAMPOS_ATIVIDADE = (
    'titulo', 'descricao', 'tipo', 'endereco', 'obrigatoria',
    'exige_validacao', 'prazo_fixo', 'dias_apos_inscricao',
)
CAMPOS_TEXTO_ATIVIDADE = ('titulo', 'descricao', 'endereco')


class RegraViolada(Exception):
    """Ação não permitida pelo estado da trilha. A mensagem é mostrada ao usuário."""


# Quem é quem

def e_is(usuario):
    return usuario.is_authenticated and usuario.papel == Usuario.Papel.IS


def e_dono(usuario, trilha):
    """TRL-01: a dona da trilha de etapa é a IS (papel); a da personalizada, quem a criou."""
    if trilha.e_de_etapa:
        return e_is(usuario)
    return usuario.is_authenticated and trilha.usuario_criador_id == usuario.pk


def empreendimentos_atendidos(professor):
    """Vocabulário da spec mãe: inscritos, em qualquer status, em trilhas do professor."""
    return Empreendimento.objects.filter(
        inscricoes__trilha__usuario_criador=professor,
    ).distinct()


# Ver

def trilhas_visiveis(usuario):
    """TRL-10 (spec 3.6): as trilhas que cada papel pode ver."""
    if not usuario.is_authenticated:
        return Trilha.objects.none()

    if usuario.papel == Usuario.Papel.IS:
        return Trilha.objects.all()

    if usuario.papel == Usuario.Papel.PROFESSOR:
        de_outros = (
            Q(etapa='')
            & Q(status__in=[Trilha.Status.PUBLICADA, Trilha.Status.ARQUIVADA])
            & Q(inscricoes__empreendimento__in=empreendimentos_atendidos(usuario))
        )
        return Trilha.objects.filter(
            Q(usuario_criador=usuario) | ~Q(etapa='') | de_outros,
        ).distinct()

    if usuario.papel == Usuario.Papel.EMPREENDEDOR:
        return (
            Trilha.objects
            .filter(inscricoes__empreendimento__representante=usuario)
            .exclude(status=Trilha.Status.RASCUNHO)
            .distinct()
        )

    return Trilha.objects.none()  # admin: RN-16


def pode_ver(usuario, trilha):
    """TRL-10."""
    return trilhas_visiveis(usuario).filter(pk=trilha.pk).exists()


# Editar

def pode_editar(usuario, trilha):
    """TRL-07 (spec 3.3): o dono e a IS. Nunca outro professor, empreendedor ou admin."""
    return e_dono(usuario, trilha) or e_is(usuario)


def exige_confirmacao(usuario, trilha):
    """TRL-07 (spec 3.3.5, decisão 7.7): a IS confirma antes de alterar trilha de professor."""
    return (
        e_is(usuario)
        and not trilha.e_de_etapa
        and trilha.usuario_criador.papel == Usuario.Papel.PROFESSOR
    )


def _exigir_edicao(usuario, trilha):
    if not pode_editar(usuario, trilha):
        raise PermissionDenied
    if trilha.status == Trilha.Status.ARQUIVADA:
        raise RegraViolada('Trilha arquivada não pode ser alterada.')  # A-14


# Estados

def publicar(trilha, usuario):
    """TRL-05: rascunho → publicada, com pelo menos uma atividade ativa (A-09, A-10)."""
    _exigir_edicao(usuario, trilha)
    if trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('Só uma trilha em rascunho pode ser publicada.')
    if not trilha.atividades.filter(arquivada_em__isnull=True).exists():
        raise RegraViolada('Acrescente pelo menos uma atividade antes de publicar.')
    trilha.status = Trilha.Status.PUBLICADA
    trilha.publicada_em = timezone.now()
    trilha.save(update_fields=['status', 'publicada_em'])


def arquivar(trilha, usuario):
    """TRL-05: publicada → arquivada; só personalizada e sem inscrição ativa ou pausada (A-03, A-15)."""
    _exigir_edicao(usuario, trilha)
    if trilha.e_de_etapa:
        raise RegraViolada('Trilhas de etapa não podem ser arquivadas.')
    if trilha.status != Trilha.Status.PUBLICADA:
        raise RegraViolada('Só uma trilha publicada pode ser arquivada.')
    if trilha.inscricoes.filter(
        status__in=[Inscricao.Status.ATIVA, Inscricao.Status.PAUSADA],
    ).exists():
        raise RegraViolada(
            'A trilha tem inscrições ativas ou pausadas. '
            'Peça à IS para concluí-las ou cancelá-las antes de arquivar.'
        )
    trilha.status = Trilha.Status.ARQUIVADA
    trilha.arquivada_em = timezone.now()
    trilha.save(update_fields=['status', 'arquivada_em'])


# Atividades

def campos_editaveis(trilha):
    """TRL-06 (spec 3.5): em rascunho, todos; publicada, só os textos; arquivada, nenhum (A-11)."""
    if trilha.status == Trilha.Status.RASCUNHO:
        return CAMPOS_ATIVIDADE
    if trilha.status == Trilha.Status.PUBLICADA:
        return CAMPOS_TEXTO_ATIVIDADE
    return ()


@transaction.atomic
def acrescentar_atividade(trilha, usuario, dados):
    """TRL-04, TRL-06: atividade nova entra no fim, em rascunho ou publicada (A-08, A-12)."""
    _exigir_edicao(usuario, trilha)
    ultima = trilha.atividades.aggregate(maior=Max('ordem'))['maior'] or 0
    campos = {campo: valor for campo, valor in dados.items() if campo in CAMPOS_ATIVIDADE}
    return AtividadeTrilha.objects.create(trilha=trilha, ordem=ultima + 1, **campos)


def apagar_atividade(atividade, usuario):
    """RN-10: só se apaga atividade de trilha em rascunho; depois disso, só arquivar (A-13)."""
    _exigir_edicao(usuario, atividade.trilha)
    if atividade.trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('Atividade de trilha publicada não pode ser apagada; arquive-a.')
    atividade.delete()


def arquivar_atividade(atividade, usuario):
    """RN-10: atividade arquivada sai da trilha, mas continua no histórico de quem a fez."""
    _exigir_edicao(usuario, atividade.trilha)
    if atividade.arquivada_em is not None:
        raise RegraViolada('Esta atividade já está arquivada.')
    atividade.arquivada_em = timezone.now()
    atividade.save(update_fields=['arquivada_em'])


@transaction.atomic
def mover_atividade(atividade, usuario, direcao):
    """TRL-08: troca a atividade de lugar com a vizinha, só em rascunho (A-23)."""
    trilha = atividade.trilha
    _exigir_edicao(usuario, trilha)
    if trilha.status != Trilha.Status.RASCUNHO:
        raise RegraViolada('A ordem só pode ser mudada enquanto a trilha está em rascunho.')

    ativas = trilha.atividades.filter(arquivada_em__isnull=True)
    if direcao == 'cima':
        vizinha = ativas.filter(ordem__lt=atividade.ordem).order_by('-ordem').first()
    elif direcao == 'baixo':
        vizinha = ativas.filter(ordem__gt=atividade.ordem).order_by('ordem').first()
    else:
        raise ValueError(f'Direção inválida: {direcao}')

    if vizinha is None:
        return  # já é a primeira (ou a última)
    atividade.ordem, vizinha.ordem = vizinha.ordem, atividade.ordem
    atividade.save(update_fields=['ordem'])
    vizinha.save(update_fields=['ordem'])
