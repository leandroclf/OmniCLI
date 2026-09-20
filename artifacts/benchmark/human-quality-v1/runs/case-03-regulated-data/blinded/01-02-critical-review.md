# Revisão crítica da proposta

## 1. Fatos fornecidos

O único fato disponível é:

> Criar um serviço que processa documentos de saúde de pacientes.

Não foram definidos:

- tipo de documento;
- usuário ou cliente pagante;
- finalidade do processamento;
- grau de automação;
- volume esperado;
- país ou ambiente regulatório;
- necessidade de integração;
- impacto do resultado no atendimento ao paciente.

A proposta, portanto, ainda descreve um tema de produto, não um requisito implementável.

## 2. Premissas frágeis

### “Processar” é tratado como uma capacidade única

A proposta anterior lista OCR, classificação, extração estruturada, normalização, armazenamento, integração e workflow como funcionalidades candidatas. Essas capacidades atendem problemas diferentes e possuem riscos distintos.

Por exemplo:

- converter uma imagem em texto não é o mesmo que interpretar um resultado clínico;
- classificar um documento não é o mesmo que gerar dados para um prontuário;
- armazenar documentos não exige necessariamente extração semântica;
- exportar dados estruturados pode exigir validações e integrações que não são necessárias para uma solução de indexação.

**Correção:** definir uma operação principal para o MVP, com entrada, saída e usuário claramente especificados.

### Automação pode ser confundida com confiabilidade clínica

A extração automática de nomes, datas, medicamentos ou resultados pode produzir dados aparentemente plausíveis, mas incorretos. Em saúde, um erro silencioso pode ser mais perigoso do que uma falha explícita.

A ideia não esclarece se o resultado será:

- apenas auxiliar para busca;
- usado por um profissional para conferência;
- incorporado automaticamente a um sistema clínico;
- usado para decisões de atendimento, autorização ou cobrança.

**Correção:** classificar o impacto de cada campo extraído e estabelecer revisão humana obrigatória para resultados de maior risco. A confiança da ferramenta não deve, sozinha, autorizar uso clínico automático.

### Conformidade aparece como item posterior, embora seja requisito inicial

A proposta anterior trata segurança, retenção, controle de acesso e requisitos regulatórios como riscos a considerar. Para documentos de saúde, esses aspectos condicionam o desenho do produto desde o início.

Ainda não é possível afirmar quais obrigações específicas se aplicam sem conhecer jurisdição, papéis das organizações, finalidade do tratamento e fluxo de dados. A menção genérica à LGPD também não substitui uma avaliação jurídica e de privacidade.

**Correção:** validar previamente, com responsáveis jurídicos e de segurança, pelo menos:

- quem controla e quem processa os dados;
- finalidade e base autorizativa do tratamento;
- minimização de dados;
- retenção e descarte;
- acesso por função e segregação entre organizações;
- auditoria;
- resposta a incidentes;
- uso ou não dos documentos para treinamento de modelos;
- transferência para serviços externos.

### “API” e “integração” podem ampliar excessivamente o primeiro escopo

A possibilidade de oferecer uma API, integração com prontuário eletrônico ou conversão para padrões de interoperabilidade não implica que isso deva fazer parte do primeiro produto.

Cada integração adiciona contratos, autenticação, suporte a falhas, versionamento e responsabilidade operacional. Um formato estruturado interno pode ser suficiente para validar o problema inicialmente.

**Correção:** escolher uma única fronteira inicial, por exemplo:

> receber PDF ou imagem, extrair texto e metadados básicos, permitir conferência humana e disponibilizar o resultado para download.

Qualquer integração externa deve ser considerada uma etapa posterior, salvo se for indispensável ao problema original.

## 3. Riscos prioritários

### Risco de escopo indefinido

“Documentos de saúde” pode incluir receitas, laudos, exames laboratoriais, imagens, prontuários, guias, autorizações e documentos administrativos. Esses formatos têm layouts, vocabulários, níveis de sensibilidade e critérios de qualidade diferentes.

**Mitigação:** começar com um único tipo de documento e uma pequena amostra real, devidamente autorizada e protegida.

### Risco de dados inadequados para validação

Não foi informado se existem documentos reais, anonimizados ou sintéticos para testar a solução. Sem uma amostra representativa, a avaliação de qualidade será especulativa.

**Mitigação:** definir antes:

- conjunto de documentos de referência;
- variação de qualidade, idioma, manuscrito e layout;
- campos esperados;
- taxa mínima aceitável de erro;
- método de comparação com a verdade de referência.

### Risco de erro de identidade

Associar um documento ao paciente errado é potencialmente mais grave do que não extrair um campo. O fluxo não explica como a identidade será confirmada nem se o serviço receberá identificadores diretamente.

**Mitigação:** evitar inferir identidade a partir do conteúdo do documento. Exigir identificador fornecido por um sistema autorizado, aplicar validações e registrar a origem da associação.

### Risco de exposição e retenção excessiva

Uploads, textos extraídos, logs, filas, arquivos temporários e cópias de suporte podem multiplicar os locais onde dados sensíveis ficam armazenados.

**Mitigação:** elaborar um inventário de dados antes da implementação, definir retenção por artefato e proibir dados clínicos desnecessários em logs, métricas e mensagens de erro.

### Risco de desempenho e custo operacional

OCR e processamento de documentos podem ser demorados ou consumir recursos variáveis, especialmente com PDFs grandes, imagens de alta resolução ou lotes. O requisito ainda não informa se a resposta precisa ser síncrona ou assíncrona.

**Mitigação:** escolher explicitamente o modo de processamento e impor limites de tamanho, páginas, formato e tempo. Não prometer tempo de resposta ou custo antes de medir uma amostra representativa.

### Risco de responsabilidade indefinida

Não está claro quem revisa erros, quem corrige os dados, quem autoriza a publicação do resultado e quem responde por um documento processado incorretamente.

**Mitigação:** definir papéis operacionais e estados do documento, como `recebido`, `processando`, `requer revisão`, `aprovado`, `rejeitado` e `eliminado`.

## 4. Decisões que exigem validação humana

Estas decisões não devem ser inferidas pela equipe técnica:

1. O serviço fará apenas conversão/indexação ou também interpretação clínica?
2. Qual é o primeiro tipo de documento suportado?
3. O resultado poderá alimentar sistemas clínicos automaticamente?
4. Quais campos exigem revisão humana?
5. Quais organizações terão acesso aos dados?
6. Qual jurisdição e quais requisitos de privacidade se aplicam?
7. Os documentos poderão ser enviados a provedores externos de OCR ou IA?
8. Qual é a política de retenção e descarte?
9. Qual erro é aceitável para cada tipo de campo?
10. Qual volume e prazo de processamento são necessários?
11. Existem documentos reais autorizados para validação?
12. Qual é o critério para considerar o MVP bem-sucedido?

## 5. Recomendações objetivas

### Reescrever a proposta em formato verificável

Uma formulação mínima poderia ser:

> “Permitir que [usuário definido] envie [tipo específico de documento] em [formatos], para obter [resultado limitado], com [revisão ou validação definida], em até [prazo], sem publicação automática em sistemas clínicos.”

Os trechos entre colchetes precisam ser decididos pelo responsável pelo produto.

### Reduzir o MVP

O MVP deveria conter, no máximo:

- ingestão de um tipo de documento;
- validação de formato e tamanho;
- processamento definido;
- resultado limitado a campos previamente escolhidos;
- indicação explícita de campos ausentes ou incertos;
- revisão humana;
- controle de acesso e auditoria mínimos;
- política de retenção definida.

OCR, classificação ampla, normalização clínica, FHIR, múltiplas integrações e automação completa devem permanecer fora do MVP até haver justificativa concreta.

### Separar processamento documental de decisão clínica

O serviço deve declarar se produz:

- texto transcrito;
- metadados;
- dados estruturados;
- uma interpretação;
- uma recomendação.

Essas categorias não são equivalentes. Se o produto ultrapassar transcrição e organização documental, a validação de segurança e responsabilidade deverá ser significativamente mais rigorosa.

### Definir critérios de aceitação antes da escolha da tecnologia

Não escolher fornecedor, modelo ou arquitetura antes de responder:

- quais campos precisam ser extraídos;
- qual taxa de acerto é necessária;
- como erros serão detectados;
- quais documentos ficam fora do suporte;
- qual é o comportamento quando a confiança é baixa.

## 6. Conclusão

A ideia é válida como direção de investigação, mas está ampla demais para iniciar implementação. O maior risco não é técnico: é construir uma solução de extração ou integração sem confirmar qual problema deve ser resolvido e qual consequência um erro pode causar.

O próximo passo recomendado é uma decisão de escopo, não uma decisão de tecnologia. O responsável pelo produto deve escolher um tipo de documento, um usuário, uma finalidade e um resultado limitado. Só então será possível avaliar arquitetura, fornecedores, métricas, segurança e esforço com alguma confiabilidade.
