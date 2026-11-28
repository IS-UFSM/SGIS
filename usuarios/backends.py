from django.contrib.auth.backends import ModelBackend

from empreendimentos.models import Empreendimento


class SgisBackend(ModelBackend):
    """EMP-06: a conta de empreendimento desativado não entra no sistema."""

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        return not Empreendimento.objects.filter(
            representante=user,
            desativado_em__isnull=False,
        ).exists()
