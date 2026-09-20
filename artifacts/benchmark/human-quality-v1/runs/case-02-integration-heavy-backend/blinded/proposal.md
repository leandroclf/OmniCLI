# Proposta Mestra de Arquitetura — API de integração de pagamentos, antifraude, CRM e notificações

## 1. Escopo

**Escopo confirmado (fato):** a ideia original define apenas o objetivo — uma API que integra pagamentos, antifraude, CRM e notificações. Nenhum provedor, volume, prazo, orçamento ou equipe foi especificado em nenhum momento da conversa.

**Escopo desta proposta (recomendação):** entregar uma fatia vertical mínima — um fluxo de pagamento ponta a ponta, com um provedor real, decisão de risco básica, propagação de evento para CRM e disparo de notificação — antes de qualquer expansão de modelo de dados ou infraestrutura.

**Fora de escopo nesta fase (recomendação):** reconciliação automatizada, múltiplos provedores, máquina de estados formal, observabilidade completa, circuit breaker por integração. Ficam como evolução condicionada a operação real.

## 2. Premissas

| Premissa | Natureza | Observação |
|---|---|---|
| Haverá 1+ provedor de pagamento a definir | Hipótese | Nenhum foi citado; qualquer custo, taxa ou SLA de provedor é inventado até confirmação |
| Antifraude será etapa síncrona de decisão | Recomendação, não fato | Correto para bloquear fraude, mas introduz dependência crítica na hot path; medir latência real antes de fixar meta de p95 |
| CRM e notificações são consumidores assíncronos de eventos | Recomendação | Reduz acoplamento; não depende de provedor específico |
| Equipe e prazo suficientes para múltiplas fases | Hipótese não confirmada | Documento não trata capacidade de equipe; se for 1-2 devs, cronograma abaixo é irrealista |
| Aplicabilidade de PCI-DSS/LGPD | Hipótese | Depende do modelo de custódia de dados de cartão/pessoais, ainda não definido; tratar como avaliação formal separada, não item de checklist |

## 3. Decisões (arquiteturais)

- **Monólito modular** como ponto de partida. *Razão:* menor custo operacional que microsserviços antes de haver tráfego real; módulos internos (Pagamento, Antifraude, CRM, Notificação) com fronteiras claras permitem extração futura se necessário.
- **Modelo de dados mínimo:** 2 entidades no MVP — `Payment` e `Event` (log de eventos/outbox). Entidades adicionais (PaymentAttempt, RiskAssessment, IntegrationDelivery) só quando volume ou auditoria justificarem a separação.
- **Webhooks de entrada tratados como não confiáveis:** validação de assinatura e idempotência obrigatórias — este é um requisito de segurança, não um corte cabível.
- **Propagação para CRM/notificações via evento assíncrono** (outbox + polling), não chamada síncrona.
- **Mensageria:** outbox transacional + polling simples no MVP; broker dedicado (Kafka/SQS/RabbitMQ) só após medição real de throughput.
- **Observabilidade inicial:** logs estruturados + 3-4 métricas de negócio (aprovação, recusa, latência, tamanho de fila). Stack completo de tracing distribuído fica para quando houver incidente real que o justifique.

## 4. Requisitos

### 4.1 Funcionais
- Iniciar cobrança com um provedor de pagamento (a definir).
- Consultar/decidir risco antes de confirmar a cobrança.
- Notificar CRM sobre mudança de status do pagamento.
- Disparar notificação ao cliente (canal a definir).
- Receber e validar webhooks do provedor de pagamento.

### 4.2 Não funcionais
- Idempotência em todas as escritas de pagamento e no processamento de webhook.
- Auditoria mínima de transições de status (mesmo antes de uma máquina de estados formal).
- Meta de latência: **não fixar número (ex. p95 500ms) sem medição real** — tratar como hipótese até haver dado de produção.

## 5. Arquitetura (visão mínima)

```
Cliente → API (monólito modular)
            ├─ Módulo Pagamento → Provedor de pagamento (a definir)
            ├─ Módulo Antifraude → decisão síncrona (bloqueio) — provedor a definir ou score nativo do gateway
            ├─ Outbox (tabela Event) → worker de polling
            │        ├─ Módulo CRM (consumidor assíncrono)
            │        └─ Módulo Notificação (consumidor assíncrono)
            └─ Webhook inbound (validação de assinatura + idempotência)
```

**Alternativa mais simples para antifraude/CRM (recomendação):** avaliar primeiro o score de risco nativo do próprio gateway de pagamento antes de integrar um provedor antifraude dedicado — elimina um adaptador inteiro e uma dependência síncrona adicional.

## 6. Riscos

- **Paralisia por especificação:** desenhar todas as fases antes de escolher um provedor real gera retrabalho quando o provedor escolhido impuser restrições não previstas.
- **Antifraude síncrono como ponto único de lentidão:** se o provedor de risco tiver latência alta, ele dita o tempo de resposta do pagamento inteiro.
- **SPOFs de infraestrutura:** banco transacional, mecanismo de fila e secret manager já são 3 dependências operacionais externas mesmo na versão mínima — cada uma precisa de plano de recuperação.
- **Conformidade não avaliada:** PCI-DSS e LGPD podem se aplicar dependendo de como dados de cartão/pessoais são custodiados; não presumir enquadramento sem avaliação especializada.

## 7. Critérios de aceite (para a fatia mínima)

- [ ] Um pagamento real é processado ponta a ponta com um único provedor confirmado.
- [ ] Decisão de risco (própria ou do gateway) bloqueia/aprova antes da confirmação.
- [ ] Evento de mudança de status chega ao CRM e dispara notificação, de forma assíncrona e sem perda (outbox garante entrega).
- [ ] Webhook de entrada rejeita payload com assinatura inválida ou duplicada (idempotência comprovada).
- [ ] Latência observada é medida e registrada — não estimada.

## 8. Decisões pendentes

1. Qual provedor de pagamento será usado (define taxas, SLA, campos obrigatórios).
2. Antifraude: usar score nativo do gateway ou contratar provedor dedicado?
3. Qual CRM será integrado e qual o contrato de eventos que ele aceita.
4. Canal de notificação (e-mail, SMS, push?) e provedor correspondente.
5. Volume esperado de transações (define se polling básico basta ou se broker dedicado é necessário desde o início).
6. Tamanho e disponibilidade da equipe (define cronograma realista).
7. Enquadramento legal (PCI-DSS/LGPD) conforme o modelo de custódia de dados escolhido.

---
**Nota:** esta proposta não deve ser tratada como especificação completa para implementação imediata. As decisões pendentes na seção 8 devem ser resolvidas antes de expandir além da fatia mínima descrita na seção 5.
