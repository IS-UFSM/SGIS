import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Renomeia usuario_empreendimento → representante, preservando os vínculos."""

    dependencies = [
        ('empreendimentos', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RenameField(
            model_name='empreendimento',
            old_name='usuario_empreendimento',
            new_name='representante',
        ),
        migrations.AlterField(
            model_name='empreendimento',
            name='representante',
            field=models.ForeignKey(
                help_text='Empreendedor responsável pelo empreendimento.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='empreendimentos',
                to=settings.AUTH_USER_MODEL,
                verbose_name='representante',
            ),
        ),
    ]
