# OrdaX Site

Repositório de **apresentação pública** do OrdaX. Independente dos builds do kernel, USB, Surface Web, Creator e Identity.

> **Cutover de desenvolvimento integrado (2026-10-24).** O `ordax-site/main` é o owner do código e build independentes. O repoint dos builds Vercel do OS foi integrado em [ordax-os#2225](https://github.com/ordaxsystems/ordax-os/pull/2225); a remoção da apresentação histórica duplicada está sendo concluída em [ordax-os#2229](https://github.com/ordaxsystems/ordax-os/pull/2229). Este estado **não** autoriza deploy de produção, alteração de DNS, ativação de Identity nem uso público dos artefatos temporários.

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

O catálogo público de downloads **permanece vazio**. O builder **rejeita** qualquer `--publications` local: campos declaratórios como `public_authorized=true` não são prova criptográfica da publicação pelo owner. A verificação do bundle e a interface **rejeitam também `ready` com manifesto autoconsistente**, pois o próprio host pode forjar catálogo, hashes e recibos; nenhum deles equivale a uma atestação independente. Esse gate somente pode ser aberto depois de integração com um pacote oficial atestado, revisionado e pinado pelo responsável pelas releases. Formulários e Conta dependem de gateway `same-origin`; recuperação/billing não são habilitados por UI.

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

## Recursos CSS e erros de navegador

O build independente é verificado contra **todas as referências CSS** (`url(...)` local e `@import`) e falha quando uma fonte ou imagem distribuída está ausente, quando uma URL sai da origem autorizada ou atravessa diretórios. Testes unitários provocam essas falhas. O Chrome observa exceções JavaScript/rejeições não tratadas desde o início da navegação e confirma ausência de recursos estáticos com status de erro (o backend de Identity propositalmente isolado continua respondendo 503). O favicon padrão de cada página é o símbolo OrdaX publicado pelo **brand verificado**, sem criar outro asset ou ícones redundantes. [CI navegador+smoke PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731).

Os checks são regressões técnicas; não substituem staging real, auditoria completa WCAG nem publicação oficial de marca/preview/ofertas.

## Fail-closed sem JavaScript e reflow de CSS (23/10/2026)

O `scripts/browser_smoke.py` mantém **33 cenários normais** (11 rotas × 3 telas) e exerce duas famílias de regressões separadas:

- **6 estados sem execução de JavaScript:** login, cadastro, recuperação, redefinição de senha, Conta e Web. O Chrome bloqueia scripts **antes da navegação** e comprova que os avisos `noscript` são visíveis, links de navegação funcionam e nenhum formulário de credenciais, sessão verificada ou entrada Web fica disponível. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051439195).
- **22 cenários de reflow:** todas as 11 rotas com viewport CSS de 640 px e 320 px em **emulação de desktop**, equivalentes à largura disponível em uma janela de 1280 px com escala de 200% e 400%. Verificam conteúdo principal, ausência de rolagem horizontal na página, demo montada, estados auth fail-closed e recursos/JavaScript sem erros. A prova detectou quatro cabeçalhos com seletor de idioma ultrapassando a largura; o **CSS Site canônico** foi corrigido para quebrar a linha em Download, Licenças, Privacidade e Termos. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051704031).

Há capturas por cenário no artefato `ordax-site-browser-evidence` do GitHub CI. **Isto não é um teste do comando de zoom real do navegador nem conformidade WCAG integral**: continuam pendentes ampliação exclusiva de texto, contraste completo e avaliação manual por leitor de tela, além de Identity em staging.

## Prova parcial de contraste (Chrome)

Nos cenários desktop, o Chrome calcula WCAG 2.x **4,5:1 para texto comum / 3:1 para texto grande** quando texto e superfície têm cores sólidas confiáveis, com cores/razões e amostras ignoradas no `report.json`. Os problemas identificados nas telas de Identity foram corrigidos no CSS Site sem atualizar os tokens visuais de origem; [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40053856203). Não equivale a auditoria de todo o site: gradientes, imagens, pseudoelementos, estados de foco/hover e avaliação humana por leitor de tela ainda exigem trabalho.

## Semântica da Conta e preferência de movimento reduzido

O Chrome agora exige um **único `h1` principal da página**, excluindo apenas os títulos internos da demonstração interativa embutida na landing. O HTML estático da Conta fornece um `h1.sr-only` de fallback dentro de `#account-session`, lido mesmo quando a aplicação não carrega ou JavaScript está desativado. O controlador substitui esse conteúdo de sessão ao montar o portal, cujo `#account-content` apresenta o `h1` dinâmico existente.

A prova de navegador também ativa de verdade `prefers-reduced-motion: reduce` via Chrome DevTools, mede o `scroll-behavior` e os tempos de animação/transição computados para os componentes pertinentes em cada rota e retorna ao modo normal após o teste. O CSS básico do Site elimina rolagem suave e transições do link de pulo e botões quando solicitado, preservando as políticas de movimento especializadas da landing, Identity, Download e Conta. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40054611865).

Essa prova não substitui inspeção com leitor de tela nem certificação WCAG integral.

## Pré-flight de integração externa (staging, somente leitura)

O Site não cria nem ativa serviços de Identity, cobrança ou publicação de releases. Quando o owner de deployment fornecer um ambiente **autorizado de staging ou preview**, execute:

```bash
python3 scripts/staging_preflight.py \
  --staging-origin https://staging.example.org \
  --expected-site-commit <full-build-source-commit> \
  --expected-manifest-sha256 <trusted-ci-bundle-manifest-sha256>
```

Substitua o domínio do exemplo pelo host de staging autorizado. Extraia o commit de `source_commit` e calcule o SHA-256 **do arquivo `public-site-manifest.json` do artefato CI confiável**, por exemplo com `sha256sum out/site/public-site-manifest.json`. Nunca obtenha esses valores apenas do próprio endpoint a ser testado, pois ele poderia falsificar a identidade. A prova lê primeiro esse manifesto publicado e exige coincidência dos bytes e do commit; percorre **todos os arquivos inventariados** e confere o SHA-256 e tamanho exatos de cada resposta. Páginas `index.html` são solicitadas pela rota de navegação pública (`/`, `/login/` etc.). Isso inclui HTML, scripts, estilos e imagens, não apenas os JSON de configuração e catálogo; o conteúdo é processado em streaming, sem armazenamento de arquivos ou dados de usuário. O comando executa **somente GET sem credenciais**, sem seguir redirecionamentos. O catálogo deve continuar vazio enquanto não houver atestação oficial. Domínios de produção, localhost e IPs diretos são rejeitados. Sem host, digest e commit confiáveis, não há prova de staging concluída.

**Situação inspecionada em 2026-10-24:** a conta Vercel OrdaX tinha `ordax-os-public` e `ordax-web`, mas nenhum projeto `ordax-site`; os previews existentes eram do legado `ordax-os` e protegidos por SSO, não evidência de deploy desta PR. Os últimos deployments de produção que o Vercel retornou para esses dois projetos estavam em `ERROR`. Não configurar ou reutilizar esses endereços como staging do Site sem preparar e autorizar um preview próprio. Nenhum deployment foi criado nesta etapa.

Os testes `tests/test_staging_preflight.py` são executados no CI **sem rede**; um resultado `SITE_STAGING_PREFLIGHT=PASS` comprova exclusivamente que contratos anônimos foram servidos adequadamente, **não** que login, recuperação de senha, faturamento, publicação de releases ou cutover estejam prontos. Os gates completos continuam em `docs/HANDOFF.md`, `docs/ACCESSIBILITY-GATES.md` e nas PRs dos owners externos.

## Regressão de segurança do catálogo público

O catálogo público continua **vazio por padrão** enquanto o publisher de releases não fornecer publicação oficialmente atestada. O validador Python (`scripts/public_release_catalog.py`) exige que o catálogo distribuído mantenha os mesmos metadados, integridade e unicidade de IDs esperados da projeção do publicador. No navegador, `site/assets/site.js` rejeita o catálogo inteiro antes de montar links quando encontra inconsistências, mesmo quando o servidor respondeu HTTP 200.

A suíte existente `scripts/browser_smoke.py` cobre seis cenários adversariais **apenas em loopback e em memória**, inclusive catálogos `ready` falsificados e a alteração simultânea do catálogo e do manifesto, além de IDs repetidos e travessia codificada em URL. O esperado é mensagem de erro e **zero links de downloads**, sem modificar o bundle nem inventar oferta/publicação. Isso não substitui atestação de publisher, staging homologado, teste E2E autenticado ou aprovação de produção.

## Identidade do candidato gerado no CI

Cada revisão de PR é compilada **uma única vez** pelo workflow `.github/workflows/site-source.yml`; a `main` permanece coberta por `push`. A execução da PR faz checkout do **commit real da branch**, não do merge temporário do GitHub. O `source_commit` de `public-site-manifest.json` corresponde a `git rev-parse HEAD`. O log do workflow publica:

```text
SITE_CANDIDATE_SOURCE_COMMIT=<SHA de 40 caracteres do checkout>
SITE_CANDIDATE_MANIFEST_SHA256=<SHA-256 do manifesto do artefato CI>
```

Para um pré-flight de staging autorizado, obter **ambos os valores na mesma execução aprovada** e usar o `ordax-site-candidate` correspondente. Não obter pins da própria hospedagem que está sendo validada. A revisão do processo está na ADR-025. Isso prova rastreabilidade do candidato, não a autorização de produção ou a existência de um preview com Identity real.

## Identidade: respostas do endpoint original

O shell público faz consultas GET a `/auth/session`, `/auth/registration-policy` e demais contratos de apresentação. Essas respostas precisam vir **diretamente da URL de mesma origem requisitada**: `site/assets/site.js::loadJson` recusa redirects, respostas entregues por aliases e paths ambíguos antes de interpretar o JSON. Não existem sessões simuladas ou fluxos de autenticação próprios do Site.

O navegador de CI injeta, **somente no loopback**, um 302 em `/auth/session` apontando para JSON 200 que imita uma sessão autenticada. A prova exige que a Conta permaneça indisponível, sem exibir e-mail fictício. Isso verifica a fronteira HTTP; a autenticação real, os cookies e o provisionamento continuam exclusivos do owner Identity/OS e dependem de ambiente de homologação autorizado (ADR-026).

## Revisões de sessão e proteção contra respostas atrasadas

Os formulários de login/cadastro/recuperação dependem exclusivamente dos contratos de Identity do mesmo origin e dos contadores compartilhados `sessionRevision` e `startRevision` de `site/assets/site.js`. Em qualquer revalidação da página, a ação e os controles são imediatamente desativados. Respostas anteriores de sessão, políticas/documentos legais ou carregamento do Turnstile não podem reativá-los: o runtime descarta conclusões e tokens fora da revisão atual.

O Chrome executa uma prova de concorrência sem credenciais reais, inserindo **somente no servidor local** uma resposta de sessão antiga `200 anonymous` deliberadamente atrasada e uma nova `503` imediata. A interface deve permanecer indisponível e sem envio de formulário (`identityRace=1`). Essa prova não corresponde a login real; autorização de staging continua com o owner do Identity/OS.

## Transporte JSON compartilhado e limitado

`site/assets/site.js` contém o leitor canônico `readJsonBytes` para respostas JSON da aplicação (configuração, Identity, política legal, manifesto, catálogo de downloads e consulta observacional de uso MCP). O limite de leitura é **256 KiB**, verificado tanto contra `Content-Length` quanto contra os bytes efetivamente recebidos; o leitor exige `Content-Type: application/json`, URL original sem redirect e UTF-8 válido. Para releases, o catálogo também precisa corresponder exatamente ao **tamanho/SHA-256** da entrada já publicada no bundle, permanecendo `empty` até o publicador oficial fornecer atestação.

A Conta reutiliza esse transporte por `OrdaXPublicAccount.readMcpUsage`, sem implementar outro fetch sem limite; o servidor continua proprietário de autorização, planos e limites. No Chrome de CI, respostas JSON de Identity de 270 KB sem tamanho anunciado e respostas com MIME errado são testadas apenas no loopback, exigindo **zero identidade validada**. Consulte ADR-028; isso não ativa autenticação, releases nem produção.

## Fragmentos antigos de autenticação no login

O shell em `/login/` descarta sincronicamente qualquer fragmento de URL legado antes de consultar configuração ou Identity. Isso protege o endereço de tokens de redirecionamentos hospedados antigos sem tentar trocá-los ou persistir credenciais no Site; a navegação continua no mesmo pathname/query. A suíte Chrome retém artificialmente a resposta de configuração em loopback e exige que o fragmento já tenha desaparecido (`fragmentScrub=1`). Os protocolos reais de autenticação permanecem responsabilidade do owner Identity/OS, com staging ainda não autorizado (ADR-030).

## Documentos legais: prova positiva de integridade

O gate de cadastro verifica as páginas imutáveis de Privacidade e Termos com URL canônica, MIME HTML, limite de 2 MiB e SHA-256 do contrato legal. O CI agora executa `node tests/test_legal_documents.mjs` sobre a função **real** do Site em VM isolado: aceita documentos íntegros com `Content-Length` numérico ou ausente e rejeita adulteração, redirecionamento, tamanho excessivo e política não habilitada. O teste não publica documentos sintéticos nem ativa cadastro. Consulte ADR-031.

## Hospedagem independente de desenvolvimento

`vercel.json` pertence ao **ordax-site** e produz seu próprio build com `scripts/build.py` e o lock imutável de migração. Esta configuração destina-se **somente ao projeto Vercel separado `ordax-site-dev`**, sem domínio `ordax.com.br` e sem Identity/gateway: `/auth/*`, `/account/*` e funções de cobrança não são implementadas por este repositório. Os formulários permanecem indisponíveis, downloads vazios, e um cabeçalho global `X-Robots-Tag: noindex` impede indexação deste ambiente. Apenas commits de `main` produzem builds Git automáticos.

A publicação de produção, eventual migração de DNS/alias e os endpoints de sessão/autorização exigem etapa explícita do owner de deployment, **não** são consequência do merge de código ou da criação do ambiente de desenvolvimento.
