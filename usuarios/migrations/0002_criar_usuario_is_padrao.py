import os

from django.db import migrations


def criar_usuario_is_padrao(apps, schema_editor):
    """Cria a conta inicial da IS.

    Em produção, email e senha vêm de IS_EMAIL e IS_SENHA_INICIAL; sem a senha,
    a conta não é criada. Localmente usa a senha de desenvolvimento.
    """
    from django.contrib.auth.hashers import make_password

    Usuario = apps.get_model('usuarios', 'Usuario')
    email = os.environ.get('IS_EMAIL', 'is@sgis.com')
    senha = os.environ.get('IS_SENHA_INICIAL')
    if not senha:
        if 'RENDER' in os.environ:
            print('\n  IS_SENHA_INICIAL não definida: usuário IS padrão não foi criado.')
            return
        senha = 'is123456'

    if not Usuario.objects.filter(email=email).exists():
        Usuario.objects.create(
            email=email,
            nome='Incubadora Social Padrão',
            papel='is',
            password=make_password(senha),
            is_active=True,
            is_staff=False,
        )


def reverter_usuario_is_padrao(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(email=os.environ.get('IS_EMAIL', 'is@sgis.com')).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_usuario_is_padrao, reverter_usuario_is_padrao),
    ]
