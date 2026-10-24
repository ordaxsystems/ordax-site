# OrdaX Site — instruções para agentes

Este repositório é o **owner do código de apresentação do site público** após cutover aprovado, não do OS, Surface Web, Identity, cobranças ou publicação de releases.

## Ordem de leitura
1. `README.md`
2. `docs/AUDIT.md`
3. `docs/DECISIONS.md`
4. `docs/HANDOFF.md`
5. `scripts/build.py`
6. `site/config/public-site.json`

## Autoridades e limites
- `ordax-site/main` é a autoridade do site **somente após conclusão de migração validada**; até lá, o site atual em `ordax-os/main` não deve ser removido.
- Nunca importar `system/surface`, `tools/surface-web` ou código de kernel, USB, Creator ou apps.
- Marca e demos da Surface são **artefatos publicados, imutáveis e verificáveis**, nunca cópias de código para compilar no site.
- Backend de Identity, sessão, autorização, pagamentos e banco pertence a seus respectivos owners (`ordax-platform` / serviços canônicos). Browser só consome APIs autorizadas de mesma origem.
- Não versionar secrets, chaves ou tokens. Não fabricar Conta, sincronização, assinatura, download, release ou produtos publicados.
- Não alterar domínio, deploy de produção nem credenciais sem aprovação específica.
- Recuperação e Conta continuam fail-closed enquanto seus gates reais não estiverem aprovados.
- O catálogo público vem exclusivamente de projeção autorizada do publicador de releases; sem publicação, catálogo vazio.
- Não alterar API/comportamento de `ordax-os` sem reconciliação das PRs da Surface.
- Preservar commits da `main`; não usar force-push/rebase da main.

## Fluxo
Branch -> auditoria de diffs e conflitos -> testes de rotas/i18n/segurança -> pacote com provenance SHA-256 -> CI -> PR review -> cutover OS só depois de prova de paridade -> publicação sob autorização separada. Registrar atualizações em `docs/HANDOFF.md`.

## Status
Extração é **candidata em draft**; todos os assets originais, incluindo dois PNGs grandes, foram preservados. Build CI independente, smoke estático e snapshot de ofertas/brand de migração aprovados. Há E2E **local isolado** em navegador. Faltam a publicação **oficial** desses insumos pelo owner Surface/Platform, testes completos de acessibilidade e Identity em staging, e cutover no OS. Nenhum build de produção autorizado.


## Gates de implementação atualmente verificados
- Testes ChromeDriver: 11 rotas × 3 viewports; screenshots no artefato CI [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40041263365).
- Landing: somente `site/assets/playground-fixture.json`; proibido recolocar fixture inline como segundo estado.
- `contracts/site-routes.json`: único catálogo de rotas do Site; robots, sitemap e testes o consomem.
- `--public-origin` deve ser fornecido pelo owner de deployment (OS/Platform); nunca mover DNS ou aceitar origem definida pelo browser.
- A PR concorrente [ordax-os#2198](https://github.com/ordaxsystems/ordax-os/pull/2198) envolve remoção de fonte visual. O Site ainda requer material oficial versionado e não autoriza o cutover por essa PR.


- A prova Chrome deve manter `main#conteudo` programaticamente focável, skip link acionável por teclado, nomes na árvore AX, `img[alt]` e troca real PT/EN. [Teclado+AX PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042024846), [locale E2E PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042154013).
- Não declarar conformidade WCAG completa: contrastes, leitor de tela, zoom e fluxos autenticados de staging ainda exigem provas específicas.

## Publicação Surface — contrato de consumo

- Fixture e CSS gerados **não** pertencem a `site/assets`; sua única entrada é `--surface-preview-dir`, acompanhada de `--surface-preview-manifest-sha256` pinado. O bundle materializa os arquivos após verificar proveniência e integridade.
- Sem arquivo `surface-snapshot.json` distribuído duplicando `fixture.surface`. O preview source é imutável e a eventual correção de URL de fonte ocorre **apenas na saída de build** com fingerprint recalculado.
- `artifacts/surface-preview/os-migration-70b0f7eb` é um pacote de migração **não oficial**, vindo do OS, e não uma release/assinatura da Surface. Não alterar o status para `official` sem verificação real do publisher.
- A obrigação de publicação oficial de brand/demo pertence à [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3). Até essa entrega, o Site permanece em draft, sem cutover nem deploy.

## Lock SSOT de insumos externos e segurança de releases

- `contracts/migration-artifact-lock.json` é a única lista de caminhos e pins SHA-256 dos três insumos de migração. O CI usa `--migration-lock` e proíbe overrides individuais; não mantenha digests copiados em workflow, código ou docs.
- Os manifestos de brand, preview e offers são validados **contra o digest pinado no lock antes de ler suas alegações internas**. Revisão OS de origem deve coincidir entre todos. Lock é estritamente **dev-only**; não autoriza produção.
- O builder **rejeita** `--publications` mesmo que o JSON local afirme `public_authorized=true`. Downloads permanecem vazios até integração explícita de evidência oficial do publisher (mais que flags autorreferentes).

## Prova de integridade visual entregue (2026-10-23)

- O smoke estático varre o **CSS realmente distribuído**, não os artefatos-fonte, e rejeita `url(...)` externos, com travessia de diretório, que referenciem arquivos ausentes, e `@import` não controlado. `data:image/` e referências fragmento permanecem permitidas. Os recursos externos/gerados da Surface também estão cobertos.
- O Chrome instala um observador **antes** dos scripts da página para capturar erros JS, rejeições de promise e carregamento de imagem/script/stylesheet com erro, além de HTTP 4xx/5xx para recursos estáticos. Erros esperados nos serviços `/auth/`, `/account/`, `/api/`, `/sync/` não são confundidos com falhas de asset.
- O SEO projection injeta `rel="icon"` apontando para `/assets/ordax-symbol.png` do **brand verificado**, salvo quando o source já declara favicon. Isso impede a requisição implícita a `/favicon.ico` inexistente sem replicar recursos. [CI integrado PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731).

## Reflow e no-JavaScript — regressões obrigatórias

- A suite `scripts/browser_smoke.py` inclui 33 provas regulares, **22 reflows de CSS em modo desktop** (640/320 px) e **6 estados sem execução de JavaScript**, capturados em `out/browser-evidence`. O controle auth permanece desativado também sem scripts. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051704031).
- **Não esconder horizontal overflow com `overflow-x:hidden` global.** O problema identificado era o seletor de idioma anexado ao `.site-nav` excedendo a largura em quatro rotas. A correção é `flex-wrap` e linha própria para `.public-locale-switcher` em largura estreita, no único `site/assets/site.css`.
- Não declarar testado o zoom real ou WCAG completo: o reflow usa viewports CSS equivalentes a 200/400% de uma janela de 1280 px. Text-only zoom, contraste, leitores de tela e gateway real continuam pendentes.
