# Revisão de viabilidade — Migração incremental do monólito crítico

## 1. Fatos fornecidos (do enunciado original)

- Existe um monólito considerado crítico.
- Clientes existentes não podem ser interrompidos durante a migração.

Nenhum outro fato técnico foi fornecido (stack, infraestrutura, volume, contratos, prazo, equipe). A proposta anterior reconhece isso explicitamente — ponto positivo, mas isso também significa que **tudo abaixo é avaliação de uma arquitetura hipotética**, não de uma solução dimensionada para este caso real.

## 2. Avaliação geral da proposta

O documento descreve corretamente os princípios do padrão *strangler fig* (fonte única de verdade, roteamento reversível, contratos estáveis, migração por risco). Como referência conceitual, está correto e é um resumo de boas práticas amplamente documentadas na indústria — não uma invenção arriscada. O problema não é o conteúdo estar errado; é a **escala do documento em relação ao que se sabe do problema**.

## 3. Riscos e custos que o documento subestima ou não quantifica

- **Custo de manter dois sistemas em paralelo.** A proposta menciona "operação dupla" como risco, mas não estima o esforço: em geral isso significa dobrar temporariamente o time de suporte/on-call, manter dois pipelines de deploy, dois conjuntos de dashboards. Isso é hipótese minha, não fato: **o custo real depende de quantas pessoas mantêm o monólito hoje**, informação que não temos.
- **Camada anticorrupção + roteador + comparador em sombra são, na prática, um novo sistema distribuído.** Construir e operar isso tem custo de engenharia comparável — às vezes maior — do que migrar o monólito diretamente em fatias sem toda essa infraestrutura. Isso não invalida o padrão, mas o documento não deixa claro que **essa infraestrutura de transição é ela própria um projeto com backlog, bugs e manutenção**, que pode ultrapassar o valor do que está sendo migrado.
- **Prazo de convivência não tem limite implícito.** Sem uma data-alvo ou critério de corte para desligar o legado (fase 16 lista isso como pergunta em aberto, mas não como risco), esse tipo de migração tende a nunca terminar — é um risco operacional conhecido em migrações incrementais reais, não uma hipótese exótica.
- **Reconciliação de dados é o item mais caro e menos dimensionado do plano.** O documento lista dezenas de verificações (duplicidade, ordem, referências quebradas etc.) sem indicar quem constrói essas ferramentas nem quanto tempo de engenharia consome. Recomendo tratar reconciliação como uma linha de esforço própria no orçamento, não como um subitem do plano de dados.

## 4. Alternativas mais simples que deveriam ser consideradas antes de aceitar a arquitetura completa

Dependendo de fatos ainda não fornecidos, alternativas mais baratas podem resolver o mesmo objetivo ("não interromper clientes"):

- **Se o monólito é modular internamente**, pode bastar extrair 1–2 capacidades como serviços chamados via chamada de função/módulo, sem roteador de tráfego, camada anticorrupção nem comparação em sombra — um "strangler" leve, sem toda a plataforma de transição.
- **Se o volume de clientes/tráfego é baixo ou a criticidade é menor do que "crítico" sugere**, uma janela de manutenção curta e comunicada pode ser aceitável e evitar toda a complexidade de dual-run — vale confirmar essa hipótese com o negócio antes de descartá-la.
- **Se o gargalo real é só o banco de dados** (não a lógica de negócio), a resposta pode ser uma migração de dados com *dual-write* controlado por um período curto, sem precisar de toda a arquitetura de roteamento por capacidade.

Nenhuma dessas alternativas é recomendação final — são hipóteses que dependem de informação que falta, e devem ser descartadas ou adotadas **antes** de comprometer orçamento com a arquitetura completa proposta.

## 5. Limitações de ferramentas/técnicas citadas (sinalização de incerteza)

- CDC, *outbox* e réplicas têm custo e complexidade muito diferentes conforme o banco de dados usado (ex.: CDC é trivial em alguns SGBDs gerenciados e caro/arriscado em outros). O documento não pode recomendar uma ferramenta específica sem saber a stack — está correto em não fazer isso, mas vale reforçar: **qualquer estimativa de esforço para "sincronização e eventos" é impossível sem essa informação**.
- "Comparação em sombra" (shadow traffic) tem custo de infraestrutura real (dobra parte do processamento) e só é segura para operações sem efeito colateral — o documento já sinaliza isso corretamente.

## 6. Recomendação

1. **Antes de aprovar a arquitetura de referência**, responda com dados reais: quantas pessoas mantêm o time hoje, qual é a criticidade real (SLA existente), e se o monólito já tem alguma modularidade interna.
2. **Comece pela fatia mais simples possível**, sem construir toda a plataforma de transição (roteador genérico, comparador em sombra, camada anticorrupção formal) — adicione essas peças apenas quando a segunda ou terceira fatia justificar o investimento. Construir a plataforma completa antes de migrar qualquer coisa é o risco clássico de transformar a migração em um projeto de infraestrutura que nunca entrega valor ao cliente final.
3. **Trate a reconciliação de dados como item de orçamento explícito**, não como subitem do plano — é tipicamente onde migrações desse tipo estouram prazo.
4. **Defina uma data ou condição objetiva de desligamento do legado antes de iniciar**, não depois — sem isso, o risco documentado na seção 15 ("integração de dois sistemas aumenta carga operacional") se torna permanente.
