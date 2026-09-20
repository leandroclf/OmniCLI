# Arquitetura proposta — Plataforma de colaboração

## 1. Resumo executivo

A proposta ainda não contém informações suficientes para definir uma arquitetura definitiva. “Plataforma de colaboração” pode representar produtos muito diferentes: gestão de tarefas, comunicação, documentos, revisão de conteúdo, comunidades ou coordenação de equipes.

A recomendação é adotar uma arquitetura inicial evolutiva, capaz de suportar colaboração assíncrona sem assumir, prematuramente, recursos complexos como edição simultânea de documentos, videoconferência ou comunicação em tempo real.

A primeira versão deve ser construída como um **monólito modular**, com:

- API autenticada;
- aplicação web ou cliente equivalente;
- banco de dados relacional;
- armazenamento separado para arquivos;
- processamento assíncrono para notificações e tarefas demoradas;
- trilha de auditoria para eventos relevantes;
- observabilidade desde o início.

Essa escolha mantém o custo operacional e a complexidade sob controle, preservando a possibilidade de extrair componentes posteriormente se houver evidência de necessidade.

---

## 2. Fatos, hipóteses e recomendações

### Fatos fornecidos

- O objetivo geral é construir uma plataforma de colaboração.
- Não foram definidos:
  - público-alvo;
  - problema principal;
  - caso de uso prioritário;
  - modelo de acesso;
  - requisitos de segurança;
  - integrações;
  - volume esperado;
  - prazo;
  - equipe;
  - orçamento;
  - critérios de sucesso.

### Hipóteses de arquitetura

As seguintes hipóteses são necessárias apenas para produzir uma arquitetura de referência:

- A colaboração inicial será predominantemente assíncrona.
- Usuários precisarão pertencer a um ou mais espaços de colaboração.
- Haverá recursos compartilhados, como tarefas, comentários, mensagens ou documentos.
- O sistema precisará controlar acesso por usuário e espaço.
- Algumas operações poderão ser executadas fora da requisição principal.
- O produto poderá evoluir para um modelo multi-organização ou multi-tenant.

Essas hipóteses não devem ser tratadas como requisitos confirmados.

### Recomendações

- Validar um único fluxo principal antes de implementar módulos amplos.
- Priorizar colaboração assíncrona na primeira versão.
- Evitar iniciar com chat em tempo real, videoconferência, editor colaborativo ou busca avançada, salvo se forem indispensáveis ao problema validado.
- Preferir monólito modular a microsserviços.
- Separar claramente identidade, autorização, domínio, arquivos, notificações e auditoria.
- Manter decisões específicas de fornecedor ou nuvem fora do núcleo de domínio.

---

## 3. Escopo arquitetural inicial recomendado

O menor núcleo tecnicamente viável deve permitir:

1. autenticação de usuários;
2. criação ou participação em um espaço de colaboração;
3. criação e acompanhamento de um recurso compartilhado;
4. comentários ou atualizações relacionadas a esse recurso;
5. controle de permissões;
6. notificações básicas;
7. histórico de alterações relevantes.

O “recurso compartilhado” deve ser definido pelo produto. Pode ser uma tarefa, discussão, documento, solicitação, item de projeto ou outro objeto central.

A arquitetura não deve presumir que todos esses recursos coexistirão na primeira entrega. O núcleo pode começar com um único tipo de recurso.

---

## 4. Arquitetura lógica

```text
Cliente web ou aplicativo
          |
          v
API / camada de entrada
          |
          v
Monólito modular
├── Identidade e sessão
├── Organizações e espaços
├── Autorização
├── Domínio colaborativo
├── Comentários e atividade
├── Notificações
├── Arquivos e anexos
├── Auditoria
└── Administração
          |
          ├── Banco relacional
          ├── Armazenamento de arquivos
          ├── Fila ou mecanismo assíncrono
          └── Serviço de e-mail/push, se necessário
```

### Componentes

#### Cliente

Responsável por:

- autenticação;
- navegação pelos espaços;
- visualização e alteração dos recursos;
- envio de comentários;
- upload de arquivos, se aplicável;
- exibição de notificações e histórico;
- tratamento de estados de carregamento, erro e conflito.

O cliente não deve concentrar regras críticas de autorização. Toda permissão deve ser validada no servidor.

#### API

Responsável por:

- receber requisições;
- validar formato e limites de entrada;
- autenticar o usuário;
- autorizar a operação;
- chamar os módulos de domínio;
- padronizar respostas e erros;
- registrar correlação e métricas;
- publicar eventos para processamento assíncrono quando necessário.

A API deve evitar expor diretamente tabelas ou estruturas internas do banco.

#### Módulo de identidade

Responsável por:

- usuários;
- credenciais ou integração com provedor de identidade;
- sessões e tokens;
- recuperação de acesso;
- verificação de e-mail, caso necessária;
- estados de usuário, como ativo, bloqueado ou removido.

A opção entre autenticação própria e provedor externo depende de requisitos comerciais, corporativos e regulatórios ainda não informados.

#### Módulo de espaços e organização

Responsável por:

- organizações, equipes ou espaços;
- associação entre usuários e espaços;
- papéis básicos;
- convite e remoção de membros;
- configurações do espaço.

Esse módulo deve ser desenhado para permitir isolamento lógico entre organizações, mesmo que o primeiro lançamento tenha apenas um contexto organizacional.

#### Módulo de autorização

Deve centralizar as decisões de acesso.

Modelo inicial recomendado:

- usuário;
- espaço;
- papel;
- permissão;
- relação do usuário com o recurso.

Uma implementação inicial baseada em papéis pode ser suficiente:

- administrador;
- membro;
- colaborador limitado;
- leitor.

Permissões mais granulares devem ser adicionadas somente quando houver necessidade comprovada. Um sistema de autorização excessivamente flexível aumenta o risco de falhas e complexidade operacional.

#### Módulo de domínio colaborativo

Representa o principal fluxo do produto.

Responsável por:

- criação e atualização do recurso central;
- estados e transições;
- regras de negócio;
- participantes;
- comentários ou interações;
- validação de conflitos;
- publicação de eventos de domínio.

Esse módulo deve conter regras de negócio, não apenas operações CRUD.

#### Módulo de arquivos

Caso anexos sejam necessários, os arquivos devem ser armazenados fora do banco relacional, em armazenamento de objetos ou serviço equivalente.

O banco deve armazenar apenas metadados, como:

- identificador;
- nome original;
- tipo declarado;
- tamanho;
- localização interna;
- proprietário;
- recurso relacionado;
- estado de processamento;
- checksum, quando aplicável;
- data de criação;
- data de remoção lógica.

Uploads devem utilizar URLs temporárias ou fluxo equivalente, evitando transportar arquivos grandes pelo processo principal da API.

#### Módulo de notificações

Responsável por:

- notificações dentro da aplicação;
- preferências do usuário;
- eventos que geram notificações;
- deduplicação;
- controle de falhas;
- entrega por e-mail ou outros canais, caso necessários.

As notificações devem ser processadas de forma assíncrona quando não forem necessárias para concluir a operação principal.

#### Módulo de auditoria

Deve registrar eventos relevantes, como:

- alteração de permissões;
- inclusão ou remoção de membros;
- alterações sensíveis;
- acesso administrativo;
- exclusão ou restauração de dados;
- mudanças de configuração.

A auditoria não deve depender exclusivamente dos logs de aplicação. Logs técnicos e trilha de auditoria têm objetivos diferentes.

---

## 5. Fluxos principais

### 5.1 Autenticação

```text
Cliente
  → API: solicitação de autenticação
  → Identidade: valida credencial ou provedor
  → API: cria sessão ou emite tokens
  → Cliente: recebe contexto autenticado
```

Requisitos:

- não armazenar senhas em texto puro;
- aplicar política adequada de sessão;
- invalidar sessões quando necessário;
- limitar tentativas;
- registrar eventos de segurança;
- evitar revelar se um usuário existe em fluxos de recuperação.

### 5.2 Leitura de recurso

```text
Cliente
  → API: consulta recurso
  → Autenticação: identifica usuário
  → Autorização: verifica acesso
  → Domínio: busca e monta representação
  → API: retorna resposta
```

A autorização deve ocorrer antes de expor dados do recurso ou de seus relacionamentos.

### 5.3 Criação ou alteração

```text
Cliente
  → API: envia comando
  → API: valida entrada
  → Autorização: verifica permissão
  → Domínio: aplica regra de negócio
  → Banco: grava transação
  → Auditoria: registra evento relevante
  → Fila: publica tarefas secundárias
  → API: retorna resultado
```

A resposta não deve depender de e-mail ou notificações que não são essenciais para concluir a alteração.

### 5.4 Comentário ou atividade

O comentário deve estar vinculado ao recurso e ao espaço autorizado.

A operação deve:

- validar tamanho e conteúdo;
- impedir associação a recursos inexistentes ou inacessíveis;
- registrar autor e horário;
- manter histórico de edição ou exclusão conforme a política definida;
- gerar notificações de forma assíncrona, se necessário.

### 5.5 Upload de arquivo

```text
Cliente → API: solicita autorização de upload
API → Cliente: fornece operação temporária
Cliente → Armazenamento: envia arquivo
Cliente → API: confirma upload
API → Banco: grava metadados
Worker → Armazenamento: valida ou processa arquivo
```

O sistema deve tratar uploads incompletos, arquivos malformados, tipos proibidos, tamanho excedido e falhas de processamento.

### 5.6 Notificação assíncrona

```text
Evento de domínio
  → Fila
  → Worker
  → Preferências do usuário
  → Canal de entrega
  → Registro de sucesso ou falha
```

O processamento deve ser idempotente para suportar reentregas.

---

## 6. Modelo de dados conceitual

O modelo abaixo é uma referência e precisa ser adaptado ao caso de uso confirmado.

### Entidades principais

- `User`
- `Organization` ou `Workspace`
- `Membership`
- `Role`
- `Permission`
- `CollaborativeResource`
- `ResourceParticipant`
- `Comment`
- `Attachment`
- `Notification`
- `AuditEvent`
- `OutboxEvent`

### Relacionamentos essenciais

```text
Usuário ──< Membership >── Espaço
Espaço ──< Recurso colaborativo
Usuário ──< Comentário >── Recurso
Recurso ──< Anexo
Usuário ──< Notificação
Espaço ──< Evento de auditoria
```

### Regras de persistência

- Cada entidade pertencente a um espaço deve carregar uma referência explícita ao espaço.
- Índices devem refletir as consultas reais, principalmente por:
  - espaço;
  - usuário;
  - estado;
  - data de atualização;
  - recurso relacionado.
- Exclusões devem ser avaliadas caso a caso:
  - exclusão física para dados descartáveis;
  - exclusão lógica quando houver necessidade de histórico, auditoria ou restauração.
- Alterações importantes devem ter controle de concorrência, por versão, timestamp ou mecanismo equivalente.
- Eventos destinados a processamento assíncrono devem usar o padrão Outbox ou mecanismo equivalente para evitar divergência entre transação e publicação.

---

## 7. Integrações

Nenhuma integração externa foi especificada. Portanto, a arquitetura deve tratar integrações como pontos substituíveis.

### Categorias prováveis

- provedor de identidade;
- serviço de e-mail;
- armazenamento de arquivos;
- mecanismo de filas;
- serviço de busca;
- ferramenta de calendário;
- sistemas corporativos;
- monitoramento e alertas.

### Recomendação de desenho

Cada integração deve possuir um adaptador interno com:

- contrato definido pelo domínio;
- tratamento de timeout;
- retry limitado;
- idempotência;
- circuit breaker apenas se o comportamento justificar;
- métricas de sucesso e falha;
- logs sem exposição de segredos;
- estratégia de degradação.

Não se deve acoplar regras de negócio diretamente ao SDK de um fornecedor.

### Estratégia inicial

Começar apenas com integrações necessárias ao fluxo principal. Para cada integração futura, registrar:

- finalidade;
- dados enviados;
- dados recebidos;
- responsável pelo contrato;
- limites e falhas esperadas;
- requisito de disponibilidade;
- estratégia de substituição ou desligamento.

---

## 8. Requisitos não funcionais

Os valores abaixo são propostas iniciais, não compromissos de serviço. Devem ser confirmados após conhecer usuários, volume e criticidade.

### Disponibilidade

- Definir se o produto é interno, comercial ou crítico para operação.
- Estabelecer janela de manutenção e comportamento em indisponibilidade.
- Garantir que falhas em notificações não impeçam operações principais.

### Desempenho

Como meta inicial de produto, pode-se medir:

- tempo de resposta de consultas comuns;
- tempo de resposta de comandos;
- tempo para carregar a tela principal;
- tempo de conclusão de uploads;
- atraso na entrega de notificações.

Percentis, como p95 ou p99, devem ser definidos com base no uso real, não apenas em médias.

### Escalabilidade

A primeira arquitetura deve escalar verticalmente e horizontalmente dentro dos limites do monólito.

Pontos que podem exigir evolução independente:

- processamento de arquivos;
- notificações;
- busca;
- atividades em tempo real;
- relatórios;
- ingestão de eventos.

A adoção de microsserviços não é recomendada sem sinais concretos de necessidade organizacional, técnica ou de escala.

### Consistência

- Alterações do recurso principal devem ser transacionais.
- Notificações e integrações secundárias podem ser eventualmente consistentes.
- A interface deve indicar quando uma operação assíncrona ainda está em processamento.
- Operações repetidas pelo cliente não devem criar duplicidades indevidas.

### Recuperação

Definir:

- política de backup;
- ponto máximo aceitável de perda de dados;
- tempo máximo aceitável de recuperação;
- retenção de backups;
- procedimento de restauração testado.

Não é possível especificar RPO ou RTO sem conhecer a criticidade do negócio.

### Evolução

- Contratos da API devem ter versionamento ou compatibilidade planejada.
- Migrações de banco devem ser reversíveis quando possível.
- Novos campos devem ser introduzidos de modo compatível.
- Funcionalidades experimentais devem ser isoláveis por configuração ou feature flag, se necessário.

---

## 9. Segurança e privacidade

### Identidade

- Senhas, quando houver autenticação própria, devem ser armazenadas com algoritmo apropriado e parâmetros atualizados.
- Tokens e sessões devem ter expiração e revogação.
- Operações sensíveis devem permitir reautenticação ou autenticação reforçada quando aplicável.
- Contas administrativas devem ser protegidas com controles adicionais.

### Autorização

- Negar por padrão.
- Validar acesso no servidor para cada operação.
- Impedir que identificadores previsíveis permitam acesso direto a recursos de outro espaço.
- Testar explicitamente isolamento entre organizações.
- Separar privilégios administrativos de privilégios operacionais.

### Entrada e conteúdo

- Validar formato, tamanho, cardinalidade e codificação.
- Sanitizar conteúdo exibido em HTML.
- Limitar tipos e tamanhos de arquivo.
- Não confiar em extensão ou `Content-Type` enviado pelo cliente.
- Aplicar proteção contra abuso, automação e excesso de requisições.

### Dados e segredos

- Criptografar comunicação em trânsito.
- Proteger dados armazenados conforme sua sensibilidade.
- Nunca registrar senhas, tokens, chaves ou conteúdo sensível sem necessidade.
- Gerenciar segredos fora do código-fonte.
- Restringir acesso operacional ao mínimo necessário.

### Auditoria

Registrar, no mínimo:

- identidade do autor;
- ação;
- recurso afetado;
- espaço ou organização;
- horário;
- resultado;
- origem técnica relevante;
- correlação da requisição.

A retenção desses registros depende de requisitos de negócio e legais, que ainda não foram fornecidos.

### Privacidade

Antes da implementação comercial, devem ser definidas:

- categorias de dados pessoais;
- finalidade de tratamento;
- retenção;
- exportação;
- correção;
- exclusão;
- controle de acesso interno;
- responsabilidades entre operadores e controladores, quando aplicável.

Não se deve assumir requisitos legais específicos sem conhecer jurisdição e contexto.

---

## 10. Observabilidade

### Logs

Logs estruturados devem conter:

- timestamp;
- nível;
- serviço ou módulo;
- ambiente;
- identificador de correlação;
- identificador do usuário, quando seguro;
- identificador do espaço, quando seguro;
- operação;
- resultado;
- duração;
- código de erro.

Devem evitar:

- tokens;
- senhas;
- dados completos de arquivos;
- conteúdo privado de mensagens;
- informações pessoais desnecessárias.

### Métricas

Métricas iniciais:

- taxa de requisições;
- latência por operação;
- erros por endpoint e categoria;
- autenticações bem-sucedidas e falhas;
- recusas de autorização;
- tamanho e atraso da fila;
- falhas de processamento;
- uploads concluídos e rejeitados;
- notificações enviadas e falhas;
- conexões e saturação do banco;
- uso de armazenamento.

### Rastreamento

Rastreamento distribuído é recomendável quando houver múltiplos processos, workers ou integrações. Em um monólito inicial, a correlação entre logs e eventos pode ser suficiente, desde que consistente.

### Alertas

Alertas devem representar impacto operacional, por exemplo:

- erro elevado em operações principais;
- fila crescendo continuamente;
- falha de envio de notificações;
- banco próximo do limite;
- aumento anormal de recusas de autorização;
- falha de backup;
- degradação persistente de latência.

Alertas baseados apenas em uma exceção isolada tendem a gerar ruído.

---

## 11. Decisões arquiteturais recomendadas

### ADR-001 — Monólito modular para a primeira versão

**Decisão:** iniciar com um único deploy organizado por módulos de domínio.

**Motivo:** os requisitos, limites de escala e fronteiras organizacionais ainda são desconhecidos. O monólito reduz complexidade de rede, deploy, observabilidade e transações distribuídas.

**Alternativas consideradas:**

- microsserviços desde o início;
- arquitetura serverless distribuída;
- backend sem separação explícita de módulos.

**Trade-off:** menor complexidade inicial, com necessidade de disciplina para evitar acoplamento interno.

### ADR-002 — Banco relacional como fonte principal

**Decisão:** usar um banco relacional para usuários, permissões, recursos, comentários e auditoria operacional.

**Motivo:** colaboração normalmente exige relações, filtros, transações e consistência entre entidades.

**Trade-off:** algumas funcionalidades futuras, como busca textual avançada ou presença em tempo real, podem precisar de componentes especializados.

### ADR-003 — Arquivos fora do banco

**Decisão:** armazenar arquivos em armazenamento dedicado e metadados no banco.

**Motivo:** reduz crescimento do banco e permite processamento, expiração e distribuição independentes.

**Trade-off:** exige coordenação entre metadados e armazenamento, incluindo limpeza de uploads incompletos.

### ADR-004 — Processamento assíncrono para efeitos secundários

**Decisão:** usar fila ou mecanismo equivalente para notificações, processamento de arquivos e integrações não críticas.

**Motivo:** reduz latência da API e isola falhas externas.

**Trade-off:** introduz consistência eventual, reentrega e necessidade de idempotência.

### ADR-005 — Tempo real somente mediante validação

**Decisão:** não assumir WebSocket, edição simultânea ou presença online na primeira arquitetura.

**Motivo:** esses recursos mudam significativamente o modelo de concorrência, escalabilidade e observabilidade.

**Condição para adoção:** evidência de que o fluxo principal não funciona adequadamente com atualização sob demanda, polling controlado ou notificações assíncronas.

---

## 12. Plano de implementação

### Fase 0 — Definição e validação

Entregáveis:

- público-alvo;
- problema observável;
- fluxo principal;
- alternativa atual;
- critério de sucesso;
- tipo de recurso compartilhado;
- política inicial de acesso;
- restrições de prazo e operação.

Critério de saída:

> Uma frase de problema validada e um fluxo principal que possa ser demonstrado de ponta a ponta.

### Fase 1 — Fundação técnica

Implementar:

- estrutura do monólito modular;
- configuração por ambiente;
- persistência;
- migrações;
- autenticação;
- autorização básica;
- tratamento padronizado de erros;
- logs estruturados;
- testes automatizados essenciais;
- pipeline de build e validação.

### Fase 2 — Fluxo principal

Implementar somente:

- espaço de colaboração;
- recurso central;
- criação;
- consulta;
- atualização;
- regras de estado;
- participação dos usuários;
- histórico mínimo.

Critério de saída:

> Um usuário consegue concluir o fluxo principal sem intervenção manual da equipe.

### Fase 3 — Colaboração complementar

Adicionar, se necessário ao fluxo:

- comentários;
- menções;
- anexos;
- notificações internas;
- preferências;
- atividade recente;
- auditoria ampliada.

### Fase 4 — Operação controlada

Adicionar:

- backups testados;
- métricas e alertas;
- limites de requisição;
- revisão de permissões;
- testes de carga direcionados;
- testes de recuperação;
- documentação operacional;
- piloto com usuários representativos.

### Fase 5 — Evolução baseada em evidência

Somente após observar uso real avaliar:

- busca especializada;
- tempo real;
- integrações corporativas;
- processamento independente de arquivos;
- separação de serviços;
- escalabilidade por módulo;
- recursos administrativos avançados.

---

## 13. Critérios de aceitação arquitetural

A arquitetura deve ser considerada pronta para implementação apenas quando:

- o problema e o usuário inicial estiverem definidos;
- houver um fluxo principal único;
- o modelo de acesso inicial estiver documentado;
- os dados sensíveis estiverem classificados;
- os requisitos mínimos de disponibilidade e recuperação estiverem acordados;
- o volume esperado tiver ao menos uma estimativa;
- as integrações obrigatórias estiverem identificadas;
- houver critérios objetivos de sucesso;
- as decisões relevantes estiverem registradas;
- o escopo da primeira versão estiver limitado.

## 14. Riscos e pontos de atenção

- A ausência de um caso de uso específico pode levar à construção de um produto genérico e pouco adotado.
- Permissões podem se tornar o maior ponto de complexidade se forem modeladas de forma excessivamente flexível.
- Arquivos e notificações tendem a introduzir processamento assíncrono e problemas de consistência.
- Recursos em tempo real podem exigir uma arquitetura diferente da recomendada para o MVP.
- Multi-tenancy, retenção e auditoria podem alterar significativamente o modelo de dados.
- Integrações externas não devem definir o domínio antes que o fluxo de negócio esteja claro.
- Uma arquitetura tecnicamente sólida não compensa ausência de validação de produto.

## Conclusão

A arquitetura tecnicamente viável, dado o nível atual de informação, é um **monólito modular orientado a domínio, com banco relacional, armazenamento separado para arquivos, processamento assíncrono e controles de segurança e observabilidade desde o início**.

Essa é uma arquitetura de referência, não uma especificação final. Antes de escolher tecnologias, dimensionar infraestrutura ou iniciar módulos adicionais, é necessário validar o usuário, o problema e o fluxo colaborativo prioritário.
