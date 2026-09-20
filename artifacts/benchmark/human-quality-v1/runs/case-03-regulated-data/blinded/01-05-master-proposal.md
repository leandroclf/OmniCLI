# Proposta Mestra de Arquitetura — Serviço de Processamento de Documentos de Saúde

## 1. Escopo

**Fato confirmado (entrada original):** criar um serviço que processa documentos de saúde de pacientes. Nenhum outro elemento de escopo (tipo documental, volume, consumidor, jurisdição, orçamento, equipe) foi fornecido em nenhum ciclo anterior.

Escopo desta proposta: um serviço mínimo, de fluxo único e síncrono, que recebe um documento, executa extração (OCR/parsing), passa por um ponto de decisão de confiança e publica um resultado — sem infraestrutura distribuída, sem múltiplos perfis de acesso, sem fases de rollout, até que requisitos reais existam.

**Fora de escopo nesta etapa (hipóteses do ciclo anterior, não descartadas — apenas adiadas):** fila assíncrona dedicada, workers horizontalmente escaláveis, storage segregado por tenant, catálogo de observabilidade completo, múltiplos perfis de acesso (integrador/revisor/auditor/operador/administrador), roadmap de 4 fases.

## 2. Premissas

| Premissa | Status |
|---|---|
| Baixo volume inicial, primeiro tipo documental ainda não validado | Hipótese, não confirmada — mas é a premissa mais segura para não sobre-construir |
| Processamento pode exceder o tempo de uma requisição HTTP síncrona (OCR pesado) | Plausível, não medido |
| Jurisdição/regime legal aplicável a dados de saúde | Não definida — nenhuma obrigação legal específica é presumida aqui |
| Orçamento para provedor externo de OCR/IA e para revisão humana recorrente | Não fornecido |
| Equipe disponível para revisão humana de casos incertos | Não confirmada |

## 3. Decisões (mantidas do ciclo anterior como princípios permanentes)

Estas decisões são independentes de escala e devem valer mesmo no protótipo mínimo:

- **ADR-001 (proposto):** Resultados de extração com confiança abaixo do limiar não são publicados automaticamente — exigem revisão humana antes de liberação. *Motivo:* dado de saúde tem custo alto de erro silencioso.
- **ADR-002 (proposto):** Associação paciente-documento exige identificador externo explícito na ingestão; nunca inferida por OCR. *Motivo:* erro de associação é o risco mais caro do sistema.
- **ADR-003 (proposto):** Qualquer provedor externo de OCR/IA é acessado por meio de uma camada de abstração própria (adapter), nunca integrado diretamente no núcleo do serviço. *Motivo:* preserva a opção de troca de provedor e isola incerteza contratual (retenção, localização de dados, uso para treinamento — **não verificada, sinalizada como risco**, não como fato).

## 4. Requisitos

### Funcionais (mínimos, ciclo 1)
1. Receber um documento (upload único) associado a um identificador de paciente fornecido externamente.
2. Executar extração de texto/campos do documento.
3. Classificar o resultado por nível de confiança.
4. Se confiança abaixo do limiar: reter para revisão humana antes de publicar.
5. Publicar o resultado final (aprovado automaticamente ou por revisão) para o consumidor.

### Não funcionais (mínimos)
- Persistência de status por documento (recebido → extraído → revisado/aprovado → publicado).
- Log de auditoria mínimo (quem/quando processou, sem exigir plataforma completa de observabilidade ainda).
- Sem SLA de tempo real definido — não inventado aqui.

## 5. Arquitetura recomendada (ciclo 1 — protótipo mínimo)

```
[Cliente] → [API única] → [Storage de objetos] + [Banco relacional único: status/metadados]
                              ↓
                     [Extração (síncrona ou job simples em processo)]
                              ↓
                 confiança baixa? → [fila de revisão humana simples, mesma tabela]
                              ↓
                        [Publicação do resultado]
```

- **Monólito modular**, um único banco relacional, um único bucket de storage.
- Extração pode ser síncrona na requisição ou um job simples em background — **sem fila gerenciada dedicada nem workers separados**, até que volume medido justifique.
- Sem múltiplos perfis de acesso — um único papel operador é suficiente até haver evidência de necessidade de segregação.
- Provedor de OCR/IA encapsulado por um adapter (ADR-003), independentemente da simplicidade do restante.

**Justificativa da simplificação:** nenhuma hipótese de volume fornecida sustenta fila assíncrona e workers escaláveis. Essa arquitetura cobre o mesmo fluxo funcional (ingestão → extração → revisão → publicação) com o menor investimento possível, validando o risco técnico real (qualidade de extração) antes de comprometer infraestrutura distribuída.

## 6. Riscos

| Risco | Natureza | Mitigação nesta proposta |
|---|---|---|
| Qualidade de OCR/extração desconhecida no tipo documental real | Hipótese não testada | Validar com protótipo antes de qualquer expansão de escopo |
| Dependência de provedor externo de OCR/IA sem contrato validado (retenção, localização de dados, uso para treinamento) | Incerteza sinalizada, não invenção | Encapsulamento via adapter (ADR-003); não assumir cláusulas contratuais |
| Ausência de jurisdição definida | Lacuna de informação | Nenhuma arquitetura de retenção/criptografia deve ser fixada em contrato antes da definição jurídica |
| Custo recorrente de revisão humana não dimensionado | Lacuna de informação | Não estimar valor sem dado; medir taxa real de revisão no protótipo antes de comprometer orçamento |
| Erro de associação paciente-documento | Risco de produto | ADR-002 (identificador externo obrigatório) |
| Sobre-investimento em desenho de produto completo antes de validar o problema central | Risco de processo | Este documento propõe explicitamente adiar fila, múltiplos perfis e fases de rollout |

## 7. Critérios de aceite (ciclo 1)

- [ ] Um documento real (ou sintético representativo do tipo documental alvo) é processado de ponta a ponta: ingestão → extração → decisão de confiança → publicação ou retenção para revisão.
- [ ] Resultado de baixa confiança nunca é publicado automaticamente (ADR-001 verificável em teste).
- [ ] Documento não pode ser publicado sem identificador de paciente explícito (ADR-002 verificável em teste).
- [ ] Provedor de OCR/IA é acessado exclusivamente via camada de abstração, nunca diretamente pelo núcleo do serviço (ADR-003 verificável por inspeção de código).
- [ ] Status de cada documento é rastreável em log de auditoria mínimo.

## 8. Decisões pendentes

Estas são bloqueadoras reais para qualquer evolução além do protótipo — nenhuma foi resolvida em nenhum ciclo:

1. **Tipo(s) documental(is)** que o serviço deve suportar primeiro.
2. **Volume esperado** (documentos/dia ou /mês) — determina se fila/workers algum dia se justificam.
3. **Consumidor do resultado** — sistema interno, API pública, outro time.
4. **Jurisdição aplicável** — determina requisitos legais de retenção, criptografia e localização de dados (nenhum presumido até aqui).
5. **Orçamento disponível** para provedor externo de OCR/IA e para equipe de revisão humana recorrente.
6. **Disponibilidade e capacidade da equipe de revisão humana** — sem isso, ADR-001 não tem custo operacional estimável.
7. **Necessidade real de múltiplos perfis de acesso** — hoje não sustentada por nenhum requisito de equipe conhecido.

**Recomendação final:** aprovar as decisões de princípio (ADR-001 a ADR-003) e a arquitetura mínima da seção 5 como ponto de partida. Tratar as 7 decisões pendentes acima como pré-requisito para qualquer expansão de escopo (fila, múltiplos perfis, fases de rollout) — não como detalhes a resolver depois da infraestrutura já estar comprometida.
