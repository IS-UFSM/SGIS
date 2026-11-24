# F4 · Inscrição e etapas — spec

**Estado:** aprovado · **Data:** 2026-11-24 (revisão para a spec mãe v0.5)
**Spec mãe:** [`SGIS_SPEC_MVP_v0.4.md`](../SGIS_SPEC_MVP_v0.4.md), seção 5 (F4) e jornadas J-3 e J-4 · **Constituição:** [`00-constituicao.md`](../00-constituicao.md) · **Depende de:** [`F3-trilhas`](../F3-trilhas/spec.md) (concluída). É feita antes da [`F2-empreendimentos`](../F2-empreendimentos/spec.md), cujas telas recebem depois as entradas para esta feature (decisão 7.9)

---

## 1. Objetivo

A IS decide em quais trilhas cada empreendimento entra e conduz o empreendimento pelas etapas da incubação: todo empreendimento começa na Pré-incubação e a IS o avança, uma etapa por vez. As inscrições guardam todo o caminho do empreendimento, sem apagar nada.

## 2. Requisitos cobertos

| ID | Prior. | Resumo |
|---|---|---|
| INS-01 | M | A IS inscreve em trilha personalizada publicada |
| INS-02 | M | Inscrição automática na Pré-incubação |
| INS-03 | M | Avançar etapa |
| INS-04 | M | Uma etapa por vez |
| INS-05 | M | Etapa atual calculada pelas inscrições |
| INS-06 | M | Status Ativa, Pausada, Concluída, Cancelada; pausar, reativar, cancelar |
| INS-07 | M | Sem duas inscrições ativas ou pausadas na mesma trilha |
| INS-08 | M | Inscrição pausada: vê, não marca; prazos não correm |
| INS-09 | M | Empreendedor vê só as próprias inscrições |
| INS-10 | S | Inscrição em lote |
| INS-11 | — | Avançar a partir da Desincubação |
| INS-12 | M | Desistência do empreendedor em trilha personalizada |
| RN-09 | — | Uma única etapa por vez |
| RN-18 | — | O empreendedor só desiste de trilha personalizada; o professor não cancela inscrições |

## 3. Regras

### 3.1 Inscrição em trilha personalizada
1. Só a **IS** inscreve.
2. A IS inscreve um empreendimento **ativo** numa trilha **personalizada publicada**. Trilhas em rascunho, arquivadas ou de etapa não aparecem para escolha, nem forjando o formulário.
3. Não pode haver duas inscrições **ativas ou pausadas** do mesmo empreendimento na mesma trilha. Depois de concluída ou cancelada, o empreendimento pode ser inscrito de novo.
4. Quem inscreveu e quando ficam registrados.

### 3.2 Trilhas de etapa
1. Nas trilhas de etapa, ninguém inscreve à mão: a inscrição acontece **só** pela entrada automática na Pré-incubação (3.3) e pelo **avançar etapa** (3.4).
2. O empreendimento tem **no máximo uma** inscrição ativa ou pausada em trilha de etapa.
3. A **etapa atual** é a etapa dessa inscrição; sem ela, o empreendimento está "sem etapa". Nunca é guardada em campo próprio.

### 3.3 Entrada na Pré-incubação
1. Todo empreendimento novo é inscrito **automaticamente** na trilha de etapa Pré-incubação, se ela estiver **publicada**.
2. Se ela não estiver publicada, o empreendimento fica "sem etapa" e a IS vê um aviso ao criar o empreendedor. Quando a trilha de Pré-incubação for publicada, todos os empreendimentos ativos sem etapa e que **nunca passaram por nenhuma etapa** são inscritos nela.
3. A inscrição automática não tem autor (aparece como "inscrição automática").

### 3.4 Avançar etapa
1. Tela própria, só da **IS**, a partir do perfil ou da lista de empreendimentos. Enquanto essas telas não existem, a entrada é pela tela de inscrições (decisão 7.9).
2. A ordem das etapas é **Pré-incubação → Incubação → Desincubação**. Só se avança para a **seguinte**.
3. Ao avançar:
   - a inscrição na etapa atual vira **Concluída**, com a data;
   - o empreendimento é inscrito na trilha da próxima etapa, como **Ativa**;
   - as duas coisas acontecem juntas: se uma falhar, nenhuma acontece.
4. Só se avança se a trilha da próxima etapa estiver **publicada**; senão, o sistema recusa e diz qual trilha falta publicar.
5. Só se avança com a inscrição atual **ativa**: se estiver pausada, a IS reativa antes.
6. **A partir da Desincubação**, "avançar" **encerra a incubação**: a inscrição na Desincubação vira Concluída e o empreendimento fica sem etapa ativa, marcado como "incubação concluída".
7. Empreendimento **desativado** não avança, nem a partir da Desincubação.

### 3.5 Status da inscrição
| Ação | De | Para | Quem | Observação |
|---|---|---|---|---|
| Pausar | Ativa | Pausada | IS | Motivo opcional |
| Reativar | Pausada | Ativa | IS | — |
| Cancelar | Ativa, Pausada | Cancelada | IS, em qualquer trilha | Motivo opcional |
| Desistir | Ativa (Pausada: adiada, 7.12) | Cancelada | Empreendedor, só em trilha personalizada do próprio empreendimento | Sem motivo, com confirmação (3.9) |
| Concluir | Ativa | Concluída | Sistema, ao avançar etapa; IS, à mão, nas trilhas personalizadas | — |

1. Uma inscrição concluída ou cancelada **não volta**. Para continuar, a IS faz uma inscrição nova (3.1.3).
2. Nada é apagado: todas as inscrições ficam no histórico do empreendimento, com as datas de cada mudança.
3. **Cancelar a inscrição de etapa** deixa o empreendimento sem etapa.
4. Cada inscrição guarda a data **mais recente** de cada tipo de mudança e **um único** motivo: pausar de novo substitui a data da pausa, e um motivo novo substitui o anterior.
5. A inscrição cancelada guarda **quem cancelou**. Assim se distingue a **desistência** (cancelada pelo próprio empreendimento) do **cancelamento pela IS**, e as telas mostram "Desistência" ou "Cancelada pela IS".
6. O **professor** não pausa, reativa, cancela nem conclui inscrições, nem nas suas trilhas.

### 3.5a Definir etapa (correção)
1. Para corrigir um avanço errado ou um cancelamento, a **IS** pode **definir a etapa** de um empreendimento que está **sem etapa ativa**: escolhe a etapa e ele é inscrito, como Ativa, na trilha dessa etapa, que precisa estar publicada.
2. É a única forma de inscrever à mão numa trilha de etapa (exceção a 3.2.1). A inscrição fica registrada com quem a fez.
3. Empreendimento **desativado** não tem a etapa definida.

### 3.6 Inscrição pausada
1. O empreendedor **vê** a trilha, mas **não marca** atividades (a marcação é da F5).
2. Os prazos das atividades **não correm** durante a pausa: enquanto a inscrição está pausada, nenhuma atividade dela fica atrasada.
3. Ao **reativar**, o prazo de cada execução ainda não concluída é **adiado** pelo número de dias em que a inscrição ficou pausada. Com várias pausas, os adiamentos se somam.
4. Se o adiamento vale também para o **prazo fixo** fica para depois (7.14).
5. As execuções e seus prazos são da **F5**; esta feature define a regra, e a F5 a aplica.

### 3.7 O que o empreendedor vê
1. Só as inscrições do **próprio** empreendimento.
2. Em "Minhas trilhas": as inscrições ativas e pausadas, e as concluídas como histórico. As canceladas não aparecem na lista, mas a trilha continua acessível pelo detalhe (F3, TRL-10).

### 3.8 Inscrição em lote (prioridade S)
1. A IS escolhe uma trilha personalizada publicada e marca vários empreendimentos de uma vez.
2. Os que já estão inscritos (ativa ou pausada) ou estão desativados são ignorados, e a IS vê quantos foram inscritos e quantos foram ignorados.

### 3.9 Desistência (INS-12)
1. O empreendedor **desiste** de uma inscrição do **próprio** empreendimento numa trilha **personalizada**, com a inscrição **ativa**. Desistir de inscrição **pausada** fica para depois (7.12).
2. **Não** desiste de trilha de etapa: a opção não aparece, e uma tentativa forjada é recusada. Sair da incubação é decisão da IS.
3. A desistência pede **confirmação** e **não pede motivo**. Ela não altera o motivo já guardado na inscrição [ASSUMIDO].
4. A inscrição fica **Cancelada**, com a data e com o próprio empreendimento como quem cancelou (3.5.5). Como qualquer cancelada, não volta: para retomar, a IS faz uma inscrição nova (3.1.3).
5. Depois da desistência, a trilha sai de "Minhas trilhas", como as demais canceladas (3.7.2).

## 4. Critérios de aceite

**Inscrição em trilha personalizada**
- **A-01 (INS-01, J-4):** *Dado* uma trilha personalizada publicada, *quando* a IS inscreve o empreendimento A, *então* a trilha aparece para A e não para B.
- **A-02 (INS-01):** *Dado* trilhas em rascunho, arquivadas ou de etapa, *então* elas não aparecem para escolha, e uma inscrição forjada nelas é recusada.
- **A-03 (INS-07):** *Dado* A inscrito (ativa ou pausada) numa trilha, *quando* a IS tenta inscrevê-lo de novo, *então* o sistema recusa. *Depois de concluída ou cancelada*, *então* a nova inscrição é aceita.
- **A-04 (INS-01):** *Dado* um professor ou empreendedor, *quando* tenta inscrever, *então* o acesso é negado.

**Pré-incubação**
- **A-05 (INS-02):** *Dado* a Pré-incubação publicada, *quando* um empreendimento é criado, *então* ele é inscrito nela automaticamente, sem autor.
- **A-06 (INS-02):** *Dado* a Pré-incubação em rascunho, *quando* um empreendimento é criado, *então* ele fica sem etapa e a IS vê um aviso. *Quando* a Pré-incubação é publicada, *então* ele é inscrito nela.
- **A-07 (INS-02):** *Dado* um empreendimento que já concluiu a incubação, *quando* a Pré-incubação é publicada de novo ou recebe atividades, *então* ele **não** é reinscrito.

**Avançar etapa**
- **A-08 (INS-03, J-3):** *Dado* A na Pré-incubação, *quando* a IS avança, *então* a inscrição na Pré-incubação fica Concluída, A é inscrito na Incubação como Ativa, e a etapa atual de A passa a ser Incubação.
- **A-09 (INS-04, RN-09):** *Dado* qualquer sequência de ações (avançar, inscrever, reativar), *então* A nunca fica com duas inscrições ativas ou pausadas em trilhas de etapa.
- **A-10 (3.4.4):** *Dado* a trilha de Incubação em rascunho, *quando* a IS tenta avançar A, *então* o sistema recusa, diz que a Incubação precisa ser publicada, e nada muda.
- **A-11 (3.4.5):** *Dado* a inscrição de etapa de A pausada, *quando* a IS tenta avançar, *então* o sistema recusa e nada muda.
- **A-12 (INS-11):** *Dado* A na Desincubação, *quando* a IS avança, *então* a inscrição fica Concluída, A fica sem etapa ativa e aparece como "incubação concluída".
- **A-12b (3.4.7, 3.5a.3):** *Dado* um empreendimento desativado, *quando* a IS tenta avançar ou definir a etapa, *então* o sistema recusa e nada muda.
- **A-13 (3.2.1):** *Dado* a tela de inscrição, *então* não há como inscrever à mão numa trilha de etapa.
- **A-13b (3.5a):** *Dado* A sem etapa ativa (inscrição de etapa cancelada), *quando* a IS define a etapa como Incubação, *então* A é inscrito na Incubação como Ativa. *Dado* A com etapa ativa, *então* a opção de definir etapa não está disponível e uma tentativa forjada é recusada.
- **A-13c (7.2):** *Dado* uma inscrição ativa em trilha personalizada, *quando* a IS a conclui, *então* ela fica Concluída com a data, e o empreendimento pode ser inscrito de novo nessa trilha.

**Status**
- **A-14 (INS-06):** *Dado* uma inscrição ativa, *quando* a IS pausa (com motivo), reativa e depois cancela, *então* cada passo muda o status e grava a data; o motivo fica guardado.
- **A-15 (INS-06):** *Dado* uma inscrição concluída ou cancelada, *quando* alguém tenta reativá-la ou pausá-la, *então* o sistema recusa.
- **A-16 (INS-05):** *Dado* A sem inscrição de etapa ativa ou pausada, *então* a etapa atual de A é "sem etapa", e nenhuma tabela guarda a etapa.

**O que o empreendedor vê**
- **A-17 (INS-09):** *Dado* o representante de A, *então* "Minhas trilhas" mostra as inscrições ativas, pausadas e concluídas de A, e nenhuma de B.
- **A-18 (INS-08):** *Dado* uma inscrição pausada, *então* o empreendedor vê a trilha com o aviso de que está pausada. (O bloqueio de marcar é testado na F5.)
- **A-18b (INS-08, 3.6):** *Dado* uma atividade com prazo em 10 dias, *quando* a IS pausa a inscrição por 5 dias e reativa, *então* o prazo passa para 15 dias depois da data original de início, e a atividade não aparece como atrasada durante a pausa. *Dado* duas pausas de 3 e 4 dias, *então* o prazo é adiado em 7 dias. (Testado na F5, onde as execuções existem.)

**Lote (S)**
- **A-19 (INS-10):** *Dado* três empreendimentos, um deles já inscrito e outro desativado, *quando* a IS inscreve os três em lote, *então* só um é inscrito e a IS vê "1 inscrito, 2 ignorados".

**Desistência e cancelamento**
- **A-20 (INS-12):** *Dado* A inscrito, como Ativa, numa trilha personalizada, *quando* a conta de A desiste e confirma, *então* a inscrição fica Cancelada, com a data, registrada como desistência, e a IS a vê como "Desistência".
- **A-21 (INS-12):** *Desistência de inscrição pausada:* critério adiado junto com a decisão 7.12.
- **A-22 (INS-12, RN-18):** *Dado* A na trilha de etapa, *então* a opção de desistir não aparece, e uma desistência forjada é recusada sem mudar nada.
- **A-23 (INS-12, INS-09):** *Dado* a conta de B, *quando* tenta desistir de uma inscrição de A, *então* o acesso é negado e nada muda.
- **A-24 (INS-12):** *Dado* uma inscrição concluída ou cancelada, *quando* a conta do empreendimento tenta desistir, *então* o sistema recusa.
- **A-25 (INS-06, RN-18):** *Dado* um professor, dono ou não da trilha, *quando* tenta pausar, reativar, cancelar ou concluir uma inscrição, *então* o acesso é negado.
- **A-26 (3.5.5):** *Dado* uma inscrição cancelada pela IS e outra por desistência, *então* as telas mostram "Cancelada pela IS" na primeira e "Desistência" na segunda.

## 5. Fora de escopo

- Marcar atividades, progresso, prazos e o efeito da pausa sobre a marcação: **F5**.
- Etapa atual na lista e no perfil do empreendimento: a regra é daqui; as telas são da **F2**.
- "Voltar uma etapa" como ação própria: fora do MVP. A correção é cancelar a inscrição atual e definir a etapa (3.5a).
- Professor sugerir inscrição à IS: fora do MVP.

## 6. Situação atual (de [`levantamento-codigo-v0.4.md`](../levantamento-codigo-v0.4.md))

- A IS inscreve em `/trilhas/inscricoes/`, mas o formulário oferece **qualquer** trilha: em rascunho, arquivada ou de etapa.
- Um signal inscreve todo empreendimento novo na trilha de etapa Pré-incubação, **mesmo em rascunho**. Se ela não existir, só grava um aviso no log.
- Status existentes: Ativa, Pausada e Cancelada, com motivo e datas de pausa e cancelamento. **Falta Concluída.**
- A restrição do banco impede duas inscrições "não canceladas" na mesma trilha. Com o status Concluída, ela precisa passar a valer só para ativas e pausadas (3.1.3).
- Não existem avançar etapa, etapa atual calculada nem inscrição em lote.
- As transições de inscrição estão em `trilhas/views.py`; pela constituição (Art. 7.5), devem ir para um módulo de regras, como o `trilhas/regras.py` da F3.
- O empreendedor já vê só as inscrições do próprio empreendimento, sem as canceladas.
- **Revisão v0.5 (2026-11-24), ainda não implementada:** não existe desistência, e a inscrição não guarda quem cancelou.

## 7. Decisões

| # | Pergunta | Decisão |
|---|---|---|
| 7.1 | O que acontece ao "avançar" a partir da Desincubação (pendência 2 da spec mãe)? | Encerra a incubação: a inscrição fica Concluída e o empreendimento fica sem etapa ativa, marcado como "incubação concluída" (3.4.6). |
| 7.2 | Inscrição em trilha personalizada pode ser concluída? Por quem? | Sim, pela IS, à mão. A conclusão automática por progresso fica para a F5. |
| 7.3 | Como a IS corrige um avanço errado ou um cancelamento de etapa? | A IS pode **definir a etapa** de um empreendimento sem etapa ativa: escolhe a etapa e ele é inscrito na trilha dela, que precisa estar publicada. É a única exceção a 3.2.1, só para correção. |
| 7.4 | Empreendimento com incubação concluída pode ser inscrito em trilhas personalizadas? | Sim. |
| 7.5 | A inscrição em lote (S) entra nesta feature? | Sim, como última tarefa, separada das obrigatórias. |
| 7.6 | A IS pode avançar ou definir a etapa de um empreendimento desativado? | Não, seguindo a F2 (3.6.2). A recusa vale também para avançar a partir da Desincubação, para a regra ser uma só. |
| 7.7 | A reativação grava data? | Sim, como as demais mudanças de status (A-14). |
| 7.8 | O que acontece com a data e o motivo quando a inscrição muda de novo? | O valor novo substitui o anterior (3.5.4). O histórico de cada mudança depende de auditoria, adiada no MVP. |
| 7.9 | A F4 vem antes da F2? | Sim. Até a F2 existir, a entrada para a tela de etapa fica na tela de inscrições; a F2 acrescenta as entradas pelo perfil e pela lista. |
| 7.10 | O empreendedor pode desistir? De quais trilhas? | Sim, só das personalizadas (v0.5, segunda reunião com a IS). O professor não cancela nada. |
| 7.11 | A desistência pede motivo? | Não (v0.5). |
| 7.12 | Pode desistir de inscrição pausada? | **Adiada** (2026-11-24), com as demais questões da pausa (pendência 10 da spec mãe). Proposta: sim, como na ativa. Enquanto isso, só a inscrição ativa admite desistência. |
| 7.13 | Os prazos devem continuar correndo com a inscrição pausada (3.6.2)? | **Não** (decisão de 2026-11-24, que substitui a anterior). Ao reativar, os prazos são adiados pelo tempo da pausa (3.6). |
| 7.14 | O prazo fixo também é adiado pela pausa? | **Adiada** (2026-11-24), com as demais questões da pausa (pendência 12 da spec mãe). Proposta: sim. |
