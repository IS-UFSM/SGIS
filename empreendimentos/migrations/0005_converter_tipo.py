import re

from django.db import migrations

# EMP-01, decisão 7.1 da F2: os tipos em texto livre viram "outro", e o texto
# antigo vai para o fim da descrição, numa linha que a reversa sabe encontrar.
TIPOS_VALIDOS = {'mei', 'associacao', 'coletivo', 'outro'}
PREFIXO = 'Tipo anterior: '
LINHA_FINAL = re.compile(r'(?:\n*)' + re.escape(PREFIXO) + r'(?P<tipo>[^\n]*)\Z')


def converter_tipo(apps, schema_editor):
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
    for empreendimento in Empreendimento.objects.exclude(tipo__in=TIPOS_VALIDOS):
        linha = PREFIXO + empreendimento.tipo
        descricao = empreendimento.descricao.rstrip()
        empreendimento.descricao = f'{descricao}\n\n{linha}' if descricao else linha
        empreendimento.tipo = 'outro'
        empreendimento.save(update_fields=['tipo', 'descricao'])


def restaurar_tipo(apps, schema_editor):
    """Só age onde encontra a linha no fim da descrição; os demais ficam em "outro"."""
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
    for empreendimento in Empreendimento.objects.filter(tipo='outro', descricao__contains=PREFIXO):
        achado = LINHA_FINAL.search(empreendimento.descricao)
        if not achado:
            continue
        empreendimento.tipo = achado.group('tipo')
        empreendimento.descricao = empreendimento.descricao[:achado.start()]
        empreendimento.save(update_fields=['tipo', 'descricao'])


class Migration(migrations.Migration):

    dependencies = [
        ('empreendimentos', '0004_email_telefone_contato'),
    ]

    operations = [
        migrations.RunPython(converter_tipo, restaurar_tipo),
    ]
