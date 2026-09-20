# Revisão de viabilidade — API global com picos sazonais e orçamento limitado

## 1. Fatos fornecidos

- Alcance global.
- Picos sazonais.
- Orçamento limitado.

Nada além disso foi dado. Qualquer número de tráfego, custo, SLA ou tecnologia citado abaixo é hipótese ou estimativa qualitativa, não dado confirmado.

---

## 2. Avaliação geral

A proposta está tecnicamente correta como cardápio de padrões (borda global + região única + filas + degradação), mas é **grande demais para as três frases que a originaram**. O documento tem 16 seções, 7 fases de implementação e dezenas de componentes — para uma ideia que ainda não tem volume de tráfego, duração de pico, nem teto de custo definidos. Isso é risco de projeto, não só de arquitetura: o time pode gastar semanas documentando e "preparando" componentes (fila, workers, DLQ, observabilidade completa) antes de saber se precisa de metade deles.

**Recomendação central:** tratar este documento como checklist de referência para consultar por fase, não como escopo do primeiro incremento. O primeiro incremento real deveria caber em 1 página.

---

## 3. Pontos onde a proposta é sólida (preservar)

- Separar "alcance global" (borda/CDN) de "processamento multi-região" é a decisão certa e evita o erro mais caro e comum: multi-região ativo-ativo sem necessidade comprovada.
- Recusar-se a escolher banco de dados sem conhecer padrão de acesso é correto — evita lock-in prematuro.
- O trade-off da seção 12 ("elasticidade protege disponibilidade, mas transfere risco para a fatura") é o ponto mais importante do documento inteiro e deveria estar na introdução, não enterrado no meio.
- Classificar operações em síncronas/assíncronas/degradáveis antes de desenhar infraestrutura é uma ordem de trabalho saudável.

---

## 4. Riscos e inconsistências a apontar

### 4.1 Complexidade fora de proporção com o orçamento declarado
O documento assume "orçamento limitado" mas propõe fila gerenciada, workers assíncronos, cache distribuído, WAF, CDN, gateway, observabilidade com tracing distribuído e amostragem, e um serviço de identidade dedicado — **antes** de qualquer volume ser conhecido. Cada um desses componentes tem custo fixo mensal (mesmo ocioso) que pode consumir a maior parte de um orçamento apertado. Isso é hipótese não sinalizada como tal no documento original: "orçamento limitado" foi tratado só como política de escala, não como restrição de quais componentes cabem desde o dia 1.

**Recomendação:** para uma primeira versão, um monólito stateless simples atrás de um único load balancer gerenciado, com banco gerenciado e cache em memória local (não distribuído), pode cobrir tráfego moderado com pico sazonal a uma fração do custo operacional. Fila e workers separados só se justificam quando houver operação comprovadamente lenta ou volume que não cabe em request/response síncrono.

### 4.2 "API global" não implica infraestrutura distribuída
O fato "alcance global de clientes" foi silenciosamente traduzido em "arquitetura com borda global, CDN, WAF dedicado". Isso é uma alternativa mais simples ignorada: um provedor de PaaS/serverless com edge global embutido (ex.: funções na borda de um CDN, ou um único backend atrás de um CDN com cache) atende "alcance global" sem exigir que a equipe opere WAF, DNS multi-região e gateway separadamente. Não tenho informação suficiente sobre stack já adotada para recomendar um produto específico — mas a pergunta "quem vai operar o WAF e o roteamento global?" não está no documento e deveria estar antes de decidir por componentes autogerenciados.

### 4.3 Picos sazonais podem não justificar autoscaling + fila + pré-aquecimento simultâneos
Três mecanismos de absorção de pico (autoscaling, filas, pré-aquecimento manual) são propostos em conjunto sem critério de quando usar apenas um. Se os picos são **prováveis, mas não é dito se são previsíveis com antecedência** (é hipótese explícita do próprio documento, não fato), a alternativa mais simples é: autoscaling com limite máximo travado por orçamento, e só adicionar fila/pré-aquecimento manual se o autoscaling comprovadamente não responder a tempo em teste de carga real. Adicionar os três de saída é esforço de engenharia sem evidência de necessidade.

### 4.4 Observabilidade completa (fase 2/6) é cara e não gratuita
Tracing distribuído com amostragem diferenciada, métricas de negócio, custo por endpoint — tudo isso tem custo de armazenamento e, em muitos provedores gerenciados, custo por métrica/trace ingerido. Para orçamento limitado, começar com logs estruturados + 3-4 métricas técnicas (erro, latência, saturação, fila) cobre a operação inicial. Tracing distribuído completo é mais defensável depois que houver múltiplos serviços de fato, não antes.

### 4.5 Segunda região "avaliar somente após medir necessidade" está correto, mas o documento já gasta espaço projetando-a (seção 2, "Recuperação")
Pequena inconsistência: a seção 4.1 já inclui "replicação para segunda região" como parte da "Região primária + Recuperação", enquanto a seção 13 (Fase 7) diz para avaliar isso só depois de medir necessidade. Alinhar: não descrever replicação para segunda região como componente da topologia inicial se a decisão está condicionada a RTO/RPO ainda não definidos.

### 4.6 Nenhuma menção a limitações reais de provedores citados implicitamente
O documento fala em "CDN", "WAF", "fila gerenciada", "gateway" sem nomear provedores — o que é correto dado que não há stack definida. Mas isso significa que **nenhuma característica concreta de limite de throughput, cota de requisições, ou tabela de preços pode ser assumida** neste momento. Qualquer estimativa de custo feita depois desta etapa deve vir com fonte (tabela de preços do provedor real), não de memória.

---

## 5. O que falta para reduzir a incerteza (bloqueadores reais)

Sem os itens abaixo, qualquer arquitetura — simples ou complexa — é chute:

1. Volume médio e de pico (requisições/segundo, não "picos sazonais" genérico).
2. Duração e previsibilidade do pico (dias? horas? sabido com quanto tempo de antecedência?).
3. Teto de orçamento mensal em valor absoluto — "limitado" não é acionável.
4. Distribuição geográfica real dos usuários (afeta se CDN/edge é sequer necessário).
5. Tipo de dado e exigência de consistência (decide se cache/fila valem a pena).
6. Se já existe stack/provedor cloud contratado (evita redesenhar o que já está decidido).

---

## 6. Recomendação de escopo mínimo viável

Para o primeiro ciclo, sugiro reduzir a proposta a:

- Backend stateless único, atrás de um serviço gerenciado de API/load balancer com TLS e rate limiting nativos do provedor.
- Banco gerenciado único (sem multi-região).
- Autoscaling horizontal com **limite máximo travado por orçamento** — este é o único mecanismo de contenção de custo indispensável desde o início.
- Logs estruturados + 3-4 métricas técnicas básicas.
- Cache só se um endpoint específico já mostrar custo/latência alto em teste real.
- Fila/workers/segunda região/WAF dedicado/tracing distribuído: adiar para quando o teste de carga ou a operação real comprovarem necessidade.

Isso não substitui o roadmap do documento original como referência de "para onde crescer" — mas evita que a equipe construa a fase 4-7 antes de validar que a fase 1-3 já resolve o problema com o orçamento disponível.
