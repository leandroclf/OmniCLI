# Exploração de Produto — Migração de Monólito Crítico Sem Interrupção

## Fatos fornecidos

- A ideia original contém apenas uma frase: "Migrar um monólito crítico sem interromper clientes existentes."
- Não há saída anterior deste pipeline para este item.
- Nenhum dado concreto foi fornecido sobre: stack atual, domínio de negócio, motivo da migração, arquitetura-alvo, tamanho da base de clientes, SLAs vigentes ou prazo.

Tudo abaixo além desta seção é hipótese, inferência ou recomendação — nada foi confirmado pelo usuário.

## Problema (hipótese)

Um sistema monolítico é classificado como "crítico" — presumivelmente por sustentar receita, operação ou obrigações contratuais — e precisa evoluir (para outra arquitetura, plataforma ou fornecedor) sem gerar indisponibilidade, perda de dados ou regressão perceptível para quem já o usa.

**Perguntas em aberto (não posso presumir):**
- Migrar *para* o quê? (microsserviços, outro monólito, outra linguagem, outra nuvem, outro banco de dados?)
- "Crítico" segundo qual critério? (receita, compliance, contrato de SLA, segurança?)
- O que motiva a migração agora? (dívida técnica, custo, fim de suporte, aquisição, escala?)

## Público-alvo (hipótese)

Dois públicos distintos, com necessidades conflitantes:
1. **Clientes finais do sistema atual** — não devem perceber nada além de eventual melhoria.
2. **Time técnico responsável pela migração** — precisa de visibilidade, rollback e controle de risco.

**Pergunta em aberto:** quem são os clientes concretamente? B2B, B2C, integrações via API, quantos usuários/tenants ativos?

## Objetivos prováveis (não confirmados)

- Zero downtime perceptível (ou downtime dentro de uma janela de SLA já existente, ainda não informada).
- Sem perda ou corrupção de dados durante o corte.
- Capacidade de reverter (rollback) rapidamente se algo falhar.
- Paridade funcional com o sistema legado, ao menos no primeiro corte.

**Recomendação:** definir metas mensuráveis antes de qualquer desenho técnico (ex.: downtime máximo tolerado, taxa de erro aceitável durante a transição, tempo máximo de rollback). Sem esses números, "sem interromper" é ambíguo — pode significar "zero downtime absoluto" ou "downtime dentro da janela de manutenção contratual".

## Funcionalidades/capacidades plausíveis de um projeto assim (hipótese, não uma proposta de arquitetura)

- Estratégia de corte incremental (ex.: strangler fig, feature flags, dual-write, shadow traffic) — cito esses termos apenas como categorias conhecidas do mercado, não como recomendação técnica definitiva para este caso, já que não conheço a stack.
- Sincronização ou migração de dados entre sistema antigo e novo, com plano de reconciliação.
- Observabilidade comparativa entre os dois sistemas durante a transição (métricas, logs, alertas).
- Plano de rollback testado, não apenas documentado.
- Comunicação com clientes sobre janelas de manutenção, caso alguma seja inevitável.

**Sinalizo incerteza explícita:** não tenho informação sobre quais dessas técnicas são viáveis, permitidas ou já usadas neste ambiente. Não invento aqui integrações, custos de nuvem, ferramentas específicas ou obrigações legais — isso depende do contexto real do sistema, que ainda não foi descrito.

## Riscos a validar (recomendação)

- Acoplamento com sistemas externos/terceiros que dependem de contratos de API do monólito atual.
- Estado transacional (ex.: pagamentos, estoque) que não tolera inconsistência durante uma janela de dual-write.
- Dependências de infraestrutura (banco de dados, filas, autenticação) que podem ser pontos únicos de falha na transição.

## Perguntas não respondidas (lista consolidada)

1. Qual é a tecnologia/arquitetura atual do monólito e qual é o alvo da migração?
2. Qual é a motivação de negócio (custo, escala, fim de vida, aquisição, compliance)?
3. Quantos clientes/tenants são afetados e qual é o perfil deles (B2B/B2C/API)?
4. Existe SLA contratual já definido para downtime e para reversão?
5. Há dados de compliance/regulatórios (ex.: financeiro, saúde) que restringem estratégias como dual-write?
6. Existe prazo (deadline) externo (fim de contrato de fornecedor, EOL de tecnologia)?
7. Qual é o orçamento e a equipe disponível para conduzir a migração?
8. Já existe algum diagnóstico técnico do monólito (dependências, acoplamentos, dívida técnica) ou este é o ponto de partida?
