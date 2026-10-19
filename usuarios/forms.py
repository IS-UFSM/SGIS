from django import forms
from django.contrib.auth import authenticate


class LoginForm(forms.Form):
    """Formulário de login por email e senha."""

    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={
            'placeholder': 'seu@email.com',
            'autofocus': True,
            'autocomplete': 'email',
            'class': (
                'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
                'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
                'placeholder:text-slate-400 transition duration-150'
            ),
        }),
    )
    senha = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Sua senha',
            'autocomplete': 'current-password',
            'class': (
                'w-full px-3.5 py-2.5 text-slate-800 bg-slate-50 border border-slate-300 '
                'rounded-lg focus:outline-none focus:border-brand focus:ring-4 focus:ring-brand/10 '
                'placeholder:text-slate-400 transition duration-150'
            ),
        }),
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        email = cleaned.get('email')
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
