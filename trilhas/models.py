from django.conf import settings
from django.db import models


class Trilha(models.Model):
    """Trilha de atividades — padrão (IS) ou personalizada (professor)."""

    class Tipo(models.TextChoices):
        PADRAO = 'padrao', 'Padrão'
        CUSTOM = 'custom', 'Personalizada'

    titulo = models.CharField('título', max_length=200)
    descricao = models.TextField('descrição', blank=True)
    tipo = models.CharField('tipo', max_length=10, choices=Tipo.choices)
    usuario_criador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='trilhas_criadas',
        verbose_name='criador',
    )

    class Meta:
        verbose_name = 'trilha'
        verbose_name_plural = 'trilhas'

    def __str__(self):
        return self.titulo
