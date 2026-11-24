# F2 · Empreendimentos — spec

**Estado:** rascunho (revisão para a spec mãe v0.5; a versão anterior foi aprovada em 2026-11-04) · **Data:** 2026-11-24
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seção 5 (F2) · **Constituição:** [`00-constituicao.md`](../00-constituicao.md) · **Depende de:** [`F1-acesso`](../F1-acesso/spec.md) (criação do empreendimento junto com o empreendedor)

---

## 1. Objetivo

Dar à IS o cadastro completo dos empreendimentos, com as pessoas de contato de cada um, e a cada pessoa envolvida uma página de perfil do empreendimento, com os dados, os contatos, a etapa atual e as trilhas. O empreendimento entra no sistema por **uma única conta**, compartilhada pelas suas pessoas. O perfil é o lugar onde as features seguintes acrescentam os níveis por eixo (F8) e o prontuário (F7).

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| EMP-01 | M | Cadastro e edição pela IS: nome, tipo, descrição, contato |
| EMP-02 | M | Uma única conta (representante) por empreendimento, compartilhada pelas suas pessoas |
| EMP-03 | M | Lista da IS com filtros: ativos, desativados, por etapa atual |
| EMP-04 | M | Perfil do empreendimento, com os contatos |
| EMP-05 | M | Quem vê o perfil |
| EMP-06 | S | Desativar sem apagar histórico; o representante perde o acesso |
| EMP-07 | M | Contatos do empreendimento, sem login, com um responsável que pode mudar |
| RN-01, RN-02 | — | A conta de empreendedor representa exatamente um empreendimento; o empreendimento tem uma única conta, e as pessoas ficam como contatos |
| TXT-01, RN-19 | — | A descrição do empreendimento é texto formatado, limpo no servidor |
| RN-03 | — | Sem supervisão: o professor só se relaciona com o empreendimento pelas trilhas |

## 3. Regras

### 3.1 Dados do empreendimento
1. Campos: **nome** (obrigatório), **tipo** (MEI, Associação, Coletivo ou Outro; obrigatório), **descrição** (texto formatado, TXT-01), **e-mail de contato** e **telefone de contato** (opcionais).
2. O e-mail e o telefone de contato são o **contato geral** do empreendimento e **não** são usados para login; o login é o e-mail da conta do empreendimento (F1). As pessoas ficam nos contatos (3.3a).

### 3.2 Criação e conta do empreendimento
1. Um empreendimento **só é criado junto com a sua conta**, na criação da conta de empreendedor pela IS ou pelo admin (F1, ACE-05). Não existe empreendimento sem conta. Os campos desta seção entram no mesmo formulário.
2. Cada empreendimento tem **exatamente uma conta**, com papel empreendedor. Ela é o **representante** do empreendimento e é **compartilhada** pelas pessoas dele: não há uma conta por pessoa.
3. Cada conta de empreendedor representa **exatamente um** empreendimento.
4. A conta **não muda** pelas telas do MVP. Quando as pessoas do empreendimento mudam, atualizam-se os contatos (3.3a) e, se for preciso, a IS redefine a senha da conta (F1, ACE-08). [ASSUMIDO]
5. Nas telas, a conta aparece como **"conta do empreendimento"**. O código do papel continua `empreendedor`.

### 3.3 Edição
1. Só a **IS** edita os dados do empreendimento (3.1). A conta do empreendimento e os professores só leem.
2. A conta do empreendimento não é trocada pela edição (3.2.4).

### 3.3a Contatos (EMP-07)
1. Cada empreendimento tem uma lista de **contatos**: os meios pelos quais a IS e os professores falam com o empreendimento. Um contato costuma ser uma pessoa, mas **não precisa** ser: pode ser um setor ou um e-mail geral. Contato **não faz login** e **não tem vínculo** com nenhum usuário do sistema.
2. **Por que existem:** o **responsável** pelo empreendimento pode mudar com o tempo. Como a conta é uma só e compartilhada (3.2), quem responde pelo empreendimento fica registrado nos contatos, e não na conta.
3. Campos de cada contato: **nome**, **e-mail** e **telefone**, obrigatórios, e **função** (por exemplo, "presidente", "tesoureira"), opcional. O e-mail precisa ser válido.
4. No máximo **um** contato é o **responsável**. **Trocar de responsável** é marcar outro contato: o anterior deixa de ser responsável e continua na lista, e a conta do empreendimento não muda.
5. **Só a IS** cria, edita e remove os contatos, inclusive a troca de responsável. A conta do empreendimento e os professores só leem.
6. Os contatos podem ser cadastrados junto com o empreendimento (3.2.1) ou depois, no perfil.
7. **Remover:** a IS remove um contato que deixou de valer (por exemplo, quando a pessoa sai do empreendimento), depois de confirmar. O contato é **apagado de vez**: não é registro de negócio (Constituição, Art. 4). Se o removido era o responsável, o empreendimento fica sem responsável até a IS marcar outro contato.
8. **Quem vê** os contatos: as mesmas pessoas que veem o perfil (3.5.3).
9. **Empreendimentos que já existem:** na migração, cada um ganha **um contato provisório** (placeholder), marcado como responsável, para a IS substituir pelos dados reais. Ele é a única exceção aos campos obrigatórios (3.3a.3). O perfil mostra que o contato é provisório, e a IS só consegue salvá-lo de novo com nome, e-mail e telefone válidos.

### 3.4 Lista da IS
1. Mostra nome, tipo, representante, etapa atual e situação (ativo ou desativado).
2. Filtros combináveis: **ativos / desativados** e **etapa atual** (Pré-incubação, Incubação, Desincubação, sem etapa).
3. A **etapa atual** é calculada a partir das inscrições (F4, INS-05), nunca guardada.

### 3.5 Perfil do empreendimento
1. Mostra: **dados** (3.1), **contatos** (3.3a), com o responsável em destaque, **conta do empreendimento**, **etapa atual**, **trilhas em que está ou esteve inscrito**, com o status de cada inscrição.
2. As seções de **níveis por eixo** (F8) e **prontuário** (F7) entram no perfil quando essas features forem feitas.
3. **Quem vê** (EMP-05): a IS vê o perfil de todos; um professor vê o perfil dos empreendimentos que **atende** (inscritos, agora ou antes, em alguma trilha dele); o representante vê o do **próprio** empreendimento. O admin não vê (RN-16).
4. Quem não pode ver recebe acesso negado (403), pela lista e pelo endereço direto.

### 3.6 Desativação (prioridade S)
1. A **IS** desativa e reativa um empreendimento. Nada é apagado: dados, inscrições e histórico continuam.
2. **Empreendimento desativado:**
   - não pode receber novas inscrições (já é assim hoje);
   - o **representante não consegue entrar** no sistema enquanto o empreendimento estiver desativado, com a mesma mensagem genérica de login da F1; a conta dele continua ativa e volta a entrar quando o empreendimento for reativado;
   - as inscrições existentes ficam como estão.
3. Desativar o empreendimento não desativa a conta do representante, e vice-versa (F1, decisão 7.5).

## 4. Critérios de aceite

**Dados e criação**
- **A-01 (EMP-01):** *Dado* a IS criando um empreendedor (F1), *então* o formulário pede também nome, tipo, descrição, e-mail e telefone de contato do empreendimento, e todos são salvos.
- **A-02 (EMP-01):** *Dado* um tipo fora da lista, ou um e-mail de contato inválido, *quando* a IS salva, *então* o sistema recusa e nada é criado.
- **A-03 (EMP-01):** *Dado* a IS, *quando* edita o nome e o telefone de um empreendimento, *então* a mudança é salva. *Dado* um professor ou o representante, *quando* tenta editar, *então* o acesso é negado.

- **A-02b (TXT-01, RN-19):** *Dado* a IS, *quando* salva uma descrição com negrito e um link, *então* o perfil mostra o negrito e o link clicável. *Quando* a descrição enviada contém `<script>` ou um atributo `onclick`, *então* essas partes são removidas antes de gravar.

**Conta do empreendimento**
- **A-04 (EMP-02, RN-01, RN-02):** *Dado* uma conta de empreendedor que já representa um empreendimento, *então* não há como ligá-la a um segundo. *Dado* uma conta que não é de empreendedor, *então* ela não pode ser representante.
- **A-05 (3.2.4):** *Dado* a edição do empreendimento, mesmo forjando o formulário, *então* a conta do empreendimento não muda.

**Contatos**
- **A-13 (EMP-07):** *Dado* a IS, *quando* cadastra dois contatos para A, com nome, função, e-mail e telefone, *então* eles aparecem no perfil de A, e nenhum deles consegue entrar no sistema.
- **A-14 (EMP-07):** *Dado* A com o contato Maria como responsável, *quando* a IS marca João como responsável, *então* Maria deixa de ser responsável e continua na lista, A fica com exatamente um responsável, e a conta de A não muda.
- **A-14b (3.3a.9):** *Dado* empreendimentos que existiam antes dos contatos, *quando* a migração roda, *então* cada um fica com exatamente um contato, provisório e responsável, e o perfil indica que ele é provisório. Desfazer a migração remove esses contatos.
- **A-15 (EMP-07, EMP-05):** *Dado* o professor X, que atende A, e a conta de A, *então* os dois veem os contatos de A. *Dado* o professor Z, que não atende A, ou a conta de B, *então* recebem 403.
- **A-16 (EMP-07):** *Dado* um professor ou a conta do empreendimento, *quando* tenta criar, editar ou remover um contato, inclusive trocar o responsável, *então* o acesso é negado.
- **A-16d (3.3a.7):** *Dado* A com dois contatos, *quando* a IS remove um deles e confirma, *então* ele some da lista e do banco, e o outro continua. *Quando* a IS cancela a confirmação, *então* nada muda. *Dado* que o removido era o responsável, *então* A fica sem responsável.
- **A-16b (EMP-07):** *Dado* a IS, *quando* tenta salvar um contato sem nome, sem e-mail, sem telefone ou com e-mail inválido, *então* o sistema recusa e nada é salvo.
- **A-16c (3.3a.1):** *Dado* a IS, *quando* cadastra um contato com nome "Secretaria" e um e-mail geral, *então* ele é aceito, sem exigir nenhuma conta de usuário.

**Lista**
- **A-06 (EMP-03):** *Dado* empreendimentos ativos e desativados, em etapas diferentes, *quando* a IS filtra por "desativados" ou por uma etapa, *então* aparecem só os que correspondem, e os filtros se combinam.
- **A-07 (EMP-03, INS-05):** *Dado* um empreendimento que avançou para a Incubação (F4), *então* a lista mostra "Incubação" como etapa atual, sem que nenhum campo de etapa tenha sido gravado.

**Perfil**
- **A-08 (EMP-04):** *Dado* um empreendimento com inscrições, *quando* a IS abre o perfil, *então* vê os dados, os contatos, a conta do empreendimento, a etapa atual e as trilhas com o status de cada inscrição.
- **A-09 (EMP-05):** *Dado* o professor X, dono de uma trilha em que o empreendimento A esteve inscrito, *então* X vê o perfil de A, mesmo com a inscrição encerrada. *Dado* o professor Z, que nunca atendeu A, *então* recebe 403.
- **A-10 (EMP-05):** *Dado* o representante de A, *então* vê o perfil de A e recebe 403 no perfil de B. *Dado* o admin, *então* recebe 403 em qualquer perfil.

**Desativação (S)**
- **A-11 (EMP-06):** *Dado* um empreendimento desativado, *então* ele continua no banco com as inscrições, a IS o vê no filtro "desativados", e ele não aparece na lista de empreendimentos para inscrever.
- **A-12 (EMP-06):** *Dado* o representante de um empreendimento desativado, *quando* tenta entrar, *então* não entra e vê a mensagem genérica de login. *Quando* a IS reativa o empreendimento, *então* ele volta a entrar.

## 5. Fora de escopo

- Criação da conta do empreendedor e a regra "criados juntos": **F1** (ACE-05). A F2 só acrescenta os campos ao formulário.
- Níveis por eixo e prontuário no perfil: **F8** e **F7**.
- Progresso das trilhas no perfil: **F5**.
- Troca da conta do empreendimento e contas individuais para cada pessoa: fora do MVP (a v0.5 adotou uma conta compartilhada mais contatos).
- O mini editor de texto formatado em si (TXT-01) é comum a várias features; esta feature só o usa na descrição.

## 6. Situação atual (de [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md))

- O model tem nome, **tipo como texto livre**, descrição, `desativado_em` e o **representante** (FK). Faltam e-mail e telefone de contato.
- **Sobra do modelo antigo:** o campo `usuario_professor_supervisor`, que a v0.4 descartou (RN-03). Aparece no admin e no `popular_banco`, e precisa sair.
- Nada impede um empreendedor de representar dois empreendimentos, nem uma conta que não é de empreendedor de ser representante.
- **Não há tela** de empreendimentos: lista, perfil e edição só existem no `/admin/`, que a F0 vai fechar para dados de negócio.
- Empreendimento desativado já não pode ser inscrito; o representante dele continua entrando normalmente.
- Os empreendimentos que já existem têm o tipo em texto livre ("alimentos", "Artesanato / Textil").
- **Revisão v0.5 (2026-11-24):** não existem contatos; a descrição é texto simples; as telas usam "representante" ou "empreendedor" onde a v0.5 diz "conta do empreendimento". Esta seção será atualizada ao levantar o código das tarefas da F2.

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | O que fazer com o tipo em texto livre dos empreendimentos que já existem? | A migração converte para "Outro" e acrescenta o texto antigo ao fim da descrição. |
| 7.2 | O representante pode ser trocado no MVP? | Não. A troca da conta do empreendimento fica para depois do MVP. Com a conta compartilhada (v0.5), a mudança de pessoas se resolve pelos contatos e pela redefinição de senha (3.2.4). |
| 7.3 | Desativar o empreendimento pausa as inscrições ativas? | Não; as inscrições ficam como estão. A IS pausa ou cancela à mão se quiser. |
| 7.4 | Desativar o empreendimento tira o acesso do representante (pendência 7 da spec mãe)? | Sim, como em 3.6.2: o representante não entra enquanto o empreendimento estiver desativado; a conta dele continua ativa. |
| 7.5 | O que fazer com dados de produção fora de RN-01? | Cada empreendedor fica com **exatamente um** empreendimento. A produção é consultada antes da migração; havendo casos, a IS diz qual é o certo, e a correção vira um comando revisado (F0, decisão 7.2). |
| 7.6 | Quem cria e edita os contatos? | Só a IS (decisão de 2026-11-24). |
| 7.7 | Quais campos do contato são obrigatórios? | Nome, e-mail e telefone (decisão de 2026-11-24). A função é opcional. O contato provisório da migração (3.3a.9) é a exceção. |
| 7.8 | Um contato pode ser removido? | Sim, pela IS, com confirmação, e ele é apagado de vez (decisão de 2026-11-24). O contato não é registro de negócio (Constituição, Art. 4), e guardar dados de quem saiu do empreendimento contraria a coleta mínima (Art. 5.5). |
| 7.11 | O contato precisa corresponder a uma pessoa ou a um usuário? | Não (decisão de 2026-11-24). Pode ser um setor ou um e-mail geral, e não tem vínculo com usuários. |
| 7.9 | Os empreendimentos que já existem ganham algum contato na migração? | Sim: um contato **provisório** (placeholder), marcado como responsável, para a IS preencher (decisão de 2026-11-24). |
| 7.10 | Para que servem os contatos? | O responsável pelo empreendimento pode mudar; os contatos registram quem responde por ele sem trocar a conta (decisão de 2026-11-24). O termo "principal" da primeira versão da v0.5 passou a ser **responsável**. |
