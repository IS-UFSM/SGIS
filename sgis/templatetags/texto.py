"""Filtros de exibição do texto formatado (TXT-01, RN-19). Uso: `{% load texto %}`."""

import html

from django import template
from django.utils.html import strip_tags

from sgis.texto import html_seguro

register = template.Library()


@register.filter
def texto_formatado(valor):
    """RN-19: limpa de novo ao exibir, o que protege também dados antigos ou gravados por fora."""
    return html_seguro(valor)


@register.filter
def texto_resumo(valor, tamanho=160):
    """Texto sem marcações e cortado, para cartões e listas. O template escapa a saída."""
    texto = ' '.join(html.unescape(strip_tags(valor or '')).split())
    tamanho = int(tamanho)
    if len(texto) <= tamanho:
        return texto
    return texto[:tamanho - 1].rstrip() + '…'
