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
    pre_incubacao = models.BooleanField(
        'trilha de pré-incubação',
        default=False,
        help_text='Novos empreendimentos são inscritos automaticamente nesta trilha.',
    )

    class Meta:
        verbose_name = 'trilha'
        verbose_name_plural = 'trilhas'
        constraints = [
            models.UniqueConstraint(
                fields=['pre_incubacao'],
                condition=models.Q(pre_incubacao=True),
                name='trilha_pre_incubacao_unica',
            ),
        ]

    def __str__(self):
        return self.titulo


class Inscricao(models.Model):
    """Inscrição de um empreendimento em uma trilha, feita pela IS."""

    class Status(models.TextChoices):
        ATIVA = 'ativa', 'Ativa'
        PAUSADA = 'pausada', 'Pausada'
        CANCELADA = 'cancelada', 'Cancelada'

    empreendimento = models.ForeignKey(
        'empreendimentos.Empreendimento',
        on_delete=models.PROTECT,
        related_name='inscricoes',
        verbose_name='empreendimento',
    )
    trilha = models.ForeignKey(
        Trilha,
        on_delete=models.PROTECT,
        related_name='inscricoes',
        verbose_name='trilha',
    )
    status = models.CharField(
        'status', max_length=10, choices=Status.choices, default=Status.ATIVA,
    )
    inscrito_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='inscricoes_realizadas',
        verbose_name='inscrito por',
        help_text='Vazio = inscrição automática feita pelo sistema.',
    )
    inscrito_em = models.DateTimeField('inscrito em', auto_now_add=True)
    pausado_em = models.DateTimeField('pausado em', null=True, blank=True)
    cancelado_em = models.DateTimeField('cancelado em', null=True, blank=True)
    motivo = models.TextField('motivo', blank=True)

    class Meta:
        verbose_name = 'inscrição'
        verbose_name_plural = 'inscrições'
        constraints = [
            # Só uma inscrição não cancelada por empreendimento e trilha.
            models.UniqueConstraint(
                fields=['empreendimento', 'trilha'],
                condition=~models.Q(status='cancelada'),
                name='inscricao_unica_nao_cancelada',
            ),
        ]

    def __str__(self):
        return f'{self.empreendimento} → {self.trilha}'
