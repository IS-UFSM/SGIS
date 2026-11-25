from django import forms

from sgis.texto import TextoFormatadoField
from usuarios.forms import CLASSES_INPUT

from .models import Contato, Empreendimento


class EmpreendimentoCadastroForm(forms.ModelForm):
    """ACE-05: dados do empreendimento informados ao criar o empreendedor (F1, decisão 7.1)."""

    descricao = TextoFormatadoField(label='Descrição', required=False)  # TXT-01

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

    descricao = TextoFormatadoField(label='Descrição', required=False)  # TXT-01

    class Meta:
        model = Empreendimento
        fields = ['nome', 'tipo', 'descricao', 'email_contato', 'telefone_contato']
        widgets = {
            'nome': forms.TextInput(attrs={'class': CLASSES_INPUT}),
            'tipo': forms.Select(attrs={'class': CLASSES_INPUT}),
            'email_contato': forms.EmailInput(attrs={'class': CLASSES_INPUT}),
            'telefone_contato': forms.TextInput(attrs={'class': CLASSES_INPUT}),
        }


class ContatoForm(forms.ModelForm):
    """EMP-07 (spec 3.3a.3): nome, e-mail e telefone obrigatórios; função opcional.

    `empreendimento` e `provisorio` ficam de fora: o servidor define (A-13, A-16b).
    """

    class Meta:
        model = Contato
        fields = ['nome', 'funcao', 'email', 'telefone', 'responsavel']
        labels = {
            'nome': 'Nome',
            'funcao': 'Função',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'responsavel': 'Responsável pelo empreendimento',
        }
        help_texts = {
            'nome': 'Uma pessoa, um setor ou um e-mail geral. O contato não entra no sistema.',
            'funcao': 'Opcional. Ex.: presidente, tesoureira.',
            'responsavel': 'Se marcado, o responsável atual deixa de ser.',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Ex.: Maria Souza', 'class': CLASSES_INPUT}),
            'funcao': forms.TextInput(attrs={'placeholder': 'Ex.: presidente', 'class': CLASSES_INPUT}),
            'email': forms.EmailInput(attrs={'placeholder': 'Ex.: maria@atelie.com', 'class': CLASSES_INPUT}),
            'telefone': forms.TextInput(attrs={'placeholder': 'Ex.: (55) 99999-0000', 'class': CLASSES_INPUT}),
            'responsavel': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 rounded border-slate-300 text-brand focus:ring-brand',
            }),
        }


class ContatoCriacaoForm(ContatoForm):
    """3.3a.6: bloco opcional do responsável na criação do empreendedor pela IS.

    Em branco, nada é criado; com qualquer campo preenchido, os obrigatórios valem.
    Já vem marcado como responsável (plano da F2, seção 5), e essa marca sozinha não
    conta como preenchimento.
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('prefix', 'contato')
        kwargs.setdefault('initial', {'responsavel': True})
        super().__init__(*args, empty_permitted=True, use_required_attribute=False, **kwargs)
        self.fields['responsavel'].help_text = ''

    def has_changed(self):
        return any(name in self.changed_data for name in ('nome', 'funcao', 'email', 'telefone'))
