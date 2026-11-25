"""Regras dos empreendimentos: quem vê e quem edita.

F2 · Empreendimentos (specs/F2-empreendimentos/spec.md, seção 3). As views só chamam
estas funções. Falta de permissão vira `PermissionDenied` (403).
"""

from django.core.exceptions import PermissionDenied

from trilhas import regras as regras_trilhas
from usuarios.models import Usuario

from .models import Empreendimento


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
