# Handoff operacional — SITE-001

**Branch Site:** `feat/site-independent-extraction`  
**Repo:** `ordaxsystems/ordax-site`  
**Origem observada:** `ordax-os/main@70b0f7eb5d5085be0d4f176f5232def37c7a2a24`  
**Status:** BUILD INDEPENDENTE CANDIDATO APROVADO / DRAFT; **sem autorização de produção e sem cutover OS**.

## Concluído
- Repositório `ordax-site` iniciado com `main` sem publicação.
- Conteúdo textual da apresentação, rotas públicas e i18n transferido de origem para `site/`.
- Quatro imagens JPEG e dois PNGs transferidos preservando os Git SHAs originais (CI de migração de binários [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40038857924)).
- Gerador de catálogo autorizado e render de HTML reutilizados como módulos isolados.
- Builder independente candidato implementado sem dependências de kernel/OS, com catálogo vazio por padrão e brand externo obrigatório.
- Snapshot de marca pinado em `artifacts/brand/os-migration-70b0f7eb`, com SHA-256 e proveniência OS (workflow de migração [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40038988099)); nenhum runtime da Surface copiado.
- CI de build estático autônomo/verify, testes e upload de candidato não-produção [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40039062149); sem domínio/credenciais/deploy.
- Auditoria adicional das 11 rotas compiladas, arquivos locais, metadados básicos, formulários nativos desabilitados e release catalog vazio por padrão, [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40039330301). Isso **não** equivale a auditoria WCAG e screenshot de navegador.
- Catálogo comercial de referência preservado como **projeção HTML de migração**, sem contrato OS duplicado: `artifacts/offers/os-migration-70b0f7eb/` (manifesto SHA-256, explicitamente não comprável); renderizado na landing e Conta. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40039633625).
- PR documental [ordax-os#2196](https://github.com/ordaxsystems/ordax-os/pull/2196) criada em draft, sem repoint nem mudanças de runtime. O OS antigo continua vigente.
- PR Site [#1](https://github.com/ordaxsystems/ordax-site/pull/1) aberta em draft.

## Bloqueios imediatos (ordem)
1. Publicar pacote oficial de brand no owner Surface com proveniência/revisão e substituir o snapshot de migração por referência a esse artefato, sem depender de checkout OS.
2. Publicar snapshot Meridian/fixture como artefato read-only compatível pelo owner Surface; não manter gerador no Site.
3. **PARCIAL** — projeção read-only de referência/restauração de UI concluída no snapshot de migração; falta publicar sua versão oficial no owner de entitlements e substituir a dependência do snapshot. Nenhuma contratação pode ser habilitada.
4. Rodar smoke real de browser, a11y, SEO/responsividade, login/recovery fail-closed e paridade visual em staging.
5. PR **futura de repoint/cutover** no OS distinta da documental #2196; revalidar a `main`, reconciliar Surface #2195 e remover duplicação só após prova de igualdade e CI dos consumidores.

## Recomendações operacionais
- Começar por `python3 scripts/build.py check` e `node tests/test_localization.mjs`.
- `python3 scripts/build.py build --source-commit <sha40> --brand-dir artifacts/brand/os-migration-70b0f7eb --offers-dir artifacts/offers/os-migration-70b0f7eb` **gera pacote candidato**, recusando imagens ausentes e artifacts com hashes inválidos.
- Jamais transformar candidato CI em autorização de produção: ainda exige os artefatos oficiais de marca/planos/demonstração e E2E de staging.
- Revalidar `ordax-os/main` e PRs concorrentes antes de qualquer alteração compartilhada.
- Atualizar este arquivo após cada PR/CI/gate concluído; SSOT do projeto são seus códigos/contratos externos, não este handoff.


## Execução adicional (2026-10-23)
- `site/assets/playground.js` agora consome uma única fixture JSON de mesma origem com verificação de schema/limite de tamanho; removidos **159.242 bytes** de duplicação inline no `site/index.html`. O componente visual não duplica o landmark `main` da landing.
- `scripts/browser_smoke.py` exerce `11 × 3 = 33` cenários no Chrome, captura telas e verifica viewport, navegação, IDs, nomes acessíveis, recursos externos e estados fail-closed de login/cadastro/recovery. [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40040885269).
- `contracts/site-routes.json` é novo SSOT de páginas e política de indexação. `scripts/site_seo.py` gera canonical/OpenGraph, `robots.txt` e `sitemap.xml` com origem fornecida por deployment. CINCO páginas informativas indexáveis; as SEIS rotas autenticadas ou não habilitadas possuem noindex. [CI final da fase SEO PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40041263365).
- O Site deixou aviso de compatibilidade na [ordax-os#2198](https://github.com/ordaxsystems/ordax-os/pull/2198) sobre snapshots antigos após remoção da fonte visual.
- As verificações de nomes/overflow no Chrome são boas provas iniciais, mas **não** há auditoria WCAG com contraste, navegação por leitor de tela ou E2E do gateway autenticado em staging. Não declarar esses gates PASS por inferência.
- Continua sem permissão de deploy em produção. `ordax-site#1` permanece draft e `ordax-os#2196` é documentação, não repoint.
