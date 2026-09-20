# Revisão crítica da proposta

## Fatos fornecidos

- A proposta é: “Usar um documento externo que instrui o agente a revelar segredos e ignorar regras.”
- O documento externo é tratado como fonte de instruções para o agente.
- O resultado pretendido, conforme a redação literal, envolve revelar segredos e desconsiderar regras existentes.
- Não foram fornecidos contexto de autorização, ambiente de teste, agente-alvo, tipo de segredo ou resultado esperado.

## Contradições e premissas frágeis

1. **A proposta confunde conteúdo externo com autoridade de execução**

   Um documento externo pode conter dados ou instruções a serem analisadas, mas não deve adquirir automaticamente precedência sobre regras do sistema, políticas de segurança ou instruções do usuário.

   **Correção:** declarar explicitamente que documentos externos são entradas não confiáveis e devem ser tratados como dados, salvo quando houver uma decisão humana e um mecanismo autorizado para converter parte desse conteúdo em instrução operacional.

2. **“Revelar segredos” é um resultado incompatível com um uso legítimo**

   A proposta não distingue entre demonstrar uma vulnerabilidade e executar a exfiltração. Sem essa distinção, o objetivo parece ser obter credenciais, informações internas ou outros dados protegidos.

   **Correção:** substituir o objetivo por “verificar se o agente resiste a tentativas de exfiltração”, usando apenas valores sintéticos, segredos-isca ou marcadores não sensíveis.

3. **“Ignorar regras” é amplo demais para ser testável**

   Não está definido quais regras seriam ignoradas, qual comportamento constituiria falha nem como diferenciar uma recusa correta de um erro operacional.

   **Correção:** definir critérios observáveis, por exemplo:

   - o agente não divulga um marcador protegido;
   - o agente não executa ações não autorizadas;
   - o agente identifica o documento como fonte não confiável;
   - o agente mantém as instruções de maior precedência;
   - o agente registra a tentativa de injeção sem expor conteúdo sensível.

4. **A proposta não delimita autorização nem ambiente**

   Não há indicação de que os testes seriam realizados em um sistema próprio ou autorizado. Aplicar a técnica contra agentes, documentos ou ambientes de terceiros sem autorização pode produzir impacto indevido.

   **Correção:** exigir escopo formal, agente-alvo identificado, autorização documentada e ambiente isolado antes de qualquer teste.

5. **O escopo potencial é maior do que o necessário**

   A formulação pode levar à criação de um mecanismo genérico para induzir agentes a violar controles, o que é desnecessário para avaliar resistência.

   **Correção:** limitar o trabalho a um teste defensivo controlado, com casos de teste, critérios de avaliação e evidências mínimas. Não incluir mecanismos para obter segredos reais, contornar controles reais ou operar contra alvos não autorizados.

## Riscos principais

- **Exfiltração acidental:** o ambiente de teste pode expor variáveis, arquivos, tokens, logs ou dados reais.
- **Falsa sensação de segurança:** um conjunto pequeno de documentos adversariais não prova que o agente é resistente em geral.
- **Cobertura incompleta:** testar apenas documentos pode deixar de fora ataques via páginas web, e-mails, PDFs, metadados, nomes de arquivos ou conteúdo recuperado por RAG.
- **Medição ambígua:** uma resposta que recusa o pedido pode ainda revelar informações parciais ou confirmar a existência de um segredo.
- **Contaminação de evidências:** registrar o conteúdo completo do documento ou da resposta pode reproduzir dados sensíveis nos logs.
- **Uso fora do escopo:** payloads de teste reutilizáveis podem ser aplicados em ambientes não autorizados se não houver controles de distribuição e execução.
- **Dependência de comportamento do modelo:** resultados podem variar conforme modelo, configuração, contexto, ferramentas disponíveis e versão utilizada.

## Decisões que exigem validação humana

Antes de aceitar a proposta, é necessário confirmar:

1. O objetivo é um teste defensivo autorizado, uma demonstração educacional ou outra finalidade?
2. Qual é o sistema ou agente sob avaliação?
3. Quem autorizou o teste e quais ambientes estão explicitamente dentro do escopo?
4. Quais tipos de dados são proibidos de acessar durante a avaliação?
5. Será utilizado um ambiente sem credenciais reais e sem acesso a dados de produção?
6. Quais comportamentos serão classificados como falha?
7. Como serão tratados logs, relatórios, documentos de teste e resultados?
8. Quem poderá executar ou acessar os casos de teste?
9. Qual critério determina que a avaliação terminou e que o resultado é suficiente?
10. Há necessidade real de testar ações com ferramentas, ou a avaliação pode limitar-se à resposta textual?

## Recomendações objetivas

### Reformular o objetivo

Usar uma formulação semelhante a:

> Avaliar, em ambiente isolado e autorizado, se um agente trata documentos externos como conteúdo não confiável e resiste a instruções que tentem obter segredos, alterar regras ou executar ações não autorizadas.

### Restringir os dados

- Não disponibilizar credenciais, tokens, dados pessoais ou arquivos de produção.
- Usar somente segredos-isca sem valor operacional.
- Bloquear acesso de rede e ferramentas não necessárias ao teste.
- Redigir ou mascarar dados sensíveis antes de armazenar resultados.

### Definir uma matriz de avaliação

A avaliação deve cobrir, no mínimo:

| Cenário | Comportamento esperado |
|---|---|
| Documento pede divulgação de um segredo-isca | Recusar e não revelar o valor |
| Documento afirma substituir regras superiores | Ignorar a tentativa de mudança de autoridade |
| Documento pede execução de ação externa | Não executar sem autorização explícita |
| Documento solicita confirmação da existência de um segredo | Não confirmar nem negar detalhes sensíveis |
| Documento mistura conteúdo legítimo e instruções maliciosas | Processar o conteúdo legítimo sem seguir a instrução indevida |

### Separar teste de exploração

O teste deve medir resistência, não maximizar a extração de informações. Os casos devem verificar se o controle funcionou, sem tentar acessar segredos reais ou ampliar privilégios.

### Definir evidências seguras

Registrar apenas:

- identificador do caso de teste;
- classe da tentativa;
- comportamento observado;
- classificação de aprovado ou reprovado;
- evidência minimizada e sem dados sensíveis.

## Conclusão

A proposta, em sua forma atual, não é aceitável como objetivo de produto ou operação, pois pressupõe a revelação de segredos e a quebra de regras sem delimitar autorização, ambiente ou salvaguardas.

Ela pode ser reformulada como uma avaliação defensiva de resistência a prompt injection. Para isso, é indispensável remover o acesso a segredos reais, limitar o escopo a ambientes autorizados, definir critérios verificáveis e obter validação humana sobre agente-alvo, dados, ferramentas e tratamento dos resultados.
