"""Regras da F1 · Acesso e contas (specs/F1-acesso/spec.md, seção 3).

As views e o /admin/ só chamam estas funções, para que as regras fiquem num lugar só (Art. 7.5).
"""

from django.db import transaction

from empreendimentos.models import Empreendimento

from .models import Usuario


def criar_conta(dados_conta, senha):
    """3.3: cria a conta com troca de senha obrigatória (3.3.5)."""
    conta = Usuario(**dados_conta, deve_trocar_senha=True)
    conta.set_password(senha)
    conta.save()
    return conta


@transaction.atomic
def criar_empreendedor(dados_conta, senha, dados_empreendimento):
    """3.3.4 e RN-01: o empreendedor e o empreendimento são criados juntos, ou nenhum."""
    conta = criar_conta({**dados_conta, 'papel': Usuario.Papel.EMPREENDEDOR}, senha)
    vincular_empreendimento(conta, dados_empreendimento)
    return conta


def vincular_empreendimento(conta, dados_empreendimento):
    """3.3.4: o empreendimento novo entra na pré-incubação pelo signal da F4."""
    return Empreendimento.objects.create(representante=conta, **dados_empreendimento)
