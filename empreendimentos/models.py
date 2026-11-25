from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from usuarios.models import Usuario


class Empreendimento(models.Model):
    """Empreendimento acompanhado pela incubadora."""

    class Tipo(models.TextChoices):
        """EMP-01: lista fechada (decisão 7.1 converte os tipos em texto livre)."""

        MEI = 'mei', 'MEI'
        ASSOCIACAO = 'associacao', 'Associação'
        COLETIVO = 'coletivo', 'Coletivo'
        OUTRO = 'outro', 'Outro'

    nome = models.CharField('nome', max_length=200)
    tipo = models.CharField('tipo', max_length=20, choices=Tipo.choices)
    descricao = models.TextField('descrição', blank=True)
    # 3.1.2: contato geral do empreendimento; as pessoas ficam nos contatos (T7).
    email_contato = models.EmailField('e-mail de contato', blank=True)
    telefone_contato = models.CharField('telefone de contato', max_length=30, blank=True)
    desativado_em = models.DateTimeField(
        'desativado em',
        null=True,
        blank=True,
        help_text='Nulo = ativo. Preenchido = data da desativação.',
    )
    # RN-01 e RN-02: uma única conta por empreendimento, e cada conta representa um só.
    representante = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='empreendimento',
        verbose_name='conta do empreendimento',
        help_text='Conta de empreendedor, compartilhada pelas pessoas do empreendimento.',
    )

    class Meta:
        verbose_name = 'empreendimento'
        verbose_name_plural = 'empreendimentos'

    def __str__(self):
        return self.nome

    def clean(self):
        """RN-01: só uma conta de empreendedor pode ser representante (A-04)."""
        super().clean()
        if self.representante_id and self.representante.papel != Usuario.Papel.EMPREENDEDOR:
            raise ValidationError({'representante': ValidationError(
                'Só uma conta de empreendedor pode representar um empreendimento.',
                code='papel_invalido',
            )})

    @property
    def ativo(self):
        return self.desativado_em is None


class Contato(models.Model):
    """EMP-07 (spec 3.3a): meio de falar com o empreendimento. Sem login e sem vínculo com usuário."""

    # Não é registro de negócio: é apagado de vez (3.3a.7). O empreendimento nunca é apagado,
    # então o CASCADE só diz que o contato pertence a ele (plano da F2, seção 2a).
    empreendimento = models.ForeignKey(
        Empreendimento,
        on_delete=models.CASCADE,
        related_name='contatos',
        verbose_name='empreendimento',
    )
    nome = models.CharField('nome', max_length=200)
    funcao = models.CharField('função', max_length=100, blank=True)
    email = models.EmailField('e-mail')
    telefone = models.CharField('telefone', max_length=30)
    responsavel = models.BooleanField('responsável', default=False)
    # 3.3a.9: criado pela migração, com e-mail e telefone vazios, para a IS preencher.
    provisorio = models.BooleanField('provisório', default=False)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'contato'
        verbose_name_plural = 'contatos'
        ordering = ['-responsavel', 'nome']
        constraints = [
            # 3.3a.4: no máximo um responsável, garantido pelo banco.
            models.UniqueConstraint(
                fields=['empreendimento'],
                condition=Q(responsavel=True),
                name='um_responsavel_por_empreendimento',
            ),
        ]

    def __str__(self):
        return self.nome
