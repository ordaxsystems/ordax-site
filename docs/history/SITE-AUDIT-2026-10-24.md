> **Arquivo histórico imutável — não é documentação operacional.** Este texto registra estados intermediários da extração em 23–24/10/2026. Paths `artifacts/*`, `migration-artifact-lock.json`, `--migration-lock`, PRs draft, snapshots OS e alegações de gates pendentes podem ter deixado de existir. Para estado atual, use [README](../../README.md), [handoff](../HANDOFF.md) e [contrato Dev](../../contracts/dev-artifact-lock.json).

---

> **Atualização Dev 2026-10-24:** os achados de snapshots abaixo são históricos. `ordax-site` não mantém mais pacotes OS de demo, marca ou ofertas; o source visual e as duas releases Dev assinadas pertencem à Surface. O estado comercial é não disponível. Consulte `contracts/dev-artifact-lock.json` e o `README.md` atual para execução.

# Auditoria de extração — baseline 2026-10-23

## Inventário e proveniência
- Origem: `ordaxsystems/ordax-os`, branch `main`, revisão observada `70b0f7eb5d5085be0d4f176f5232def37c7a2a24`.
- Árvore original da apresentação: `sites/public/`, Git tree `bc516a313eaa78a83652237a6d9d0cdbf295d28b` (36 blobs de arquivo, com 11 rotas HTML).
- Implementação original: `tools/public-site/`, incluindo build, geradores Meridian, validação legal, catálogo público, deploy e smoke.
- Artefato novo: `site/`; todo HTML, JS, CSS e i18n copiado de origem sem reconstrução por IA; Todos os seis PNG/JPEG do site copiados preservando **o mesmo blob SHA Git**.
- **Imagens originais transferidas e comprovadas**: `site/assets/aurora-titanium.png` (Git blob `e4574877f57a66574d001ebcfbfc8718782a2c23`, 2016680 bytes) e `site/assets/download-hero.png` (Git blob `7c23ed6070890d81a11474108f0a52a0965ce501`, 1629858 bytes). Um workflow temporário fez checkout do commit OS exato e verificou `git hash-object` antes de gravar ambas; [execução aprovada](https://github.com/ordaxsystems/ordax-site/actions/runs/40038857924). O workflow foi retirado depois da importação, sem legado permanente.
- O snapshot `artifacts/surface-preview/os-migration-70b0f7eb` guarda apenas CSS e fixture; `surface-snapshot.json` era conteúdo idêntico a `fixture.surface` e foi eliminado. São artefatos **gerados** de demonstração, nunca imports dinâmicos. A procedência original deve permanecer identificável, e atualizações futuras devem consumir artefatos publicados pelo owner da Surface.
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


## Navegação acessível real — resolução de causa raiz (2026-10-23)
O teste estático só confirmava a existência de `href="#conteudo"`. A primeira prova W3C com teclado revelou ausência de foco em cinco `main` informativos, corrigida no próprio HTML por `tabindex="-1"`. A Conta possui roteamento de hash próprio e intencionalmente faz `preventDefault()` e `focus()`, por isso a asserção reconhece o foco real como sucesso, não exige mudança desnecessária de URL. O CSS `.skip-link` tem transição de 180 ms; a prova mede a visibilidade após o tempo de animação para evitar falso negativo. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042024846).

Foi adicionada prova de nomenclatura na árvore Chrome Accessibility e `alt` das imagens visíveis. O seletor local de idioma passou a ser exercitado na UI real com ida/volta PT-BR/en-US e persistência. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40042154013). Ainda sem alegação de conformidade WCAG completa.

## Consolidação de insumos da Surface — sem duplicação (2026-10-23/24)

A auditoria de `site/assets/surface-snapshot.json` (154.860 bytes), `playground-fixture.json` (159.840 bytes) e `surface-snapshot.css` (246.748 bytes) mostrou que o JSON snapshot **é literalmente igual como objeto JSON a** `fixture.surface`. Evitou-se redistribuí-lo duas vezes. Os dois recursos ainda necessários foram movidos por **mesmo blob SHA Git** para `artifacts/surface-preview/os-migration-70b0f7eb/assets/`, fora da árvore editável `site/`. CSS bruto: `SHA256=0465205d606ebe3b33eba2aaa689c52f1d2d9b99ee79620f72eb06d9113448da`; fixture: `SHA256=c4c020e0cc4858a4fd011ff2c006bdfb330f1d0478fd7c74bbcb851692fead0c`. Manifesto pinado em CI: `d7142242a5a4ff38b71cfcc952123b48a34e8bd643052b8143de9b5d36fc0cc3`.

O builder valida manifesto externo, Git blob, SHA-256, tamanhos, esquema e compatibilidade de CSS/fixture antes de produzir o site. Verificação negativa rejeita manifesto alterado, fixture adulterada ou status de publicação falsamente oficial. A referência herdada à fonte `/assets/inter-latin-wght-normal-Dx4kXJAl.woff2` foi identificada como dependência órfã; no **bundle final**, a referência aponta à fonte Inter do artifact `brand` verificado, e o query hash do CSS passa a refletir o conteúdo servido. O CSS bruto de migração permanece intacto.

**Gate ainda bloqueado:** `ordax-surface/main` não possui release pública do brand/demo. Pedido de publicação oficial, proveniência e redução de snapshots espelhados em [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3). O pacote de migração não é prova de publicação pelo owner.

## Trust gap fechado: pins de todos os insumos e download fail-closed (2026-10-23/24)

Auditoria identificou inconsistência: o Surface preview exigia hash externo do manifesto, enquanto `stage_brand` e `load_reference_offers` confiavam em seus próprios hashes internos sem um pin independente. Isso permitiria substituir o manifesto inteiro e recalcular hashes internos sem bloquear o consumo. O builder agora exige pins SHA-256 **externos ao respectivo manifesto** para os três tipos de artefato, testa adulteração de conteúdo, mudança de status/compra e entradas inválidas, e compara a revisão OS entre eles. Os pins estão em **um** arquivo: `contracts/migration-artifact-lock.json` (`development-only-not-authorized-for-production`), sem espelhos no workflow.

Outra lacuna: o parâmetro `--publications` aceitava flags como `public_authorized=true` em um JSON escolhido localmente, insuficientes para estabelecer autorização do publicador. Entrada **desabilitada em build** até contrato oficial com origem autenticada, release imutável e integridade verificável. O gerador puro permanece para testes offline de formato, mas nenhuma entrada arbitrária pode ativar downloads no artefato distribuído.

Esses controles asseguram consistência contra alteração acidental ou adulteração sem atualizar o lock; **não** constituem atestação criptográfica de publisher nem validação de um ambiente externo de produção.

## Auditoria de assets realmente servidos e exceções JS (2026-10-23/24)

O CSS distribuído não estava sendo analisado de ponta a ponta: um bundler legado já havia deixado um caminho de fonte órfã dentro da demo. Foi adicionada inspeção de `url(...)` em **todos os CSS empacotados** — tokens/brand, Surface preview e estilos Site — exigindo arquivo existente e same-origin, com tratamento correto para imagens SVG em `data:image/` que contêm aspas internas. São proibidos CSS `@import`, URLs remotas e travessias. O smoke informa a quantidade de dependências válidas verificadas. Testes negativos rejeitam imagem ausente, URL remota e caminhos com `../`.

No navegador, a prova antiga verificava layout e presença de recursos, mas não capturava exceções JS nem status 4xx/5xx de assets após carregamento. Agora é instalado observador antes de executar qualquer script (`Page.addScriptToEvaluateOnNewDocument`), cobrindo `error`, `unhandledrejection`, erro de carregamento e Resource Timing HTTP. O endpoint de autenticação intencionalmente 503 é excluído da classe de recursos estáticos.

A primeira rodada rigorosa encontrou erro HTTP na visita inicial da landing; páginas sem favicon explícito deixavam o Chrome consultar `/favicon.ico` inexistente. O gerador HTML passou a associar `/assets/ordax-symbol.png` do mesmo brand verificado (sem duplicar tags). A prova integrada passou em [CI](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731), com as 11 rotas e 3 resoluções. Não foi alterada nenhuma publicação em produção.

## Diagnóstico de 400% reflow — causa raiz e solução (2026-10-23)

A suite passou de 33 para 33+22 cenários: os 22 complementares usam `Emulation.setDeviceMetricsOverride` do Chrome, sem `mobile`, para 640/320 px de área útil de layout, correspondentes à largura de 1280 px dividida por 2/4. No primeiro ciclo surgiram **quatro** falhas de rolagem horizontal em Download, Licenças, Privacidade e Termos, todas a 320 px. A instrumentação identificou a causa concreta: `.public-locale-switcher` injetado dinamicamente em `.site-nav` ocupava 193 px e terminava fora do viewport (bordas direitas acima de 320 px). Foi corrigido em `site/assets/site.css` com wrapping de navegação e linha exclusiva para a seleção de idioma nas quatro páginas a 430 px ou menos. Não foi aplicado corte global de overflow. [Evidência Chrome PASS após correção](https://github.com/ordaxsystems/ordax-site/actions/runs/40051704031).

A suite ganhou ainda 6 provas adicionais sem JavaScript: o carregamento é feito com `Emulation.setScriptExecutionDisabled=true` antes da navegação, e a página estática é inspecionada em seguida. Os avisos `noscript` ficam visíveis; nenhum botão de auth/form credencial, identidade verificada ou lançamento Web pode ser habilitado. [Evidência PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051439195). Nenhum servidor de identidade foi iniciado; APIs continuam 503 no runner.

Escopo **parcial** da WCAG: valida reflow em CSS viewports estreitos e estados no-JS, mas **não** prova zoom real do navegador, ampliação isolada do tamanho do texto, contraste visual integral ou uso por leitor de tela.

## Contraste calculável em Chrome — gate parcial (2026-10-23/24)

A prova E2E usa `solid_surface_contrast_probe()` sobre elementos de texto e navegação visíveis. Compara **luminância linear sRGB** entre texto e fundo plano composto, exigindo **4,5:1** em texto comum e **3:1** em texto grande conforme os limiares WCAG 2.x. Não contabiliza como aprovação fundos em imagem/gradiente, transparência por camadas ou estilos impossíveis de identificar; o relatório JSON preserva `unchecked`, `measured` e cada falha com cores e proporção. Fora da landing em gradiente, as rotas devem ter amostras de fundo plano efetivamente medidas.

O primeiro CI encontrou **cinco telas de identidade** com problemas de contraste: o link de pulo herdava cor escura sobre fundo escuro, e textos secundários em painéis claros tinham proporções de aproximadamente **4,31–4,37:1**, abaixo de 4,5. Ajustado apenas em `site/assets/account.css`, sem alterar as cores canônicas da Surface: `.account-ui .skip-link` recupera contraste e `--account-muted` faz mescla contextual com a tinta Meridian. O portal de Conta passou a incluir a topbar/breadcrumb na amostra. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40053856203).

**Não atesta WCAG global.** Contraste de gradientes/fotos, pseudoelementos, estados hover/focus específicos, leitores de tela, ampliação somente de texto/zoom real e fluxos autenticados de staging continuam por validar.

## Auditoria de títulos e preferência do usuário para movimento (2026-10-23)

O HTML da Conta tinha `<main>` e links skip funcionais, mas **nenhum `<h1>`** quando o JS estivesse inativo ou antes da montagem de dados. Essa omissão fora tolerada pelo smoke estático porque ele abria exceção explícita para `account-content` vazio. O fallback foi implementado **no `#account-session`**, região que o controlador já substitui ao montar uma sessão, de modo que o `h1` estático não se soma ao título gerado dinamicamente. A exceção do smoke foi removida. O Chrome também passou a checar título principal nas 11 rotas; os subtítulos dentro da demonstração Surface são excluídos porque pertencem a uma UI embutida e não ao documento institucional.

Na política de movimento, o CSS comum usava `scroll-behavior:smooth` e transições no link de pulo e botões sem tratar universalmente a preferência por menos animação; CSS de regiões especializadas possuía regras específicas. A folha **do Site** agora respeita `prefers-reduced-motion:reduce`. O Chrome injeta a preferência de mídia via DevTools, mede os estilos finais em componentes representativos e verifica o resultado de cada rota, sem introduzir dependência ou copiar tokens de Surface. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40054611865).

**Limite honesto:** automação de headings e CSS/mídia não é substituto para leitores de tela, auditoria WCAG completa ou teste de texto ampliado.
