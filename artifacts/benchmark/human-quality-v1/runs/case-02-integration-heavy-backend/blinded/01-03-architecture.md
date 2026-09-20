# Arquitetura proposta para API de integração de pagamentos

## 1. Resumo executivo

A solução recomendada é uma plataforma de integração com:

- uma API de negócio voltada para operações de pagamento;
- um módulo de orquestração do ciclo de vida da transação;
- adaptadores isolados para pagamentos e antifraude;
- processamento assíncrono para CRM e notificações;
- persistência de um modelo canônico interno;
- recebimento de webhooks de provedores;
- mecanismos explícitos de idempotência, reconciliação, auditoria e observabilidade.

A recomendação é iniciar com um monólito modular, com processamento assíncrono por fila ou broker, em vez de separar imediatamente cada domínio em um microsserviço. Essa decisão reduz a complexidade operacional sem impedir uma futura extração de módulos.

O fluxo principal deve ser orientado pela transação financeira:

1. receber e validar a solicitação;
2. executar ou solicitar análise antifraude;
3. autorizar ou criar o pagamento;
4. persistir o estado interno;
5. propagar eventos para CRM e notificações;
6. atualizar o estado por webhooks, consultas ou reconciliação;
7. disponibilizar consulta e auditoria da transação.

CRM e notificações não devem bloquear o resultado financeiro, salvo quando houver requisito explícito de negócio.

---

## 2. Fatos, hipóteses e recomendações

### 2.1 Fatos fornecidos

- O objetivo é projetar uma API que integre:
  - pagamentos;
  - antifraude;
  - CRM;
  - notificações.
- Não foram definidos provedores, canais, volumes, consumidores, requisitos de disponibilidade ou ambiente de implantação.
- Não foi informado se as capacidades serão construídas internamente ou consumidas de terceiros.
- A etapa anterior identificou corretamente que o ciclo de pagamento pode ser síncrono, assíncrono ou híbrido, dependendo da operação e do provedor.

### 2.2 Hipóteses arquiteturais

As hipóteses abaixo permitem elaborar uma arquitetura implementável, mas precisam ser confirmadas:

- A API será consumida por sistemas internos, parceiros ou aplicações de negócio.
- O sistema não será um adquirente, emissor ou motor antifraude próprio no primeiro release.
- Pagamentos e antifraude serão integrados por provedores externos.
- O sistema terá um identificador próprio para cada operação.
- O resultado financeiro poderá ser definitivo somente após eventos posteriores do provedor.
- CRM e notificações serão capacidades complementares ao fluxo financeiro.
- Haverá necessidade de proteger contra requisições e webhooks duplicados.
- A solução poderá utilizar uma fila ou broker de mensagens.
- Os dados de cartão poderão ser tokenizados no provedor, reduzindo o escopo de armazenamento interno.

### 2.3 Recomendações

- Definir pagamento como domínio central da primeira versão.
- Utilizar um modelo canônico interno, separado dos contratos dos provedores.
- Tratar antifraude como uma etapa de decisão, não como mero consumidor de eventos.
- Executar CRM e notificações de forma assíncrona.
- Começar com um monólito modular e contratos internos bem definidos.
- Adotar arquitetura orientada a eventos apenas onde houver benefício concreto:
  - desacoplamento;
  - reprocessamento;
  - entrega assíncrona;
  - integração com múltiplos consumidores.
- Evitar armazenar dados completos de cartão.
- Adiar múltiplos provedores, múltiplos canais e múltiplos fluxos de pagamento até validar o primeiro fluxo vertical.

---

## 3. Escopo funcional inicial

### 3.1 Capacidades do primeiro release

O primeiro release deve suportar, no mínimo:

- criação de uma intenção ou ordem de pagamento;
- submissão de pagamento;
- análise antifraude;
- autorização ou recusa;
- consulta de status;
- recebimento e validação de webhooks;
- idempotência para comandos e eventos;
- envio de atualização ao CRM;
- envio de notificação por um canal;
- auditoria da transação;
- reprocessamento de integrações não financeiras;
- reconciliação básica com o provedor de pagamentos.

### 3.2 Operações que podem ser posteriores

Estas operações não devem ser presumidas como parte do MVP:

- captura separada;
- cancelamento parcial;
- estorno parcial;
- split de pagamento;
- múltiplos adquirentes;
- múltiplos motores antifraude;
- orquestração de campanhas de CRM;
- múltiplos canais de notificação;
- conciliação contábil completa;
- motor próprio de decisão antifraude.

A inclusão dessas capacidades depende dos requisitos reais dos consumidores e dos provedores escolhidos.

---

## 4. Componentes da solução

```text
Cliente / Sistema consumidor
            |
            v
      API de integração
            |
            v
    Módulo de orquestração
       /        |         \
      v         v          v
 Pagamentos  Antifraude  Persistência
      |         |          |
      v         v          v
 Provedor    Provedor   Banco transacional
 externo     externo
            |
            v
     Eventos transacionais
            |
       Fila / Broker
        /          \
       v            v
    CRM       Notificações
       |            |
       v            v
  Provedor      Provedor
   CRM          de canal

Provedores externos ---> Webhook Receiver ---> Orquestração ---> Estado interno
```

### 4.1 API de entrada

Responsabilidades:

- autenticar e autorizar o consumidor;
- validar formato e regras básicas;
- exigir chave de idempotência;
- gerar ou aceitar um identificador de correlação;
- encaminhar comandos ao módulo de aplicação;
- retornar o estado conhecido, sem prometer conclusão quando ela for assíncrona.

A API não deve expor diretamente os contratos dos provedores. Payloads externos devem ser convertidos para o modelo canônico interno.

### 4.2 Módulo de orquestração

Responsabilidades:

- controlar as transições do ciclo de vida;
- decidir quando chamar antifraude e pagamento;
- impedir transições inválidas;
- coordenar fluxos síncronos e assíncronos;
- registrar comandos, respostas e eventos;
- iniciar compensações quando aplicável.

O orquestrador não deve conter detalhes específicos de cada provedor. Esses detalhes pertencem aos adaptadores.

### 4.3 Adaptador de pagamentos

Responsabilidades:

- converter o modelo canônico para o contrato do provedor;
- executar autorização, captura, cancelamento ou estorno, quando suportados;
- converter respostas e erros externos;
- interpretar status e códigos do provedor;
- receber ou auxiliar a validação de webhooks;
- preservar identificadores externos para rastreabilidade.

Cada provedor deve possuir uma implementação isolada atrás de uma interface comum.

### 4.4 Adaptador antifraude

Responsabilidades:

- enviar os dados mínimos necessários para análise;
- converter o resultado externo para uma decisão canônica;
- representar estados como:
  - aprovado;
  - recusado;
  - revisão manual;
  - indisponível;
  - pendente;
- aplicar timeout e política de fallback definida pelo negócio.

Não se deve assumir que indisponibilidade do antifraude significa aprovação automática. O comportamento deve ser uma decisão explícita de risco.

### 4.5 Publicador de eventos

Responsabilidades:

- publicar mudanças relevantes de estado;
- garantir que eventos não sejam perdidos entre a transação no banco e a publicação;
- incluir versão do evento;
- permitir reprocessamento;
- não expor dados desnecessários ou sensíveis.

A recomendação é utilizar o padrão outbox transacional:

1. atualizar a transação e gravar o evento na mesma transação do banco;
2. um publicador independente envia os eventos;
3. marcar o evento como publicado;
4. repetir com segurança em caso de falha.

### 4.6 Consumidor de CRM

Responsabilidades:

- criar ou atualizar cliente, pedido ou oportunidade;
- consumir eventos de pagamento;
- aplicar mapeamentos específicos do CRM;
- reprocessar falhas;
- evitar duplicação com uma chave de idempotência própria.

O CRM não deve ser a fonte de verdade do estado financeiro.

### 4.7 Serviço de notificações

Responsabilidades:

- receber eventos de negócio;
- selecionar o template e o canal;
- enviar a mensagem ao provedor;
- controlar tentativas e backoff;
- evitar duplicidade;
- registrar o resultado da entrega.

O envio de notificação deve ser separado da decisão financeira. Uma falha no e-mail ou SMS não deve desfazer um pagamento aprovado.

### 4.8 Receptor de webhooks

Responsabilidades:

- receber notificações externas;
- autenticar ou verificar assinatura;
- aplicar proteção contra replay;
- registrar o evento bruto de forma controlada;
- deduplicar pelo identificador externo;
- encaminhar o evento para processamento;
- responder rapidamente ao provedor.

O webhook não deve executar uma cadeia longa de chamadas síncronas antes de retornar. O processamento deve ser colocado em uma fila ou agenda interna sempre que possível.

### 4.9 Reconciliação

Responsabilidades:

- comparar operações internas com registros dos provedores;
- detectar operações ausentes, divergentes ou presas;
- identificar diferenças de valor, moeda, status e identificador;
- gerar pendências operacionais;
- permitir correção controlada, sem alterar histórico indevidamente.

A reconciliação é necessária porque webhooks podem ser atrasados, duplicados, perdidos ou entregues fora de ordem.

---

## 5. Fluxos principais

## 5.1 Criação e processamento de pagamento

```text
Cliente
  |
  | POST /payments + Idempotency-Key
  v
API
  |
  | valida autenticação, payload e idempotência
  v
Orquestrador
  |
  | cria pagamento em estado CREATED
  v
Antifraude
  |
  +--> APPROVED ------> Provedor de pagamento
  |                         |
  |                         +--> AUTHORIZED
  |                         +--> DECLINED
  |                         +--> PENDING
  |
  +--> REVIEW_REQUIRED
  +--> DECLINED
  +--> UNAVAILABLE
```

A resposta pode ser:

- `201 Created` quando a intenção foi criada;
- `202 Accepted` quando o processamento continuará de forma assíncrona;
- `200 OK` quando o resultado síncrono estiver disponível;
- `4xx` para erro de contrato, autorização ou regra de negócio;
- `5xx` apenas quando houver falha interna não tratada.

O status HTTP não deve ser usado como substituto do estado financeiro. O consumidor deve consultar o recurso ou receber eventos.

## 5.2 Atualização por webhook

```text
Provedor
   |
   v
Webhook Receiver
   |
   | valida assinatura, timestamp e id externo
   v
Inbox / fila
   |
   v
Processador de eventos
   |
   | verifica duplicidade e ordem
   v
Orquestrador
   |
   | aplica transição válida
   v
Banco + Outbox
   |
   +--> CRM
   +--> Notificações
```

O processamento deve aceitar duplicidade técnica, mas produzir efeito funcional apenas uma vez.

## 5.3 Falha do antifraude

A política deve ser definida explicitamente. Opções possíveis:

- bloquear a transação até o antifraude responder;
- colocar a operação em revisão;
- permitir autorização apenas para determinados segmentos;
- usar um segundo provedor;
- recusar por indisponibilidade.

A recomendação inicial é colocar a operação em `REVIEW_REQUIRED` ou `RISK_UNAVAILABLE`, evitando aprovação automática sem autorização formal do negócio.

## 5.4 Falha do CRM

O pagamento continua com seu estado próprio. O evento para o CRM permanece pendente e é reprocessado conforme política de retry.

Após esgotar as tentativas:

- mover a mensagem para uma DLQ;
- registrar alerta operacional;
- disponibilizar reprocessamento manual ou automatizado;
- preservar o evento original e o erro final.

## 5.5 Falha de notificação

O evento financeiro não deve ser revertido. A notificação deve:

- ser reprocessada;
- respeitar limite de tentativas;
- evitar envio duplicado;
- registrar o status de entrega separadamente;
- permitir consulta operacional.

---

## 6. Modelo de dados canônico

### 6.1 Entidades principais

#### Payment

Representa a operação financeira interna.

Campos sugeridos:

- `payment_id`;
- `merchant_id` ou identificador do consumidor;
- `external_reference`;
- `amount`;
- `currency`;
- `payment_method_type`;
- `status`;
- `risk_status`;
- `provider`;
- `provider_payment_id`;
- `created_at`;
- `updated_at`;
- `expires_at`;
- `version`.

#### PaymentAttempt

Representa uma tentativa contra um provedor.

Campos sugeridos:

- `attempt_id`;
- `payment_id`;
- `provider`;
- `provider_attempt_id`;
- `operation`;
- `request_hash`;
- `status`;
- `provider_code`;
- `provider_message`;
- `started_at`;
- `finished_at`.

Essa separação permite que uma transação interna tenha mais de uma tentativa controlada, sem sobrescrever o histórico.

#### RiskAssessment

Representa a análise antifraude.

Campos sugeridos:

- `assessment_id`;
- `payment_id`;
- `provider`;
- `provider_assessment_id`;
- `decision`;
- `score`, se aplicável;
- `reason_codes`;
- `status`;
- `created_at`;
- `completed_at`.

#### ProviderEvent

Representa o webhook ou evento recebido.

Campos sugeridos:

- `provider_event_id`;
- `provider`;
- `event_type`;
- `payload_reference`;
- `signature_status`;
- `received_at`;
- `processed_at`;
- `processing_status`;
- `retry_count`.

#### OutboxEvent

Representa um evento interno a publicar.

Campos sugeridos:

- `event_id`;
- `aggregate_type`;
- `aggregate_id`;
- `event_type`;
- `event_version`;
- `payload`;
- `status`;
- `available_at`;
- `published_at`;
- `attempt_count`.

#### IntegrationDelivery

Controla a entrega a CRM ou notificações.

Campos sugeridos:

- `delivery_id`;
- `event_id`;
- `destination`;
- `destination_reference`;
- `status`;
- `attempt_count`;
- `last_error`;
- `next_attempt_at`;
- `delivered_at`.

### 6.2 Fonte de verdade

Recomendação inicial:

| Informação | Fonte de verdade |
|---|---|
| Estado interno do fluxo | Plataforma de integração |
| Estado final do pagamento externo | Provedor, reconciliado internamente |
| Decisão antifraude | Provedor antifraude, com histórico interno |
| Dados de relacionamento | CRM ou plataforma, conforme atributo |
| Entrega de comunicação | Provedor de canal, com histórico interno |
| Auditoria de comandos e eventos | Plataforma de integração |

O sistema interno deve armazenar o estado necessário para operar e auditar, mas não deve fingir ser a autoridade absoluta sobre fatos que somente o provedor externo pode confirmar.

---

## 7. Máquina de estados

Um conjunto inicial de estados pode ser:

```text
CREATED
  -> RISK_PENDING
  -> RISK_APPROVED
  -> RISK_REJECTED
  -> REVIEW_REQUIRED

RISK_APPROVED
  -> PAYMENT_PENDING
  -> AUTHORIZED
  -> DECLINED
  -> FAILED

AUTHORIZED
  -> CAPTURE_PENDING
  -> CAPTURED
  -> CANCELLED
  -> REFUND_PENDING
  -> REFUNDED

PAYMENT_PENDING
  -> AUTHORIZED
  -> DECLINED
  -> EXPIRED
  -> RECONCILIATION_REQUIRED
```

A lista precisa ser ajustada ao provedor e ao modelo de negócio. Particularmente:

- `AUTHORIZED` não deve ser tratado como `CAPTURED`;
- `PENDING` não deve ser tratado como falha;
- `DECLINED` não deve ser alterado silenciosamente por um evento posterior incompatível;
- transições devem ser monotônicas quando possível;
- correções de reconciliação devem preservar o histórico original.

Cada transição deve registrar:

- estado anterior;
- estado novo;
- causa;
- ator ou sistema;
- identificador externo;
- timestamp;
- versão do recurso.

---

## 8. Contrato de API sugerido

Os nomes abaixo são ilustrativos e devem ser ajustados ao consumidor real.

### 8.1 Pagamentos

```http
POST /v1/payments
GET  /v1/payments/{paymentId}
POST /v1/payments/{paymentId}/capture
POST /v1/payments/{paymentId}/cancel
POST /v1/payments/{paymentId}/refund
```

A chave `Idempotency-Key` deve ser obrigatória para comandos que criem ou alterem uma operação financeira.

### 8.2 Webhooks

```http
POST /v1/webhooks/{provider}/payments
POST /v1/webhooks/{provider}/risk
POST /v1/webhooks/{provider}/notifications
```

Essas rotas devem ser separadas por provedor ou possuir um mecanismo seguro e explícito de identificação do remetente.

### 8.3 Consulta operacional

```http
GET /v1/payments/{paymentId}/timeline
GET /v1/payments/{paymentId}/attempts
GET /v1/payments/{paymentId}/deliveries
```

Esses endpoints devem respeitar controle de acesso e não expor dados sensíveis de provedores.

### 8.4 Reprocessamento

O reprocessamento deve ser uma operação administrativa protegida, por exemplo:

```http
POST /v1/operations/{operationId}/retry
```

Deve exigir:

- autorização elevada;
- motivo;
- identificação do operador;
- auditoria;
- limite de repetição;
- proteção contra reprocessamento de operações financeiras irreversíveis.

---

## 9. Idempotência, consistência e falhas

### 9.1 Idempotência de comandos

Para cada comando:

- armazenar a chave de idempotência;
- associá-la ao consumidor e ao tipo de operação;
- guardar hash do payload;
- retornar o mesmo resultado para repetição equivalente;
- rejeitar a mesma chave com payload diferente;
- definir uma janela de retenção compatível com o risco financeiro.

A captura, o cancelamento e o estorno devem ter chaves próprias, mesmo que pertençam ao mesmo pagamento.

### 9.2 Idempotência de webhooks

A combinação recomendada é:

```text
provider + provider_event_id
```

Quando o provedor não oferecer identificador confiável, deve ser usada uma estratégia composta com cautela, como hash do payload, tipo de evento, identificador da operação e timestamp. Essa alternativa pode gerar colisões ou não detectar todos os duplicados e precisa ser validada por provedor.

### 9.3 Retries

Aplicar retry apenas a erros potencialmente transitórios:

- timeout;
- conexão recusada;
- indisponibilidade temporária;
- respostas explícitas de throttling.

Não repetir automaticamente:

- payload inválido;
- autenticação inválida;
- cartão recusado;
- regra antifraude recusada;
- operação não suportada.

Usar:

- backoff exponencial;
- jitter;
- limite de tentativas;
- DLQ;
- alertas;
- classificação de erro.

### 9.4 Timeouts e circuit breaker

Cada integração deve ter timeout próprio, baseado em comportamento observado do provedor. Não há um valor universal correto antes de medir.

O circuito deve impedir que a indisponibilidade de um provedor consuma todos os recursos da API. A abertura do circuito deve gerar métrica e alerta, não apenas erro silencioso.

### 9.5 Consistência

A transação financeira deve ter consistência forte dentro do banco interno para:

- transição de estado;
- idempotência;
- gravação de outbox;
- registro de auditoria.

CRM e notificações podem operar com consistência eventual, desde que:

- os eventos sejam duráveis;
- haja reprocessamento;
- o status de entrega seja observável;
- o consumidor possa consultar a situação.

---

## 10. Requisitos não funcionais

Os valores abaixo são metas iniciais recomendadas, não requisitos confirmados.

| Categoria | Meta inicial | Observação |
|---|---:|---|
| Disponibilidade da API | 99,9% | Validar criticidade e janela de manutenção |
| Latência da API de criação | p95 abaixo de 500 ms sem aguardar decisão externa | Pode variar conforme o fluxo |
| Latência de consulta | p95 abaixo de 300 ms | Exclui indisponibilidade do banco |
| Processamento de eventos | 99% em até alguns minutos | Confirmar com operação |
| Durabilidade de eventos | Sem perda após confirmação de persistência | Requer outbox e armazenamento durável |
| Rastreabilidade | Correlação ponta a ponta | API, banco, fila e provedores |
| Recuperação | RTO e RPO definidos antes da produção | Dependem da infraestrutura escolhida |
| Escalabilidade | Escalar API e consumidores independentemente | Requer processamento assíncrono |
| Segurança | Menor escopo possível de dados sensíveis | Validar com segurança e jurídico |

Devem ser definidos formalmente:

- RTO;
- RPO;
- volume médio e pico;
- taxa de webhooks;
- número de consumidores;
- tamanho máximo de payload;
- limites por consumidor;
- retenção de dados;
- janela de reconciliação.

---

## 11. Segurança

## 11.1 Identidade e autorização

- autenticar consumidores por mecanismo apropriado ao contexto;
- separar autenticação de autorização;
- aplicar autorização por tenant, conta ou estabelecimento;
- limitar operações administrativas a perfis privilegiados;
- não confiar em identificadores enviados pelo cliente para definir posse de dados;
- registrar decisões de autorização relevantes.

O mecanismo concreto — OAuth 2.0, mTLS, API keys ou outro — depende do tipo de consumidor e do ambiente. Não deve ser escolhido sem essa informação.

## 11.2 Proteção de dados de pagamento

Recomendação:

- utilizar tokenização ou campos hospedados pelo provedor;
- não armazenar número completo do cartão;
- não registrar CVV;
- mascarar identificadores em logs;
- criptografar dados sensíveis em trânsito e em repouso;
- restringir acesso operacional;
- separar dados de produção e homologação.

A aplicabilidade e o escopo de requisitos de segurança de pagamentos devem ser confirmados por avaliação especializada. A arquitetura reduz exposição, mas não comprova conformidade.

## 11.3 Webhooks

Implementar:

- verificação de assinatura;
- validação de timestamp;
- prevenção contra replay;
- allowlist de origem apenas quando tecnicamente confiável;
- limitação de taxa;
- armazenamento controlado do payload bruto;
- auditoria da validação;
- rejeição de eventos malformados.

A assinatura deve ser verificada sobre o conteúdo original, antes de normalização ou transformação.

## 11.4 Segredos

- armazenar credenciais em um gerenciador de segredos;
- nunca mantê-las no código ou em arquivos versionados;
- aplicar rotação;
- limitar escopo das credenciais;
- separar credenciais por ambiente;
- auditar acessos;
- evitar imprimir tokens em exceções e traces.

## 11.5 Privacidade

A solução deve classificar:

- dados de identificação;
- dados de contato;
- dados de pagamento;
- dados de risco;
- dados de comunicação;
- metadados de auditoria.

A retenção, exclusão, anonimização, finalidade e compartilhamento devem ser definidos com responsáveis de privacidade e jurídico. A arquitetura não deve presumir obrigações legais específicas sem confirmação do contexto.

## 11.6 Abuso e disponibilidade

- rate limiting por consumidor;
- limites de tamanho de requisição;
- proteção contra replay;
- quotas de webhook;
- circuit breaker;
- filas com limites;
- isolamento de consumidores ruidosos;
- validação de referências externas;
- alertas para aumento de recusas, retries e chamadas administrativas.

---

## 12. Observabilidade

## 12.1 Logs estruturados

Cada log deve conter, quando aplicável:

- `timestamp`;
- `level`;
- `service`;
- `environment`;
- `trace_id`;
- `request_id`;
- `payment_id`;
- `provider`;
- `provider_operation_id`;
- `event_id`;
- `idempotency_key_hash`;
- `error_code`;
- `duration_ms`.

Não registrar:

- número completo do cartão;
- CVV;
- tokens de autenticação;
- payloads sensíveis sem mascaramento;
- dados pessoais além do necessário.

## 12.2 Métricas

### API

- taxa de requisições;
- latência por endpoint;
- erros por classe;
- respostas por status HTTP;
- falhas de idempotência;
- requisições rejeitadas por limite.

### Pagamentos

- pagamentos por estado;
- aprovação, recusa e pendência;
- latência por provedor;
- timeout por operação;
- falhas de captura, cancelamento e estorno;
- divergências de reconciliação.

### Antifraude

- tempo de decisão;
- decisões por resultado;
- taxa de revisão manual;
- indisponibilidade;
- fallback acionado.

### Mensageria

- tamanho da fila;
- idade da mensagem mais antiga;
- throughput;
- retries;
- mensagens na DLQ;
- tempo de processamento;
- falhas por destino.

### CRM e notificações

- taxa de entrega;
- falhas por provedor;
- tempo até confirmação;
- duplicidades evitadas;
- pendências por integração.

## 12.3 Tracing distribuído

Usar um identificador de correlação propagado entre:

```text
cliente -> API -> orquestrador -> adaptador -> provedor
        -> webhook -> fila -> CRM/notificação
```

O tracing deve preservar contexto sem incluir dados sensíveis nos atributos.

## 12.4 Alertas

Alertas de alta prioridade:

- aumento de pagamentos em estado pendente;
- crescimento anormal de recusas;
- indisponibilidade de provedor;
- fila envelhecendo;
- DLQ acima do limite;
- falhas de validação de webhook;
- divergência de reconciliação;
- aumento de duplicidades;
- expiração de credenciais;
- falha no banco ou no mecanismo de eventos.

Alertas de negócio e técnicos devem ser separados para evitar fadiga operacional.

---

## 13. Estratégia de implantação

A topologia exata depende do ambiente disponível, que ainda não foi informado. Em qualquer ambiente, a separação lógica recomendada é:

- camada pública de entrada;
- camada de aplicação;
- banco transacional privado;
- mecanismo de filas ou broker;
- workers de integração;
- armazenamento de segredos;
- sistema de logs e métricas;
- área administrativa restrita.

Ambientes mínimos:

- desenvolvimento;
- homologação;
- produção.

Deve existir isolamento de credenciais e dados por ambiente. Testes de homologação precisam cobrir:

- respostas de sucesso;
- recusas;
- timeouts;
- webhooks duplicados;
- webhooks fora de ordem;
- indisponibilidade;
- reprocessamento;
- divergência de valores;
- expiração;
- falha de CRM;
- falha de notificação.

---

## 14. Decisões arquiteturais registradas

### ADR-001 — Monólito modular no primeiro release

**Decisão:** implementar os módulos em uma unidade implantável inicialmente, mantendo limites internos claros.

**Motivo:**

- escopo ainda incerto;
- necessidade de evoluir rapidamente o fluxo;
- menor custo operacional;
- transações e auditoria mais simples;
- menor risco de criar comunicação distribuída prematuramente.

**Trade-off:**

- menor isolamento de falhas entre módulos;
- necessidade de disciplina para evitar acoplamento interno;
- extração futura exigirá contratos estáveis.

### ADR-002 — Modelo canônico interno

**Decisão:** separar entidades e estados internos dos contratos de provedores.

**Motivo:**

- evitar vazamento de detalhes externos;
- permitir troca ou adição de provedores;
- padronizar consulta e auditoria;
- controlar o ciclo de vida da transação.

**Trade-off:**

- exige mapeamentos;
- alguns recursos específicos de provedores precisarão de extensões;
- pode haver perda de detalhes se o modelo for excessivamente genérico.

### ADR-003 — Eventos para efeitos posteriores

**Decisão:** CRM, notificações e tarefas de integração serão acionados por eventos duráveis.

**Motivo:**

- não bloquear o resultado financeiro;
- permitir retry e reprocessamento;
- reduzir acoplamento temporal;
- suportar consumidores adicionais.

**Trade-off:**

- consistência eventual;
- maior complexidade de diagnóstico;
- necessidade de outbox, idempotência e DLQ.

### ADR-004 — Tokenização de dados de cartão

**Decisão:** evitar armazenar dados completos de cartão na plataforma.

**Motivo:**

- reduzir exposição;
- limitar impacto de incidentes;
- simplificar controles internos;
- delegar armazenamento sensível ao provedor apropriado.

**Trade-off:**

- dependência de tokenização do provedor;
- limitações de migração entre provedores;
- necessidade de compreender o ciclo de vida dos tokens.

### ADR-005 — Webhooks como entrada não confiável

**Decisão:** tratar cada webhook como potencialmente duplicado, atrasado, fora de ordem ou malformado.

**Motivo:**

- comportamento comum de integrações externas;
- necessidade de preservar consistência;
- prevenção de efeitos financeiros duplicados.

**Trade-off:**

- persistência adicional;
- processamento assíncrono;
- necessidade de reconciliação.

---

## 15. Plano de implementação

### Fase 0 — Validação do escopo

Confirmar:

- consumidor da API;
- fluxo prioritário;
- provedor de pagamento;
- provedor antifraude;
- CRM;
- canal de notificação;
- volumes;
- requisitos de disponibilidade;
- dados que serão recebidos;
- política de falha antifraude;
- requisitos de segurança e privacidade.

**Critério de saída:** um fluxo vertical definido, com estados e responsáveis aprovados.

### Fase 1 — Fundação técnica

Implementar:

- autenticação e autorização;
- modelo canônico;
- persistência de pagamentos;
- máquina de estados;
- idempotência;
- correlação;
- auditoria;
- contrato inicial da API;
- configuração de segredos;
- logs e métricas básicas.

**Critério de saída:** criar e consultar um pagamento sem integração externa.

### Fase 2 — Pagamentos

Implementar:

- primeiro adaptador de pagamentos;
- autorização;
- tratamento de sucesso, recusa e pendência;
- webhooks;
- retries;
- outbox;
- reconciliação inicial;
- testes de duplicidade e fora de ordem.

**Critério de saída:** processar o fluxo financeiro completo em homologação.

### Fase 3 — Antifraude

Implementar:

- adaptador antifraude;
- estados de risco;
- timeout;
- decisão de indisponibilidade;
- revisão manual, se necessária;
- métricas de decisão;
- testes de recusa e pendência.

**Critério de saída:** nenhuma transação seguir uma política antifraude implícita ou ambígua.

### Fase 4 — CRM e notificações

Implementar:

- consumidores de eventos;
- mapeamento para CRM;
- primeiro canal de notificação;
- retries e DLQ;
- idempotência por destino;
- consulta de entregas;
- templates versionados, se aplicável.

**Critério de saída:** falhas nessas integrações não alterarem incorretamente o estado financeiro.

### Fase 5 — Operação e endurecimento

Implementar:

- reconciliação automatizada;
- dashboards;
- alertas;
- testes de carga;
- testes de recuperação;
- revisão de permissões;
- rotação de credenciais;
- runbooks;
- processo de reprocessamento;
- avaliação de segurança e privacidade.

**Critério de saída:** operação assistida com evidência de recuperação, rastreabilidade e controle de falhas.

---

## 16. Riscos e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Provedor possui estados incompatíveis | Transições incorretas | Adaptador por provedor e máquina canônica explícita |
| Webhook duplicado ou fora de ordem | Cobrança ou atualização duplicada | Inbox, idempotência e validação de transição |
| Antifraude indisponível | Aprovação indevida ou queda de conversão | Política formal de fallback |
| CRM bloqueia fluxo financeiro | Aumento de latência e falhas em cascata | Processamento assíncrono |
| Notificação duplicada | Má experiência e risco reputacional | Chave de deduplicação por mensagem |
| Perda de evento interno | Dados divergentes | Outbox transacional |
| Diferença entre sistema e provedor | Conciliação incorreta | Reconciliação periódica |
| Escopo cresce para múltiplos produtos | Atraso e baixa qualidade | Primeiro fluxo vertical e backlog controlado |
| Dados sensíveis em logs | Incidente de segurança | Mascaramento, filtros e revisão automatizada |
| Dependência de um único provedor | Indisponibilidade e lock-in | Interfaces de adaptador e plano de contingência |

---

## 17. Critérios de aceite arquiteturais

A arquitetura deve ser considerada pronta para implementação quando:

- o fluxo principal estiver definido de ponta a ponta;
- os estados e transições tiverem responsáveis claros;
- cada integração tiver contrato e política de erro;
- comandos financeiros tiverem idempotência;
- webhooks tiverem autenticação, deduplicação e replay protection;
- eventos internos forem duráveis;
- CRM e notificações não bloquearem indevidamente o pagamento;
- existir uma estratégia de reconciliação;
- dados sensíveis e retenção tiverem sido classificados;
- métricas, logs, traces e alertas mínimos estiverem definidos;
- RTO, RPO, volume e disponibilidade tiverem sido aprovados;
- houver um único fluxo vertical demonstrável em homologação.

## Conclusão

A solução tecnicamente viável é uma plataforma de integração centrada no ciclo de vida do pagamento, com antifraude acoplado à decisão financeira e CRM/notificações desacoplados por eventos.

A arquitetura deve permanecer modular e provider-neutral, mas sem tentar generalizar todos os provedores ou operações no primeiro release. O maior fator de sucesso não será a quantidade de integrações, e sim a correção das transições financeiras, o tratamento de duplicidades e falhas, a reconciliação e a rastreabilidade operacional.
