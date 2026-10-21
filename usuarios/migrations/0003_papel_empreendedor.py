from django.db import migrations, models


def para_empreendedor(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(papel='empreendimento').update(papel='empreendedor')


def para_empreendimento(apps, schema_editor):
    Usuario = apps.get_model('usuarios', 'Usuario')
    Usuario.objects.filter(papel='empreendedor').update(papel='empreendimento')


class Migration(migrations.Migration):
    """Papel 'empreendimento' passa a se chamar 'empreendedor' (a pessoa, não o negócio)."""

    dependencies = [
        ('usuarios', '0002_criar_usuario_is_padrao'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='papel',
            field=models.CharField(
                choices=[
                    ('admin', 'Administrador'),
                    ('is', 'Incubadora Social'),
                    ('professor', 'Professor'),
                    ('empreendedor', 'Empreendedor'),
                ],
                max_length=20,
                verbose_name='papel',
            ),
        ),
        migrations.RunPython(para_empreendedor, para_empreendimento),
    ]
