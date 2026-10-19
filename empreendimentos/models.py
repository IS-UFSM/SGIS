from django.conf import settings
from django.db import models


class Empreendimento(models.Model):
    """Empreendimento acompanhado pela incubadora."""

    nome = models.CharField('nome', max_length=200)
    tipo = models.CharField('tipo', max_length=100)
    descricao = models.TextField('descrição', blank=True)
    desativado_em = models.DateTimeField(
        'desativado em',
        null=True,
        blank=True,
        help_text='Nulo = ativo. Preenchido = data da desativação.',
    )
    usuario_empreendimento = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='empreendimentos',
        verbose_name='empreendedor',
    )
    usuario_professor_supervisor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='empreendimentos_supervisionados',
        verbose_name='professor supervisor',
    )

    class Meta:
        verbose_name = 'empreendimento'
        verbose_name_plural = 'empreendimentos'

    def __str__(self):
        return self.nome

    @property
    def ativo(self):
        return self.desativado_em is None
