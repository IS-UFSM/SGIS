from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models


class UsuarioManager(BaseUserManager):
    """Manager que usa email em vez de username."""

    def create_user(self, email, nome, senha=None, **extra_fields):
        if not email:
            raise ValueError('O email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, nome=nome, **extra_fields)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, senha=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('papel', Usuario.Papel.ADMIN)
        return self.create_user(email, nome, senha, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """Usuário do sistema. Login feito por email."""

    class Papel(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        IS = 'is', 'Incubadora Social'
        PROFESSOR = 'professor', 'Professor'
        EMPREENDIMENTO = 'empreendimento', 'Empreendimento'

    email = models.EmailField('email', unique=True)
    nome = models.CharField('nome', max_length=150)
    papel = models.CharField('papel', max_length=20, choices=Papel.choices)
    is_active = models.BooleanField('ativo', default=True)
    is_staff = models.BooleanField('acesso ao admin', default=False)

    objects = UsuarioManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        verbose_name = 'usuário'
        verbose_name_plural = 'usuários'

    def __str__(self):
        return self.nome
