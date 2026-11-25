from django import forms

from usuarios.forms import CLASSES_INPUT

from .models import Empreendimento


class EmpreendimentoCadastroForm(forms.ModelForm):
    """ACE-05: dados do empreendimento informados ao criar o empreendedor (F1, decisão 7.1)."""

    class Meta:
        model = Empreendimento
        fields = ['nome', 'tipo', 'descricao', 'email_contato', 'telefone_contato']
        labels = {
            'nome': 'Nome do empreendimento',
            'tipo': 'Tipo',
            'descricao': 'Descrição',
            'email_contato': 'E-mail de contato do empreendimento',
            'telefone_contato': 'Telefone de contato do empreendimento',
        }
        help_texts = {
            # 3.1.2: o contato geral não é o login; o login é o e-mail da conta.
            'email_contato': 'Opcional. Não é usado para entrar no sistema.',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex.: Ateliê da Praça',
                'class': CLASSES_INPUT,
            }),
            # F2: o tipo passou a ser uma lista fechada (EMP-01).
            'tipo': forms.Select(attrs={'class': CLASSES_INPUT}),
            'descricao': forms.Textarea(attrs={
                'rows': 3,
                'class': CLASSES_INPUT,
            }),
            'email_contato': forms.EmailInput(attrs={
                'placeholder': 'Ex.: contato@atelie.com',
                'class': CLASSES_INPUT,
            }),
            'telefone_contato': forms.TextInput(attrs={
                'placeholder': 'Ex.: (55) 3220-0000',
                'class': CLASSES_INPUT,
            }),
        }


class EmpreendimentoForm(forms.ModelForm):
    """EMP-01 (spec 3.3): a IS edita os dados. A conta do empreendimento fica de fora (3.2.4, A-05)."""

    class Meta:
        model = Empreendimento
        fields = ['nome', 'tipo', 'descricao', 'email_contato', 'telefone_contato']
        widgets = {
            'nome': forms.TextInput(attrs={'class': CLASSES_INPUT}),
            'tipo': forms.Select(attrs={'class': CLASSES_INPUT}),
            'descricao': forms.Textarea(attrs={'rows': 4, 'class': CLASSES_INPUT}),
            'email_contato': forms.EmailInput(attrs={'class': CLASSES_INPUT}),
            'telefone_contato': forms.TextInput(attrs={'class': CLASSES_INPUT}),
        }
