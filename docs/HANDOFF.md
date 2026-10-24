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
4. **PARCIAL:** navegador Chrome isolado cobre reflow CSS, teclado/AX e estados fail-closed inclusive sem JavaScript; faltam contraste/zoom real/leitor de tela e paridade visual + Identity com gateway em staging.
5. PR **futura de repoint/cutover** no OS distinta da documental #2196; revalidar a `main`, reconciliar Surface #2195 e remover duplicação só após prova de igualdade e CI dos consumidores.

## Recomendações operacionais
- Começar por `python3 scripts/build.py check` e `node tests/test_localization.mjs`.
- `python3 scripts/build.py build --source-commit <sha40> --migration-lock contracts/migration-artifact-lock.json --public-origin https://ordax.com.br` **gera pacote candidato**, recusando imagens ausentes e artifacts com hashes inválidos.
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


## Acessibilidade e seleção de idioma — prova em navegador (2026-10-23)
- O Chrome CDP agora audita a árvore de acessibilidade nativa, exige nomes para controles interativos expostos e `alt` nas imagens renderizadas. O fluxo com teclado usa **Tab e Enter reais**, verifica o foco inicial, a exposição visual do skip link após a transição CSS e a chegada ao conteúdo principal.
- A primeira revisão [identificou cinco páginas](https://github.com/ordaxsystems/ordax-site/actions/runs/40041891745) que não recebiam foco corretamente no `main`; receberam `tabindex="-1"` sem tornar `main` mais um destino Tab ordinário. O teste foi ajustado para reconhecer o handler intencional da Conta, que dá foco direto sem alterar `location.hash`. [CI de teclado/AX PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042024846).
- A segunda prova aciona o **seletor real PT-BR/en-US**, verifica `html[lang]`, conteúdo traduzido de “Ir para o conteúdo” e a preferência `ordax.public.locale` no storage; restaura português para não contaminar a navegação subsequente. [CI locale E2E PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042154013).
- **Ainda pendentes:** inspeção manual com leitor de tela, levantamento de contraste por estados interativos, testes a 200%/400% de zoom e teclado com modais reais conectados à Conta, além do end-to-end com gateway autorizado. Esses gates não são cobertos pelas provas acima.
- `ordax-os/main` foi rechecado em `7677226def5fd027d37a84a8c7981c3c90d49b10` neste ciclo; a PR `#2198` da Surface continuava draft. Nenhum repoint/deploy foi feito.

## Pacote Surface externo, consumidor fechado (2026-10-23/24)

- `site/assets/` deixou de conter o snapshot/fixture gerados. Uma fixture contém o próprio `surface` snapshot; a cópia JSON idêntica foi excluída. Dados demo read-only agora vivem apenas em `artifacts/surface-preview/os-migration-70b0f7eb` com manifesto de origem OS.
- O build exige `--surface-preview-dir` **e** `--surface-preview-manifest-sha256 d7142242a5a4ff38b71cfcc952123b48a34e8bd643052b8143de9b5d36fc0cc3`. Testes de integridade validam SHA256, SHA Git, source commit, status não oficial e coerência `fixture.surface.cssSha256`/CSS; manifest e bytes incorretos são rejeitados.
- A fonte Inter herdada no CSS Surface possuía caminho de bundler não presente. No output, a referência passou a usar **a mesma fonte do brand** já validado, com cache fingerprint recalculado. O artefato de migração não é modificado.
- Issue ao owner Surface para publicação real de marca/demo: [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3). **Ainda não há release oficial detectada**; Site continua proibindo status de publicação autoafirmado, sem autorização para produção.
- Envolve apenas `ordax-site#1` em draft; OS atual continua owner até cutover validado. Se outra equipe gerar sua release, primeiro verificar origem e adaptar explicitamente o gate, nunca modificar os hashes no silêncio nem restaurar source espelhado.

## Trust pin único e bloqueio de release não atestada (2026-10-23/24)

- O CI/builder lê `contracts/migration-artifact-lock.json` como **SSOT de hashes e caminhos** dos três insumos externos temporários. O lock é dev-only e não admite overlays de parâmetros individuais; valida os três manifestos contra pins **antes** de confiar no conteúdo, e exige origem/revisão OS coerentes.
- `stage_brand`, `stage_surface_preview` e `load_reference_offers` rejeitam digests ausentes, adulterados e status não permitidos; regressões no `tests/test_site_contract.py` verificam falsificação de manifesto e entradas inválidas.
- Sem publicação oficial e atestada pelo owner de releases, `--publications` **não pode ativar downloads**; catálogo gerado é somente `empty`. `public_authorized=true` declarado por JSON local isolado não é autorização confiável.
- CI desta etapa confirma build independente, smoke estático, prova de 33 cenários em Chrome e nenhum deployment. Atestação de owner para brand/preview/ofertas ainda pendente; não promover PR à main antes dos gates documentados.

## CSS e runtime/browser errors — prova acrescentada (2026-10-23/24)

- Os 12 arquivos CSS (incluindo material brand/preview do build) passam pelo novo `scripts/smoke_static.py::check_css_dependencies`: toda URL local deve resolver para um arquivo existente no **bundle**, independentemente do source. `data:image/` e âncoras SVG são tratados como recursos embutidos; CSS `@import` remoto e travessia são bloqueados. Testes negativos foram adicionados em `tests/test_site_contract.py`.
- O Chrome agora captura `error` e `unhandledrejection` antes do primeiro script, falhas de carregamento e respostas estáticas HTTP 4xx/5xx. Fluxos auth simulados com 503 preservam o estado fail-closed, sem mascarar problemas de CSS/JS/favicon.
- Erro de recurso na landing levou à inclusão determinística de favicon usando **o símbolo já verificado do brand**, sem copiar arquivos ou duplicar ícones. [Prova integrada PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731).
- Sem alegação de WCAG completa nem teste de identidade em staging. `ordax-surface#3` e os owners de releases/entitlements ainda precisam fornecer os pacotes oficiais antes de qualquer cutover.

## Reflow desktop e modo sem JavaScript (2026-10-23)

- `scripts/browser_smoke.py` agora produz **33 capturas base + 22 capturas de reflow (640/320 px em desktop) + 6 capturas sem JavaScript**. A segunda suite NÃO é equivalente a testes de zoom real ou aumento só da fonte: comprova reflow e ausência de horizontal-scroll para viewports CSS equivalentes a 200/400% de 1280 px.
- O Chrome desativa a execução JS antes da carga das seis rotas de Identity/Conta/Web e verifica `noscript` visível, navegação de retorno, forms de credenciais fechados, nenhuma sessão validada e Web indisponível. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051439195).
- O primeiro CI de reflow evidenciou overflow a 320 px em Download, Licenças, Privacidade e Termos. Instrumentação identificou `.public-locale-switcher` com posição à direita do viewport. A correção foi **somente no CSS Site**, permitindo flex-wrap e linha dedicada no nav dos quatro templates a `<=430px`; nenhum `overflow-x:hidden` paliativo. [CI com reflow corrigido PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051704031).
- **Continuam pendentes:** prova da ampliação real de browser e text-only, contraste por estado, leitor de tela, e paridade/autenticação em ambiente de staging autorizado; não homologar estes gates sem executar.

## Contraste texto/superfície mensurável — regressão (2026-10-23/24)

- `scripts/browser_smoke.py::solid_surface_contrast_probe` aplica 4,5:1 ou 3:1 conforme tamanho/peso do texto **somente** em superfícies de cor plana cuja composição pode ser inferida. Fundo com imagem/gradiente, opacity/filter/blend não entram na medição positiva; o relatório publica `unchecked`. Cada rota não-landing deve medir amostras reais.
- A primeira prova reprovou cinco telas Identity por `.skip-link` escuro sobre escuro e texto `--md-muted` abaixo de 4,5:1 em painéis Sage/Amber/Danger. A correção é **local à camada de apresentação** (`site/assets/account.css`), sem editar o pacote imutável de tokens Surface.
- Evidências: [CI branch PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40053856203); o Chrome mantém os 33 cenários normais + 22 reflows + 6 no-JS já existentes. Este passo adiciona o contraste como regra dos cenários desktop, sem duplicar o conjunto de rotas.
- **Gates ainda pendentes:** contraste de fundos complexos e estados interativos, zoom real/text-only, avaliação de leitores de tela e paridade/Identity em staging. Publicação oficial da Surface permanece dependente de [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3).

## Estrutura de headings e movimento reduzido (2026-10-23)

- A auditoria de `<h1>` encontrou uma lacuna real na página `/conta/`: no source só existia `#account-content`, inicialmente vazio, e o título era produzido inteiramente por JS. Foi acrescentado `<h1 class="sr-only">Minha Conta OrdaX</h1>` dentro de `#account-session`. O JS da Conta **substitui** o conteúdo desse elemento quando prepara a sessão e cria seu próprio título na região dinâmica. O smoke agora exige 1 heading principal por rota estática; o Chrome exige 1 heading de página renderizado, excetuando a demo interativa da landing. A prova sem JavaScript também exige o título da Conta.
- `site/assets/site.css` agora atende `prefers-reduced-motion: reduce` com `scroll-behavior: auto` e desativa as transições de `.skip-link` e botões. A suite Chrome aplica a preferência em cada rota desktop, verifica `matchMedia`, scrolling e durações de movimento nos elementos relevantes; depois restaura `no-preference`.
- Ambos os workflows passaram no [commit de implementação](https://github.com/ordaxsystems/ordax-site/actions/runs/40054611865). Continua pendente inspeção manual por leitor de tela e estados autenticados reais em staging; isso **não** concede autorização para merge, DNS nem deploy.
