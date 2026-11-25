"""F2 · T8: a descrição em texto simples vira HTML (TXT-01; plano da F2, seções 3 e 7a).

`linebreaks(escape(texto))` mantém as quebras de linha como parágrafos e `<br>`. A reversa
desfaz isso e devolve texto simples. Descrições que já são HTML ficam como estão.
"""

import html
import re

from django.db import migrations
from django.utils.html import escape, linebreaks, strip_tags

TEM_MARCACAO = re.compile(r'</?[a-zA-Z][^>]*>')


def para_html(apps, schema_editor):
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
    for empreendimento in Empreendimento.objects.exclude(descricao=''):
        if TEM_MARCACAO.search(empreendimento.descricao):
            continue
        empreendimento.descricao = linebreaks(escape(empreendimento.descricao))
        empreendimento.save(update_fields=['descricao'])


def para_texto(apps, schema_editor):
    Empreendimento = apps.get_model('empreendimentos', 'Empreendimento')
    for empreendimento in Empreendimento.objects.exclude(descricao=''):
        texto = empreendimento.descricao
        texto = re.sub(r'</p>\s*<p>', '\n\n', texto)
        texto = re.sub(r'<br\s*/?>', '\n', texto)
        texto = re.sub(r'</(div|li)>', '\n', texto)
        texto = html.unescape(strip_tags(texto)).strip()
        empreendimento.descricao = texto
        empreendimento.save(update_fields=['descricao'])


class Migration(migrations.Migration):

    dependencies = [
        ('empreendimentos', '0006_tipo_representante_unico'),
    ]

    operations = [
        migrations.RunPython(para_html, para_texto),
    ]
