# Auditoria de extração — baseline 2026-10-23

## Inventário e proveniência
- Origem: `ordaxsystems/ordax-os`, branch `main`, revisão observada `70b0f7eb5d5085be0d4f176f5232def37c7a2a24`.
- Árvore original da apresentação: `sites/public/`, Git tree `bc516a313eaa78a83652237a6d9d0cdbf295d28b` (36 blobs de arquivo, com 11 rotas HTML).
- Implementação original: `tools/public-site/`, incluindo build, geradores Meridian, validação legal, catálogo público, deploy e smoke.
- Artefato novo: `site/`; todo HTML, JS, CSS e i18n copiado de origem sem reconstrução por IA; PNG/JPEG pequenos copiados preservando **o mesmo blob SHA Git**.
- **Pendência de duas imagens originais**: `site/assets/aurora-titanium.png` (blob `e4574877f57a66574d001ebcfbfc8718782a2c23`, 2016680 bytes) e `site/assets/download-hero.png` (blob `7c23ed6070890d81a11474108f0a52a0965ce501`, 1629858 bytes). Não fabricar alternativas. Transferir os bytes com Git via executor CI autorizado e verificar SHA do blob antes de propor cutover.
- O snapshot `site/assets/surface-snapshot.json` + CSS, `playground-fixture.json` são artefatos **gerados** de demonstração, nunca imports dinâmicos. A procedência original deve permanecer identificável, e atualizações futuras devem consumir artefatos publicados pelo owner da Surface.
- Fonts, símbolo, tokens e wallpaper continuam **fora** do site até serem publicados como artefato de marca versionado; `scripts/build.py` exige manifesto e SHA-256 de cada recurso.

## Dependências e owner correto
| Subsistema | Fonte anterior | Destino/correção |
|---|---|---|
| Landing, páginas produto, legal | `sites/public/` | `ordax-site/site/` |
| UI de Identity | `sites/public/assets/site.js` + `account.css` | apresentação no site; operações **same-origin** no owner remoto |
| Conta (visual) | `account-portal.js` + `account-dashboard.css` | site apenas; sem implementação de sessão/billing |
| Traduções | `sites/public/i18n/` | `site/i18n/`, único dicionário de site |
| Downloads | `platform/releases/publications.json` via gerador | somente catálogo autorizado produzido pelo owner; default vazio |
| Planos/preços | `docs/contracts/entitlements.json` via `plan_catalog.py` | **não** copiar contrato; aguarda publicação de projeção verificável; aquisição e checkout desabilitados |
| Marca | `system/surface/ui/` e `tools/brand` | artefato externo imutável por SHA + manifesto |
| Demo visual | `surface_snapshot.mjs` e `playground_fixture.py` | snapshot aprovado/publicado pela Surface; JS runtime do site não importa Surface |
| Build e deploy | `tools/public-site/deployment.py` importa `tools/surface-web/build.py` | nunca acoplar; build estático isolado com manifest e CI próprios; deploy não autorizado |
| Gateway | `services/public-identity/gateway.py` | permanece com backend responsável; site não o copia |

## PRs concorrentes verificadas
- `ordax-os#2194`: integrada; passa a consumir Surface externa no pipeline de release, sem remover ainda fonte histórica.
- `ordax-os#2195`: draft; staging do Supervisor com revisão Surface pinada. **Não tocar** em seu escopo.
- `ordax-os#2010`, `#1983`: drafts concorrentes da geração playground Meridian; não importar patches pendentes como se fossem canônicos.
- `ordax-os#1989`: integrada; a apresentação e fixture base derivam da `main` já corrigida.
- Outras PRs de Foundation, USB, Creator, Conta e OS não são responsabilidade desta extração.

## Gates de cutover
1. Copiar imagens originais pendentes e verificar byte-for-byte.
2. Publicar brand artifact e demo com origem/revisão/impressão digital independentes do pipeline OS.
3. Consumir um catálogo comercial público autorizado (se houver) sem copiar contrato de entitlements.
4. Rodar build estático autônomo e testes em CI, com screenshots comparativos e validação WCAG/responsividade/SEO por rota.
5. Exercitar autenticação, sessão, recovery e catálogo em staging **sem habilitar funcionalidades indevidas**.
6. Atualizar ownership/caminhos, CI e deploy orquestrador do OS em PR separada, reconciliar com Surface e validar referências.
7. Só então retirar fonte duplicada do OS mediante prova de equivalência; sem publicar produção automaticamente.
