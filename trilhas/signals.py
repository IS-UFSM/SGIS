import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from empreendimentos.models import Empreendimento

from . import regras

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Empreendimento)
def inscrever_na_pre_incubacao(sender, instance, created, raw=False, **kwargs):
    """INS-02: todo empreendimento novo entra na Pré-incubação, se ela estiver publicada."""
    if not created or raw:
        return

    if regras.trilha_pre_incubacao() is None:
        logger.warning(
            'Nenhuma trilha de pré-incubação definida; %s não foi inscrito.', instance,
        )
        return

    regras.inscrever_na_pre_incubacao(instance)  # em rascunho, fica sem etapa (3.3.2)
