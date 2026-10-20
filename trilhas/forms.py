from django import forms

from empreendimentos.models import Empreendimento

from .models import Inscricao, Trilha

CLASSES_INPUT = (
    'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
    'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
    'placeholder:text-slate-400 transition duration-150'
)


class TrilhaForm(forms.ModelForm):
    """Formulário de criação de trilha personalizada pelo professor."""

    class Meta:
        model = Trilha
        fields = ['titulo', 'descricao']
        labels = {
            'titulo': 'Título',
            'descricao': 'Descrição',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'placeholder': 'Ex.: Gestão financeira básica',
                'autofocus': True,
                'class': CLASSES_INPUT,
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Objetivo da trilha e o que o empreendimento vai aprender',
                'rows': 5,
                'class': CLASSES_INPUT,
            }),
        }

    def clean_titulo(self):
        titulo = self.cleaned_data['titulo'].strip()
        if not titulo:
            raise forms.ValidationError('Informe um título.')
        return titulo


class InscricaoForm(forms.ModelForm):
    """IS inscreve um empreendimento ativo em uma trilha."""

    class Meta:
        model = Inscricao
        fields = ['empreendimento', 'trilha']
        widgets = {
            'empreendimento': forms.Select(attrs={'class': CLASSES_INPUT}),
            'trilha': forms.Select(attrs={'class': CLASSES_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['empreendimento'].queryset = (
            Empreendimento.objects.filter(desativado_em__isnull=True).order_by('nome')
        )
        self.fields['trilha'].queryset = Trilha.objects.order_by('titulo')

    def clean(self):
        cleaned = super().clean()
        empreendimento = cleaned.get('empreendimento')
        trilha = cleaned.get('trilha')
        if empreendimento and trilha:
            existe = (
                Inscricao.objects
                .filter(empreendimento=empreendimento, trilha=trilha)
                .exclude(status=Inscricao.Status.CANCELADA)
                .exists()
            )
            if existe:
                raise forms.ValidationError(
                    'Este empreendimento já está inscrito nesta trilha.'
                )
        return cleaned
