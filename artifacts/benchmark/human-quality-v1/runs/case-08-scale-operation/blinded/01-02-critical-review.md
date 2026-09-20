# Revisão crítica — API global com picos sazonais e orçamento limitado

## 1. Fatos fornecidos

- A API deve ter alcance global.
- A demanda apresenta picos sazonais.
- Existe restrição orçamentária.
- Não foram fornecidos números de tráfego, orçamento, SLA, regiões ou características da API.

## 2. Premissas frágeis ou ainda não demonstradas

### “Global” não significa necessariamente multi-região ativo

A proposta anterior associa alcance global a possíveis componentes como CDN e presença multi-região, mas isso ainda não é consequência necessária. “Global” pode significar:

- consumidores em vários países;
- endpoint acessível internacionalmente;
- implantação em múltiplas regiões;
- requisitos de residência ou processamento local de dados.

Cada interpretação tem custos e riscos diferentes. Uma implantação multi-região ativa pode ser incompatível com o orçamento, enquanto um único ponto de presença com CDN pode não atender aos requisitos de latência ou disponibilidade.

**Correção recomendada:** definir “global” por requisitos mensuráveis: países atendidos, latência máxima por região, regiões obrigatórias e necessidade — ou não — de failover regional.

### “Atender o pico” não implica disponibilidade sem degradação

A saída anterior infere como objetivo “manter disponibilidade durante os picos sem downtime”. Isso é mais forte do que os dados permitem. Com orçamento limitado, pode ser necessário escolher entre:

- preservar disponibilidade, mas aceitar latência maior;
- limitar ou enfileirar requisições;
- degradar funcionalidades secundárias;
- rejeitar tráfego acima de uma cota;
- manter um SLA restrito fora das janelas críticas.

**Correção recomendada:** separar disponibilidade, latência, taxa de erro e capacidade. Definir quais degradações são aceitáveis antes de afirmar que o objetivo é ausência de downtime.

### Auto-scaling não resolve picos instantâneos por si só

Escalonamento automático pode reagir tarde a picos abruptos, especialmente quando há tempo de inicialização, limites de quota ou dependências lentas. Também pode aumentar o custo de forma descontrolada durante um evento ou ataque.

**Correção recomendada:** avaliar conjuntamente:

- previsão e pré-aquecimento para picos conhecidos;
- limites máximos de escala;
- filas e backpressure;
- rate limiting;
- proteção contra abuso;
- capacidade das dependências, e não apenas da camada da API.

### Serverless ou cobrança por uso não garantem menor custo

O modelo de cobrança pode ser vantajoso para tráfego variável, mas o custo depende de duração, memória, chamadas externas, transferência de dados, logs, cache, banco e tráfego de saída. Em picos longos ou previsíveis, capacidade reservada ou uma arquitetura híbrida pode ser mais econômica.

**Correção recomendada:** não escolher “serverless versus capacidade reservada” sem uma simulação com pelo menos três cenários: base, pico esperado e pico extremo.

## 3. Contradições e riscos que ficaram subexplorados

### Alcance global versus orçamento

A tensão foi identificada, mas ainda falta explicitar a decisão que precisa ser tomada: qual requisito pode ser reduzido quando houver conflito?

Possíveis limites:

- menos regiões operacionais;
- latência maior em algumas localidades;
- failover manual em vez de automático;
- SLA inferior;
- escopo funcional reduzido durante o pico;
- teto de consumo com rejeição controlada.

Sem essa prioridade, a proposta tende a prometer simultaneamente baixo custo, alta disponibilidade, baixa latência global e grande elasticidade — combinação que não deve ser tratada como garantida.

### Proteção do orçamento pode prejudicar clientes legítimos

Rate limiting e quotas são úteis, mas podem causar rejeições durante um pico legítimo. Também podem ser injustos se aplicados apenas por endereço IP, devido a NAT, proxies ou clientes distribuídos.

**Correção recomendada:** definir quotas por identidade contratual ou consumidor, política de burst, resposta de erro, mecanismo de priorização e processo para aumento temporário de limite.

### Cache pode introduzir dados obsoletos ou vazamento entre consumidores

A recomendação de cache/CDN depende de a API ter respostas cacheáveis. Dados personalizados, sensíveis ou com forte requisito de consistência podem não ser compatíveis com cache compartilhado.

**Correção recomendada:** classificar endpoints por segurança, personalização, tolerância a stale data e possibilidade de invalidação antes de incluir cache na solução.

### O gargalo pode estar fora da API

A camada HTTP pode escalar enquanto banco de dados, sistema de pagamentos, provedor externo, fila ou serviço de autenticação permanece limitado. Isso pode gerar falhas em cascata e custos adicionais de retry.

**Correção recomendada:** mapear dependências críticas, limites conhecidos, comportamento sob saturação, timeouts, retries e idempotência.

### “Custo mensal máximo” pode ser incompatível com elasticidade ilimitada

Se o orçamento for um teto rígido, a plataforma precisa de uma política explícita para quando o limite for atingido. Um alerta não impede o gasto nem protege automaticamente a operação.

**Correção recomendada:** estabelecer orçamento operacional e orçamento de emergência, além de uma ação automática ou manual para contenção: reduzir funcionalidades, bloquear clientes não prioritários, limitar tráfego ou aceitar degradação.

## 4. Escopo excessivo ou prematuro na proposta anterior

A lista anterior mistura decisões de arquitetura, operação e controle financeiro antes de confirmar o problema. Em particular:

- CDN, cache, auto-scaling e serverless não são necessariamente necessários;
- alertas de orçamento são controle operacional, não solução de capacidade;
- multi-região foi sugerido indiretamente sem requisito de disponibilidade ou residência;
- rate limiting pode ser necessário por segurança mesmo sem picos, mas sua política ainda não foi definida;
- “sem downtime” foi assumido sem um SLA fornecido.

**Correção recomendada:** começar por uma caracterização mínima do tráfego e por critérios de aceitação. Só depois comparar opções de implantação.

## 5. Dependências e informações ausentes

Antes de uma decisão técnica, ainda precisam ser validados:

1. Volume normal, pico esperado, pico extremo e duração de cada cenário.
2. Distribuição geográfica dos consumidores e latência aceitável por região.
3. Tipo de API: leitura, escrita, processamento assíncrono, streaming ou mistura.
4. Percentual de requisições cacheáveis e requisitos de consistência.
5. Dependências internas e externas, incluindo limites e custos variáveis.
6. SLA desejado para disponibilidade, latência e erros.
7. Teto de custo, moeda, periodicidade e existência de orçamento de emergência.
8. Critério para bloquear, priorizar ou degradar tráfego.
9. Sensibilidade dos dados e requisitos de residência, privacidade ou auditoria.
10. Capacidade atual, se a API já existe, e métricas históricas de incidentes.
11. Previsibilidade e antecedência dos eventos sazonais.
12. Quem será responsável por operar a infraestrutura durante o pico.

## 6. Validações humanas necessárias

As seguintes decisões não devem ser inferidas apenas da ideia:

- Qual requisito prevalece quando custo, latência, disponibilidade e cobertura global entrarem em conflito?
- É aceitável rejeitar requisições acima do limite financeiro?
- Quais consumidores ou operações têm prioridade?
- Quais funcionalidades podem ser desativadas durante sobrecarga?
- Existe obrigação contratual de atender todas as regiões?
- Qual nível de indisponibilidade ou degradação é aceitável?
- O orçamento inclui observabilidade, transferência de dados, suporte operacional e incidentes?
- Há autorização para usar dados agregados de tráfego e comportamento para dimensionamento?

## 7. Recomendações objetivas

1. Substituir o objetivo genérico por uma matriz de metas: tráfego, p95/p99, taxa de erro, disponibilidade, regiões e custo máximo.
2. Definir três cenários de demanda: normal, pico planejado e pico extremo.
3. Especificar uma política de degradação antes de escolher a arquitetura.
4. Modelar o custo total, incluindo dependências, saída de dados, logs, cache, armazenamento e operação.
5. Identificar o gargalo limitante e testar a capacidade ponta a ponta, não apenas a escalabilidade da API.
6. Validar se “global” exige multi-região, baixa latência ou apenas acessibilidade internacional.
7. Tratar auto-scaling como parte de uma estratégia que inclui previsão, limites, filas, quotas e proteção contra abuso.
8. Criar um plano de teste de carga e um ensaio operacional antes do próximo pico sazonal.
9. Definir um mecanismo de contenção financeira com autoridade clara para acionamento.
10. Adiar decisões sobre provedor, serverless, CDN e multi-região até que esses critérios estejam preenchidos.

## 8. Conclusão

A ideia é válida como problema de capacidade e custo, mas ainda não sustenta uma arquitetura específica. A principal lacuna não é escolher entre auto-scaling, serverless ou multi-região; é definir quais níveis de serviço e quais comportamentos de degradação são aceitáveis dentro do orçamento.

A próxima etapa deveria produzir uma matriz de requisitos e cenários quantitativos. Sem isso, qualquer promessa simultânea de operação global, alta disponibilidade, baixa latência e custo limitado permanece uma hipótese não validada.
