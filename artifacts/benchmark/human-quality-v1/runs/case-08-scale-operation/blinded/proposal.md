# Proposta Mestra de Arquitetura — API global com picos sazonais e orçamento limitado

## 1. Escopo

Operar uma API acessada por clientes globalmente distribuídos, sujeita a picos sazonais de tráfego, sob restrição de orçamento não quantificada.

**Fora de escopo desta proposta** (por falta de dado, não por omissão): stack de tecnologia específica, valores de custo, SLA numérico, arquitetura multi-região ativa. Essas decisões dependem de dados listados na Seção 8.

## 2. Fatos fornecidos

- Alcance global de clientes.
- Existência de picos sazonais de tráfego.
- Orçamento limitado (sem valor definido).

Todo o restante deste documento — volumes, custos, provedores, prazos — é hipótese ou recomendação, sinalizada como tal.

## 3. Premissas assumidas (a validar)

| Premissa | Status | Risco se errada |
|---|---|---|
| Picos são sazonais (previsíveis por época), não aleatórios | Hipótese | Se imprevisíveis, autoscaling reativo pode não bastar |
| "Global" significa consumo distribuído, não necessariamente processamento distribuído | Recomendação, não fato | Multi-região ativo-ativo seria custo desnecessário se errado |
| Já existe (ou será escolhido) um provedor cloud único | Não informado | Sem isso, qualquer estimativa de custo é inválida |
| Volume de tráfego é "moderado" (não hiperescala) | Hipótese não confirmada | Dimensionamento pode estar sub ou superestimado |

**Correção explícita de premissa frágil:** não se deve tratar "API global" como sinônimo de "infraestrutura multi-região". A alternativa mais simples — região única de processamento + CDN/edge para distribuição — atende alcance global sem o custo operacional de multi-região, e deve ser o ponto de partida até haver evidência (medição de latência real) de que não basta.

## 4. Decisões de arquitetura (recomendadas para o incremento inicial)

1. **Uma única região de processamento**, atrás de um serviço gerenciado de borda/CDN para reduzir latência global de leitura e absorver picos de tráfego estático.
2. **Backend stateless**, permitindo autoscaling horizontal simples sem coordenação de estado entre instâncias.
3. **Autoscaling horizontal com teto máximo travado** — este é o único mecanismo de contenção de custo indispensável desde o dia 1, dado o orçamento limitado.
4. **Banco de dados gerenciado único**, sem replicação multi-região nesta fase.
5. **Cache local em memória** (não distribuído) por instância; cache distribuído só se um endpoint específico comprovar necessidade em teste de carga.
6. **Observabilidade mínima**: logs estruturados + métricas técnicas essenciais (taxa de erro, latência, saturação de CPU/memória). Tracing distribuído completo é adiado.

**Decisões explicitamente adiadas** (não descartadas — sem dado suficiente para justificar agora): fila assíncrona/workers, segunda região, WAF dedicado, pré-aquecimento manual de capacidade, serviço de identidade dedicado. Cada um só se justifica com evidência de necessidade (teste de carga, operação lenta comprovada, RTO/RPO definido).

## 5. Requisitos

### Funcionais
- Atender requisições de clientes em múltiplas regiões geográficas.
- Absorver picos de tráfego sazonais sem indisponibilidade generalizada.

### Não funcionais
- Custo operacional deve caber em orçamento — **valor ainda não definido pelo solicitante**.
- Elasticidade automática, com teto de custo travado (trade-off: elasticidade protege disponibilidade, mas transfere risco para a fatura — este é o ponto de maior atenção do orçamento).
- Simplicidade operacional prioritária sobre robustez especulativa, dado o estágio inicial do projeto.

## 6. Riscos

| Risco | Causa | Mitigação proposta |
|---|---|---|
| Estouro de orçamento em pico | Autoscaling sem teto | Travar limite máximo de instâncias/custo por política do provedor |
| Complexidade prematura consome orçamento antes de gerar valor | Componentes (fila, WAF, multi-região) adicionados sem evidência de necessidade | Adiar até teste de carga real comprovar necessidade (Seção 4) |
| Estimativas de custo inválidas | Nenhum provedor, volume ou preço confirmado | Não aprovar orçamento com base em números deste documento; buscar tabela de preços real antes de comprometer verba |
| Autoscaling não reage a tempo em pico abrupto | Picos podem não ser tão previsíveis quanto assumido (premissa não confirmada) | Validar com teste de carga simulando o pico antes de descartar fila/pré-aquecimento |
| Vendor lock-in prematuro | Escolha de banco/fila antes de conhecer padrão de acesso real | Não escolher tecnologia de dado antes de mapear padrão de leitura/escrita |

## 7. Critérios de aceite (para o incremento inicial)

- API responde a partir de qualquer região testada dentro de latência aceitável — **meta numérica pendente de definição**.
- Sistema sobrevive a um teste de carga simulando o pico sazonal esperado, dentro do teto de custo definido, sem queda total do serviço.
- Custo mensal observado em operação normal e em pico fica dentro do teto orçamentário — **valor pendente**.
- Nenhum componente de fase futura (fila, segunda região, WAF dedicado) foi implementado sem evidência registrada de necessidade.

## 8. Decisões pendentes (bloqueadores reais — sem isso, tudo abaixo é chute)

1. Volume médio e de pico em requisições/segundo (não "picos sazonais" genérico).
2. Duração e previsibilidade do pico — sabido com quanto tempo de antecedência?
3. Teto de orçamento mensal em valor absoluto.
4. Distribuição geográfica real dos usuários (afeta se CDN/edge é necessário).
5. Tipo de dado e exigência de consistência (decide se cache/fila valem o custo).
6. Stack/provedor cloud já contratado, se houver.
7. Meta de latência aceitável por região.

---

**Nota de encerramento:** este documento é referência para evolução, não escopo obrigatório do primeiro incremento. Recomenda-se não avançar para os itens da Seção 4 ("adiados") sem antes responder à Seção 8.
