from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

from .models import Usuario

CLASSES_INPUT = (
    'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
    'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
    'placeholder:text-slate-400 transition duration-150'
)


def normalizar_email(email):
    """Emails são guardados e comparados sempre em minúsculas."""
    return (email or '').strip().lower()


class LoginForm(forms.Form):
    """Formulário de login por email e senha."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu@email.com',
            'autofocus': True,
            'autocomplete': 'email',
            'class': CLASSES_INPUT,
        }),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Sua senha',
            'autocomplete': 'current-password',
            'class': CLASSES_INPUT,
        }),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = normalizar_email(cleaned.get('email'))
        senha = cleaned.get('senha')

        if email and senha:
            self.user_cache = authenticate(
                self.request, username=email, password=senha,
            )
            if self.user_cache is None:
                raise forms.ValidationError('Email ou senha incorretos.')
            if not self.user_cache.is_active:
                raise forms.ValidationError('Esta conta está desativada.')

        return cleaned

    def get_user(self):
        return self.user_cache


class UsuarioCadastroForm(forms.ModelForm):
    """IS cria um usuário professor ou de empreendimento.

    O papel é limitado aos dois perfis que a IS pode criar; mesmo
    manipulando o POST, admin e IS não passam pela validação.
    """

    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Senha inicial do usuário',
            'autocomplete': 'new-password',
            'class': CLASSES_INPUT,
        }),
    )

    class Meta:
        model = Usuario
        fields = ['nome', 'email', 'papel']
        labels = {
            'nome': 'Nome completo',
            'papel': 'Perfil',
        }
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Ex.: Maria da Silva',
                'autofocus': True,
                'class': CLASSES_INPUT,
            }),
            'email': forms.EmailInput(attrs={
                'placeholder': 'seu@email.com',
                'autocomplete': 'email',
                'class': CLASSES_INPUT,
            }),
            'papel': forms.Select(attrs={'class': CLASSES_INPUT}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        papeis_is = (Usuario.Papel.PROFESSOR, Usuario.Papel.EMPREENDIMENTO)
        self.fields['papel'].choices = [
            c for c in Usuario.Papel.choices if c[0] in papeis_is
        ]

    def clean_email(self):
        email = normalizar_email(self.cleaned_data['email'])
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Já existe um usuário com este email.')
        return email

    def clean(self):
        cleaned = super().clean()
        senha = cleaned.get('senha')
        if senha:
            usuario = Usuario(
                nome=cleaned.get('nome', ''),
                email=cleaned.get('email', ''),
            )
            try:
                validate_password(senha, user=usuario)
            except forms.ValidationError as erro:
                self.add_error('senha', erro)
        return cleaned

    def save(self, commit=True):
        """Cria o usuário com a senha já criptografada."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['senha'])
        if commit:
            user.save()
        return user