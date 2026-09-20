# Proposta Mestra de Arquitetura — Migração incremental do monólito crítico

## 1. Escopo

Migrar um sistema monolítico classificado como crítico para uma arquitetura de destino ainda não definida, sem interromper o atendimento aos clientes existentes durante o processo.

**Fora de escopo nesta proposta** (por ausência de dados): stack de destino, ferramentas específicas de infraestrutura, orçamento, prazo, dimensionamento de equipe. Qualquer decisão nesses pontos abaixo é hipótese, não fato.

## 2. Fatos fornecidos

- Existe um monólito considerado crítico pelo solicitante.
- Há clientes existentes que não podem sofrer interrupção durante a migração.

Nenhum outro dado técnico, operacional ou de negócio foi fornecido (stack atual, volume de tráfego, SLA contratual, tamanho da equipe, orçamento, prazo, grau de modularidade interna). Toda a arquitetura abaixo é, portanto, uma referência conceitual condicionada a essas lacunas — não uma solução dimensionada.

## 3. Premissas (hipóteses, não fatos)

| Premissa | Status |
|---|---|
| O monólito tem pouca ou nenhuma modularidade interna | Não confirmado — precisa validação antes de escolher arquitetura |
| A equipe atual consegue sustentar operação dupla temporária | Não confirmado |
| Existe orçamento para infraestrutura de transição (roteador, comparador em sombra, camada anticorrupção) | Não confirmado |
| "Crítico" implica SLA formal com penalidade contratual | Não confirmado — pode ser apenas relevância de negócio |

Essas premissas precisam ser confirmadas com o solicitante antes de qualquer compromisso de arquitetura.

## 4. Decisões preservadas do ciclo anterior

O ciclo anterior identificou corretamente, e este documento preserva:

- O padrão de referência conceitual é o *strangler fig* (substituição incremental com fonte única de verdade e roteamento reversível) — correto como referência de mercado, não como prescrição fechada para este caso.
- Reconciliação de dados é o item de maior risco de subdimensionamento do plano.
- Falta de critério objetivo de desligamento do legado é um risco operacional real (migrações incrementais sem data-alvo tendem a nunca terminar).
- CDC/outbox/réplicas têm custo dependente da stack de banco — não pode ser estimado sem essa informação.

## 5. Correções e inconsistências sinalizadas

- O ciclo anterior recomendou avaliar **alternativas mais simples que uma plataforma de transição completa** (extração modular leve, janela de manutenção curta, dual-write pontual) antes de comprometer orçamento com roteador + camada anticorrupção + shadow traffic. Este documento reforça essa recomendação como decisão de arquitetura, não como observação lateral: **construir a plataforma de transição completa é um risco de projeto por si só**, pois seu custo de engenharia pode superar o valor migrado.
- Não há, em nenhum dos ciclos, dado que sustente estimativa de prazo, custo ou equipe — qualquer número citado até aqui seria invenção e foi deliberadamente omitido.

## 6. Requisitos

### Requisito funcional único confirmado
- RF1: Clientes existentes devem continuar operando sem interrupção perceptível durante toda a migração.

### Requisitos não funcionais inferidos (recomendação, não fato)
- RNF1 (recomendado): Definir SLA/critério objetivo de "sem interrupção" (ex.: zero downtime vs. downtime tolerado em janela específica) — hoje indefinido.
- RNF2 (recomendado): Reversibilidade de cada etapa de migração (rollback por fatia).
- RNF3 (recomendado): Rastreabilidade/observabilidade equivalente entre sistema legado e novo durante a convivência.

## 7. Arquitetura de referência (condicional)

Aplicável **somente se** as premissas da seção 3 forem confirmadas e alternativas mais simples (seção 5) forem descartadas com justificativa:

1. Fonte única de verdade para dados compartilhados durante a transição.
2. Roteamento por capacidade/fatia, com possibilidade de reversão imediata.
3. Camada anticorrupção entre sistema novo e legado, se os contratos divergirem.
4. Comparação em sombra (shadow traffic) restrita a operações sem efeito colateral — tem custo real de infraestrutura (dobra parte do processamento).
5. Migração por fatias de menor risco primeiro.

**Alternativa mais lazy a avaliar antes desta arquitetura completa:**
- Se o monólito tiver modularidade interna suficiente, extrair 1–2 capacidades como serviços chamados diretamente, sem roteador genérico nem shadow traffic — evita construir uma plataforma de transição inteira antes de entregar qualquer valor.
- Se o gargalo real for o banco de dados, considerar dual-write controlado por período curto em vez de arquitetura completa de roteamento.

## 8. Riscos

| Risco | Impacto | Observação |
|---|---|---|
| Operação dupla (legado + novo) sem prazo de corte definido | Alto — migração pode nunca terminar | Definir critério objetivo de desligamento antes de iniciar, não depois |
| Camada de transição (roteador + anticorrupção + shadow) como projeto paralelo | Alto — pode custar mais que a migração em si | Só construir incrementalmente, conforme fatias exigirem |
| Reconciliação de dados subdimensionada | Alto — item historicamente responsável por estouro de prazo | Tratar como linha de orçamento própria, com ferramentas dedicadas |
| Estimativas de esforço para CDC/eventos sem stack definida | Médio | Impossível quantificar sem saber SGBD/infra atual |
| Ausência de SLA/critério formal de "sem interrupção" | Médio | Pode levar a expectativas divergentes entre negócio e engenharia |

## 9. Critérios de aceite

- [ ] Nenhuma interrupção perceptível ao cliente durante cada fatia migrada (critério de "perceptível" a ser definido com o negócio).
- [ ] Cada fatia migrada possui rollback funcional testado.
- [ ] Reconciliação de dados validada por fatia antes de desligar o caminho legado correspondente.
- [ ] Critério objetivo de desligamento do legado definido e registrado antes do início da execução.
- [ ] Alternativas mais simples (seção 5/7) avaliadas e descartadas ou adotadas, com justificativa documentada, antes de aprovar a arquitetura completa de transição.

## 10. Decisões pendentes

1. Qual é a stack atual do monólito (linguagem, banco de dados, infraestrutura de deploy)?
2. Qual o tamanho da equipe hoje mantendo o monólito, e há capacidade para operação dupla temporária?
3. "Crítico" implica SLA contratual formal, ou é relevância de negócio? Existe penalidade por indisponibilidade?
4. O monólito tem alguma modularidade interna (módulos, bounded contexts já esboçados) que permita uma extração leve, sem plataforma de transição completa?
5. Existe orçamento e prazo-alvo para a migração, ou o projeto é de escopo aberto?
6. Qual o critério objetivo de corte para desligar o sistema legado?
7. Qual o volume de tráfego/clientes, para avaliar se uma janela de manutenção curta e comunicada seria aceitável em vez de operação dual completa?
