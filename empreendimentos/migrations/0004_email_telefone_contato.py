from django.db import migrations, models


class Migration(migrations.Migration):
    """EMP-01: e-mail e telefone de contato geral do empreendimento (F2, 3.1)."""

    dependencies = [
        ('empreendimentos', '0003_renomeia_representante'),
    ]

    operations = [
        migrations.AddField(
            model_name='empreendimento',
            name='email_contato',
            field=models.EmailField(blank=True, max_length=254, verbose_name='e-mail de contato'),
        ),
        migrations.AddField(
            model_name='empreendimento',
            name='telefone_contato',
            field=models.CharField(blank=True, max_length=30, verbose_name='telefone de contato'),
        ),
    ]
