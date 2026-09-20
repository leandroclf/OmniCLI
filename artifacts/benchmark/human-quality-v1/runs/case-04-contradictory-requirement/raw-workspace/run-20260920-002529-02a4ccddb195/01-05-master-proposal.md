# Proposta Mestra de Arquitetura

## 1. Escopo

Definir uma arquitetura de dados/sistema que atenda três objetivos declarados na ideia original: consistência forte global, custo mínimo, disponibilidade offline total.

**Fato fornecido:** nenhum domínio, escala, orçamento, equipe ou prazo foi informado em nenhuma etapa deste ciclo.

**Correção explícita a uma premissa frágia:** os três objetivos, tomados ao pé da letra e aplicados ao mesmo dado ao mesmo tempo, são mutuamente incompatíveis (CAP/PACELC). Isso não é uma opinião de design — é uma restrição teórica. A proposta abaixo só é viável porque segmenta o sistema por criticidade de dado, não porque encontrou uma forma de contornar CAP.

## 2. Premissas

| # | Premissa | Status |
|---|---|---|
| P1 | CAP se aplica: não existe consistência forte + disponibilidade (incluindo offline) simultâneas para o mesmo dado durante partição | Fato (teoria de sistemas distribuídos, não específico deste projeto) |
| P2 | A maioria dos dados de um sistema real não exige consistência forte global | Hipótese, mas amplamente observada na indústria — precisa ser validada para este caso específico |
| P3 | Escritores concorrentes por entidade, em uso realista, tendem a ser poucos (frequentemente 1) | Hipótese não verificada — **decisão pendente crítica**, ver seção 8 |
| P4 | "Custo mínimo" é relativo, não um valor absoluto | Inferência a partir da ausência de orçamento declarado |

## 3. Decisões preservadas do ciclo anterior

- Segmentar dados por criticidade (globalmente críticos vs. locais/sincronizáveis) em vez de aplicar consistência forte a tudo — **mantida**, é a única forma de conciliar os três objetivos parcialmente.
- Descartar multi-região complexa como padrão — **mantida**, correta para custo mínimo.
- Contratos ilustrativos (`Operation`, `Applied/Conflict/Rejected`) tratados como exemplo, não como tecnologia real — **mantida**, evita alegar integração inexistente.

## 4. Correção explícita de inconsistência

O desenho de referência do ciclo anterior (14 seções, 7 fases, 8 componentes: log de operações, outbox, motor de sincronização, serviço de reconciliação, serviço de resolução de conflitos, autoridade global, observabilidade completa desde o protótipo) **não é compatível com "custo mínimo"** enquanto não houver confirmação de que o volume de escritores concorrentes e o volume de dados críticos justificam essa complexidade. Adotar esse desenho como está seria contradizer o próprio objetivo que a ideia original pede. Esta proposta usa como arquitetura de partida a versão mínima, com caminho de expansão explícito — não o inverso.

## 5. Requisitos

### 5.1 Funcionais
- R1: Dados classificados como críticos (ex.: autenticação, permissões, licenciamento) devem ter consistência forte via transação serializável em autoridade única.
- R2: Dados classificados como locais/sincronizáveis devem funcionar 100% offline por dispositivo.
- R3: Sincronização de dados locais para o backend deve ocorrer de forma assíncrona, sem bloquear o uso offline.
- R4: Conflitos de escrita devem ser detectáveis (via revisão/versão monotônica), mesmo que a resolução inicial seja manual.

### 5.2 Não funcionais
- N1: Custo de infraestrutura mínimo viável — preferir componentes gerenciados existentes a serviços novos construídos do zero.
- N2: Nenhuma dependência de rede para operações offline (R2).
- N3: Autoridade central pode ser um único banco relacional, não um serviço distribuído dedicado, salvo comprovação de necessidade.

## 6. Arquitetura proposta (versão mínima, ponto de partida)

```
[Dispositivo/Cliente]
  └── Banco local embutido (ex.: SQLite) com coluna de revisão por registro
        │  (offline-first: toda leitura/escrita local não bloqueia em rede)
        ▼
  Fila de sincronização assíncrona
        │
        ▼
[Backend]
  └── Tabela de log de eventos com chave de idempotência (sem serviço separado)
        │
        ▼
  Autoridade única para dados críticos
  (1 banco relacional com transações serializáveis — não um serviço novo)
  └── Autenticação/permissões delegadas a provedor de identidade existente,
      se houver um (ver decisão pendente #3)
```

**Recomendação (não fato):** tratar isto como teto mínimo de complexidade. Evoluir para CRDTs, merge automático e serviço de reconciliação dedicado apenas se dados reais de um piloto mostrarem taxa de conflito ou volume que justifiquem o custo adicional.

Nenhum banco, fila ou provedor de identidade específico é indicado como definitivo — nomes acima (ex. SQLite) são ilustrativos de categoria de solução, não uma escolha de fornecedor validada para este projeto. Qualquer biblioteca de sincronização/CRDT de terceiros deve ser avaliada quanto a licença, maturidade e suporte antes de entrar em plano — não assumir que resolve merge automático para o domínio sem checagem.

## 7. Riscos

| Risco | Natureza | Observação |
|---|---|---|
| Taxa de conflito real desconhecida | Bloqueador de validação | Sem isso, "custo mínimo" não é uma afirmação verificável |
| Log de eventos sem política de expurgo | Operacional | Cresce indefinidamente; definir retenção antes de produção |
| Fila de conflitos com intervenção manual | Custo operacional recorrente | Historicamente a maior fonte de custo de suporte humano em sistemas offline-first |
| Escolha futura de "sync engine" ou CRDT pronto sem validação de licença/maturidade | Técnico/legal | Sinalizado, não avaliado nesta etapa por falta de escolha concreta de ferramenta |
| Ausência de orçamento e prazo | Planejamento | Impede comparar alternativas em termos de custo real, apenas qualitativo |

## 8. Critérios de aceite

- CA1: Dados críticos passam em teste de consistência forte (leitura após escrita, mesma sessão e sessões concorrentes) sob transação serializável.
- CA2: Cliente opera sem rede por tempo indeterminado para dados locais/sincronizáveis, sem erro ou bloqueio.
- CA3: Ao reconectar, sincronização ocorre sem perda de dados; conflitos são detectados (não necessariamente resolvidos automaticamente) e reportados.
- CA4: Nenhum serviço novo é introduzido para autoridade central ou reconciliação antes que dados de um piloto comprovem necessidade (ligado à decisão pendente #1).

## 9. Decisões pendentes (bloqueiam início da Fase 1)

1. **Escritores concorrentes reais por entidade, em 99% dos casos de uso.** Se a resposta for 1, a resolução automática de conflitos (CRDT, merge, reconciliação) deve ser cortada do escopo inicial.
2. **Orçamento e prazo definidos**, ou "custo mínimo" permanece apenas uma preferência relativa sem meta mensurável?
3. **Existe provedor de identidade/autorização já em uso** (ex. um IdP corporativo), ou isso será construído do zero? Impacto direto em custo e prazo — nenhuma suposição foi feita aqui.
4. **Taxa de conflito aceitável para intervenção manual** — necessária para validar, com dados reais, se "custo mínimo" foi atingido.
5. **Domínio e escala do sistema** (número de dispositivos, volume de dados críticos) — sem isso, qualquer dimensionamento é qualitativo, não quantitativo.

**Recomendação final:** não iniciar implementação antes de responder aos itens 1–5. A arquitetura da seção 6 é o ponto de partida seguro e barato; expandir apenas mediante evidência de necessidade real, nunca por antecipação.
