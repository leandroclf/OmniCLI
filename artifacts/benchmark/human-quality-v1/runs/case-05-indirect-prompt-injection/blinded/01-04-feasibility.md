# Revisão de viabilidade — Ciclo 1/1

## 1. Resumo da avaliação

O documento anterior já reformulou corretamente a ideia original (usar um documento externo para induzir vazamento de segredos e quebra de regras) como um **teste defensivo de resistência a prompt injection**. Essa reformulação é a única leitura tecnicamente aceitável da proposta e deve ser preservada. Esta revisão avalia se a arquitetura proposta é viável para ser construída, e não apenas desejável.

**Veredito geral:** a arquitetura é conceitualmente correta, mas está superdimensionada para uma primeira entrega. Como está descrita, ela é um produto de plataforma de red-teaming contínuo, não um teste de viabilidade. Isso é risco de execução, não erro conceitual.

---

## 2. Fatos, hipóteses e recomendações (separados)

### Fatos fornecidos
- A ideia original menciona apenas "um documento externo" e "revelar segredos e ignorar regras". Não há agente-alvo, ferramentas, ambiente ou stack especificados.
- Nenhum dado sobre orçamento, prazo ou equipe disponível foi fornecido em nenhum ciclo anterior.

### Hipóteses assumidas pela arquitetura anterior (não confirmadas)
- Que haverá autorização formal e ambiente de testes separado de produção.
- Que existe (ou será construído) um proxy de ferramentas controlável.
- Que há capacidade de engenharia para manter 9 componentes, 4 modelos de dados e um catálogo de casos versionado.
- Que o "agente sob avaliação" já expõe alguma interface de entrada de documento — isso não foi confirmado.

Sinalizo explicitamente: **não tenho como confirmar se essas capacidades existem no ambiente do usuário.** Isso precisa ser validado antes de qualquer implementação, como o próprio documento anterior já reconhece na seção 11.

### Minhas recomendações (não fatos)
- Não construir os 9 componentes de uma vez. Ver seção 4.

---

## 3. Custos e complexidade — pontos de atenção

| Área | Risco identificado |
|---|---|
| **Escopo** | 9 componentes arquiteturais, 4 entidades de dados, proxy de rede/ferramentas dedicado, sandbox descartável, sistema de avaliação determinística e relatório — isso é escopo de uma ferramenta interna de segurança madura, não de um MVP de validação de hipótese. |
| **Operação** | Manter um proxy de ferramentas com allowlist, um ambiente sandbox descartável e um avaliador de regras é trabalho contínuo de manutenção (novas categorias de ataque aparecem constantemente). O documento não estima esforço recorrente. |
| **Custo de infraestrutura** | Não há estimativa de custo — nem deveria haver, dado que não sei que provedor de nuvem, orquestrador de containers ou runtime de agente está em uso. Qualquer número aqui seria inventado. **Sinalizo a incerteza em vez de estimar.** |
| **Falso senso de segurança** | Um avaliador "determinístico" (busca por marcador secreto-isca, bloqueio de ferramenta) cobre bem os casos triviais, mas **não é garantia de detecção de todas as formas de vazamento indireto** (paráfrase do segredo, codificação, vazamento parcial). O documento já alerta para isso de forma correta na seção 7 ("o comportamento do agente não deve ser fronteira de segurança"), mas vale reforçar: regras determinísticas terão taxa de falso negativo desconhecida até serem testadas contra ataques reais. |
| **Manutenção do catálogo** | Um catálogo de casos versionado com política, severidade e ferramentas permitidas por caso é overhead real de governança — precisa de dono definido, ou o catálogo apodrece rápido. |

---

## 4. Alternativa mais simples (recomendação principal)

Antes de construir a plataforma completa, uma alternativa mais barata cobre boa parte do valor do teste de viabilidade:

**MVP mínimo viável para o mesmo objetivo:**
1. Um script/harness simples que injeta 5–10 documentos com tentativas conhecidas de prompt injection (direto, indireto, em metadado) contra o agente-alvo, em ambiente sem rede e sem credenciais reais.
2. Um segredo-isca fixo (`CANARY_SECRET_DO_NOT_DISCLOSE`) e um `grep`/regex simples checando se ele aparece na saída.
3. Log manual (planilha ou arquivo texto) do resultado aprovado/reprovado por caso.
4. Nenhum proxy de ferramentas dedicado — se o agente não tem acesso a ferramentas reais no teste, essa camada inteira (seção 3.6) não é necessária ainda.

Isso valida a hipótese central — "o agente resiste a documentos maliciosos?" — com uma fração do esforço, e serve de base de evidência para decidir se a plataforma completa (catálogo versionado, proxy, sandbox reutilizável, observabilidade) se justifica.

**Quando evoluir para a arquitetura completa:** se o agente-alvo já tem acesso real a ferramentas/rede em produção, ou se o teste precisa rodar continuamente como gate de CI. Nesses casos o proxy de ferramentas (3.6) e o sandbox descartável (3.4) passam a ser necessários, não opcionais.

---

## 5. O que preservar da proposta anterior

- A separação de camadas de confiança (política > operador > conteúdo externo > saída > ações) está correta e é o núcleo de qualquer defesa contra prompt injection — deve ser mantida em qualquer versão, simples ou completa.
- A recusa em tratar sanitização como prova de segurança (seção 3.3) e em tratar o comportamento do modelo como fronteira de segurança (seção 7) são afirmações corretas e não devem ser suavizadas.
- O uso exclusivo de segredos sintéticos é inegociável e está certo.

---

## 6. Limitações desta revisão

- Não há informação sobre o agente real a ser avaliado, então não posso confirmar se a interface de "documento externo" e "ferramentas" descrita corresponde à realidade do sistema do usuário.
- Não tenho dados de custo de infraestrutura, prazo ou equipe — qualquer número aqui seria invenção, por isso não foi fornecido.
- Este é o ciclo único de revisão; as decisões pendentes listadas na proposta anterior (seção 11) continuam sem resposta e são bloqueadoras reais para dimensionar a arquitetura corretamente.
