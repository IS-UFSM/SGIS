from django.db import migrations


def criar_usuario_is_padrao(apps, schema_editor):
    from django.contrib.auth.hashers import make_password

    Usuario = apps.get_model('usuarios', 'Usuario')
    email = 'is@sgis.com'
    if not Usuario.objects.filter(email=email).exists():
        Usuario.objects.create(
            email=email,
            nome='Incubadora Social Padrão',
            papel='is',
            password=make_password('is123456'),
            is_active=True,
            is_staff=False,
        )


def reverter_usuario_is_padrao(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(email='is@sgis.com').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(criar_usuario_is_padrao, reverter_usuario_is_padrao),
    ]
