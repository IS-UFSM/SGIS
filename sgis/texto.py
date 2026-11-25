"""Texto formatado (TXT-01, RN-19): limpeza do HTML e campo com o mini editor.

Peça comum a todas as features (plano da F2, seção 7a). O editor (Trix) só ajuda a
escrever; a proteção é `limpar_html`, que roda no servidor ao gravar e ao exibir.
"""

import re

import nh3
from django import forms
from django.utils.html import escape, format_html, linebreaks
from django.utils.safestring import mark_safe

# TXT-01: negrito, itálico, lista, link e parágrafo. O Trix usa `div` e `br` nos parágrafos.
MARCACOES = {'p', 'div', 'br', 'strong', 'b', 'em', 'i', 'ul', 'ol', 'li', 'a'}
ATRIBUTOS = {'a': {'href'}, '*': set()}  # '*' vazio: nem os atributos genéricos (title, lang)
ESQUEMAS = {'http', 'https', 'mailto'}

_TEM_MARCACAO = re.compile(r'</?[a-zA-Z][^>]*>')


def limpar_html(html):
    """RN-19: só as marcações de TXT-01 sobrevivem; links abrem em nova aba."""
    if not html:
        return ''
    return nh3.clean(
        html,
        tags=MARCACOES,
        clean_content_tags={'script', 'style'},  # some a marcação e o conteúdo
        attributes=ATRIBUTOS,
        url_schemes=ESQUEMAS,
        set_tag_attribute_values={'a': {'target': '_blank'}},
        link_rel='noopener noreferrer',
        strip_comments=True,
    ).strip()


def texto_para_html(texto):
    """Texto simples vira parágrafos, sem perder as quebras de linha.

    Usado quando o valor chega sem o editor (no /admin/ ou com o CDN fora do ar) e
    na migração dos textos antigos.
    """
    return linebreaks(escape(texto)) if texto else ''


class EditorTexto(forms.Widget):
    """Campo oculto com o valor e o editor Trix ligado a ele (TXT-01)."""

    # O valor vai num campo oculto, mas o campo aparece na tela com rótulo e erros.
    is_hidden = False

    def render(self, name, value, attrs=None, renderer=None):
        id_campo = (attrs or {}).get('id') or self.attrs.get('id') or f'id_{name}'
        return format_html(
            '<input type="hidden" name="{}" id="{}" value="{}">'
            '<trix-editor input="{}" class="texto-formatado trix-sgis" '
            'aria-label="{}"></trix-editor>',
            name, id_campo, value or '', id_campo, self.attrs.get('aria-label', 'Texto'),
        )

    def value_from_datadict(self, data, files, name):
        return data.get(name)


class TextoFormatadoField(forms.CharField):
    """CharField cujo valor limpo é HTML seguro (RN-19)."""

    widget = EditorTexto

    def to_python(self, value):
        valor = super().to_python(value)
        if valor and not _TEM_MARCACAO.search(valor):
            valor = texto_para_html(valor)
        return limpar_html(valor)


def html_seguro(html):
    """Limpa de novo e marca como seguro, para exibir (RN-19: antes de exibir também)."""
    return mark_safe(limpar_html(html))
