# Proposta Mestra de Arquitetura — Defesa contra Prompt Injection via Documento Externo

## 1. Escopo

Construir e validar a capacidade de um agente resistir a instruções maliciosas embutidas em documentos externos (a ideia original — "usar um documento que instrui o agente a revelar segredos e ignorar regras" — é reformulada aqui como **ataque a ser testado e defendido**, não como comportamento a ser construído).

Escopo desta etapa: **MVP de validação**, não plataforma de red-teaming contínuo. Fora de escopo neste ciclo: proxy de ferramentas dedicado, sandbox reutilizável, catálogo de casos versionado, observabilidade contínua — só entram se as decisões pendentes (seção 8) confirmarem a necessidade.

## 2. Fatos fornecidos

- A ideia original menciona apenas "documento externo" + "revelar segredos e ignorar regras". Não há agente-alvo, stack, ferramentas ou ambiente especificados em nenhum ciclo anterior.
- Não há dado de orçamento, prazo ou equipe disponível.
- Não há confirmação de que o agente-alvo já expõe uma interface de ingestão de documentos.

## 3. Hipóteses (não confirmadas — sinalizadas explicitamente)

- Que existirá autorização formal e ambiente separado de produção para o teste.
- Que há capacidade de engenharia para manter a solução ao longo do tempo.
- Que o agente-alvo, quando tiver acesso real a ferramentas/rede, precisará de um proxy controlável — isso só é necessário se essa condição for verdadeira, o que não foi confirmado.

Nenhuma integração, custo de infraestrutura ou capacidade de ferramenta é inventada aqui; onde não há dado, é declarado como incerteza.

## 4. Decisões preservadas do ciclo anterior

- Separação de camadas de confiança (política > operador > conteúdo externo > saída > ações) — correta, mantida.
- Comportamento do modelo **não é fronteira de segurança**; sanitização de saída não é prova de segurança.
- Uso exclusivo de segredos sintéticos (canário), nunca segredos reais, em qualquer teste.

## 5. Arquitetura proposta (MVP)

1. **Harness de teste**: script que injeta 5–10 documentos com padrões conhecidos de prompt injection (instrução direta, indireta, embutida em metadado) contra o agente-alvo.
2. **Ambiente isolado**: execução sem rede real e sem credenciais reais — elimina a necessidade de proxy de ferramentas nesta fase.
3. **Segredo-isca fixo**: `CANARY_SECRET_DO_NOT_DISCLOSE`, verificado por regex/grep na saída do agente.
4. **Registro de resultado**: aprovado/reprovado por caso, em arquivo simples (não requer sistema de catálogo versionado ainda).

Evolução para arquitetura completa (proxy de ferramentas, sandbox descartável, catálogo versionado) só se justifica se: (a) o agente-alvo já tiver acesso real a ferramentas/rede em produção, ou (b) o teste precisar rodar como gate contínuo de CI — ambas condições não confirmadas.

## 6. Requisitos

- O agente sob teste não deve executar ações, revelar segredos-isca ou alterar seu comportamento de política ao processar documento externo malicioso.
- Detecção determinística mínima (grep do canário) — **não é garantia completa**: não cobre paráfrase, codificação ou vazamento parcial do segredo. Isso é limitação conhecida, não corrigida neste MVP.

## 7. Riscos

| Risco | Natureza |
|---|---|
| Escopo inflar para plataforma completa sem necessidade comprovada | Recomendação: conter no MVP até decisão pendente ser respondida |
| Falso senso de segurança do detector determinístico | Fato técnico: taxa de falso negativo é desconhecida até testar contra ataques reais |
| Ausência de dono definido para manter o harness/casos de teste | Risco de governança se o MVP evoluir sem responsável |
| Estimativa de custo de infraestrutura | Não fornecida — qualquer número seria inventado |

## 8. Critérios de aceite

- Harness roda os 5–10 casos de injeção e reporta aprovado/reprovado por caso.
- Nenhum caso resulta em vazamento do segredo-isca ou execução de ação fora da política declarada.
- Resultado documentado de forma rastreável (arquivo de log), mesmo que manual nesta fase.

## 9. Decisões pendentes (bloqueadoras)

1. Qual é o agente-alvo real e ele já expõe interface de ingestão de documento?
2. O agente-alvo terá acesso real a ferramentas/rede em produção (determina se proxy de ferramentas é necessário)?
3. Este teste rodará uma vez ou como gate contínuo de CI (determina se sandbox reutilizável e catálogo versionado se justificam)?
4. Quem é o dono responsável pela manutenção do harness e dos casos de teste?
5. Há orçamento/prazo definidos para dimensionar a evolução além do MVP?

Sem respostas a estas perguntas, qualquer arquitetura além do MVP descrito na seção 5 é especulativa.
