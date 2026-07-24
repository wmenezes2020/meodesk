---
name: prd-update
description: Atualiza obrigatoriamente o PRD na mesma entrega de qualquer mudança funcional.
---

# Atualização obrigatória do PRD

Toda feature, correção relevante, refatoração comportamental, endpoint, tela, schema, job,
integração ou regra de negócio deve atualizar o PRD na mesma entrega.

## Fonte da verdade

- Use `PRD.md` na raiz como visão consolidada.
- Atualize também o PRD detalhado em `docs/prd/` quando a mudança afetar seu domínio.
- Não crie fontes concorrentes ou divergentes.

## Checklist

1. Descrever o comportamento atual da funcionalidade.
2. Registrar fluxos, dados, contratos e integrações relevantes.
3. Revisar não-objetivos para evitar conflito de escopo.
4. Adicionar uma entrada datada no changelog.
5. Incluir PRD, implementação, testes e REPORT na mesma entrega.
6. Citar os documentos atualizados no corpo do pull request.

Uma entrega com comportamento alterado e PRD desatualizado não está concluída.
