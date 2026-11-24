import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """EMP-01, EMP-02, RN-01 a RN-03 (F2).

    Falha se uma conta representar dois empreendimentos: a produção é
    consultada antes (plano da F2, seção 10). Os supervisores removidos não
    voltam na reversa.
    """

    dependencies = [
        ('empreendimentos', '0005_converter_tipo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='empreendimento',
            name='tipo',
            field=models.CharField(
                choices=[
                    ('mei', 'MEI'),
                    ('associacao', 'Associação'),
                    ('coletivo', 'Coletivo'),
                    ('outro', 'Outro'),
                ],
                max_length=20,
                verbose_name='tipo',
            ),
        ),
        migrations.AlterField(
            model_name='empreendimento',
            name='representante',
            field=models.OneToOneField(
                help_text='Conta de empreendedor, compartilhada pelas pessoas do empreendimento.',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='empreendimento',
                to=settings.AUTH_USER_MODEL,
                verbose_name='conta do empreendimento',
            ),
        ),
        migrations.RemoveField(
            model_name='empreendimento',
            name='usuario_professor_supervisor',
        ),
    ]
