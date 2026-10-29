# OrdaX Site

Repositório de **apresentação pública** do OrdaX. Independente dos builds do kernel, USB, Surface Web, Creator e Identity.

> **Cutover de desenvolvimento integrado (2026-10-24).** O `ordax-site/main` é o owner do código e build independentes. O repoint dos builds Vercel do OS foi integrado em [ordax-os#2225](https://github.com/ordaxsystems/ordax-os/pull/2225); a apresentação histórica duplicada foi removida por [ordax-os#2229](https://github.com/ordaxsystems/ordax-os/pull/2229) (merge `c7533bc6`). Este estado **não** autoriza deploy de produção, alteração de DNS, ativação de Identity nem uso público dos artefatos temporários.

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

## Build de candidato Dev — artefatos oficiais dos owners

O Site usa **duas prereleases Dev assinadas do `ordax-surface`**, uma para marca/fontes e outra para a demonstração Meridian, fixadas por source SHA + SHA-256 de archive e manifesto em `contracts/dev-artifact-lock.json`. Os insumos de apps/atalhos da demonstração vêm da projeção canônica do OS; nenhum gerador visual ou snapshot editável permanece no OS ou no Site. A validação CI exige a identidade de assinatura do workflow Surface para cada archive antes de montar o candidato.

```sh
python3 scripts/build.py check
python3 scripts/build.py build \
  --source-commit <SHA40_DO_SITE> \
  --dev-lock contracts/dev-artifact-lock.json \
  --public-origin https://ordax.com.br \
  --out out/site
python3 scripts/build.py verify --out out/site
python3 scripts/smoke_static.py --out out/site
python3 scripts/browser_smoke.py --out out/site --evidence out/browser-evidence
```

Em Windows, deixe `chromedriver.exe` no `PATH` e informe o navegador instalado: `python scripts/browser_smoke.py --chrome-binary "C:\Program Files\Google\Chrome\Application\chrome.exe" --out out/site --evidence out/browser-evidence`. O CI Linux continua usando a descoberta padrão de `google-chrome`.

A apresentação de planos mostra apenas **Planos em preparação — contratação indisponível**; não possui catálogo de ofertas autorizado e não exibe preços/cotas fictícios. O catálogo de downloads permanece vazio sem publicação atestada do owner. Login/Identity, pagamentos, DNS e Stable continuam bloqueados pelos gates próprios; uma prerelease Dev não é autorização de produção.

## Site SSOT, SEO e prova real de browser

`contracts/site-routes.json` é o inventário único de rotas e indexação consumido por builder, testes de localização e Chrome. O domínio canônico **não** pertence a esse contrato: a origem HTTPS é injetada pelo owner de deployment por `--public-origin` (no CI candidato: `https://ordax.com.br`). O build gera canonical/OpenGraph, `robots.txt` e `sitemap.xml` apenas no artefato; Conta/Identity/entrada Web têm `noindex`.

### Owners canônicos (SSOT)

Cada domínio tem um owner editável; não se mantém uma cópia concorrente em páginas ou testes.

| Domínio | Owner canônico | Regra |
| --- | --- | --- |
| Rotas e indexação | `contracts/site-routes.json` | Builder, auditorias e testes leem este inventário. |
| Conteúdo e estrutura do header/footer público | `contracts/public-shell.json` | Perfis compartilhados cobrem rotas; desvios ficam no contrato. `scripts/public_shell.py` valida e gera o markup. |
| Geometria e breakpoints do shell | `site/assets/site.css` | Folhas de página só podem definir tema e tipografia, nunca um segundo layout do shell. |
| Catálogo e interação de idioma | `site/i18n/catalog.js` e `site/i18n/runtime.js` | Nomes dos idiomas permanecem nativos; o runtime aplica texto e atributos acessíveis. |
| Conteúdo próprio de cada página | HTML da rota e seu CSS de tema | Conteúdo exclusivo continua junto da página, sem duplicar componentes globais. |
| Demonstração visual e marca | artefatos assinados da Surface, pinados em `contracts/dev-artifact-lock.json` | O Site consome os artefatos e não mantém snapshots editáveis paralelos. |

`/conta/` é a exceção intencional: seu shell pertence à aplicação Conta. Privacidade e Termos também são exceções de fonte, pois Identity fixa os bytes HTML; o runtime normaliza a apresentação sem editar os documentos. `tests/test_site_contract.py` protege esses limites, e `scripts/browser_smoke.py` verifica reflow, posição e visibilidade do header/footer em todas as rotas.

No celular, marca e ações de conta ficam na primeira linha. Na segunda, seletor de idioma e botão disclosure formam um grupo compacto à direita; abrir o botão revela os links comuns abaixo. O mesmo runtime atende às páginas geradas e aos documentos legais com hash fixo. O placeholder vazio de idioma não é markup editável: o runtime instala um único seletor antes dos links. A navegação usa o padrão disclosure W3C com botão nativo e `aria-expanded`/`aria-controls`, sem simular um menu ARIA; os links continuam disponíveis sem JavaScript. A posição mantém o idioma acima da dobra, e cada opção mostra seu nome nativo. Consulte o [padrão disclosure WAI-ARIA APG](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e o [exemplo de navegação disclosure](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/examples/disclosure-navigation-hybrid/).

A landing lê **um** `/assets/playground-fixture.json` de mesma origem, com falha indisponível explícita. Foi removida a segunda fixture embutida na landing (~159 KB), sem copiar fonte executável da Surface. O controlador mantém um único landmark `main` para acessibilidade.

CI de candidato: `python3 scripts/browser_smoke.py --out out/site --evidence out/browser-evidence` usa ChromeDriver pré-instalado e a matriz de viewports definida em `scripts/browser_smoke.py` para exercitar as 11 rotas. A execução guarda capturas e relatório e mantém APIs de autenticação indisponíveis em loopback. O CI precisa passar na revisão atual; provas locais não substituem auditoria WCAG completa ou auth E2E em staging.

Os snapshots históricos do OS já foram eliminados do Git do Site. Marca e Meridian são consumidas de duas prereleases Dev assinadas da Surface; não existe catálogo comercial autorizado.


## Navegação de teclado e internacionalização verificada

O CI exercita o **skip link via Tab+Enter**, leitura de nomes pela Accessibility Tree nativa do Chrome, `alt` em imagens visíveis e troca de idioma pelo seletor real com persistência. O `main#conteudo` deve ter `tabindex="-1"` para permitir foco programático; a Conta usa um handler específico que move o foco diretamente. [Browser CI teclado/a11y PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042024846) e [seletor de idioma E2E PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042154013). A prova não cobre integralmente WCAG, compatibilidade com leitores de tela nem identidade em staging.

## Contrato do pacote público Surface — sem espelho

O source editável do Site **não contém** `surface-snapshot.css`, `playground-fixture.json` ou a cópia redundante `surface-snapshot.json`. A demonstração Meridian é materializada da **prerelease Dev assinada pela Surface**, com commits Surface/OS e SHA-256 do archive e manifesto fixados em `contracts/dev-artifact-lock.json`. O build valida o download, as entradas, o grafo de origem, as 11 telas e as dependências de CSS. O snapshot histórico da demonstração do OS foi excluído. O objeto `surface` já existe dentro da fixture; o JSON independente anterior era idêntico e foi eliminado.

O CSS do renderer Meridian inclui uma fonte Inter fingerprintada. A etapa de build troca **somente no output** esse URL pelo recurso Inter existente no brand verificado e usa fingerprint dos bytes realmente publicados no CSS. Não regrava artefato de origem nem duplica a fonte no bundle.

A demo Dev usa a prerelease atestada [`meridian-dev-1ab73da4…`](https://github.com/ordaxsystems/ordax-surface/releases/tag/meridian-dev-1ab73da4aae5991273a5f4ca380d5af135ffd8d5), com origem Surface e OS verificáveis. O status `candidate-not-published` impede tratá-la como autorização de produção. A marca Dev foi publicada via [Surface #14](https://github.com/ordaxsystems/ordax-surface/pull/14); a [issue Surface #3](https://github.com/ordaxsystems/ordax-surface/issues/3) registra a entrega. Produção/distribuição comercial exigem autorização própria. Este modelo não transfere ownership de DNS, Web, OS, Account, entitlements, downloads ou deploy.

## Manifestos pinados e lock único de desenvolvimento

`contracts/dev-artifact-lock.json` é a **única fonte de pins do build Dev**, contendo somente `brand` e `surface_preview`, cada um proveniente de uma prerelease assinada do `ordax-surface`. O CI verifica SHA-256 dos archives e atestações vinculadas aos commits fixados; o builder usa `--dev-lock`, verifica o manifesto e a integridade dos artefatos extraídos. **Não há entrada `offers`**, snapshot comercial do OS nem permissão para preços ou contratação. A demonstração conserva a proveniência Surface/OS verificada.

O lock tem status `development-only-not-authorized-for-production`: **as assinaturas Dev não concedem autorização de produção, Stable ou downloads**. A publicação pública depende de aprovação separada dos owners; o Site Dev não autoriza contratos comerciais nem contas reais.

## Recursos CSS e erros de navegador

O build independente é verificado contra **todas as referências CSS** (`url(...)` local e `@import`) e falha quando uma fonte ou imagem distribuída está ausente, quando uma URL sai da origem autorizada ou atravessa diretórios. Testes unitários provocam essas falhas. O Chrome observa exceções JavaScript/rejeições não tratadas desde o início da navegação e confirma ausência de recursos estáticos com status de erro (o backend de Identity propositalmente isolado continua respondendo 503). O favicon padrão de cada página é o símbolo OrdaX publicado pelo **brand verificado**, sem criar outro asset ou ícones redundantes. [CI navegador+smoke PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731).

Os checks são regressões técnicas; não substituem prova HTTP externa, homologação Identity, auditoria completa WCAG nem autorização de produção.

## Fail-closed sem JavaScript e reflow de CSS (23/10/2026)

O `scripts/browser_smoke.py` deriva as rotas de `contracts/site-routes.json`, usa `VIEWPORTS` para tamanhos representativos e descobre as larguras de transição das folhas CSS realmente ligadas em cada rota. Testa cada fronteira em `px` e seus vizinhos no mesmo runner; mantenha breakpoints como fonte no CSS, sem uma lista paralela para a suíte. As provas especializadas também ficam nesse runner:

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

**Staging Vercel protegido (sem desabilitar autenticação):** use o transporte oficial da Vercel, com sessão local já autorizada, para provar os **bytes exatos** de todos os arquivos (inclusive PNG/JPG/WOFF2). O validador de manifesto e os gates de identidade continuam os mesmos:

```sh
vercel whoami
python3 scripts/staging_preflight.py \
  --staging-origin https://SEU-DEPLOYMENT-DEV.vercel.app \
  --transport vercel-cli \
  --scope static \
  --expected-site-commit <SHA40_DO_MESMO_CI> \
  --expected-manifest-sha256 <SHA256_DO_MANIFESTO_DO_MESMO_CI>
```

O transporte usa somente GET via `vercel curl`, não segue redirects, não imprime segredos, impõe o limite de tamanho do inventário e destrói arquivos temporários. Requer sessão da Vercel CLI **com acesso ao deployment exato**; não cria deploy, bypass público, usuário de teste, DNS ou configuração de produção. Se a CLI não tiver autorização, a prova fica **BLOCKED**. O escopo `anonymous` só passa quando `/auth/session` retorna um contrato JSON real; ele não estava disponível na primeira auditoria HTTP Dev.

Para verificar **somente os bytes do Site estático**, antes de existir gateway Identity autorizado, acrescente `--scope static` ao mesmo comando. Esta opção conserva a validação de manifesto, commit, **todo o inventário de HTML/CSS/JS/imagens**, configuração pública, catálogo vazio e hashes; pula exclusivamente `/auth/session`. O relatório distingue `scope=static-bundle-integrity-only` e `identity_mode=NOT_TESTED`. Sem a opção, o modo `anonymous` padrão continua exigindo Identity anônima real e não é afrouxado. Nenhum dos modos autoriza produção.

Substitua o domínio do exemplo pelo host de staging autorizado. Extraia o commit de `source_commit` e calcule o SHA-256 **do arquivo `public-site-manifest.json` do artefato CI confiável**, por exemplo com `sha256sum out/site/public-site-manifest.json`. Nunca obtenha esses valores apenas do próprio endpoint a ser testado, pois ele poderia falsificar a identidade. A prova lê primeiro esse manifesto publicado e exige coincidência dos bytes e do commit; percorre **todos os arquivos inventariados** e confere o SHA-256 e tamanho exatos de cada resposta. Páginas `index.html` são solicitadas pela rota de navegação pública (`/`, `/login/` etc.). Isso inclui HTML, scripts, estilos e imagens, não apenas os JSON de configuração e catálogo; o conteúdo é processado em streaming, sem armazenamento de arquivos ou dados de usuário. O comando executa **somente GET sem credenciais**, sem seguir redirecionamentos. O catálogo deve continuar vazio enquanto não houver atestação oficial. Domínios de produção, localhost e IPs diretos são rejeitados. Sem host, digest e commit confiáveis, não há prova de staging concluída.

**Registro histórico da homologação inicial (24/10/2026, não representa o build `main` atual):** o projeto Vercel independente `ordax-site-dev` já existe; a revisão `9b8885124536f96c99273d6eacabbe4f13e75775` foi reportada como deployment `READY` (ID `dpl_FzxKetVx42d6TU96dzFYtD11HopN`), com alias `ordax-site-dev.vercel.app`. O projeto está configurado com proteção Vercel Authentication, `noindex` e sem o domínio público canônico. O status `READY` comprova o build da plataforma, **não** os bytes realmente servidos ou a integração Identity. Não desproteger o deploy nem reaproveitar os projetos OS/Web para contornar esse gate; a conferência HTTP externa permanece sem resultado enquanto não houver acesso autenticado autorizado.

Os testes `tests/test_staging_preflight.py` são executados no CI **sem rede**; `SITE_STAGING_PREFLIGHT=PASS` identifica explicitamente o escopo validado (`static` ou `anonymous`), mas **não** comprova autenticação, recuperação de senha, faturamento, publicação de releases ou autorização de produção. Os gates completos continuam em `docs/HANDOFF.md`, `docs/ACCESSIBILITY-GATES.md` e nas PRs dos owners externos.

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
