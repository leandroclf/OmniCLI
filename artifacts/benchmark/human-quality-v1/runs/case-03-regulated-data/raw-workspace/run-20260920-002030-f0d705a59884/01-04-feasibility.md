# Revisão de viabilidade — Ciclo 1

## 1. Enquadramento da revisão

O único fato confirmado permanece: "criar um serviço que processa documentos de saúde de pacientes". A proposta arquitetural anterior é internamente consistente e tecnicamente razoável como referência de destino, mas foi construída inteiramente sobre hipóteses — inclusive as premissas de escala, integração e conformidade nas quais os custos e riscos abaixo se apoiam. Esta revisão trata o documento anterior como entrada não confiável a ser avaliada, não como escopo já aprovado.

**Julgamento central:** a arquitetura descrita é um desenho de sistema maduro (fila, workers, revisão humana, storage segregado, observabilidade completa, 4 fases de rollout). Para um serviço cujo primeiro tipo documental, volume e consumidor ainda não existem, isso é sobre-especificação prematura. Não há hipótese fornecida de volume que justifique fila assíncrona, workers escaláveis horizontalmente e um catálogo de 10+ métricas de qualidade antes de processar o primeiro documento real.

---

## 2. Fatos, hipóteses e recomendações

### Fatos
- Requisito único confirmado: processar documentos de saúde de pacientes.
- Nenhum tipo documental, volume, consumidor, jurisdição ou orçamento foi definido em nenhum dos dois ciclos.

### Hipóteses (do documento anterior, não verificadas)
- Volume que justificaria fila e workers dedicados (não fornecido).
- Necessidade de múltiplos perfis de acesso (`integrador`, `revisor`, `auditor`, `operador`, `administrador`) — razoável em produção madura, mas não sustentada por nenhum requisito de equipe real.
- Disponibilidade de orçamento para armazenamento segregado por tenant, criptografia gerenciada, provedor de OCR externo e revisão humana com SLA.
- Que o processamento "pode demorar mais que uma requisição HTTP" — plausível para OCR, mas não medido.

### Recomendações desta revisão
- Não aprovar a Fase 1 como descrita (13+ componentes lógicos) sem antes rodar um teste de menor escala.
- Validar com um único documento real (ou sintético representativo) processado de ponta a ponta antes de desenhar fila, múltiplos estados e perfis de acesso.
- Recomendação forte: adiar qualquer decisão de infraestrutura (fila gerenciada, banco dedicado, storage segregado por tenant) até que a Fase 0 (fechamento de requisitos) esteja de fato concluída — hoje ela nem começou.

---

## 3. Custos e complexidade

### Complexidade de componentes
A arquitetura lista: API de ingestão, storage de objetos, banco de metadados, fila, worker, serviço de revisão humana, serviço de publicação — 7 serviços/componentes lógicos, cada um com contrato, observabilidade e testes próprios. Isso é o desenho correto para operação em produção com múltiplos tenants e volume real. Não é o desenho correto para "primeiro processamento de um documento de saúde", que é o único requisito confirmado.

**Alternativa mais simples a considerar:** um monólito modular (API síncrona ou com polling simples via job em processo, um único banco relacional guardando metadados e status, storage de objetos gerenciado) cobre o mesmo fluxo funcional (ingestão → OCR → extração → revisão → publicação) sem fila dedicada nem workers separados, até que o volume medido justifique o desacoplamento. Isso não é uma hipótese de capacidade técnica de nenhuma ferramenta específica — é uma observação de que o problema descrito (baixo volume, primeiro tipo documental) não exige a arquitetura distribuída proposta.

### Custo operacional recorrente não quantificado
O documento anterior lista dezenas de requisitos não funcionais (métricas, alertas, ADRs, 4 fases) sem qualquer estimativa de custo — nem de infraestrutura, nem de esforço de engenharia, nem de revisão humana contínua. Sinalizo isso como lacuna, não como erro: **nenhum valor de custo foi fornecido ou deveria ser inventado aqui.** Recomendo que a Fase 0 inclua explicitamente uma estimativa de esforço/custo antes de qualquer commitment de escopo.

### Revisão humana como centro de custo subestimado
ADR-003 decide corretamente que resultados incertos não devem ser publicados automaticamente. Isso é uma decisão de segurança correta, mas tem um custo operacional recorrente (pessoas, treinamento, SLA de revisão) que a proposta não dimensiona. Esse é o item de custo mais provável de virar gargalo em produção e deveria ter uma estimativa de taxa de revisão esperada antes de comprometer a arquitetura de fila e workers em torno dele.

---

## 4. Riscos operacionais

- **Dependência de provedor externo de OCR/IA sem contrato validado.** A seção 8 já sinaliza corretamente essa incerteza (localização de dados, retenção, treinamento). Endosso o encapsulamento (ADR-005) como mitigação correta e mínima — não recomendo substituí-la por integração direta.
- **Ausência de definição de jurisdição.** Sem jurisdição definida, qualquer afirmação sobre "requisitos legais de dados de saúde" seria invenção. O documento anterior evita isso corretamente na seção 10 ("não presume obrigações legais específicas"); mantenho essa cautela e reforço que nenhuma arquitetura de retenção/criptografia deveria ser fixada em contrato antes da definição jurídica.
- **Erro de associação paciente-documento (ADR-004).** Decisão correta e barata de manter (exigir identificador externo em vez de inferir por OCR). Não há razão para revisar essa escolha.
- **Escopo de fases excessivo para o estágio atual do projeto.** Fases 0–4 do documento anterior descrevem um roadmap de produto maduro. O risco operacional real agora é investir em desenho de 4 fases antes de validar se o primeiro tipo documental sequer é viável tecnicamente (qualidade de OCR na prática, taxa de campos ilegíveis) — esse é o risco que deveria ser eliminado primeiro, com o menor experimento possível.

---

## 5. Limitações de ferramentas (sinalização de incerteza)

Não há confirmação de que:
- Um provedor de OCR específico atinja a precisão necessária para os campos ainda não definidos — não invento números de acurácia.
- Existe capacidade orçamentária ou disponibilidade de equipe de revisão humana.
- A infraestrutura de fila/worker mencionada (não nomeada) é a já usada no ambiente do usuário ou exigiria nova adoção.

Essas são lacunas de informação, não afirmações — precisam ser preenchidas antes de qualquer estimativa de custo real.

---

## 6. Alternativa mais simples recomendada para este estágio

Antes de aprovar a arquitetura de 7 componentes, execute um protótipo mínimo:

1. Um endpoint único que recebe o arquivo, roda OCR síncrono (ou job em background simples) e retorna o texto/campos extraídos.
2. Armazenamento em um único bucket + um único banco relacional para status.
3. Sem fila dedicada, sem múltiplos perfis de acesso, sem fases de observabilidade completas.

Isso valida a hipótese de maior risco (qualidade de OCR/extração no tipo documental real) com o menor investimento possível. Se o volume e a necessidade de revisão humana se confirmarem na prática, a evolução para a arquitetura completa do ciclo anterior é justificada — e as decisões de ADR-001 a ADR-005 continuam válidas como destino, não como ponto de partida obrigatório.

---

## 7. Síntese

| Item | Avaliação |
|---|---|
| Correção técnica geral | Sólida como arquitetura-alvo de produção |
| Adequação ao estágio atual (nenhum requisito fechado) | Sobredimensionada — recomendo protótipo mínimo primeiro |
| Decisões de segurança/privacidade (ADR-003, ADR-004, ADR-005) | Corretas, manter independentemente da escala escolhida |
| Estimativa de custo | Ausente — não deve ser inventada, deve ser produzida na Fase 0 |
| Maior risco não mitigado | Investir em desenho de produto completo antes de validar OCR/extração no tipo documental real |

**Recomendação final:** aprovar as decisões de segurança e privacidade (ADRs 003–005) como princípios permanentes, mas reduzir o escopo de implementação inicial a um protótipo de fluxo único e síncrono antes de comprometer fila, múltiplos serviços e quatro fases de rollout. Fase 0 (fechamento de requisitos) continua sendo o bloqueador real e deve preceder qualquer decisão de infraestrutura.
