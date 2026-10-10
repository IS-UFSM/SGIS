# Sistema Gerenciador da Incubadora Social

O SGIS tem como foco auxiliar a Incubadora Social da UFSM na organização das relações entre Empreendimentos, Professores e a própria Administração.

Este documento tem como objetivo guiar os devs durante a orquestração e implementação das funcionalidades do sistema.

Os arquivos de SPEC não estão 100% corretos, alterações certamente serão feitas. Entretanto, o básico para se guiar no desenvolvimento tá está disponível.

## Reuniões
Registro das reuniões feitas:
- [Reunião 08/10](https://docs.google.com/document/d/1hjom8iviEU5f6He7RsyRFO3UuHWmsLh_FywNCSXnfks/edit?tab=t.0#heading=h.4czhe7wpdyt5)

## Stack

Discutido previamente em aula. Pode sofrer modificações

- Django


# TODO:

- Modelagem BD - Users, Trilha
- Inicializar BD com login padrao da IS e admin
- IS conseguir criar outros Usuarios
- Novos Empreendimentos são criados como do ciclo pré-incubação e possuem a trilha correspondente
- Login/logout
- Empreendimento ver seu perfil
- Professor criar uma trilha


## Descrição Trabalho WEB DEV:
### Objetivo:
Desenvolver uma aplicação web com cadastro e autenticação de usuários, integrando frontend, backend e persistência de dados.

### Requisitos

- Desenvolvimento individual ou em dupla
- Persistência de dados do lado do servidor
- Aplicação web com frontend e backend
- Cadastro de usuários
- **Login e logout**
- **Autenticação integrada entre frontend e backend**
- **Pelo menos um tipo de dado/recurso associado ao usuário autenticado**
- **Operações protegidas no backend**
- Deploy da aplicação em infraestrutura gratuita

### Exemplo:

- usuário autenticado pode criar seus próprios itens
- usuário pode consultar/alterar/excluir somente itens permitidos pela aplicação