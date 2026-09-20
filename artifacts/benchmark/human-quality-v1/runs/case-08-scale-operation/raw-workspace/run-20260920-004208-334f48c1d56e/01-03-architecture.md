# Arquitetura proposta — API global com picos sazonais e orçamento limitado

## 1. Resumo executivo

Recomenda-se iniciar com uma arquitetura global na borda, mas com uma única região primária de processamento, mantendo os componentes de aplicação stateless e escaláveis horizontalmente.

A solução deve combinar:

- ponto de entrada global com TLS, proteção contra abuso e limitação de tráfego;
- cache somente para endpoints comprovadamente cacheáveis;
- camada de API stateless com escalabilidade automática e limite máximo de capacidade;
- processamento assíncrono para operações demoradas ou não críticas;
- armazenamento principal dimensionado para o padrão de consistência exigido;
- filas e backpressure para absorver picos controláveis;
- degradação funcional explícita quando a capacidade ou o orçamento forem atingidos;
- observabilidade de capacidade, custo, dependências e experiência do cliente.

A recomendação não é começar com multi-região ativo-ativo. Essa opção deve ser habilitada somente se os requisitos de latência, disponibilidade, residência de dados ou recuperação de desastre justificarem o custo e a complexidade.

---

## 2. Fatos fornecidos

- A API terá alcance global.
- A demanda terá picos sazonais.
- O orçamento é limitado.
- Não foram informados:
  - volume médio e máximo de requisições;
  - duração e previsibilidade dos picos;
  - distribuição geográfica dos usuários;
  - requisitos de disponibilidade e latência;
  - tipo de dados processados;
  - dependências externas;
  - requisitos de residência ou retenção de dados;
  - teto financeiro mensurável.

---

## 3. Hipóteses de arquitetura

As decisões abaixo são hipóteses de trabalho e precisam ser validadas:

- A maior parte da aplicação pode ser executada sem manter estado na instância da API.
- Parte das operações pode ser processada de forma assíncrona.
- Os picos sazonais são parcialmente previsíveis.
- Nem todas as respostas exigem consistência imediata.
- É aceitável limitar, enfileirar ou degradar determinados tipos de tráfego em situações extremas.
- Uma região primária atende inicialmente aos requisitos de processamento, desde que a latência global seja validada.
- O orçamento limitado exige controle de capacidade, e não apenas alertas financeiros.

Se qualquer uma dessas hipóteses for falsa, a arquitetura deverá ser ajustada antes da implementação.

---

## 4. Decisões arquiteturais recomendadas

### 4.1 Estratégia de implantação global

Adotar três camadas lógicas:

1. **Borda global**
   - DNS ou roteamento global;
   - CDN quando houver conteúdo cacheável;
   - proteção contra DDoS e abuso;
   - terminação TLS;
   - rate limiting e quotas.

2. **Região primária**
   - gateway ou balanceador;
   - camada de API stateless;
   - workers assíncronos;
   - cache interno, quando aplicável;
   - banco de dados e armazenamento de objetos;
   - filas e mecanismos de processamento.

3. **Recuperação**
   - backups;
   - replicação ou cópia para uma segunda região, conforme criticidade;
   - procedimento de restauração;
   - failover inicialmente manual ou semiautomático, se o orçamento não comportar operação multi-região contínua.

Essa topologia separa alcance global de processamento multi-região. Clientes podem acessar a API internacionalmente sem exigir que toda a aplicação seja executada em todas as regiões.

### 4.2 Modelo de capacidade

A capacidade deve ser controlada por quatro mecanismos complementares:

- **Escalonamento automático**, para variações sustentadas;
- **Pré-aquecimento ou aumento planejado**, para picos sazonais conhecidos;
- **Filas e backpressure**, para operações que não precisam terminar na requisição;
- **Rate limiting e quotas**, para impedir que um consumidor ou evento consuma toda a capacidade.

O autoscaling deve possuir limites mínimo e máximo. Escalar sem limite protege a disponibilidade, mas pode violar o orçamento ou saturar dependências.

### 4.3 Separação entre operações síncronas e assíncronas

As operações devem ser classificadas desde o contrato da API:

- **Síncronas:** respostas rápidas, baixa variabilidade de processamento e necessidade de resultado imediato.
- **Assíncronas:** processamento demorado, alto custo, integração com terceiros ou possibilidade de execução posterior.
- **Degradáveis:** funcionalidades secundárias que podem ser adiadas, desativadas ou respondidas por cache durante sobrecarga.

Para operações assíncronas, o fluxo recomendado é:

1. API valida a solicitação.
2. API registra a intenção ou comando com identificador idempotente.
3. API publica uma mensagem em uma fila.
4. Worker processa a mensagem.
5. O resultado é persistido.
6. O cliente consulta o status ou recebe notificação, caso esse mecanismo seja necessário.
7. Falhas são encaminhadas para retry controlado e, posteriormente, DLQ.

### 4.4 Banco de dados

A escolha depende do padrão de acesso, mas a arquitetura deve preservar estas propriedades:

- separação entre dados transacionais e dados temporários;
- índices definidos a partir de consultas reais;
- controle de concorrência;
- paginação obrigatória em consultas potencialmente grandes;
- limites de conexão;
- pool de conexões compatível com o número de instâncias;
- backups e testes periódicos de restauração.

Se o banco for relacional, a camada de aplicação deve evitar criar uma conexão por requisição ou por instância sem limite. Se o padrão for predominantemente chave-valor e de alta escala, um armazenamento distribuído pode ser mais adequado.

Não se recomenda escolher entre banco relacional, NoSQL ou outro mecanismo sem conhecer:

- volume de escrita;
- necessidade de transações;
- consultas;
- consistência;
- retenção;
- distribuição geográfica;
- tamanho dos registros.

### 4.5 Cache

O cache deve ser aplicado por endpoint, e não globalmente.

Cada endpoint deve ser classificado por:

- possibilidade de compartilhamento entre consumidores;
- tolerância a dados obsoletos;
- sensibilidade dos dados;
- necessidade de invalidação;
- custo de recomputação;
- impacto de cache miss.

Dados personalizados, sensíveis ou dependentes da identidade do cliente não devem entrar em cache compartilhado sem uma política rigorosa de chave, autorização e expiração.

---

## 5. Componentes lógicos

| Componente | Responsabilidade | Decisões importantes |
|---|---|---|
| DNS/roteamento global | Direcionar clientes para a entrada da API | Estratégia de failover e health checks |
| CDN, quando aplicável | Cache de respostas e redução de latência | Somente para conteúdo cacheável |
| WAF/antiabuso | Filtrar tráfego malicioso e anômalo | Regras, falsos positivos e exceções |
| Gateway de API | TLS, autenticação, quotas, roteamento e limites | Política por consumidor e operação |
| Serviço de API | Regras síncronas e orquestração | Stateless, timeouts e idempotência |
| Cache | Reduzir chamadas repetidas e carga | TTL, invalidação e proteção de dados |
| Fila | Absorver picos e desacoplar processamento | Ordenação, visibilidade, retry e DLQ |
| Workers | Processar comandos assíncronos | Concorrência, idempotência e limites |
| Banco transacional | Dados de negócio e estados | Consistência, índices e backup |
| Armazenamento de objetos | Arquivos, exportações, logs de negócio ou backups | Retenção, criptografia e lifecycle |
| Serviço de identidade | Autenticação e identidade do consumidor | Rotação, escopos e revogação |
| Observabilidade | Métricas, logs, traces e alertas | Correlação e controle de custo |
| Controle financeiro | Acompanhar e conter consumo | Limites operacionais e ação de emergência |

A implementação concreta pode usar serviços gerenciados ou componentes autogerenciados. A escolha do provedor não deve ser feita antes da análise de tráfego, requisitos regulatórios e custos de transferência.

---

## 6. Fluxos principais

### 6.1 Requisição síncrona

```text
Cliente
  |
  v
DNS/roteamento global
  |
  v
WAF + rate limiting + autenticação
  |
  v
Gateway
  |
  v
API stateless
  | \
  |  \--> Cache, quando permitido
  |
  v
Banco ou serviço externo
  |
  v
Resposta ao cliente
```

Regras essenciais:

- timeout total definido;
- timeout individual por dependência;
- número limitado de retries;
- retry somente para erros transitórios;
- uso de idempotência em operações de escrita;
- resposta padronizada para limitação de tráfego;
- não expor detalhes internos de falhas.

### 6.2 Requisição assíncrona

```text
Cliente
  |
  v
API
  |
  +--> Registra comando e idempotency key
  |
  +--> Publica mensagem
           |
           v
        Fila
           |
           v
        Worker
           |
           +--> Serviço externo
           +--> Banco
           +--> Armazenamento
           |
           v
      Estado concluído ou falho
```

A resposta inicial deve indicar que o processamento foi aceito, sem declarar sucesso do processamento final.

### 6.3 Pico sazonal planejado

Antes do evento:

1. estimar volume e duração;
2. validar limites das dependências;
3. aumentar capacidade mínima temporariamente;
4. preparar regras de rate limiting;
5. pré-aquecer componentes que tenham inicialização lenta;
6. congelar mudanças de alto risco;
7. executar teste de carga representativo;
8. definir responsáveis e critérios de escalonamento.

Durante o evento:

- acompanhar saturação, latência e erros;
- controlar consumo por cliente;
- priorizar operações críticas;
- reduzir funcionalidades secundárias;
- evitar retries indiscriminados;
- aumentar trabalhadores assíncronos apenas até o limite das dependências.

Após o evento:

- reduzir capacidade gradualmente;
- revisar custos;
- analisar filas, erros e latência;
- registrar o comportamento observado para o próximo ciclo.

### 6.4 Pico extremo ou abuso

Quando os limites forem excedidos:

1. bloquear tráfego claramente malicioso;
2. aplicar quotas por consumidor;
3. preservar operações críticas;
4. enfileirar operações tolerantes a atraso;
5. servir respostas cacheadas quando seguro;
6. desabilitar funcionalidades não essenciais;
7. rejeitar novas solicitações com resposta explícita e documentada;
8. acionar o procedimento de incidente.

Um alerta de custo sem mecanismo de contenção não deve ser considerado proteção orçamentária.

---

## 7. Modelo de dados operacional

Independentemente do banco escolhido, os conceitos abaixo devem existir.

### Identidade e consumo

- consumidor;
- credencial ou vínculo de identidade;
- escopos e permissões;
- plano ou classe de prioridade;
- quota;
- limite de burst;
- status de bloqueio.

### Idempotência

- chave de idempotência;
- consumidor associado;
- operação;
- hash ou representação da solicitação;
- estado;
- resposta ou referência do resultado;
- expiração.

A mesma chave não deve ser reutilizada para solicitações semanticamente diferentes.

### Processamento assíncrono

- identificador do comando;
- tipo da operação;
- estado: recebido, processando, concluído, falho ou cancelado;
- número de tentativas;
- timestamps;
- erro sanitizado;
- referência do resultado;
- correlação da requisição original.

### Telemetria de negócio

- consumidor;
- operação;
- status;
- latência;
- região;
- tamanho aproximado da solicitação e resposta;
- custo estimado por classe de operação, quando disponível.

Dados pessoais e segredos não devem ser registrados nesse modelo.

---

## 8. Integrações

As integrações externas devem ser tratadas como recursos potencialmente lentos, indisponíveis ou limitados.

Para cada dependência, documentar:

- contrato e versão;
- autenticação;
- limite de requisições;
- timeout;
- códigos de erro;
- comportamento de retry;
- necessidade de idempotência;
- custo variável;
- dados enviados;
- dados retornados;
- política de fallback;
- contato ou procedimento de incidente.

A integração deve possuir um adaptador próprio para evitar espalhar detalhes de terceiros por toda a aplicação.

### Política de resiliência

- timeout curto e explícito;
- circuit breaker ou mecanismo equivalente quando necessário;
- bulkhead para impedir que uma integração consuma todos os recursos;
- retry com backoff e jitter;
- limite de tentativas;
- DLQ para mensagens não processáveis;
- fallback somente quando o resultado alternativo for semanticamente seguro.

Não se deve aplicar retry automaticamente a toda falha. Retries podem multiplicar a carga justamente quando a dependência está degradada.

---

## 9. Requisitos não funcionais propostos

Os valores abaixo são pontos de partida, não compromissos finais.

### Disponibilidade

Definir disponibilidade por operação, e não apenas para a API inteira:

- operações críticas;
- operações secundárias;
- processamento assíncrono;
- endpoints administrativos.

A arquitetura inicial pode oferecer uma meta inferior à de uma topologia multi-região ativa-ativo, desde que isso seja explícito.

### Latência

Medir pelo menos:

- p50;
- p95;
- p99;
- latência por região de origem;
- latência sem cache;
- latência das dependências;
- tempo de permanência em fila.

A meta deve diferenciar endpoints síncronos de operações assíncronas.

### Capacidade

Dimensionar e testar:

- requisições por segundo;
- concorrência;
- tamanho das mensagens;
- taxa de leitura e escrita;
- profundidade máxima da fila;
- tempo máximo de espera;
- limite das integrações externas;
- conexões com o banco.

### Elasticidade

Definir:

- tempo máximo para aumentar capacidade;
- capacidade mínima fora do pico;
- capacidade máxima;
- critérios de escalonamento;
- capacidade reservada para operações críticas;
- comportamento quando o limite máximo for atingido.

### Recuperação

Estabelecer:

- RPO — perda máxima aceitável de dados;
- RTO — tempo máximo aceitável para recuperação;
- frequência de backup;
- retenção;
- local de armazenamento;
- procedimento de restauração;
- periodicidade dos testes.

### Custo

Acompanhar pelo menos:

- computação;
- banco;
- filas;
- armazenamento;
- transferência de dados;
- observabilidade;
- chamadas a serviços externos;
- ambientes não produtivos;
- capacidade adicional durante picos.

O orçamento deve possuir:

- limite normal;
- reserva de emergência;
- responsável pela decisão;
- ação automática ou manual de contenção;
- critério para priorização de consumidores.

---

## 10. Segurança

### Entrada e autenticação

- TLS obrigatório;
- autenticação adequada ao tipo de consumidor;
- autorização por escopo, recurso e operação;
- validação rigorosa de payloads;
- limite de tamanho de requisição;
- proteção contra replay quando aplicável;
- rotação de credenciais;
- revogação de tokens ou chaves comprometidos.

### Autorização

A autorização não deve depender apenas do gateway. A aplicação deve validar:

- identidade;
- escopo;
- vínculo com o recurso;
- estado do recurso;
- classe de operação;
- regras de segregação entre consumidores.

### Segredos

- armazenar segredos em serviço próprio de gerenciamento;
- nunca versionar credenciais;
- evitar segredos em logs, variáveis expostas ou mensagens;
- rotacionar credenciais;
- limitar acesso por identidade de workload.

### Proteção contra abuso

- rate limiting por identidade;
- quotas por contrato;
- limites por operação;
- detecção de comportamento anômalo;
- proteção contra payloads excessivos;
- bloqueio de padrões de ataque;
- tratamento especial para tráfego não autenticado.

Limitar apenas por IP pode penalizar usuários legítimos atrás de NAT ou proxies compartilhados.

### Dados

Classificar os dados por sensibilidade e definir:

- criptografia em trânsito e em repouso;
- retenção;
- mascaramento;
- acesso operacional;
- auditoria;
- exclusão;
- localização de processamento.

Requisitos legais e regulatórios não podem ser inferidos sem conhecer os países, os dados tratados e o modelo de negócio.

---

## 11. Observabilidade

A observabilidade deve permitir responder a quatro perguntas:

1. A API está disponível?
2. Está rápida o suficiente?
3. Qual componente está saturado?
4. Quanto o evento está custando?

### Métricas técnicas

- taxa de requisições;
- taxa de erros por classe;
- p50, p95 e p99;
- concorrência;
- saturação de CPU, memória e conexões;
- reinicializações;
- taxa de cache hit/miss;
- profundidade e idade das filas;
- tempo de processamento dos workers;
- retries;
- circuit breakers acionados;
- erros e latência por dependência;
- capacidade usada versus limite máximo.

### Métricas de negócio

- operações concluídas;
- operações rejeitadas por quota;
- operações degradadas;
- comandos pendentes;
- taxa de sucesso por consumidor;
- volume por região;
- consumo por classe de operação;
- custo estimado por unidade de negócio.

### Logs

Os logs devem ser estruturados e conter:

- timestamp;
- nível;
- ambiente;
- serviço;
- versão;
- request ID;
- correlation ID;
- consumidor pseudonimizado;
- operação;
- resultado;
- duração;
- motivo de falha.

Não registrar tokens, senhas, dados pessoais desnecessários ou payloads completos por padrão.

### Tracing

Usar rastreamento distribuído para acompanhar:

```text
Cliente → gateway → API → cache/banco → fila → worker → dependência externa
```

A amostragem deve ser maior para erros e incidentes do que para tráfego normal, para controlar custo.

### Alertas

Alertas acionáveis devem cobrir:

- erro acima do limite;
- p99 acima da meta;
- fila crescendo continuamente;
- consumidores excedendo quota;
- dependência externa degradada;
- banco próximo da saturação;
- falha de backup;
- aumento anormal de custo;
- região ou componente sem tráfego esperado;
- divergência entre mensagens aceitas e processadas.

---

## 12. Estratégia de custo

A contenção de custo deve ocorrer na arquitetura e na operação.

### Medidas recomendadas

- manter a capacidade mínima baixa fora dos períodos sazonais;
- aumentar capacidade antecipadamente em eventos previsíveis;
- usar processamento sob demanda quando o perfil de carga justificar;
- evitar multi-região permanente sem requisito claro;
- aplicar cache apenas onde reduzir custo ou latência comprovadamente;
- limitar logs de alto volume;
- aplicar retenção diferenciada;
- controlar transferência de dados;
- usar filas para suavizar picos de processamento;
- desligar ambientes não produtivos fora do horário;
- definir limites de escala;
- acompanhar custo por endpoint ou classe de operação.

### Trade-off principal

Uma arquitetura totalmente elástica pode proteger a disponibilidade, mas transferir o risco para a fatura. Uma arquitetura com teto rígido de custo pode preservar o orçamento, mas precisa aceitar rejeição, atraso ou degradação.

Essa decisão deve ser formalizada como política operacional, não deixada para o comportamento implícito da plataforma.

---

## 13. Plano de implementação

### Fase 1 — Descoberta e dimensionamento

Entregas:

- inventário de endpoints;
- classificação síncrono/assíncrono;
- mapa de dependências;
- distribuição geográfica;
- estimativas de tráfego normal, pico esperado e pico extremo;
- metas de latência, erro, disponibilidade e custo;
- política de degradação;
- critérios de aceite.

### Fase 2 — Fundação operacional

Entregas:

- ambientes separados;
- infraestrutura versionada;
- pipeline de entrega;
- gerenciamento de segredos;
- TLS;
- autenticação e autorização;
- logs estruturados;
- métricas básicas;
- health checks;
- alarmes mínimos;
- backup inicial.

### Fase 3 — API stateless e proteção de entrada

Entregas:

- gateway;
- rate limiting;
- quotas;
- validação de entrada;
- timeouts;
- tratamento padronizado de erros;
- idempotência para escritas;
- escalonamento horizontal;
- limites máximos de capacidade.

### Fase 4 — Picos e processamento assíncrono

Entregas:

- filas;
- workers;
- retry com backoff;
- DLQ;
- estados de processamento;
- métricas de backlog;
- prioridade por classe de operação;
- mecanismo de degradação.

### Fase 5 — Cache e otimização seletiva

Entregas:

- classificação dos endpoints;
- cache somente nos casos aprovados;
- testes de invalidação;
- validação de isolamento entre consumidores;
- comparação de custo e latência antes e depois.

### Fase 6 — Testes de capacidade e preparação sazonal

Executar:

- teste de carga;
- teste de pico abrupto;
- teste de duração prolongada;
- teste de saturação do banco;
- teste de indisponibilidade de dependência;
- teste de crescimento de fila;
- teste de restauração;
- simulação de contenção orçamentária;
- ensaio de degradação.

### Fase 7 — Recuperação avançada

Avaliar somente após medir a necessidade:

- segunda região;
- réplica de leitura;
- failover automatizado;
- replicação de dados;
- operação ativa-passiva;
- operação ativa-ativo.

A decisão deve ser baseada em RTO, RPO, latência e custo, não apenas na intenção de ser “global”.

---

## 14. Critérios de aceite

A arquitetura pode ser considerada pronta para o primeiro pico quando:

- os cenários normal, esperado e extremo estão quantificados;
- o limite máximo de capacidade está definido;
- o comportamento acima do limite está documentado;
- os consumidores possuem quotas e prioridades;
- endpoints assíncronos não bloqueiam a camada síncrona;
- dependências têm timeout, retry e fallback definidos;
- há proteção contra duplicidade de operações;
- a profundidade da fila e a idade das mensagens são monitoradas;
- backups foram restaurados em teste;
- alertas acionáveis foram validados;
- o custo é acompanhado por ambiente e componente;
- o teste de carga atingiu a capacidade-alvo;
- a equipe sabe quem pode ativar degradação ou contenção de emergência.

---

## 15. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Pico superior ao previsto | Saturação e rejeições | Limites, quotas, fila e plano de degradação |
| Autoscaling lento | Aumento de latência | Pré-aquecimento e capacidade mínima sazonal |
| Banco como gargalo | Falhas em cascata | Teste ponta a ponta, limites de conexão e otimização de consultas |
| Dependência externa indisponível | Erros e acúmulo de retries | Timeout, circuit breaker, backoff e DLQ |
| Custo acima do orçamento | Interrupção financeira ou operacional | Teto de escala, alertas e contenção automática/manual |
| Cache com dados incorretos | Respostas obsoletas ou vazamento | Classificação por endpoint e isolamento por consumidor |
| Rate limiting inadequado | Bloqueio de clientes legítimos | Quotas por identidade e política de prioridade |
| Logs excessivos | Custo e exposição de dados | Amostragem, retenção e mascaramento |
| Falha regional | Indisponibilidade | Backup, runbook e eventual segunda região |
| Mensagens duplicadas | Efeitos de negócio repetidos | Idempotência no produtor e consumidor |

---

## 16. Informações necessárias para fechar a arquitetura

Antes de contratar capacidade ou escolher serviços concretos, validar:

1. Qual é o tráfego médio, o pico esperado e o pico extremo?
2. Quanto tempo dura cada pico?
3. Com quanta antecedência os eventos são conhecidos?
4. Quais países concentram os consumidores?
5. Qual latência é aceitável por região?
6. Qual disponibilidade é necessária para cada operação?
7. Quais operações podem ser atrasadas?
8. Quais operações podem ser rejeitadas ou desativadas?
9. Qual é o RTO e o RPO?
10. Qual é o teto mensal e qual é a reserva de emergência?
11. Existem requisitos de residência ou retenção de dados?
12. Quais dependências externas possuem limites ou cobrança por chamada?
13. O cliente aceita polling, callback ou outro modelo assíncrono?
14. Quem autoriza a ativação da política de contenção?
15. A API já possui métricas históricas ou será necessário medir a linha de base?

## Conclusão

A arquitetura recomendada começa com alcance global na borda, uma região primária de processamento, serviços stateless, filas para absorção de picos, limites explícitos de capacidade e uma política de degradação vinculada ao orçamento.

Essa abordagem reduz o custo inicial e mantém um caminho de evolução para multi-região, mas só será tecnicamente segura se os limites de tráfego, latência, disponibilidade, consistência e custo forem definidos antes do primeiro pico sazonal.
