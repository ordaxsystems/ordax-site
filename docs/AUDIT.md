# Auditoria de extração — baseline 2026-10-23

## Inventário e proveniência
- Origem: `ordaxsystems/ordax-os`, branch `main`, revisão observada `70b0f7eb5d5085be0d4f176f5232def37c7a2a24`.
- Árvore original da apresentação: `sites/public/`, Git tree `bc516a313eaa78a83652237a6d9d0cdbf295d28b` (36 blobs de arquivo, com 11 rotas HTML).
- Implementação original: `tools/public-site/`, incluindo build, geradores Meridian, validação legal, catálogo público, deploy e smoke.
- Artefato novo: `site/`; todo HTML, JS, CSS e i18n copiado de origem sem reconstrução por IA; Todos os seis PNG/JPEG do site copiados preservando **o mesmo blob SHA Git**.
- **Imagens originais transferidas e comprovadas**: `site/assets/aurora-titanium.png` (Git blob `e4574877f57a66574d001ebcfbfc8718782a2c23`, 2016680 bytes) e `site/assets/download-hero.png` (Git blob `7c23ed6070890d81a11474108f0a52a0965ce501`, 1629858 bytes). Um workflow temporário fez checkout do commit OS exato e verificou `git hash-object` antes de gravar ambas; [execução aprovada](https://github.com/ordaxsystems/ordax-site/actions/runs/40038857924). O workflow foi retirado depois da importação, sem legado permanente.
- O snapshot `site/assets/surface-snapshot.json` + CSS, `playground-fixture.json` são artefatos **gerados** de demonstração, nunca imports dinâmicos. A procedência original deve permanecer identificável, e atualizações futuras devem consumir artefatos publicados pelo owner da Surface.
- Os valores comerciais de referência foram projetados **apenas como HTML público** por gerador canônico do commit OS de origem, em `artifacts/offers/os-migration-70b0f7eb/` com contrato-fonte identificado por digest e bloqueios explícitos de compra. [Prova de geração](https://github.com/ordaxsystems/ordax-site/actions/runs/40039542832). Nada altera o sistema de assinatura.
- Fontes, símbolo, tokens e wallpaper foram **preservados como artefato de migração separado do source** em `artifacts/brand/os-migration-70b0f7eb`, com manifesto, origem OS pinada e SHA-256 por arquivo ([prova de geração](https://github.com/ordaxsystems/ordax-site/actions/runs/40038988099)). Esse artefato permite build independente, mas **não** substitui o futuro artefato publicado e mantido pelo owner oficial de marca/Surface.

## Dependências e owner correto
| Subsistema | Fonte anterior | Destino/correção |
|---|---|---|
| Landing, páginas produto, legal | `sites/public/` | `ordax-site/site/` |
| UI de Identity | `sites/public/assets/site.js` + `account.css` | apresentação no site; operações **same-origin** no owner remoto |
| Conta (visual) | `account-portal.js` + `account-dashboard.css` | site apenas; sem implementação de sessão/billing |
| Traduções | `sites/public/i18n/` | `site/i18n/`, único dicionário de site |
| Downloads | `platform/releases/publications.json` via gerador | somente catálogo autorizado produzido pelo owner; default vazio |
| Planos/preços | `docs/contracts/entitlements.json` via `plan_catalog.py` | **não** copiar contrato; snapshot de projeção HTML read-only `artifacts/offers/os-migration-70b0f7eb` gerado no commit fonte e verificado; publicação oficial pelo owner ainda pendente; compra/cotas desabilitadas |
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
1. **PASS** — todas as imagens originais preservadas e blobs verificados.
2. **PARTIAL** — snapshot imutável de migração da marca gerado; artefatos oficiais da Surface e demo ainda precisam de publicação pelo owner.
3. **PARTIAL** — apresentação comercial de referência restaurada por artefato de migração verificado (sem contrato duplicado); CI das quatro opções na landing e Conta [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40039633625). Falta projeção oficial mantida pelo owner e autorização do conteúdo publicado.
4. **PARTIAL** — build e verificação independentes aprovados no [CI de candidato](https://github.com/ordaxsystems/ordax-site/actions/runs/40039062149); 11 rotas, assets, metadados básicos, formulários fail-closed e catálogo default vazio aprovados na [prova estática ampliada](https://github.com/ordaxsystems/ordax-site/actions/runs/40039330301). Screenshots, WCAG, responsividade e SEO completo ainda exigem browser/staging.
5. Exercitar autenticação, sessão, recovery e catálogo em staging **sem habilitar funcionalidades indevidas**.
6. **PREPARED** — PR documental [ordax-os#2196](https://github.com/ordaxsystems/ordax-os/pull/2196) registra o handoff, sem alterar caminhos. O repoint de ownership, CI/deploy e remoção duplicada exige uma **outra PR** após reconciliação Surface.
7. Só então retirar fonte duplicada do OS mediante prova de equivalência; sem publicar produção automaticamente.


## Evolução de provas da extração (2026-10-23)
- Browser ChromeDriver sem dependências de produção: 11 rotas × três resoluções = 33 checks, 0 falhas no [CI](https://github.com/ordaxsystems/ordax-site/actions/runs/40040704257). Corrigido segundo landmark `main` causado pela inserção do snapshot da Surface, sem editar o snapshot gerado.
- Single fixture: a landing deixou de serializar `playground-fixture.json` dentro de `index.html`. Diferença source: **159.242 bytes** a menos no HTML inicial; o JavaScript agora consome a única fixture same-origin, valida schema e falha fechado se não encontrar o recurso. [Prova Chrome após remoção](https://github.com/ordaxsystems/ordax-site/actions/runs/40040885269).
- SEO: `contracts/site-routes.json` substitui inventários hardcoded redundantes em scripts e testes. A origem canônica é fornecida pelo deployment; conteúdo do Site não controla domínio. 5 URLs informativas no sitemap; Conta, login, cadastro, recuperação e entrada Web noindex. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40041263365).
- [ordax-os#2198](https://github.com/ordaxsystems/ordax-os/pull/2198) em draft mexe no workflow e na apresentação pública derivada ao remover fontes visuais. Compatibilidade e fase de repoint do Site **devem ser reconciliadas antes do merge**, sem restabelecer source espelhado.
- **Pendente:** publicação oficial dos pacotes de brand/preview/offers; diff visual e WCAG completos, autenticação real end-to-end em staging, CI de repoint e cutover no OS, aprovação separada de produção.
