# Handoff operacional — SITE-001

**Branch Site:** `feat/site-independent-extraction`  
**Repo:** `ordaxsystems/ordax-site`  
**Origem observada:** `ordax-os/main@70b0f7eb5d5085be0d4f176f5232def37c7a2a24`  
**Status:** EXTRAÇÃO PARCIAL / DRAFT; **sem autorização de produção**.

## Concluído
- Repositório `ordax-site` iniciado com `main` sem publicação.
- Conteúdo textual da apresentação, rotas públicas e i18n transferido de origem para `site/`.
- Quatro imagens JPEG transferidas preservando SHA Git.
- Gerador de catálogo autorizado e render de HTML reutilizados como módulos isolados.
- Builder independente candidato implementado sem dependências de kernel/OS, com catálogo vazio por padrão e brand externo obrigatório.
- Estrutura de testes, CI source-only e políticas locais criada na branch.

## Bloqueios imediatos (ordem)
1. Transferir duas imagens PNG > 1MiB com mecanismo de Git do executor autorizado e confirmar blobs; ferramentas de fetch textual não retornaram bytes destes dois blobs.
2. Definir contrato/versionamento e publicação de `ordax-brand` (tokens, fontes, artwork), assinaturas/hashes, sem import da Surface.
3. Publicar snapshot Meridian (HTML/CSS/fixture) como artefato read-only compatível, removendo a dependência do gerador antigo no OS.
4. Projetar catálogo de preços como artefato de leitura derivado do owner de entitlements, sem cópia do contrato.
5. Verificar regressões de UI, navegação, downloads e Conta em staging.
6. Abrir PR independente no OS de repoint do site/build/deploy, somente depois de green. Reconciliar Surface #2195 e outras PRs antes de merge.

## Recomendações operacionais
- Começar por `python3 scripts/build.py check` e `node tests/test_localization.mjs`.
- `python3 scripts/build.py build --source-commit <sha40> --brand-dir <dir>` **deve recusar** imagens ausentes e brand sem manifesto pinado.
- Jamais transformar build check em aprovação de produção: source-only não equivale a pacote candidato verificado.
- Revalidar `ordax-os/main` e PRs concorrentes antes de qualquer alteração compartilhada.
- Atualizar este arquivo após cada PR/CI/gate concluído; SSOT do projeto são seus códigos/contratos externos, não este handoff.
