# Arquitetura proposta — aplicativo local de lista de tarefas

## 1. Resumo executivo

A arquitetura recomendada para uma equipe pequena é um aplicativo web local, hospedado em um único computador ou servidor dentro da rede da equipe, acessado pelos navegadores dos usuários.

O MVP deve manter uma única fonte de dados compartilhada e oferecer somente o necessário para organizar tarefas:

- criação e edição de tarefas;
- conclusão e reabertura;
- atribuição opcional a um membro da equipe;
- filtros por status e responsável;
- persistência local;
- exportação e backup manual.

A proposta pressupõe que “local” significa “acessível na rede local, sem depender de SaaS ou internet”. Essa interpretação ainda precisa ser confirmada. Caso o uso seja individual, a arquitetura pode ser reduzida para um aplicativo desktop ou web local com banco embutido, eliminando autenticação, servidor compartilhado e controle de concorrência.

---

## 2. Fatos, hipóteses e recomendações

### Fatos fornecidos

- O produto é uma lista de tarefas.
- O produto deve ser local.
- O público é uma equipe pequena.
- O objetivo desta etapa é estruturar uma arquitetura tecnicamente viável.

### Hipóteses de arquitetura

As seguintes hipóteses são usadas para produzir uma proposta concreta:

- mais de uma pessoa poderá acessar as mesmas tarefas;
- os usuários estarão na mesma rede local;
- não haverá necessidade inicial de acesso externo pela internet;
- a equipe aceitará manter um computador ou servidor ligado quando o sistema precisar ser utilizado;
- o volume de tarefas será pequeno ou moderado;
- não haverá integrações externas no MVP;
- colaboração em tempo real avançada não será necessária;
- o produto não armazenará arquivos ou dados altamente sensíveis no primeiro ciclo.

### Recomendações

- Adotar um aplicativo web local centralizado, em vez de instalações independentes em cada computador.
- Usar um único banco de dados local para evitar divergência entre cópias.
- Manter a API e a interface no mesmo sistema no MVP.
- Começar com um banco relacional embutido, como SQLite, se o volume e a concorrência forem baixos.
- Planejar uma migração para PostgreSQL apenas se surgirem requisitos de maior concorrência, disponibilidade ou crescimento.
- Não implementar notificações, comentários, histórico detalhado, integrações ou permissões granulares sem necessidade comprovada.

---

## 3. Visão geral da solução

```text
+-------------------+       HTTP na rede local       +----------------------+
| Navegador usuário | ------------------------------> | Aplicação local      |
+-------------------+                                | UI + API + regras    |
                                                      +----------+-----------+
                                                                 |
                                                                 | acesso local
                                                                 v
                                                      +----------------------+
                                                      | Banco de dados       |
                                                      | SQLite               |
                                                      +----------+-----------+
                                                                 |
                                                                 | exportação/backup
                                                                 v
                                                      +----------------------+
                                                      | Arquivo de backup    |
                                                      | JSON/CSV + banco     |
                                                      +----------------------+
```

### Componentes principais

| Componente | Responsabilidade |
|---|---|
| Interface web | Exibir tarefas, formulários, filtros e estados de operação |
| API HTTP local | Receber comandos e consultar tarefas |
| Camada de aplicação | Validar regras de negócio e coordenar operações |
| Persistência | Armazenar tarefas, usuários e configurações |
| Backup/exportação | Produzir cópias recuperáveis dos dados |
| Registro operacional | Registrar erros, operações relevantes e saúde do serviço |

A interface pode ser servida pelo próprio backend para reduzir a quantidade de componentes e simplificar a instalação.

---

## 4. Modelo de implantação

### Opção recomendada: servidor local único

Um computador da equipe executa a aplicação. Os demais usuários acessam um endereço interno, por exemplo:

```text
http://nome-do-computador:porta
```

Características:

- uma única base de dados;
- instalação centralizada;
- comportamento consistente para todos os usuários;
- backup concentrado;
- funcionamento sem internet, desde que a rede local esteja disponível.

Riscos:

- se o computador estiver desligado, o sistema ficará indisponível;
- falha no disco pode afetar todos os dados;
- alguém precisará cuidar da atualização e do backup;
- a rede local se torna uma dependência operacional.

### Alternativa: aplicativo individual

Cada usuário executa sua própria cópia, com dados locais.

Essa opção só é adequada quando:

- as tarefas não precisam ser compartilhadas;
- cada pessoa mantém sua própria lista;
- ou a sincronização será deliberadamente deixada fora do escopo.

Não é recomendada para uma lista compartilhada, pois criaria problemas de sincronização, merge, conflitos e recuperação.

### Alternativa futura: servidor dedicado

Caso o uso cresça, a aplicação pode ser transferida para:

- um servidor interno;
- um equipamento dedicado;
- uma máquina virtual;
- ou uma infraestrutura self-hosted administrada pela equipe.

Essa alternativa não deve ser adotada no MVP sem necessidade operacional clara.

---

## 5. Escopo funcional do MVP

### Entidades e campos

#### Tarefa

- `id`
- `title`
- `description` opcional
- `status`
- `assignee_id` opcional
- `due_date` opcional
- `created_at`
- `updated_at`
- `completed_at` opcional

Status mínimos:

- `OPEN`
- `IN_PROGRESS`
- `DONE`

Se a equipe desejar um fluxo ainda mais simples, `IN_PROGRESS` pode ser removido e mantidos apenas `OPEN` e `DONE`.

#### Usuário

- `id`
- `name`
- `active`
- `created_at`

No MVP, o usuário pode ser selecionado em uma lista local. Autenticação completa só deve ser incluída se houver necessidade de identificar e restringir cada pessoa.

#### Configuração

Pode conter:

- nome da equipe;
- fuso horário;
- regras simples de retenção;
- diretório de backup;
- preferências da interface.

### Operações principais

- listar tarefas;
- criar tarefa;
- editar tarefa;
- atribuir responsável;
- alterar status;
- concluir tarefa;
- reabrir tarefa;
- filtrar por status;
- filtrar por responsável;
- ordenar por atualização ou prazo;
- exportar dados;
- executar ou agendar backup.

### Fora do MVP

- comentários;
- anexos;
- notificações;
- recorrência;
- múltiplos projetos;
- quadros Kanban;
- permissões por projeto;
- integração com e-mail, calendário ou mensageria;
- sincronização com instalações independentes;
- edição colaborativa em tempo real;
- auditoria detalhada de cada campo.

---

## 6. Fluxos principais

### Criar tarefa

1. O usuário abre o formulário.
2. A interface valida campos obrigatórios.
3. A API recebe a solicitação.
4. A camada de aplicação valida novamente os dados.
5. A tarefa é gravada no banco.
6. A API retorna a tarefa criada.
7. A interface atualiza a lista.

Validações mínimas:

- título não vazio;
- limite de tamanho do título;
- data válida, quando informada;
- responsável existente e ativo, quando informado;
- status permitido.

### Atualizar tarefa

1. O usuário abre uma tarefa.
2. A interface envia os campos alterados.
3. A API verifica se a tarefa existe.
4. A aplicação valida a transição de status.
5. O banco atualiza a tarefa.
6. O sistema atualiza `updated_at`.
7. Se o status for `DONE`, preenche `completed_at`.
8. Se a tarefa for reaberta, limpa `completed_at`.

### Concorrência simples

Dois usuários podem abrir a mesma tarefa simultaneamente. Para evitar sobrescrita silenciosa, a atualização deve usar controle otimista:

- o cliente envia a versão ou `updated_at` conhecido;
- o servidor verifica se a tarefa ainda está na mesma versão;
- se tiver sido alterada, retorna conflito;
- a interface informa o usuário e oferece recarregar os dados.

Para um MVP muito simples, pode ser aceitável usar “última gravação vence”, mas essa decisão deve ser explícita porque pode causar perda de alterações.

### Consulta e filtros

A interface envia filtros para a API:

```text
GET /api/tasks?status=OPEN&assignee_id=3
```

A API deve aplicar os filtros no banco, evitando carregar dados desnecessários para o navegador.

### Backup

1. O sistema inicia uma operação de backup.
2. O banco é colocado em estado consistente para cópia.
3. É gerado um arquivo de banco ou exportação estruturada.
4. O arquivo recebe data e hora no nome.
5. O sistema valida se o arquivo foi criado.
6. Registra o resultado da operação.
7. A equipe copia o arquivo para outro dispositivo ou local seguro.

O backup no mesmo disco do sistema protege contra erro lógico, mas não contra perda do equipamento. A recomendação mínima é manter pelo menos uma cópia em outro dispositivo.

---

## 7. API interna

Uma API HTTP simples é suficiente para separar a interface das regras de negócio.

### Rotas sugeridas

```text
GET    /api/tasks
POST   /api/tasks
GET    /api/tasks/{id}
PATCH  /api/tasks/{id}
DELETE /api/tasks/{id}

GET    /api/users
POST   /api/users
PATCH  /api/users/{id}

GET    /api/health
POST   /api/backups
GET    /api/export
```

A exclusão física de tarefas não é recomendada inicialmente. É preferível:

- permitir arquivamento; ou
- manter exclusão apenas para administradores; ou
- não oferecer exclusão no primeiro MVP.

### Respostas e erros

A API deve utilizar respostas previsíveis:

- `200` para consulta ou atualização bem-sucedida;
- `201` para criação;
- `400` para dados inválidos;
- `404` para recurso inexistente;
- `409` para conflito de atualização;
- `422` para regra de negócio inválida;
- `500` para erro inesperado.

Os erros devem conter uma mensagem compreensível para a interface, sem expor stack trace, credenciais ou caminhos internos.

---

## 8. Persistência e dados

### Banco recomendado para o MVP

SQLite é tecnicamente adequado se:

- a aplicação estiver em um único servidor;
- houver poucos usuários simultâneos;
- as operações forem curtas;
- não existirem grandes volumes de dados;
- o arquivo do banco não for compartilhado diretamente por vários computadores.

Os clientes devem acessar o banco somente por meio da aplicação. Não se deve colocar o arquivo SQLite em uma pasta de rede para que cada usuário o abra diretamente.

### Esquema conceitual

```text
users
-----
id
name
active
created_at

tasks
-----
id
title
description
status
assignee_id -> users.id
due_date
created_at
updated_at
completed_at
version
```

Restrições recomendadas:

- título obrigatório;
- status limitado a valores conhecidos;
- chave estrangeira para responsável;
- índices em `status`, `assignee_id` e `updated_at`;
- `version` incremental para controle de concorrência;
- timestamps armazenados de forma consistente, preferencialmente em UTC.

### Evolução para PostgreSQL

A migração para PostgreSQL deve ser considerada se houver:

- muitos acessos simultâneos;
- necessidade de execução em infraestrutura compartilhada;
- crescimento significativo do volume;
- maior exigência de disponibilidade;
- múltiplas instâncias da aplicação;
- relatórios ou consultas mais complexas.

Não há justificativa para adicionar PostgreSQL ao MVP apenas por precaução.

---

## 9. Integrações

### MVP

Não são necessárias integrações externas.

A solução pode operar completamente dentro da rede local, sem depender de:

- serviços de autenticação externos;
- serviços de notificação;
- APIs de calendário;
- e-mail;
- chat;
- armazenamento em nuvem.

### Integrações futuras possíveis

Somente após validação de necessidade:

- exportação CSV ou JSON;
- importação inicial a partir de planilha;
- calendário para prazos;
- mensageria para notificações;
- diretório corporativo para autenticação;
- armazenamento externo para backup.

Cada integração acrescentará credenciais, disponibilidade externa, tratamento de falhas e risco de exposição de dados.

---

## 10. Segurança

Mesmo sendo uma aplicação local, a rede interna não deve ser tratada como totalmente confiável.

### Controles mínimos

- escutar apenas na interface de rede necessária;
- não expor a aplicação diretamente à internet;
- validar e limitar tamanho de todos os campos;
- usar consultas parametrizadas;
- escapar conteúdo exibido na interface;
- proteger operações administrativas;
- não registrar senhas ou dados sensíveis em logs;
- controlar permissões do arquivo do banco e dos backups;
- manter o sistema operacional e o runtime atualizados;
- proteger o computador servidor com autenticação do sistema operacional;
- restringir o diretório de backup.

### Autenticação

Há duas opções:

#### Sem autenticação individual

Adequada se:

- a rede for pequena e controlada;
- qualquer usuário autorizado puder editar qualquer tarefa;
- o campo de responsável for apenas organizacional;
- não houver exigência de auditoria.

Nesse caso, o sistema deve deixar claro que o nome do responsável não comprova quem realizou a alteração.

#### Autenticação local

Recomendada se for necessário:

- saber quem alterou uma tarefa;
- restringir acesso;
- distinguir administradores de usuários comuns;
- manter alguma responsabilidade operacional.

A autenticação pode começar com contas locais e senhas armazenadas usando hash seguro. Não é necessário integrar um provedor externo no primeiro ciclo.

### Backup e proteção de dados

- backups não devem ficar disponíveis para download sem controle;
- arquivos de backup devem ter permissões restritas;
- cópias externas devem ser protegidas conforme a sensibilidade dos dados;
- o procedimento de restauração deve ser testado, não apenas o de criação;
- a equipe deve definir quem é responsável pela recuperação.

---

## 11. Requisitos não funcionais

Os valores abaixo são metas iniciais e devem ser validados com a equipe.

### Disponibilidade

- O sistema deve funcionar enquanto o servidor e a rede local estiverem disponíveis.
- A indisponibilidade do servidor deve ser claramente comunicada.
- O sistema não precisa de alta disponibilidade no MVP.

### Desempenho

- Consultas comuns devem responder rapidamente em uma rede local.
- Listagens devem ser paginadas ou limitadas quando o volume crescer.
- Operações de escrita devem ser curtas e transacionais.
- Backup deve ocorrer sem corromper ou bloquear indefinidamente o uso normal.

### Recuperação

- Deve existir uma forma documentada de restaurar a base.
- O backup deve incluir dados suficientes para reconstruir o sistema.
- A equipe deve definir o máximo aceitável de perda de dados, ainda que informalmente.

### Usabilidade

- Criar uma tarefa deve exigir poucos campos.
- O estado da tarefa deve ser compreensível sem treinamento extenso.
- Erros de validação devem ser exibidos próximos ao campo afetado.
- A interface deve funcionar em computadores usados pela equipe.
- O sistema deve continuar útil em uma rede sem internet.

### Manutenibilidade

- Configurações devem ficar fora do código quando possível.
- O esquema de dados deve ter migrações versionadas.
- A instalação deve ser reproduzível.
- O processo de backup e restauração deve estar documentado.
- O sistema deve ter testes para as regras de tarefa e status.

---

## 12. Observabilidade

A observabilidade deve ser proporcional ao tamanho do sistema. Não há necessidade inicial de uma plataforma externa de monitoramento.

### Logs

Registrar:

- inicialização e encerramento da aplicação;
- erros de banco;
- falhas de validação relevantes;
- falhas de backup;
- operações administrativas;
- conflitos de atualização;
- tempo e resultado de operações importantes.

Não registrar:

- senhas;
- tokens;
- conteúdo sensível desnecessário;
- dados completos de todas as tarefas em cada requisição.

Cada requisição deve possuir um identificador de correlação para facilitar a investigação de erros.

### Health check

Disponibilizar um endpoint simples:

```text
GET /api/health
```

Ele deve indicar, no mínimo:

- aplicação em execução;
- banco acessível;
- versão da aplicação;
- horário do último backup bem-sucedido, se disponível.

O endpoint não deve expor detalhes internos ou segredos.

### Métricas básicas

Podem ser coletadas localmente:

- quantidade de tarefas por status;
- quantidade de tarefas atrasadas;
- duração das requisições;
- quantidade de erros;
- último backup realizado;
- espaço disponível no disco, se for possível medir com segurança.

Inicialmente, logs estruturados e uma tela administrativa simples podem ser suficientes.

### Alertas operacionais

No MVP, os alertas podem ser manuais:

- exibir aviso quando o backup estiver atrasado;
- exibir erro quando o disco estiver próximo do limite;
- exibir o estado do sistema em uma página de diagnóstico.

Alertas por e-mail ou mensageria devem ser considerados apenas se a equipe realmente precisar deles.

---

## 13. Plano de implementação

### Fase 0 — validação das decisões

Confirmar:

- se o uso é compartilhado;
- se todos os usuários estarão na mesma rede;
- se a aplicação poderá rodar em um computador sempre disponível;
- se autenticação individual é necessária;
- quem será responsável por backup e restauração;
- quais campos são indispensáveis em uma tarefa;
- qual é o prazo ou restrição de ambiente.

Sem essas respostas, a arquitetura deve ser tratada como uma proposta-base, não como decisão definitiva.

### Fase 1 — núcleo funcional

Implementar:

- criação e edição de tarefas;
- alteração de status;
- atribuição opcional;
- listagem e filtros;
- banco local;
- validações;
- tratamento de erros;
- interface básica.

Critério de aceite: uma pequena equipe consegue registrar, acompanhar e concluir tarefas em uma única instalação.

### Fase 2 — operação compartilhada

Implementar:

- acesso por navegador na rede local;
- controle de concorrência;
- cadastro de usuários;
- configuração inicial;
- endpoint de saúde;
- logs estruturados;
- instruções de instalação e inicialização.

Critério de aceite: dois usuários conseguem utilizar o sistema sem sobrescrever silenciosamente as alterações um do outro.

### Fase 3 — proteção e recuperação

Implementar:

- exportação;
- backup consistente;
- restauração documentada;
- validação de arquivos de backup;
- permissões do diretório de dados;
- autenticação, se confirmada como necessária.

Critério de aceite: a equipe consegue recuperar a aplicação a partir de um backup testado.

### Fase 4 — melhorias condicionais

Avaliar somente com base no uso real:

- histórico de alterações;
- comentários;
- múltiplos projetos;
- notificações;
- anexos;
- integração com calendário;
- PostgreSQL;
- implantação em servidor dedicado.

---

## 14. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| “Local” ser interpretado de formas diferentes | Arquitetura inadequada | Confirmar o modelo de uso antes da implementação |
| Servidor desligado | Indisponibilidade para toda a equipe | Escolher máquina estável, documentar inicialização e avaliar servidor dedicado |
| Falha no disco | Perda dos dados | Backup frequente e cópia em outro dispositivo |
| Dois usuários editarem a mesma tarefa | Perda de alterações | Controle otimista e resposta de conflito |
| Escopo crescer para uma ferramenta completa | Atraso e maior manutenção | Definir MVP e critérios de inclusão |
| Rede local não ser confiável | Acesso indevido | Restringir exposição, autenticar quando necessário e proteger o host |
| Ninguém assumir a operação | Backups e atualizações não realizados | Nomear responsável e documentar rotina mínima |
| SQLite deixar de atender | Bloqueios ou degradação | Manter camada de persistência isolada e planejar migração somente quando necessário |

---

## 15. Decisão arquitetural recomendada

Adotar, como baseline:

- aplicativo web local;
- uma instalação centralizada;
- acesso pela rede local;
- backend servindo interface e API;
- SQLite no primeiro ciclo;
- tarefas e usuários como entidades principais;
- controle otimista de concorrência;
- exportação e backup local;
- autenticação opcional, condicionada ao requisito de identificação;
- nenhuma integração externa no MVP.

Essa arquitetura é suficiente para uma equipe pequena, reduz a complexidade operacional e preserva um caminho de evolução. A principal decisão pendente não é tecnológica: é confirmar se “local” significa colaboração em uma rede local ou uso individual.
