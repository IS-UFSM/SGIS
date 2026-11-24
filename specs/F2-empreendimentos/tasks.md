# F2 · Empreendimentos — tasks

**Estado:** aprovado · **Data:** 2026-11-24 (revisão para a spec v0.5)
**Spec:** [`spec.md`](spec.md) (aprovada) · **Plano:** [`plan.md`](plan.md) (aprovado)

Cada tarefa cabe num PR e vira uma issue no GitHub. O título da issue é o título da tarefa; o corpo é o bloco da tarefa. Toda tarefa termina com `python manage.py test` e `python manage.py makemigrations --check --dry-run` sem erros.

**Tamanho:** P (algumas horas) · M (1 a 2 dias).

**Revisão v0.5:** T1 a T6 continuam, com ajustes de termos e de migrações. Entram **T7 · Contatos** e **T8 · Texto formatado**.

---

## Ordem e dependências

```text
F1 e F4 ─▶ T1 ─▶ T2 ─▶ T3 ─▶ T4
           T1 ─▶ T5
           T3 + T5 ─▶ T7
           T4 + T5 ─▶ T8
           T3 ─▶ T6 (S)
```

- **T1** vem primeiro: as outras usam o model novo.
- **T2 → T3 → T4** é sequencial: a lista leva ao perfil, e o perfil leva à edição.
- **T5** pode andar em paralelo depois de T1.
- **T7** precisa do perfil (T3) e do formulário de criação (T5).
- **T8** precisa dos formulários de edição (T4) e de criação (T5), onde a descrição ganha o editor.
- **T6** é prioridade S e fica por último.

---

## T1 · Model e migrações do empreendimento

**Branch:** `feat/f2-t1-models` · **Tamanho:** M · **Depende de:** F1, F4

**Objetivo:** lista de tipos, e-mail e telefone gerais, representante único e fim do supervisor (EMP-01, EMP-02, RN-01, RN-02, RN-03).

**Fazer** ([`plan.md`](plan.md) seções 2, 3 e 8):
- [ ] `Empreendimento.Tipo`, `email_contato`, `telefone_contato`.
- [ ] `representante` como `OneToOneField`; `clean` valida o papel.
- [ ] Remover `usuario_professor_supervisor`.
- [ ] Migrações `0004_email_telefone_contato`, `0005_converter_tipo` (com função reversa) e `0006_tipo_representante_unico`.
- [ ] `popular_banco`: sem supervisor, com tipos da lista, e-mail e telefone gerais.

**Testes novos** (em `empreendimentos/tests.py`):
- [ ] `test_a04_empreendedor_nao_representa_dois`, `test_a04_so_empreendedor_e_representante`
- [ ] `test_migracao_converte_tipo_e_reversa_restaura`

**Pronto quando:**
- [ ] A produção foi consultada, e os casos da seção 10 do plano foram corrigidos.
- [ ] As três migrações foram rodadas para frente e para trás numa cópia do `db.sqlite3`. Resultado descrito no PR.
- [ ] `popular_banco` roda sem erro num banco novo.

---

## T2 · Lista de empreendimentos

**Branch:** `feat/f2-t2-lista` · **Tamanho:** M · **Depende de:** T1

**Objetivo:** a IS vê os empreendimentos, com filtros por situação e etapa atual (EMP-03).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 8):
- [ ] `trilhas.regras.anotar_etapa_atual`.
- [ ] `empreendimentos/urls.py`, rota `lista` e `lista.html`, com a coluna "conta do empreendimento".
- [ ] Link "Empreendimentos" no cabeçalho e link para a tela de etapa em cada linha.

**Testes novos:**
- [ ] `test_a06_filtros_se_combinam`
- [ ] `test_a07_lista_mostra_etapa_calculada`

**Pronto quando:**
- [ ] A lista não faz uma consulta por linha para calcular a etapa.

---

## T3 · Perfil do empreendimento

**Branch:** `feat/f2-t3-perfil` · **Tamanho:** M · **Depende de:** T2

**Objetivo:** cada pessoa envolvida vê o perfil do empreendimento (EMP-04, EMP-05).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 8):
- [ ] `empreendimentos_visiveis` e `pode_ver`.
- [ ] Rota `perfil` e `perfil.html`, com "conta do empreendimento" no lugar de "representante". A seção de contatos entra na T7.
- [ ] Link "Meu empreendimento" no cabeçalho.

**Testes novos:**
- [ ] `test_a08_perfil_mostra_dados_contatos_etapa_e_inscricoes` (a parte dos contatos é completada na T7)
- [ ] `test_a09_professor_ve_quem_atendeu_e_outro_recebe_403`
- [ ] `test_a10_representante_ve_o_proprio_e_admin_recebe_403`

**Pronto quando:**
- [ ] Quem não pode ver recebe 403, inclusive pelo endereço direto.

---

## T4 · Edição do empreendimento

**Branch:** `feat/f2-t4-editar` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** a IS edita os dados, sem trocar a conta do empreendimento (EMP-01, 3.2.4).

**Fazer** ([`plan.md`](plan.md) seções 4 a 6):
- [ ] `EmpreendimentoForm`, `exigir_edicao`, rota `editar` e `editar.html`.

**Testes novos:**
- [ ] `test_a03_is_edita`, `test_a03_professor_e_representante_nao_editam`
- [ ] `test_a05_representante_forjado_e_ignorado`

**Pronto quando:**
- [ ] A conta do empreendimento não muda, nem forjando o formulário.

---

## T5 · Campos novos na criação do empreendedor

**Branch:** `feat/f2-t5-criacao` · **Tamanho:** P · **Depende de:** T1

**Objetivo:** o formulário da F1 pede todos os dados do empreendimento (EMP-01).

**Fazer** ([`plan.md`](plan.md) seção 5):
- [ ] `EmpreendimentoCadastroForm`: `tipo` em lista, `email_contato` e `telefone_contato`.
- [ ] Campos novos em `criar_usuario.html` e no formulário de criação do `/admin/`.

**Testes novos:**
- [ ] `test_a01_criar_empreendedor_salva_todos_os_campos`
- [ ] `test_a02_tipo_ou_email_invalido_nao_cria_nada`

**Pronto quando:**
- [ ] Um dado inválido não deixa conta nem empreendimento criados.

---

## T6 · Desativar e reativar empreendimento (S)

**Branch:** `feat/f2-t6-desativar` · **Tamanho:** P · **Depende de:** T3

**Objetivo:** a IS desativa sem apagar, e a conta do empreendimento perde o acesso enquanto isso durar (EMP-06).

**Fazer** ([`plan.md`](plan.md) seções 4, 6 e 7):
- [ ] `desativar`, `reativar` e a rota `situacao`.
- [ ] `usuarios/backends.py` e `AUTHENTICATION_BACKENDS`.
- [ ] Botões no perfil.

**Testes novos:**
- [ ] `test_a11_desativado_fica_no_filtro_e_fora_da_inscricao`
- [ ] `test_a12_representante_nao_entra_ate_reativar`

**Pronto quando:**
- [ ] Reativar devolve o acesso sem mexer na conta nem nas inscrições.

---

## T7 · Contatos do empreendimento

**Branch:** `feat/f2-t7-contatos` · **Tamanho:** M · **Depende de:** T3, T5

**Objetivo:** a IS mantém os contatos de cada empreendimento, com um responsável que pode mudar (EMP-07).

**Fazer** ([`plan.md`](plan.md) seções 2a, 3, 4, 5, 6 e 8):
- [ ] Model `Contato`, com a restrição de um responsável por empreendimento.
- [ ] Migrações `0007_contato` e `0008_contato_provisorio` (com função reversa).
- [ ] `salvar_contato`, `tornar_responsavel` e `remover_contato` em `empreendimentos/regras.py`.
- [ ] `ContatoForm`, rotas `contato_novo`, `contato_editar`, `contato_responsavel` e `contato_remover`, e `contato_form.html`.
- [ ] Seção de contatos no perfil, com o responsável em destaque e o selo "Provisório".
- [ ] Bloco opcional do responsável na criação do empreendedor pela IS (não no `/admin/`).
- [ ] `popular_banco`: dois contatos por empreendimento, um responsável.

**Testes novos:**
- [ ] `test_a01_contato_opcional_na_criacao`, `test_a02_contato_incompleto_na_criacao_nao_cria_nada`
- [ ] `test_a13_is_cadastra_contatos_sem_login`
- [ ] `test_a14_trocar_responsavel_mantem_um_so`, `test_banco_recusa_dois_responsaveis`
- [ ] `test_a14b_migracao_cria_contato_provisorio_e_reversa_remove`
- [ ] `test_a15_quem_ve_o_perfil_ve_os_contatos`
- [ ] `test_a16_professor_e_conta_nao_mexem_em_contatos`
- [ ] `test_a16b_contato_sem_campo_obrigatorio_e_recusado`
- [ ] `test_a16c_contato_nao_precisa_ser_pessoa`
- [ ] `test_a16d_remover_contato_com_confirmacao`

**Pronto quando:**
- [ ] As duas migrações foram rodadas para frente e para trás numa cópia do `db.sqlite3`, e cada empreendimento ficou com um contato provisório. Resultado descrito no PR.
- [ ] Um contato de A não é alcançado pelo endereço de B.

---

## T8 · Texto formatado

**Branch:** `feat/f2-t8-texto-formatado` · **Tamanho:** M · **Depende de:** T4, T5

**Objetivo:** a descrição do empreendimento usa o mini editor, e todo texto formatado é limpo no servidor (TXT-01, RN-19). A peça fica pronta para as outras features.

**Fazer** ([`plan.md`](plan.md) seções 1, 7a e 8):
- [ ] `nh3` no `requirements.txt`, com a versão fixada.
- [ ] `sgis/texto.py`: `limpar_html` e `TextoFormatadoField`.
- [ ] `sgis/templatetags/texto.py`: filtros `texto_formatado` e `texto_resumo`; `'sgis'` em `INSTALLED_APPS`.
- [ ] Trix por CDN em `base.html`, com versão exata, só os botões de TXT-01, anexos bloqueados e a classe `texto-formatado`.
- [ ] `descricao` com `TextoFormatadoField` em `EmpreendimentoCadastroForm` e `EmpreendimentoForm`; perfil com `texto_formatado`.
- [ ] Migração `0009_descricao_html` (com função reversa).

**Testes novos:**
- [ ] `test_a02b_descricao_formatada_e_limpa`
- [ ] `test_rn19_limpar_html_remove_script_e_onclick`, `test_rn19_link_abre_em_nova_aba`, `test_rn19_filtro_limpa_dado_antigo` (em `sgis/tests.py`)
- [ ] `test_migracao_descricao_vira_html_e_reversa_restaura`

**Pronto quando:**
- [ ] Negrito, itálico, lista e link aparecem formatados no perfil, e um `<script>` enviado à mão some antes de gravar.
- [ ] A migração foi rodada para frente e para trás numa cópia do `db.sqlite3`, sem perder as quebras de linha.
