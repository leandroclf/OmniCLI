# Revisão de viabilidade — API de integração de pagamentos, antifraude, CRM e notificações

## 1. Veredito geral

A proposta arquitetural é tecnicamente sólida e madura para uma decisão de fase 0/1. O maior risco não está na arquitetura em si, mas no tamanho do documento em relação à informação disponível: ele especifica praticamente todo um sistema de pagamentos de nível produção sem que nenhum provedor, volume, consumidor ou requisito legal tenha sido confirmado. Isso é um sinal de over-engineering documental, não necessariamente de código — mas se o próximo passo for "implementar o que está escrito", o custo real será alto antes de qualquer validação de mercado.

## 2. Fatos, hipóteses e recomendações

### 2.1 Fatos
- A ideia original é apenas uma frase: "projetar uma API que integra pagamentos, antifraude, CRM e notificações". Nenhum provedor, volume, prazo ou orçamento foi informado em nenhum momento da conversa.
- O documento anterior já assume corretamente essa lacuna e lista as hipóteses como tal (seção 2.1 dele).

### 2.2 Hipóteses (minhas, sobre a proposta em si)
- Presumo que este documento será usado como referência de decisão antes de qualquer linha de código — não há evidência de que já exista time, prazo ou orçamento alocado.
- Presumo que "monólito modular" nas seções 14/ADR-001 é uma recomendação e não uma decisão já tomada pelo negócio.

### 2.3 Recomendações
Meu principal apontamento: **antes de aprovar esta arquitetura, reduza-a a uma fatia vertical mínima e teste-a com o provedor real escolhido.** O documento já reconhece isso na Fase 0, mas o restante do texto (seções 6 a 12) já está desenhado como se a Fase 0 tivesse terminado.

## 3. Custos e complexidade

| Item | Custo/complexidade | Observação |
|---|---|---|
| 6 entidades canônicas (Payment, PaymentAttempt, RiskAssessment, ProviderEvent, OutboxEvent, IntegrationDelivery) | Alto para MVP | Isso é modelo de dados de plataforma de pagamentos madura, não de primeiro release. Duas entidades (Payment + um log de eventos) já cobrem 80% do valor do MVP proposto na seção 3.1. |
| Outbox transacional + fila/broker + DLQ + retry com backoff/jitter + circuit breaker por integração | Alto | Cada um desses é um subsistema operacional próprio (monitoramento, alertas, runbook). Juntos, antes de ter um único provedor testado, é uma aposta de engenharia considerável. |
| Reconciliação automatizada + máquina de estados formal + auditoria de transições | Médio-alto | Justificável para dinheiro real, mas é trabalho de Fase 2+ que o documento já detalha campo a campo na Fase 0/1. |
| Observabilidade completa (logs estruturados, métricas por domínio, tracing distribuído, alertas segmentados) | Médio | Correto na direção, mas normalmente essa profundidade evolui com o sistema; especificá-la toda de antemão é esforço que pode não sobreviver ao primeiro provedor real. |

**Hipótese não confirmada:** não há indicação de tamanho de equipe. Esse escopo (5 fases, dezenas de componentes) presume uma equipe dedicada por várias semanas/meses. Se for 1-2 desenvolvedores, o cronograma implícito é irrealista — sinalizo essa incerteza porque o documento não trata capacidade de equipe em nenhum momento.

## 4. Riscos operacionais

- **Risco de "paralisia por especificação":** com 17 seções normativas e nenhum provedor escolhido, existe risco real de gastar mais tempo desenhando do que integrando. A Fase 0 do próprio documento deveria ser executada e revisitar o resto antes de continuar.
- **Antifraude como bloqueio síncrono:** a decisão de tratar antifraude como "etapa de decisão" (não apenas consumidor de eventos) é correta para evitar fraude, mas adiciona uma dependência síncrona crítica na hot path de pagamento — se o provedor de antifraude tiver alta latência, o p95 de 500ms citado na seção 10 fica sob risco. O documento já assinala isso, mas a meta numérica é apresentada como "meta inicial" sem medição real; trato-a como hipótese, não fato.
- **Múltiplos SPOFs de infraestrutura:** banco transacional + fila/broker + secret manager + observability stack são pelo menos 4 dependências operacionais externas para operar em produção. Cada uma exige runbook, alerta e plano de recuperação — custo operacional real mesmo em monólito modular.

## 5. Limitações e incertezas de ferramentas não confirmadas

O documento é honesto ao marcar como não decidido: provedor de pagamento, provedor antifraude, CRM, canal de notificação, mecanismo de fila/broker, mecanismo de autenticação (OAuth2/mTLS/API key). Isso é correto — sinalizo apenas que **nenhuma dessas escolhas foi feita nesta conversa**, então qualquer estimativa de custo de integração, taxa de provedor, ou obrigação legal (PCI-DSS, LGPD) citada de forma implícita nas seções 11.2 e 11.5 permanece hipótese, não fato verificado. Recomendo tratar conformidade PCI-DSS como um projeto formal separado com avaliação especializada, não como um item de checklist arquitetural.

## 6. Alternativas mais simples

- **Para antifraude e CRM no MVP:** considerar usar as capacidades nativas do próprio provedor de pagamento (a maioria de gateways modernos já embute score de risco) antes de integrar um provedor antifraude dedicado. Isso eliminaria um adaptador inteiro, uma máquina de decisão de risco e uma dependência síncrona na Fase 3.
- **Para o modelo de dados:** começar com 2 tabelas (Payment, Event) em vez das 6 entidades propostas; promover PaymentAttempt/RiskAssessment/IntegrationDelivery a tabelas próprias somente quando o volume ou a necessidade de auditoria justificar a separação.
- **Para mensageria:** se o volume esperado for baixo (não informado), um outbox + polling simples (sem broker dedicado) atende à Fase 1-2 inteira, adiando Kafka/RabbitMQ/SQS até haver medição real de throughput.
- **Para observabilidade:** iniciar com logs estruturados + 3-4 métricas de negócio (aprovação, recusa, latência, fila) em vez do catálogo completo da seção 12; expandir sob demanda de incidentes reais.

## 7. Recomendação final

Aprovar a direção arquitetural geral (monólito modular, modelo canônico, eventos assíncronos para CRM/notificações, webhooks como entrada não confiável) — essas são decisões corretas e bem justificadas. Porém, antes de qualquer implementação, executar literalmente a Fase 0 do próprio documento (escolher provedor de pagamento, antifraude, CRM, canal, e confirmar volumes) e então **cortar as seções 6–12 para o subconjunto mínimo que aquele provedor específico exige**, adicionando reconciliação, circuit breaker e observabilidade completa incrementalmente conforme o sistema realmente rodar em produção — não como pré-requisito de design.
