"""Regras dos empreendimentos e dos contatos: quem vê e quem edita.

F2 · Empreendimentos (specs/F2-empreendimentos/spec.md, seção 3). As views só chamam
estas funções. Falta de permissão vira `PermissionDenied` (403).
"""

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.utils import timezone

from trilhas import regras as regras_trilhas
from usuarios.models import Usuario

from .models import Contato, Empreendimento


def empreendimentos_visiveis(usuario):
    """EMP-05 (spec 3.5.3): IS, todos; professor, os que atende; conta, o próprio; admin, nenhum."""
    if not usuario.is_authenticated:
        return Empreendimento.objects.none()
    if usuario.papel == Usuario.Papel.IS:
        return Empreendimento.objects.all()
    if usuario.papel == Usuario.Papel.PROFESSOR:
        # Inscritos em qualquer status, agora ou antes, numa trilha dele (A-09).
        return regras_trilhas.empreendimentos_atendidos(usuario)
    if usuario.papel == Usuario.Papel.EMPREENDEDOR:
        return Empreendimento.objects.filter(representante=usuario)
    return Empreendimento.objects.none()  # admin: RN-16


def pode_ver(usuario, empreendimento):
    """EMP-05; vale também para os contatos (3.3a.8)."""
    return empreendimentos_visiveis(usuario).filter(pk=empreendimento.pk).exists()


def exigir_edicao(usuario):
    """Spec 3.3.1 e 3.3a.5: só a IS edita os dados e os contatos; os demais recebem 403 (A-03)."""
    if not (usuario.is_authenticated and usuario.papel == Usuario.Papel.IS):
        raise PermissionDenied


def desativar(empreendimento, usuario):
    """EMP-06: desativa sem apagar dados, inscrições ou a conta do empreendimento."""
    exigir_edicao(usuario)
    if empreendimento.desativado_em is None:
        empreendimento.desativado_em = timezone.now()
        empreendimento.save(update_fields=['desativado_em'])


def reativar(empreendimento, usuario):
    """EMP-06: devolve o acesso sem alterar a conta nem as inscrições."""
    exigir_edicao(usuario)
    if empreendimento.desativado_em is not None:
        empreendimento.desativado_em = None
        empreendimento.save(update_fields=['desativado_em'])


# Contatos (EMP-07, spec 3.3a). Só a IS mexe neles (3.3a.5).

def _passar_responsabilidade(contato):
    """3.3a.4: desmarca o responsável atual antes de marcar o novo, para não violar o banco."""
    (Contato.objects
     .filter(empreendimento_id=contato.empreendimento_id, responsavel=True)
     .exclude(pk=contato.pk)
     .update(responsavel=False))


@transaction.atomic
def salvar_contato(usuario, form, empreendimento):
    """3.3a.3 e 3.3a.4: grava o contato do formulário; o servidor define o empreendimento.

    Salvo pelo formulário, o contato deixa de ser provisório (3.3a.9). Se vier marcado
    como responsável, o anterior deixa de ser (A-14).
    """
    exigir_edicao(usuario)
    contato = form.save(commit=False)
    contato.empreendimento = empreendimento
    contato.provisorio = False
    if contato.responsavel:
        _passar_responsabilidade(contato)
    contato.save()
    return contato


@transaction.atomic
def tornar_responsavel(usuario, contato):
    """3.3a.4 e A-14: o contato vira o responsável; o anterior continua na lista."""
    exigir_edicao(usuario)
    _passar_responsabilidade(contato)
    contato.responsavel = True
    contato.save(update_fields=['responsavel'])


def remover_contato(usuario, contato):
    """3.3a.7 e A-16d: o contato é apagado de vez. Sem ele, pode ficar sem responsável."""
    exigir_edicao(usuario)
    contato.delete()
