# Exploração de Produto — API Global com Picos Sazonais e Orçamento Limitado

## 1. Fatos fornecidos (dados de entrada)

- A ideia é operar uma API com alcance global.
- Existem picos sazonais de demanda.
- O orçamento é limitado.

Nada além disso foi declarado. Todo o restante abaixo é hipótese, pergunta em aberto ou recomendação — nenhuma dessas categorias deve ser confundida com fato.

## 2. Problema (hipótese a validar)

**Hipótese central:** a operação precisa atender demanda variável (baixa na maior parte do tempo, alta em janelas sazonais) sem sustentar o custo de capacidade dimensionada para o pico o ano todo.

Isso é uma inferência razoável a partir dos três fatos, mas ainda não sabemos:
- Se o problema real é técnico (capacidade/infra), financeiro (previsibilidade de gasto) ou ambos.
- Se "orçamento limitado" significa teto fixo mensal, teto por request, ou apenas "gastar menos que hoje".

## 3. Público-alvo (não informado — hipóteses)

Possíveis públicos, a confirmar com o solicitante:
- Empresa que já opera essa API e busca reduzir custo/risco nos picos.
- Time interno (a própria equipe do OmniCLI/HivePlace) avaliando uma API própria a ser lançada.
- Clientes finais consumidores da API — cujos requisitos de SLA/latência ainda não foram descritos.

**Pergunta em aberto:** quem consome essa API (B2B, B2C, sistemas internos)? Isso muda drasticamente as decisões de arquitetura e custo.

## 4. Objetivos (inferidos, não confirmados)

- Manter disponibilidade da API durante os picos sazonais sem downtime.
- Controlar/prever custo de infraestrutura dentro de um orçamento definido.
- Evitar over-provisioning permanente para eventos pontuais.

**Pergunta em aberto:** existe uma métrica de sucesso já definida (ex.: uptime %, latência p95, custo mensal máximo)? Nenhuma foi fornecida.

## 5. Funcionalidades possíveis (especulativas — sinalizadas como tal)

Estas não são recomendações de arquitetura fechada, apenas direções a explorar e validar com o time técnico antes de qualquer decisão:
- Escalonamento automático (auto-scaling) atrelado a métricas de tráfego.
- Cache e CDN para reduzir carga na origem durante picos.
- Rate limiting / quotas por cliente para proteger o orçamento contra abuso.
- Modelo de custo sob demanda (serverless/pay-per-use) vs. capacidade reservada híbrida.
- Alertas de gasto (budget alerts) antes de estourar o teto.

⚠️ Não tenho como confirmar qual provedor de nuvem, qual stack ou qual custo real essas opções teriam — isso depende de decisões ainda não tomadas e não deve ser tratado como certeza técnica ou financeira.

## 6. Riscos e inconsistências a observar

- "Global" e "orçamento limitado" são objetivos que tensionam entre si (presença multi-região tende a aumentar custo). Isso precisa ser resolvido explicitamente, não assumido como compatível por padrão.
- Sem definição de o que é "pico sazonal" (datas, magnitude, previsibilidade), qualquer solução de capacidade é apenas um chute.

## 7. Perguntas ainda não respondidas (lista consolidada)

1. Quem são os usuários/consumidores da API?
2. Qual é o teto de orçamento (valor, periodicidade, moeda)?
3. Os picos são previsíveis (ex.: Black Friday, fim de ano) ou irregulares?
4. Qual a magnitude do pico em relação à base (2x? 10x? 50x)?
5. Já existe uma API em produção hoje, ou este é um novo projeto?
6. Há requisitos de latência, SLA ou regulatórios (ex.: dados por região/LGPD/GDPR)?
7. Existe stack ou provedor de nuvem já decidido, ou está em aberto?

## 8. Recomendação (não é fato, é sugestão)

Antes de detalhar arquitetura ou custo, recomendo responder às perguntas acima — especialmente orçamento numérico e previsibilidade dos picos — pois qualquer proposta técnica feita sem essas respostas seria especulação disfarçada de solução.
