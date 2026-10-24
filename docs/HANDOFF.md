## Cutover da demonstração Dev — 24/10/2026

**Estado atual:** o código Site foi extraído, e a apresentação duplicada do OS foi removida na [OS #2229](https://github.com/ordaxsystems/ordax-os/pull/2229). A projeção canônica de apps/atalhos do OS pertence à [OS #2234](https://github.com/ordaxsystems/ordax-os/pull/2234), sem ressuscitar os geradores de páginas. A [Surface #13](https://github.com/ordaxsystems/ordax-surface/pull/13) publicou a prerelease Dev durável e atestada com 11 telas e 4 apps. O Site consome o archive e manifesto fixados por SHA-256 no único `contracts/migration-artifact-lock.json`, verificando assinatura no CI, procedência Surface/OS, integridade e segurança de extração no build.

O snapshot histórico `artifacts/surface-preview/os-migration-70b0f7eb` foi removido do Git do Site; não há cópia do renderer Surface no Site ou no OS. **Não concede autorização de produção**: marca e ofertas continuam com snapshots históricos OS, Identity e gateway reais dependem de staging, e downloads/Stable permanecem desativados. Os registros abaixo são cronológicos e não anulam esta atualização.

---

# Handoff operacional — SITE-001

**Branch Site:** `feat/site-independent-extraction`  
**Repo:** `ordaxsystems/ordax-site`  
**Origem observada:** `ordax-os/main@70b0f7eb5d5085be0d4f176f5232def37c7a2a24`  
**Status atual (2026-10-24):** SOURCE/BUILD INDEPENDENTES INTEGRADOS À MAIN, CUTOVER DE BUILD DEV NO OS INTEGRADO; limpeza da apresentação histórica integrada por `ordax-os#2229` (merge `c7533bc6`). **Sem autorização de produção, Identity pública ou promoção Stable.**

## Estado corrente (2026-10-24)

O histórico abaixo descreve etapas anteriores, inclusive referências a PRs draft que já foram integradas. A autoridade atual do Site em Dev é `ordax-site/main`; [Site #1](https://github.com/ordaxsystems/ordax-site/pull/1) integrou a extração, [Site #2](https://github.com/ordaxsystems/ordax-site/pull/2) integrou o consumo Dev da demo e [OS #2225](https://github.com/ordaxsystems/ordax-os/pull/2225) repontou os builds Vercel. A remoção da cópia histórica foi **integrada** por [OS #2229](https://github.com/ordaxsystems/ordax-os/pull/2229), commit `c7533bc6cb84678fb69c3cdda71b1313ac18e4bb`, após sete verificações CI aprovadas. A [OS #2230](https://github.com/ordaxsystems/ordax-os/pull/2230) foi encerrada por redundância; isso não é autorização para deploy público. O lock de snapshots de migração permanece exclusivamente Dev, e a publicação oficial Surface/Platform, o gateway Identity e a homologação de staging são gates separados.

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

## Alto contraste nativo e foco do skip link (2026-10-23/24)

- O `scripts/browser_smoke.py` usa `Emulation.setEmulatedMedia` para ativar `forced-colors: active` **no Chrome real** em cada uma das 11 rotas desktop. Confirma `matchMedia`, foco do skip link, contorno calculado >=2px, enquadramento do atalho na viewport e ausência de scroll horizontal; as capturas `forced-colors-*.png` são incluídas no artefato de evidência. Os checks usuais continuam 33, com 22 reflows e 6 casos sem JS, sem criar outra suíte ou material Surface.
- A primeira rodada detectou o problema: 10 das 11 rotas mantinham o atalho momentaneamente acima da tela durante a transição de foco, embora já estivessem focadas e com outline. [CI diagnóstico](https://github.com/ordaxsystems/ordax-site/actions/runs/40055855014). `site/assets/site.css` agora usa `transition:none` sob `forced-colors: active` para esse atalho, com `outline:2px solid Highlight` e `transform:none` ao receber foco. **Não** alteramos os CSS publicados da Surface nem o comportamento padrão fora desse modo.
- Prova da PR [PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40055957424) sobre o commit `8e368570`. Alta visibilidade/forced-colors é **gate parcial**: ainda são exigidos testes de zoom real e somente texto, contraste visual em gradientes/imagens e validação manual com leitor de tela, além de Identity em staging e publicação atestada por Surface/Platform. PR segue draft, sem cutover nem deploy.

## Ampliação de texto 200% — stress test limitado (2026-10-24)

- O Chrome offline agora audita as 11 rotas com **fontes calculadas duplicadas**, separadamente dos 33 cenários base, 22 de reflow e 6 sem JS; produz capturas `text-200pct-*.png` e `textEnlargementResults` no mesmo relatório `out/browser-evidence/report.json`.
- O teste mede os tamanhos **antes** de aplicar as alterações, para não duplicar fatores por herança. A camada `.playground` é material publicado da Surface e não é modificada ou declarada aprovada como CSS pertencente ao Site. Exige ao menos um nó textual ampliado por rota, nenhuma divergência do fator 2, nenhuma caixa textual truncada sob overflow oculto e nenhum overflow horizontal de página. Não altera CSS fonte nem HTML entregue.
- [CI da PR aprovado](https://github.com/ordaxsystems/ordax-site/actions/runs/40056870866), commit `176a8fae`: `SITE_BROWSER_PROOF=PASS routes=11 viewports=3 checks=33 reflow=22 text200=11 noscript=6`. O job push equivalente também passou.
- **Limitação explícita:** isto é um teste de stress alterando `font-size` computado, não é o zoom somente texto nativo do browser. A prova não detecta todos os tipos de sobreposição, textos gerados em `::before/::after`, leitores de tela ou contraste com fundos complexos. Nenhum desses gates pode ser declarado concluído por inferência. Faltam também Identity em staging e os artefatos comerciais/Surface oficiais. PR Site mantém status draft; sem deploy ou cutover.


## Próxima prova presencial — sem declarar conformidade prematura

- Criado `docs/ACCESSIBILITY-GATES.md` como protocolo único de verificação manual por rota, com zoom de página **nativo** 200/400%, zoom somente texto 200% em navegador que o suporte, parâmetros de espaçamento WCAG 1.4.12, leitores de tela e critérios de evidência/aceitação. O protocolo está **pendente**, não representa validação executada.
- O teste automatizado `text200` permanece um estresse de fonte independente de zoom de browser. Não autoriza produção, cutover nem modificação da Surface. Para o próximo owner/validador, usar a revisão exata do build candidato e o catálogo `contracts/site-routes.json`, sem copiar rotas para outro SSOT.

## Prova Chrome de espaçamento de texto — WCAG 1.4.12 (2026-10-24)

- `scripts/browser_smoke.py::text_spacing_probe` amplia a cobertura da **mesma** suíte, sem criar runner paralelo ou modificar CSS entregue. Aplica `line-height=1.5`, margem após parágrafos `2em`, `letter-spacing=0.12em` e `word-spacing=0.16em` aos textos visíveis do Site em largura 390 CSS px; demonstração externa `.playground` permanece sem alteração. O browser alterna efetivamente PT-BR/EN-US pelo seletor, validando 22 cenários.
- Gate automatizado exige que cada rota/idioma tenha amostras, que propriedades computadas alcancem os patamares requeridos, que textos testados não estejam cortados por `overflow:hidden/clip`, sem scroll horizontal global nem exceção JS. Capturas `spacing-pt-BR-*.png` / `spacing-en-US-*.png` e `textSpacingResults` são anexados ao relatório `out/browser-evidence/report.json`. [CI da branch PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40057544890): `SITE_BROWSER_PROOF=PASS routes=11 viewports=3 checks=33 reflow=22 text200=11 spacing=22 noscript=6`.
- **Não é certificação WCAG completa:** o teste não demonstra visualmente ausência de sobreposição entre todos os elementos, estados autenticados de staging ou leitores de tela. O protocolo de aceitação humana continua em `docs/ACCESSIBILITY-GATES.md`. O Site permanece draft, sem merge/cutover/deploy e sem autoridade sobre artefatos Surface, Identity ou catálogo de releases.

## Preflight de integração externa e hardening de downloads (2026-10-24)

- `scripts/staging_preflight.py --staging-origin https://<host-de-staging>` é a **única prova opcional** de rede da migração no Site. Não há URL de staging definida no código, e ela não roda no CI sem endpoint explícito. A CLI aceita somente origem HTTPS explicitamente identificada como staging/preview, rejeita produção/local/IP, redirecionamento, resposta que não seja JSON, payload excessivo e cache indevido de sessão. Faz somente GET anônimo e não imprime dados de usuário.
- Reaproveita diretamente `scripts/public_identity_state.py::resolve_public_identity_mode` e `scripts/public_release_catalog.py::validate_catalog`: coteja configuração publicada, sessão anônima e catálogo vazio enquanto não houver publicação oficial. Qualquer resultado `PASS` afirma **apenas** leitura de contratos anônimos do origin escolhido, jamais login real, logout, recuperação, billing, publisher attestation, cutover ou autorização para deploy.
- `tests/test_staging_preflight.py` realiza provas positivas/negativas **sem rede** (origem malformada/produção, sessão incompatível ou gateway ausente, Web habilitado, catálogo adulterado etc.). `public_release_catalog._same_origin_path` rejeita traversal, bytes codificados, barras ambíguas e links externos; testes de contrato exercitam esses casos. Esse hardening protege o futuro consumo de artefatos atestados, **não habilita** um download agora.
- Dependências externas seguem explícitas: owner Surface deve publicar marca/demo oficial em [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3); o owner das ofertas/publicações precisa fornecer artefato autorizado; Identity exige integração real em staging e provas autenticadas separadas. Manter PR do Site em draft até homologação e cutover coordenado com o OS. Não confundir CI local com disponibilidade de staging.

## Staging: ambiente real ainda inexistente e prova pinada ao bundle (2026-10-24)

- Inspeção **read-only** da conta Vercel OrdaX retornou somente os projetos `ordax-os-public` e `ordax-web` — não há projeto `ordax-site` ou preview correspondente à PR #1. Previews disponíveis são de revisões históricas de `ordax-os` (os de `ordax-web` também vêm de branches do OS), sujeitos a SSO; os dois projetos informaram `latestDeployment.target=production` com `readyState=ERROR`. Nenhuma URL histórica deve ser usada para declarar Site staging pronto. Nenhum Vercel deploy, alteração de domínio, variável ou proteção ocorreu.
- O `scripts/staging_preflight.py` inicialmente aceitava schemas anônimos válidos mesmo em preview legado. Agora exige **origem HTTPS de staging**, `--expected-site-commit` e `--expected-manifest-sha256` obtidos de **bundle confiável do CI**. Antes de consultar a sessão verifica o manifesto entregue em `/public-site-manifest.json` por SHA-256 de bytes, schema canônico importado do builder, classe Site, commit fonte e catalogação vazia; confere `config/public-site.json` e `releases/catalog.json` contra tamanho e SHA-256 exatos do inventário. Não confundir essa verificação com publisher attestation.
- `tests/test_staging_preflight.py` incorpora provas offline negativas de manifesto divergente ou ausente, commit incorreto, configurações e catálogo adulterados, além dos gates anteriores. Comandos atualizados no README; o CI **não** usa rede nem credenciais. Para validar Identity de verdade, o owner de deployment deve preparar um preview **independente do ordax-site**, com proxy autorizado e ambiente protegido, fornecer a revisão CI correspondente e permitir testes read-only. Autenticação E2E, recuperação, assinatura, releases e acessibilidade manual continuam fases próprias e bloqueadas.

## Verificação de todos os bytes do preview independente (2026-10-24)

- O `scripts/staging_preflight.py` tinha uma lacuna de integridade: um host remoto com o manifesto, config e catálogo corretos podia servir HTML/JS/CSS diferentes. Agora, após fixar digest e revisão do manifesto a um artefato CI de confiança, verifica **o inventário inteiro** do bundle candidato por GET somente leitura, em streaming SHA-256 com contagem exata de bytes, URLs de rotas canônicas para `index.html`, sem redirecionamentos nem cookies. Isso inclui apresentação, scripts, estilos, imagens, fontes, a fixture pública de demonstração e demais arquivos listados no manifesto. Os dois JSON públicos seguem verificados por bytes e schema; a sessão anônima é consultada somente depois das provas estáticas.
- Segurança: paths relativos seguros e únicos, limite de 500 itens e 64 MiB de inventário; recusa arquivo com digest/size divergentes, deslocamento, resposta truncada/excessiva ou status não-200. Os testes offline exercitam injeção de HTML de login/JS, resposta de rota diferente, redirecionamento, ausência de arquivo, corpo com tamanho errado e inventário malformado. Nenhum serviço externo é invocado no CI.
- **Gate de rede continua PENDENTE:** a conta Vercel observada não continha `ordax-site` e os previews antigos pertenciam ao OS; não foi criada implantação ou projeto. `PASS` futuro deste pré-flight não prova Identity autenticado, pagamento, catálogo comercial atestado, conformidade WCAG total ou cutover. Essa evidência é técnica e limitada ao bundle e à projeção anônima declarados. Manter a PR draft até as dependências externas estarem prontas.

## Catálogo público integralmente fail-closed (2026-10-24)

- A auditoria encontrou divergência objetiva entre `render_catalog` (publisher projection) e `validate_catalog` (consumidor do bundle). O validador agora exige metadados não vazios `version`, `channel`, `published_at` e `target.id` exclusivo **por release**, além de todos os hashes, hrefs e compliance existentes. `tests/test_site_contract.py` cobre publicação sintética somente em unidade, rejeita duplicidade, campo vazio e travessia codificada; nenhuma release sintética foi incluída no bundle.
- O `site/assets/site.js` agora rejeita **todo o catálogo** quando `status=empty` contém releases, `status=ready` não possui releases, IDs/commits divergem, campos faltam, targets repetem ou não passam integridade, ou compliance está incompleta. O gate canônico de path no browser exclui traversal, URLs remotas e escapes `%2e/%2f`, coerente com o validador Python; nenhum link de download é exibido como efeito colateral de um catálogo parcialmente válido.
- `scripts/browser_smoke.py`, no mesmo runner isolado, injeta **somente em memória do loopback** três respostas indevidas em `/releases/catalog.json` e exige estado de erro e **zero links** em `/download/`. O arquivo do candidato permanece imutável, sem novo test runner, sem backend ou publisher externo. [CI da branch PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40066265296): 35 unit tests, `SITE_BUNDLE_VERIFY=PASS`, `SITE_BROWSER_PROOF=PASS ... catalogReject=3`. Gate de produção/release/Identity/staging segue pendente.
- O contrato do OS atual reporta `vercel_migration.preview_identity_allowed=false` e deploy Git preview desabilitado; não contornar nem ativar Identity em preview sem decisão formal do owner. Vercel não possui projeto Site independente. Nenhuma configuração/rota/digest real foi liberada nesta etapa.

## Recibo do bundle impede catálogo remoto não autorizado (2026-10-24)

- Divergência corrigida: mesmo com catálogo vazio no build verificado, o navegador podia aceitar uma resposta `ready` formalmente válida em `/releases/catalog.json` se o endpoint/CDN a trocasse. `site/assets/site.js::loadPublicCatalog` agora compara os bytes recebidos com a única entrada `releases/catalog.json` do manifesto do bundle independente; realiza leitura **streaming limitada a 256 KiB**, compara tamanho e SHA-256, confere revisão/classe/schema do manifesto e obriga `catalog_status` e `publications_sha256` coerentes. Nenhum segundo SSOT foi criado.
- `scripts/build.py::verify` recusa `catalog_status=ready` se o catálogo gerado está `empty`, e recusa recibo de publisher em catálogo vazio. `tests/test_site_contract.py` comprova esses casos. Na única suíte Chrome, `scripts/browser_smoke.py` inclui dois novos cenários negativos: `ready` **bem formado porém não autorizado pelo bundle** e `empty` com campo extra injetado; exige mensagem de erro e zero links. Dados sintéticos só existem em memória do servidor local; nenhum download ou publicação foram ativados.
- [CI de implementação (PR) PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40068811802): 36 testes unitários, bundle verify PASS e Chrome `catalogReject=5` em 11 rotas, 3 viewports e as provas anteriores. Verificar novamente o HEAD após atualização documental. **Limite de segurança:** manifesto e catálogo servidos pela mesma origem não são atestação criptográfica externa; publicação futura necessita autoridade independente do owner, ainda ausente. Nenhum preview independente foi disponibilizado; `ordax-os` ainda tem `preview_identity_allowed=false`, e Surface issue #3 permanece aberta. Não executar merge/cutover/deploy ou habilitar downloads/Identity.

## Autoridade dos downloads — fail-closed mesmo com manifesto falso (2026-10-24)

- O hash do catálogo no `public-site-manifest.json` é prova de consistência, **não** uma assinatura externa do responsável pelas releases. Uma resposta `ready` com SHA-256 correspondente a um manifesto também alterado poderia enganar um consumidor permissivo. Enquanto o Site só tem pacote de migração, `scripts/build.py::verify` e `site/assets/site.js::loadPublicCatalog` rejeitam **todo `ready`**, ainda que o catálogo esteja correto e o manifesto declare `publications_sha256` válido. A única combinação permitida é `empty` e recibo `null`.
- Prova negativa adicional no Chrome local sobrescreve **ambos** `/releases/catalog.json` e `/public-site-manifest.json` com JSON coerente, sem arquivos de produto nem rede externa, e exige erro e zero links. A validação canônica do inventário agora é `scripts/build.py::validate_bundle_inventory`, consumida também pelo staging preflight; inventário duplicado foi eliminado. Provas unitárias cobrem paths, conflitos parent/child, symlinks, limites e manifesto fictício.
- Pendências externas permanecem: Surface oficial em `ordax-surface#3`, publisher/attestation real, preview independente com autorização de Identity, WCAG manual e cutover. **Não** forçar `ready` editando JSON/manifesto ou duplicando um backend de downloads no Site.

## Candidato do CI com SHA real e sem workflow duplicado (2026-10-24)

- O workflow `.github/workflows/site-source.yml` deixou de executar `push` na branch de migração: a PR é a única verificação automática das alterações nessa branch; `push` continua na `main`. No evento PR, o checkout aponta explicitamente ao SHA do **head real**, em vez da ref temporária `pull/*/merge`. O build usa `git rev-parse HEAD` como `source_commit` e exige igualdade com o manifesto.
- Os logs da execução imprimem `SITE_CANDIDATE_SOURCE_COMMIT` e `SITE_CANDIDATE_MANIFEST_SHA256`, que devem ser obtidos **do mesmo CI confiável** para o pré-flight externo. O artefato `ordax-site-candidate` é apenas para desenvolvimento; não usar o merge sintético de uma execução anterior nem o valor servido pelo host remoto como pin de confiança. O desenho e limites estão na ADR-025; `tests/test_site_contract.py` protege a configuração contra regressões.
- **Continua pendente** a atestação de publisher, Surface oficial, autorização de staging Identity, WCAG manual e cutover. Sem deploy, DNS, segredos ou merge nesta etapa.

## Identidade read-only não aceita redirecionamentos (2026-10-24)

- Em `site/assets/site.js`, `loadJson(path)` agora exige URL literal de mesma origem, `redirect: "error"` e resposta obtida exatamente do endpoint solicitado (`response.url`), antes do parse. Corrige a possibilidade de usar a resposta 200 de um destino redirecionado como sessão ou política legal de cadastro.
- `scripts/browser_smoke.py`, **no runner já existente**, adiciona um caso de teste de sessão redirecionada: um 302 local de `/auth/session` aponta para um endpoint de prova que retornaria JSON autenticado sintético. A Conta deve permanecer `unavailable` sem exibir o e-mail de prova nem estado de sessão verificada. Nenhum teste acessa backend ou deploy real, nem disponibiliza identidade fictícia no bundle.
- Este gate verifica a barreira de **endpoint HTTP**, não autorização de sessão ou login de ponta a ponta. Autenticação real continua pertencendo ao Identity/OS, com `preview_identity_allowed=false` no contrato vigente; Surface/publisher e aprovação de staging seguem bloqueios separados.

## Revalidação assíncrona de Identity não ressuscita formulário (2026-10-24)

- Corrigida a condição de corrida no shell `site/assets/site.js`: `renderIdentity(config, generation)` confronta após cada espera assíncrona a `startRevision` e `sessionRevision` existentes; `start()` oculta e desativa imediatamente os formulários ao reiniciar a verificação, antes do GET da configuração. Carregamentos/callbacks antigos do Turnstile não podem habilitar envio e o widget anterior é revogado. Nenhum segundo gerenciador de sessão foi introduzido.
- `scripts/browser_smoke.py` foi ampliado **na suíte Chrome já existente**: dois `/auth/session` GET concorrentes, resposta antiga `200 anonymous` atrasada e nova resposta `503` imediata após `OrdaXPublicAccount.refreshSession()`, exigem que o formulário login continue `unavailable`, `hidden`, `action` ausente, todos os controles desabilitados, `data-identity-ready=false`. O teste é integralmente loopback e não habilita Identity real nem publica respostas artificiais.
- [CI da implementação aprovado](https://github.com/ordaxsystems/ordax-site/actions/runs/40081330125): 39 testes unitários, `SITE_BUNDLE_VERIFY=PASS`, `SITE_BROWSER_PROOF=PASS ... catalogReject=6 redirectIdentity=1 identityRace=1`. Conforme ADR-027, verificar o HEAD depois desta atualização documental.
- Dependências mantidas: pacote oficial Surface em `ordax-surface#3`, preview independente autorizado pelo owner, política Identity do OS ainda nega preview, atestação oficial de releases e validação manual WCAG. Sem deploy/cutover/merge.

## Consumo JSON limitado e único no navegador (2026-10-24)

- **Causa raiz:** `site.js::loadJson` fazia `response.json()` sem limite para dados de Identity/configuração/política legal, enquanto `account-portal.js` tinha outro `response.json()` para uso MCP. Catálogo de downloads usava um terceiro leitor próprio. Consolidado em `site/assets/site.js::readJsonBytes`, com um limite total de **256 KiB** para respostas JSON, verificação obrigatória `application/json`, `Content-Length` quando presente, limite real dos chunks recebidos, cancelamento em excesso e UTF-8 estrito. O catálogo exige ainda tamanho exato e SHA-256 inventariado, sem permitir redirects. Observação MCP usa o método read-only `OrdaXPublicAccount.readMcpUsage` do mesmo shell; nunca declara direitos, franquia ou faturamento e não substitui o servidor autorizado.
- A única prova Chrome injeta em loopback dois cenários de sessão JSON falsificada com `200`: payload de 270 KB **sem Content-Length** e resposta JSON sintaticamente válida com `Content-Type: text/plain`. O Site deve manter `/conta/` em `unavailable` e não renderizar e-mail do payload de prova. `tests/test_site_contract.py` impede reintrodução do segundo fetch sem limite para MCP. **Nenhum dado de teste entra no artefato público.**
- Pendências externas intactas: Surface oficial #3, Identity staging autorizado, publicador de releases com atestação independente, homologação manual e cutover OS. Revisar ADR-028 e os logs do CI antes de utilizar qualquer SHA de candidato.

## Consumo MCP isolado pela sessão atual (2026-10-24)

- **Correção da causa raiz:** `account-portal.js` não usa mais `session.email` como chave de reuso do histórico MCP: e-mail igual não significa mesma sessão. O painel associa seu estado ao objeto imutável produzido pelo **único** `OrdaXPublicAccount.subscribe`, limpa imediatamente os dados a cada refresh/troca/logout e invalida requisições pendentes via `mcpUsageRevision`. O método canônico de transporte `site.js::readMcpUsage` também rejeita dados que chegam após alteração do `sessionView`.
- A única suíte Chrome local agora inclui `usageSession=1`: três sujeitos de teste A/B/C retornam o mesmo e-mail e consumos sintéticos 91/44/7. A consulta B responde **depois** de C, e a interface deve manter **somente 7**, sem 91/44 reaparecerem. Os dados do teste existem só no `http.server` loopback de `scripts/browser_smoke.py`, não no bundle e sem acessar Identity/MCP real.
- [CI de implementação](https://github.com/ordaxsystems/ordax-site/actions/runs/40083714347) aprovado: **40 unit tests**, bundle verify, 11 rotas Chrome, `catalogReject=6 redirectIdentity=1 jsonContract=2 identityRace=1 usageSession=1`. Verificar HEAD após esta atualização documental. ADR-029 é o registro de decisão.
- Gates ainda externos: pacote oficial Surface (`ordax-surface#3`), publisher de releases, preview Identity aprovado (OS atual `preview_identity_allowed=false`), WCAG manual e cutover. Não usar `usageSession=1` como autorização de acesso ao servidor.

## Fragmentos antigos do login removidos antes da primeira espera (2026-10-24)

- Corrigida a sequência de `site/assets/site.js::start()`: o fragmento de `/login/` é apagado sincronamente via `history.replaceState` **antes** de iniciar qualquer requisição assíncrona, em vez de após `await loadConfig()`. Tokens de provedores antigos não são analisados, armazenados nem trocados pelo Site; pathname e query são preservados.
- Regressão `fragmentScrub=1` no Chrome de CI já existente: servidor Python **exclusivamente loopback** segura `GET /config/public-site.json`; navegação com fragmento de autenticação sintético exige `location.hash=""`, URL sem o marcador de token, form sem `action` ativo e zero exceções enquanto o GET ainda aguarda liberação. O testbed libera a configuração ao final; nenhuma fixture/token real chega à distribuição.
- Decisão arquitetural em ADR-030. A proteção do shell não substitui logout remoto, troca de tokens, cookies HttpOnly ou aprovação de preview Identity do OS (`preview_identity_allowed=false`). Surface oficial/publisher, WCAG manual e cutover continuam pendentes.

## Prova positiva de integridade de documentos legais (2026-10-24)

- Corrigido `site/assets/site.js::verifyPublishedRegistrationDocuments`: a verificação de `Content-Length` rejeitava erroneamente números legítimos por usar duas barras invertidas na expressão regular JavaScript. A expressão aceita dígitos decimais normais sem retirar nenhuma das barreiras existentes: URL legal canônica, resposta 200 direta, MIME HTML, máximo 2 MiB efetivamente lidos e SHA-256 exato para Privacidade e Termos.
- O teste `tests/test_legal_documents.mjs` executa a **mesma função de produção**, mas instrumenta uma cópia em memória apenas dentro do Node VM, interceptando `fetch` sem rede real. Exige dois caminhos válidos e seis rejeições adversariais. Integrado no **workflow já existente**, não cria outra build pipeline nem inclui código de teste no bundle. O resultado é `SITE_LEGAL_DOCUMENT_CONTRACT=PASS positive=2 negative=6`.
- Esses testes não confirmam aceite do usuário ou gateway real. `account_activation_ready=false` e `preview_identity_allowed=false` seguem vigentes; teste E2E autenticado somente após autorização do owner. Consulte ADR-031.
