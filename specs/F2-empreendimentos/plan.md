# F2 · Empreendimentos — plan

**Estado:** rascunho (revisão para a spec v0.5; a versão anterior foi aprovada em 2026-11-04) · **Data:** 2026-11-24
**Spec:** [`spec.md`](spec.md) (aprovada em 2026-11-24) · **Constituição:** [`../00-constituicao.md`](../00-constituicao.md) · **Situação atual:** [`../levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md) · **Depende de:** [`F1-acesso/plan.md`](../F1-acesso/plan.md) e [`F4-inscricao/plan.md`](../F4-inscricao/plan.md)

Como implementar a F2 no código atual. Nenhuma regra nova: onde este plano precisa de uma decisão técnica, ela está marcada como **Decisão de plano**.

**Ordem:** a F2 vem depois da F1, que cria o formulário de empreendedor, e da F4 (decisão 7.9 da F4), que traz a etapa atual.

**O que mudou na revisão v0.5:** contatos com responsável (seções 2a, 3, 4, 5, 6 e 9), texto formatado na descrição (seção 7a) e o termo "conta do empreendimento" nas telas (seção 8). As migrações foram renumeradas, porque nenhuma delas tinha sido feita.

---

## 1. Visão geral

| Camada | Arquivo | O que muda |
|---|---|---|
| Models | `empreendimentos/models.py` | Tipo em lista, e-mail e telefone gerais, representante único, sem supervisor; model `Contato` (**novo**) |
| Migrações | `empreendimentos/migrations/0004` a `0009` | Esquema novo, conversão do tipo, contatos provisórios e descrição em HTML |
| Regras | `empreendimentos/regras.py` (**novo**) | Quem vê, quem edita, desativar e reativar, contatos |
| Etapa na lista | `trilhas/regras.py` | `anotar_etapa_atual`, para calcular a etapa numa consulta só |
| Texto formatado | `sgis/texto.py` e `sgis/templatetags/texto.py` (**novos**) | Limpeza do HTML, campo com editor e filtro de exibição, para todas as features |
| Forms | `empreendimentos/forms.py` | Campos novos, `EmpreendimentoForm` para editar, `ContatoForm` |
| Views e URLs | `empreendimentos/views.py`, `empreendimentos/urls.py` (**novo**) | Lista, perfil, edição, desativação, contatos |
| Login | `usuarios/backends.py` (**novo**), `sgis/settings.py` | Conta de empreendimento desativado não entra |
| Templates | `empreendimentos/templates/empreendimentos/` (**novo**) | Lista, perfil, edição, contato, confirmação de remoção |
| Outros | `popular_banco`, cabeçalho, `trilhas/etapa.html`, `base.html` | Sem supervisor; links novos; editor de texto |
| Testes | `empreendimentos/tests.py`, `sgis/tests.py` | A-01 a A-16d e limpeza do HTML |

**Dependências novas** (Art. 7.3):

| Dependência | Onde | Por quê |
|---|---|---|
| `nh3` (Python) | `requirements.txt` | Limpar o HTML do texto formatado no servidor (RN-19). Sem isso, um `<script>` ou um `onclick` enviado no formulário chegaria à tela de outras pessoas (XSS). É mantida, rápida e substitui o `bleach`, que foi descontinuado. Escrever um limpador próprio seria inseguro. |
| Trix (JavaScript, por CDN) | `base.html` | O mini editor de TXT-01. Vem por CDN, como o Tailwind, sem npm nem build. É só um componente de edição: a página continua renderizada no servidor (Art. 7.2). Versão exata fixada na tarefa T8. |

---

## 2. Model `Empreendimento`

```python
class Empreendimento(models.Model):
    class Tipo(models.TextChoices):
        MEI = 'mei', 'MEI'
        ASSOCIACAO = 'associacao', 'Associação'
        COLETIVO = 'coletivo', 'Coletivo'
        OUTRO = 'outro', 'Outro'

    nome = models.CharField('nome', max_length=200)
    tipo = models.CharField('tipo', max_length=20, choices=Tipo.choices)
    descricao = models.TextField('descrição', blank=True)          # HTML limpo (seção 7a)
    email_contato = models.EmailField('e-mail de contato', blank=True)
    telefone_contato = models.CharField('telefone de contato', max_length=30, blank=True)
    desativado_em = models.DateTimeField(...)                     # sem mudança
    representante = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='empreendimento', verbose_name='conta do empreendimento',
    )

    def clean(self):
        # RN-01: só uma conta de empreendedor pode ser representante (A-04).
        ...
```

- `usuario_professor_supervisor` sai (RN-03).
- `OneToOneField` garante no banco que uma conta de empreendedor representa só um empreendimento (RN-01, A-04).
- O papel da conta não cabe numa restrição do banco, porque está em outra tabela. Quem garante é `Empreendimento.clean` e `usuarios.regras.vincular_empreendimento`, único caminho de criação, pela tela da IS e pelo `/admin/` (3.2.1).
- `email_contato` e `telefone_contato` são o **contato geral** do empreendimento (3.1.2). As pessoas ficam em `Contato`.
- Nenhum código usa o `related_name` antigo `empreendimentos`; as consultas filtram por `representante`.

## 2a. Model `Contato` (**novo**, EMP-07)

```python
class Contato(models.Model):
    empreendimento = models.ForeignKey(
        Empreendimento, on_delete=models.CASCADE,
        related_name='contatos', verbose_name='empreendimento',
    )
    nome = models.CharField('nome', max_length=200)
    funcao = models.CharField('função', max_length=100, blank=True)
    email = models.EmailField('e-mail')
    telefone = models.CharField('telefone', max_length=30)
    responsavel = models.BooleanField('responsável', default=False)
    provisorio = models.BooleanField('provisório', default=False)
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        ordering = ['-responsavel', 'nome']
        constraints = [
            models.UniqueConstraint(
                fields=['empreendimento'], condition=Q(responsavel=True),
                name='um_responsavel_por_empreendimento',
            ),
        ]
```

- **Sem vínculo com `Usuario`** (3.3a.1, decisão 7.11): o contato não tem chave para a tabela de usuários.
- `nome`, `email` e `telefone` não têm `blank=True`, então todo formulário os exige (3.3a.3, A-16b). `funcao` é opcional.
- **No máximo um responsável** (3.3a.4): garantido pela restrição condicional no banco, não só pela tela.
- `provisorio` marca o contato criado pela migração (3.3a.9). Ele é o único com e-mail e telefone vazios: o banco aceita texto vazio, e só a migração o grava assim. Ao ser salvo pelo formulário, `provisorio` volta a `False`.

**Decisão de plano · `CASCADE` em vez de `PROTECT`.** O contato não é registro de negócio e é apagado de vez (3.3a.7, decisão 7.8). O empreendimento, esse sim, nunca é apagado (Art. 4.1), então o `CASCADE` nunca dispara na prática; ele só expressa que o contato pertence ao empreendimento.

---

## 3. Migrações

| Migração | Tipo | Conteúdo | Reversa |
|---|---|---|---|
| `0004_email_telefone_contato` | Esquema | `AddField` de `email_contato` e `telefone_contato` | Automática |
| `0005_converter_tipo` | Dados | Todo tipo em texto livre vira `outro`, com o texto antigo no fim da descrição, em uma linha `Tipo anterior: <texto>` (decisão 7.1) | Devolve o texto ao tipo e remove essa linha |
| `0006_tipo_representante_unico` | Esquema | `AlterField` de `tipo` com a lista; `AlterField` de `representante` para `OneToOneField`; `RemoveField` de `usuario_professor_supervisor` | Automática; os supervisores removidos não voltam |
| `0007_contato` | Esquema | `CreateModel` de `Contato`, com a restrição de um responsável | Automática |
| `0008_contato_provisorio` | Dados | Cada empreendimento existente ganha um contato `nome='A definir'`, e-mail e telefone vazios, `responsavel=True`, `provisorio=True` (3.3a.9, decisão 7.9) | Apaga só os contatos com `provisorio=True` |
| `0009_descricao_html` | Dados | A descrição em texto simples vira HTML: `linebreaks(escape(texto))`, para não perder as quebras de linha (seção 7a) | `strip_tags` e `html.unescape`, devolvendo texto simples |

A `0006` falha se um usuário representar dois empreendimentos (seção 10). A `0005` roda antes da `0009`, então a linha `Tipo anterior` também vira um parágrafo.

**A testar à mão antes do PR** (Art. 7.4): rodar as migrações para frente e para trás numa cópia do `db.sqlite3` local e conferir o tipo, a descrição e os contatos dos empreendimentos do `popular_banco`.

---

## 4. Regras (`empreendimentos/regras.py`)

```python
def empreendimentos_visiveis(usuario): ...     # EMP-05: IS, todos; professor, os que atende; conta, o próprio; admin, nenhum
def pode_ver(usuario, empreendimento): ...     # EMP-05; vale também para os contatos (3.3a.8)
def exigir_edicao(usuario): ...                # 3.3.1 e 3.3a.5: só a IS edita dados e contatos
def desativar(empreendimento, usuario): ...    # 3.6
def reativar(empreendimento, usuario): ...     # 3.6
def salvar_contato(form, empreendimento): ...  # 3.3a.3 e 3.3a.4, atômico
def tornar_responsavel(contato): ...           # 3.3a.4, atômico
def remover_contato(contato): ...              # 3.3a.7
```

- O professor usa `trilhas.regras.empreendimentos_atendidos`, já com inscrição em qualquer status (A-09).
- Desativar e reativar só preenchem ou limpam `desativado_em`. Inscrições e conta não mudam (decisão 7.3, 3.6.3).
- Quem não pode ver recebe `PermissionDenied`, o que vira 403 (3.5.4).
- **Troca de responsável:** dentro de `transaction.atomic`, desmarca o responsável atual e marca o novo, nessa ordem, para não violar a restrição do banco. O anterior continua na lista (A-14).
- `salvar_contato` grava `provisorio=False` e, se o formulário marcar o contato como responsável, usa a mesma troca.
- `remover_contato` apaga o contato. Se era o responsável, o empreendimento fica sem responsável (3.3a.7, A-16d).
- Todas as funções de contato chamam `exigir_edicao` antes de agir.

**`trilhas.regras.anotar_etapa_atual(queryset)`:** acrescenta a etapa por `Subquery`, sobre as inscrições ativas ou pausadas em trilha de etapa. Calcula a etapa na consulta, sem gravar nada e sem uma consulta por linha (Art. 4.3, A-07). O filtro usa essa anotação; "sem etapa" é `etapa_atual` nula.

---

## 5. Forms

| Form | Campos | Usado em |
|---|---|---|
| `EmpreendimentoCadastroForm` (F1) | Passa a ter `email_contato` e `telefone_contato`; `tipo` vira lista; `descricao` usa `TextoFormatadoField` (7a). O formulário de criação do `/admin/` recebe os mesmos campos | Criar empreendedor (A-01, A-02) |
| `EmpreendimentoForm` (**novo**) | `nome`, `tipo`, `descricao` (texto formatado), `email_contato`, `telefone_contato` | Editar. `representante` fica fora, então um valor forjado é ignorado (A-05) |
| `ContatoForm` (**novo**) | `nome`, `funcao`, `email`, `telefone`, `responsavel` | Criar e editar contato (A-13, A-14, A-16b, A-16c). `empreendimento` e `provisorio` ficam fora: o servidor define (Art. 3.4) |

**Contato na criação do empreendedor (3.3a.6).** A tela da IS que cria o empreendedor ganha um bloco opcional "Responsável pelo empreendimento", com um `ContatoForm(prefix='contato', empty_permitted=True)`. Em branco, nada é criado; com qualquer campo preenchido, os três obrigatórios são exigidos, e a conta, o empreendimento e o contato são criados juntos ou nenhum (ACE-05).

**Decisão de plano · o contato da criação já vem marcado como responsável**, e a IS pode desmarcar. É o primeiro contato do empreendimento, então não há outro para disputar.

**O `/admin/` não cadastra contatos.** Só a IS cria contatos (3.3a.5), e o admin só informa os dados do empreendimento ao criar a conta (RN-16).

---

## 6. Rotas e views

Em `sgis/urls.py`, `path('empreendimentos/', include('empreendimentos.urls'))`.

| Rota | Nome | Método | Quem | O que faz | Critérios |
|---|---|---|---|---|---|
| `empreendimentos/` | `lista` | GET | IS | Lista com filtros `situacao` e `etapa`, combináveis | A-06, A-07, A-11 |
| `empreendimentos/<pk>/` | `perfil` | GET | `pode_ver` | Dados, contatos, conta do empreendimento, etapa atual e inscrições | A-08 a A-10, A-15 |
| `empreendimentos/<pk>/editar/` | `editar` | GET/POST | IS | `EmpreendimentoForm` | A-02b, A-03, A-05 |
| `empreendimentos/<pk>/<desativar\|reativar>/` | `situacao` | POST | IS | `regras.desativar` ou `regras.reativar` | A-11, A-12 |
| `empreendimentos/<pk>/contatos/novo/` | `contato_novo` | GET/POST | IS | `ContatoForm` e `regras.salvar_contato` | A-13, A-16, A-16b, A-16c |
| `empreendimentos/<pk>/contatos/<contato>/editar/` | `contato_editar` | GET/POST | IS | Idem, sobre um contato existente; serve também para preencher o provisório | A-14b, A-16, A-16b |
| `empreendimentos/<pk>/contatos/<contato>/responsavel/` | `contato_responsavel` | POST | IS | `regras.tornar_responsavel` | A-14, A-16 |
| `empreendimentos/<pk>/contatos/<contato>/remover/` | `contato_remover` | GET/POST | IS | GET mostra a confirmação; POST apaga | A-16, A-16d |

- O contato é buscado com `get_object_or_404(Contato, pk=contato, empreendimento_id=pk)`, para que o endereço de um contato não funcione sob o empreendimento de outro.
- A confirmação de remoção segue a página intermediária da F3 (`confirmar_acao.html`): sem confirmar, nada muda (A-16d).
- Filtros inválidos são ignorados, como em `todas_trilhas_view`. O nome da trilha no perfil só vira link quando `trilhas.regras.pode_ver` permite.

---

## 7. Desativação e login (S)

```python
class SgisBackend(ModelBackend):
    """EMP-06: conta de empreendimento desativado não entra."""

    def user_can_authenticate(self, user):
        if not super().user_can_authenticate(user):
            return False
        return not Empreendimento.objects.filter(
            representante=user, desativado_em__isnull=False,
        ).exists()
```

`AUTHENTICATION_BACKENDS = ['usuarios.backends.SgisBackend']`.

**Decisão de plano · backend em vez de checar no login.** O Django usa esse método ao entrar e ao recuperar a sessão. Assim, uma sessão aberta também cai ao desativar, e a mensagem continua a mesma de login inválido (A-12). A conta segue ativa e volta a entrar quando o empreendimento for reativado.

---

## 7a. Texto formatado (TXT-01, RN-19)

Peça comum a todas as features. A F2 a cria, porque é a primeira a precisar dela; a F3 e as seguintes só a usam.

| Peça | Onde | O que faz |
|---|---|---|
| `limpar_html(html)` | `sgis/texto.py` | Chama `nh3.clean` com a lista fechada de marcações: `p`, `div`, `br`, `strong`, `b`, `em`, `i`, `ul`, `ol`, `li` e `a` (só `href`, com `http`, `https` ou `mailto`). Links saem com `target="_blank"` e `rel="noopener noreferrer"`. Comentários e o conteúdo de `script` e `style` somem |
| `TextoFormatadoField` | `sgis/texto.py` | `forms.CharField` cujo `clean` devolve `limpar_html(valor)`. O widget é o editor Trix |
| Filtro `texto_formatado` | `sgis/templatetags/texto.py` | Limpa de novo e marca como seguro. A limpeza vale "antes de gravar **e** de exibir" (RN-19), o que protege também dados antigos ou gravados por fora do formulário |
| Filtro `texto_resumo` | `sgis/templatetags/texto.py` | Tira as marcações e corta o texto, para cartões e listas |
| Editor | `base.html` | Trix por CDN. Por CSS, ficam só os botões de negrito, itálico, link e listas; anexos são bloqueados no evento `trix-file-accept` |
| Estilos | `base.html` | Classe `texto-formatado`, que devolve marcadores de lista e sublinhado de link, que o Tailwind zera |

- `'sgis'` entra em `INSTALLED_APPS`, para o Django encontrar `sgis/templatetags`.
- Na F2, o texto formatado vale para a descrição do empreendimento (3.1.1). As descrições de trilha e de atividade ficam para o plano da F3.

**Decisão de plano · limpar ao gravar e ao exibir.** Limpar só ao exibir deixaria HTML perigoso no banco; limpar só ao gravar confiaria em todo dado antigo. As duas limpezas custam pouco e seguem a letra de RN-19.

---

## 8. Templates e outros ajustes

| Template | Situação |
|---|---|
| `empreendimentos/lista.html` | **Novo.** Tabela com nome, tipo, conta do empreendimento, etapa atual e situação; filtros |
| `empreendimentos/perfil.html` | **Novo.** Dados, descrição com `texto_formatado`, contatos com o responsável em destaque e o selo "Provisório", conta do empreendimento, etapa e inscrições. Botões de contato só para a IS. Com espaço para F7 e F8. Link para a tela de etapa, só para a IS |
| `empreendimentos/editar.html` | **Novo.** |
| `empreendimentos/contato_form.html` | **Novo.** Criar e editar contato |
| `usuarios/criar_usuario.html` | Bloco opcional do responsável (seção 5) |
| `partials/header.html` | Link "Empreendimentos" para a IS; "Meu empreendimento" para a conta do empreendimento |
| `trilhas/inscricoes.html` | O link provisório da F4 pode virar link para o perfil |
| `base.html` | Trix e a classe `texto-formatado` (seção 7a) |

- A lista também ganha link para a tela de etapa, cumprindo 3.4.1 da F4 (decisão 7.9).
- **Termos nas telas:** "conta do empreendimento" no lugar de "representante" ou "empreendedor" (3.2.5). O código continua com `representante` e o papel `empreendedor`.
- **`popular_banco`:** sem `usuario_professor_supervisor`; `tipo` com valores da lista; descrição em HTML; dois contatos fictícios por empreendimento, um deles responsável.
- **`empreendimentos/admin.py`:** nada a fazer; a F0 tirou o model do admin.
- Situação e "Provisório" aparecem com texto, não só com cor (RNF-05).

---

## 9. Testes

Em `empreendimentos/tests.py`, com o ID no nome (Art. 6.2). Todo controle de acesso testa o caso negado (Art. 6.3).

| Critério | Teste |
|---|---|
| A-01 | `test_a01_criar_empreendedor_salva_todos_os_campos`, `test_a01_contato_opcional_na_criacao` |
| A-02 | `test_a02_tipo_ou_email_invalido_nao_cria_nada`, `test_a02_contato_incompleto_na_criacao_nao_cria_nada` |
| A-02b | `test_a02b_descricao_formatada_e_limpa` |
| A-03 | `test_a03_is_edita`, `test_a03_professor_e_representante_nao_editam` |
| A-04 | `test_a04_empreendedor_nao_representa_dois`, `test_a04_so_empreendedor_e_representante` |
| A-05 | `test_a05_representante_forjado_e_ignorado` |
| A-06 | `test_a06_filtros_se_combinam` |
| A-07 | `test_a07_lista_mostra_etapa_calculada` |
| A-08 | `test_a08_perfil_mostra_dados_contatos_etapa_e_inscricoes` |
| A-09 | `test_a09_professor_ve_quem_atendeu_e_outro_recebe_403` |
| A-10 | `test_a10_representante_ve_o_proprio_e_admin_recebe_403` |
| A-11 | `test_a11_desativado_fica_no_filtro_e_fora_da_inscricao` |
| A-12 | `test_a12_representante_nao_entra_ate_reativar` |
| A-13 | `test_a13_is_cadastra_contatos_sem_login` |
| A-14 | `test_a14_trocar_responsavel_mantem_um_so` |
| A-14b | `test_a14b_migracao_cria_contato_provisorio_e_reversa_remove` |
| A-15 | `test_a15_quem_ve_o_perfil_ve_os_contatos` |
| A-16 | `test_a16_professor_e_conta_nao_mexem_em_contatos` |
| A-16b | `test_a16b_contato_sem_campo_obrigatorio_e_recusado` |
| A-16c | `test_a16c_contato_nao_precisa_ser_pessoa` |
| A-16d | `test_a16d_remover_contato_com_confirmacao` |
| Migração | `test_migracao_converte_tipo_e_reversa_restaura`, `test_migracao_descricao_vira_html_e_reversa_restaura` |
| Banco | `test_banco_recusa_dois_responsaveis` |

Em `sgis/tests.py`: `test_rn19_limpar_html_remove_script_e_onclick`, `test_rn19_link_abre_em_nova_aba`, `test_rn19_filtro_limpa_dado_antigo`.

**Testes existentes:** os testes de `trilhas` usam `tipo='alimentos'`, o que o banco continua aceitando em `objects.create`. Nenhum cria dois empreendimentos com o mesmo representante.

**Verificação final:** `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

---

## 10. Dados de produção

Decisão 7.5 da spec. Antes da `0006`, consultar a produção por empreendedores sem empreendimento ou com mais de um. Cada empreendedor deve ficar com **exatamente um**.

Se houver casos, a IS diz qual é o certo, e a correção vira um comando revisado, executado antes do deploy da `0006`.

Depois da `0008`, todo empreendimento da produção tem um contato provisório. A IS os preenche pela tela (3.3a.9).

---

## 11. Riscos

| Risco | Mitigação |
|---|---|
| `0006` falhar no deploy, com o `migrate` rodando no build do Render | Fazer a consulta da seção 10 antes do merge |
| Lista lenta com a etapa calculada | `anotar_etapa_atual` usa uma única consulta |
| Perfil mostrar a um professor dados de trilha que ele não pode ver | Link só com `trilhas.regras.pode_ver`; A-09 e A-10 |
| A linha `Tipo anterior` ser editada e a reversa não encontrá-la | A reversa só age quando encontra a linha; os demais ficam em `outro` |
| Trocar o responsável violar a restrição do banco no meio da troca | Desmarcar antes de marcar, na mesma transação (seção 4) |
| HTML perigoso passar pelo editor | O editor não é a proteção: `limpar_html` roda no servidor ao gravar e ao exibir (7a) |
| CDN do Trix fora do ar | O campo de descrição some até o CDN voltar, porque o Trix guarda o texto num campo oculto; o resto do formulário funciona. Versão fixada evita quebra por atualização |
| Contato provisório ficar sem preencher | O perfil mostra o selo "Provisório", e a IS vê quais faltam |
