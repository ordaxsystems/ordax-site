# OrdaX Site

Repositório de **apresentação pública** do OrdaX. Independente dos builds do kernel, USB, Surface Web, Creator e Identity.

> **Migração em andamento — draft.** A implementação atual no `ordax-os` continua vigente até a prova de cutover. Este repositório **não** publica em produção e não modifica domínios ou segredos.

## O que pertence ao Site

- `site/` — HTML/CSS/JavaScript estático, landing, downloads, login/cadastro/recuperação, UI de Conta, páginas legais, playground read-only e locales `pt-BR`/`en-US`.
- `scripts/` — build de candidato, integridade de bundle, catálogos públicos autorizados.
- `tests/` — regressões de contratos do site e localização.
- `scripts/smoke_static.py` — smoke estático do candidato para as 11 rotas (assets, metadata, formulários fail-closed e catálogo vazio).
- `.github/workflows/site-source.yml` — CI isolado, **sem publicação**.
- `docs/` — auditoria, decisões, proveniência e handoff.

Não contém backend próprio, OAuth, identidade, pagamentos, entitlements, banco, releases OS ou Surface compilável.

## Desenvolvimento

```sh
python3 scripts/build.py check
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_localization.mjs
```

`check` é inspeção de fontes; **não é um pacote pronto para publicação**.

## Build de candidato

O bundle já inclui **todos os arquivos originais do portal**, com os seis binários de imagem preservando seus Git SHAs. O CI usa o snapshot auditado de marca `artifacts/brand/os-migration-70b0f7eb` e gera o candidato estático sem compilar a Surface nem montar o produto Web. Este snapshot de migração **não** é ainda uma publicação oficial da Surface:

```sh
python3 scripts/build.py build \
  --source-commit <SHA40_DO_SITE> \
  --migration-lock contracts/migration-artifact-lock.json \
  --public-origin https://ordax.com.br \
  --out out/site
python3 scripts/build.py verify --out out/site
python3 scripts/smoke_static.py --out out/site
python3 scripts/browser_smoke.py --out out/site --evidence out/browser-evidence
```

O diretório `brand-dir` deve conter `manifest.json` com `artifact_class=ordax-brand`, `source_commit` e registros `path,size,sha256` para os recursos públicos oficiais. O site jamais recompila a Surface. O `offers-dir` contém **apenas HTML derivado para apresentação**, com manifesto SHA-256, fonte pinada, contratação e alocação de cotas desativadas. Nenhum contrato de entitlements foi copiado; ambos snapshots de migração exigem futura substituição por publicação oficial.

O catálogo público de downloads **permanece vazio**. O builder **rejeita** qualquer `--publications` local: campos declaratórios como `public_authorized=true` não são prova criptográfica da publicação pelo owner. Esse gate somente pode ser aberto depois de integração com um pacote oficial atestado, revisionado e pinado. Formulários e Conta dependem de gateway `same-origin`; recuperação/billing não são habilitados por UI.

## Próximos passos e estado preciso

Consultar [Auditoria](docs/AUDIT.md), [Decisões](docs/DECISIONS.md) e [Handoff](docs/HANDOFF.md). As transferências PNG e o build independente com integridade foram comprovados no [CI](https://github.com/ordaxsystems/ordax-site/actions/runs/40039062149). Permanecem pendentes a publicação **oficial** de marca/demonstração e ofertas pelos owners, comparação visual/acessibilidade/SEO em staging e a integração/cutover atômicos no `ordax-os`. O [CI mais recente](https://github.com/ordaxsystems/ordax-site/actions/runs/40039633625) confirma a apresentação de referência em quatro planos, sem habilitar billing. Nada disso é autorização para deploy.


## Site SSOT, SEO e prova real de browser

`contracts/site-routes.json` é o inventário único de rotas e indexação consumido por builder, testes de localização e Chrome. O domínio canônico **não** pertence a esse contrato: a origem HTTPS é injetada pelo owner de deployment por `--public-origin` (no CI candidato: `https://ordax.com.br`). O build gera canonical/OpenGraph, `robots.txt` e `sitemap.xml` apenas no artefato; Conta/Identity/entrada Web têm `noindex`.

A landing lê **um** `/assets/playground-fixture.json` de mesma origem, com falha indisponível explícita. Foi removida a segunda fixture embutida na landing (~159 KB), sem copiar fonte executável da Surface. O controlador mantém um único landmark `main` para acessibilidade.

CI de candidato: `python3 scripts/browser_smoke.py --out out/site --evidence out/browser-evidence` usa ChromeDriver pré-instalado, exercita 11 rotas em 1440, 390 e 320 px, guarda capturas e relatório e mantém APIs de autenticação indisponíveis em loopback. A execução [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40041263365) não substitui uma auditoria WCAG completa ou auth E2E em staging.

Os snapshots de marca/ofertas continuam sendo **apenas materiais de migração verificados**, não autorizações de publicação ou SSOT substitutos.


## Navegação de teclado e internacionalização verificada

O CI exercita o **skip link via Tab+Enter**, leitura de nomes pela Accessibility Tree nativa do Chrome, `alt` em imagens visíveis e troca de idioma pelo seletor real com persistência. O `main#conteudo` deve ter `tabindex="-1"` para permitir foco programático; a Conta usa um handler específico que move o foco diretamente. [Browser CI teclado/a11y PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042024846) e [seletor de idioma E2E PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042154013). A prova não cobre integralmente WCAG, compatibilidade com leitores de tela nem identidade em staging.

## Contrato do pacote público Surface — sem espelho

O source editável do Site **não contém** `surface-snapshot.css`, `playground-fixture.json` ou a cópia redundante `surface-snapshot.json`. Os dois arquivos necessários à demo são materializados exclusivamente do pacote externo `artifacts/surface-preview/os-migration-70b0f7eb` por `scripts/build.py`, que exige **SHA-256 fixo do manifesto** e valida SHA-256, SHA Git, tamanho e coerência entre fixture e CSS. O objeto `surface` já existe dentro da fixture; o JSON independente anterior era idêntico e foi eliminado.

O CSS original do artefato de migração referia-se a uma fonte com hash do antigo bundler não distribuída. A etapa de build troca **somente no output** esse URL pelo recurso Inter existente no brand verificado e usa fingerprint dos bytes realmente publicados no CSS. Não regrava artefato de origem nem duplica a fonte no bundle.

O pacote da Surface **não está publicado oficialmente**: o status explicitamente aceito pelo builder é `audited-migration-snapshot-not-official-surface-publication`, com origem `ordax-os@70b0f7eb`. A evolução para release assinada/atestada do owner exige aprovação e novo gate de proveniência; não basta o manifesto autoafirmar `official`. Solicitado em [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3). Este modelo não transfere ownership de DNS, Web, OS, Account, entitlements, downloads ou deploy.

## Manifestos pinados e lock único de desenvolvimento

`contracts/migration-artifact-lock.json` é a **única fonte de hashes de confiança** dos três insumos temporários de migração (`brand`, `surface_preview`, `offers`). O CI usa `--migration-lock`; o builder recusa overrides de `--brand-dir`, `--surface-preview-dir` ou `--offers-dir` quando recebe esse lock, verifica sha256 do manifesto **antes** de aceitar qualquer declaração interna de identidade, formato, integridade ou status e confirma uma mesma revisão do `ordax-os`. Os manifestos de marca e ofertas agora obedecem à mesma regra da demo.

O lock tem status `development-only-not-authorized-for-production`: **não é assinatura, attestation externa nem autorização para usar artefatos de migração em produção**. As releases oficiais dos owners terão contrato e política de confiança independentes. O Site permanece candidato não publicado.
