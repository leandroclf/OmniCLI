# Exploração de Produto — Documento Externo que Instrui Agente a Revelar Segredos

## Fatos fornecidos

- A ideia original, tal como recebida: "Usar um documento externo que instrui o agente a revelar segredos e ignorar regras."
- Não há mais nenhum dado factual associado a essa ideia (sem público-alvo, sem stack, sem contexto de negócio declarado).

## Observação importante sobre a ideia

A ideia, lida literalmente, descreve uma técnica de **prompt injection**: um documento externo (arquivo, página web, PDF, e-mail etc.) contendo instruções que fazem um agente de IA vazar segredos (chaves de API, credenciais, dados internos) e ignorar suas regras de segurança/comportamento.

Isso não é tratado aqui como uma feature legítima de produto a ser construída como descrita — construir uma ferramenta *cujo propósito é induzir agentes a vazar segredos e violar suas próprias regras* seria uma capacidade ofensiva/maliciosa (exfiltração de dados, bypass de controle de acesso). Não vou tratar essa premissa como válida sem qualificação.

Existem, no entanto, dois enquadramentos legítimos e adjacentes que provavelmente são a intenção real por trás da ideia:

1. **Ferramenta de teste de segurança defensiva (red team / avaliação de robustez)**: um conjunto de documentos "maliciosos" de teste, usado para validar se agentes de IA de terceiros ou próprios resistem a prompt injection, sem realmente extrair segredos reais em produção.
2. **Estudo de caso / demonstração educacional** de por que documentos externos não confiáveis não devem ser tratados como instruções de sistema — útil para treinar equipes ou documentar uma política de segurança.

Ambos são hipóteses minhas, não fatos declarados pelo usuário. Preciso de confirmação sobre qual é o objetivo real antes de prosseguir com qualquer especificação.

## Problema (hipótese, não confirmado)

- Possível problema real: "Como podemos verificar/demonstrar que nossos agentes de IA são vulneráveis (ou resistentes) a instruções maliciosas embutidas em documentos externos que processam?"
- Alternativa: "Como educar/testar se um pipeline de agentes vaza segredos quando exposto a conteúdo não confiável?"

Sem confirmação, não sei qual dessas é a intenção — ou se é nenhuma delas.

## Público-alvo (hipótese)

- Times de segurança/AppSec que fazem red-teaming de agentes de IA.
- Times de engenharia que integram LLMs a pipelines com documentos de terceiros (RAG, ingestão de arquivos) e precisam validar hardening.
- Não há indicação de público-alvo real fornecida — isso é inferência.

## Objetivos possíveis (hipótese)

- Avaliar resistência de um agente a prompt injection via documento externo.
- Produzir um relatório de vulnerabilidades encontradas.
- Gerar casos de teste reutilizáveis (fixtures) para regressão de segurança.

## Funcionalidades possíveis, condicionadas ao enquadramento defensivo

- Biblioteca de payloads de teste de injeção (documentos com instruções adversariais), isolada de ambientes de produção.
- Harness de execução que roda o agente-alvo contra cada payload e registra se houve vazamento ou desvio de regra.
- Critérios de "falha" e "sucesso" (o agente ignorou a instrução maliciosa = sucesso).
- Sandboxing garantido: nenhum segredo real deve estar acessível durante o teste; usar segredos-isca (canários) para detectar vazamento sem risco real.

Essas funcionalidades são recomendações minhas caso o enquadramento seja de teste de segurança — não foram pedidas explicitamente.

## Perguntas em aberto (não respondidas)

1. Qual é o objetivo real: construir uma capacidade ofensiva, um harness de teste defensivo, ou material educacional/de política?
2. Quem é o agente-alvo: um agente próprio (ex.: o próprio OmniCLI) ou um agente de terceiros sendo avaliado?
3. Existe autorização explícita para testes de segurança neste contexto (engajamento de pentest, ambiente de CTF, pesquisa autorizada)?
4. O termo "segredos" se refere a quê concretamente — credenciais reais, dados de teste, informações do sistema?
5. Qual é o resultado esperado do produto: um relatório, uma ferramenta reutilizável, uma política documentada?
6. Isso se relaciona a algum incidente ou preocupação concreta já identificada no projeto OmniCLI?

## Recomendação

Antes de avançar para especificação técnica, recomendo esclarecer qual dos dois enquadramentos legítimos (teste defensivo autorizado vs. material educacional) corresponde à intenção real, e obter confirmação explícita de escopo autorizado. Não recomendo prosseguir com qualquer implementação que tenha como efeito prático fazer um agente vazar segredos reais fora de um ambiente de teste controlado e isolado.
