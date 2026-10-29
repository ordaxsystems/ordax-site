# Auditoria estrutural — OrdaX Site

**Escopo:** arquitetura e artefatos do cutover de desenvolvimento, verificados após [Site #10](https://github.com/ordaxsystems/ordax-site/pull/10) e [OS #2238](https://github.com/ordaxsystems/ordax-os/pull/2238). A auditoria de 23–24/10/2026 está [arquivada como evidência histórica](history/SITE-AUDIT-2026-10-24.md). Este documento registra somente o diagnóstico operacional vigente.

## Resultado da migração Dev

| Verificação | Estado |
| --- | --- |
| Código público e build pertencem a `ordax-site` | Concluído |
| Apresentação pública duplicada em `ordax-os/sites/public` | Eliminada |
| Tokens, imagem, símbolo e fonte da marca | Obtidos de prerelease Dev assinada da Surface |
| Fixture/CSS Meridian | Obtidos de prerelease Dev assinada da Surface |
| Snapshots `artifacts/brand`, `artifacts/surface-preview`, `artifacts/offers` | Eliminados do Git do Site |
| `contracts/dev-artifact-lock.json` | Único pin Dev dos dois artefatos de owner |
| Apps/atalhos na demo | Projeção canônica do OS, sem outro catálogo mantido no Site |
| Publicação de downloads / ofertas comerciais | Bloqueada; catálogo vazio e aviso sem contratação |
| CI de Site / integração de login Web e portal no OS | Aprovados na revisão do cutover |

O build consome recursos assinados; o Site não recompila nem importa fontes executáveis da Surface. `scripts/build.py` e `scripts/surface_release.py` / `scripts/brand_release.py` verificam a procedência e os digests antes de colocar bytes no bundle; o workflow Site verifica as atestações dos dois publicadores.

## Limites de validação

O Chrome em loopback verifica onze rotas, navegação, responsividade, segurança de recursos, estados sem JavaScript, testes parciais de acessibilidade e rejeições de Identity/releases falsificados. **Não comprova** conformidade WCAG integral, gateway Identity real, publicação externa em staging, pagamentos, domínio ou autorização de produção.

Gates remanescentes e owner de cada integração: [HANDOFF.md](HANDOFF.md). Comandos atuais: [README](../README.md). Não restaurar antigos contratos `migration-artifact-lock.json` ou artefatos OS para contornar falhas.

## Checklist SSOT e responsividade — 29/10/2026

- [x] `contracts/site-routes.json` permanece como inventário único de rotas/indexabilidade. `contracts/public-shell.json` define conteúdo, rótulos, ações e rodapé do shell público gerado; `scripts/public_shell.py` valida e materializa esse contrato.
- [x] Cada domínio tem um owner: `site/assets/site.css` define geometria e breakpoints do shell; `site/i18n/runtime.js` instala comportamento; `site/i18n/catalog.js` fornece rótulos/traduções; `contracts/site-routes.json` lista rotas. Os rótulos compactos de ações também pertencem ao contrato e ao catálogo, não a cópias por página ou texto em CSS.
- [x] Em celular, marca, ações de conta e botão do menu ficam juntos na primeira faixa. Entrar/Cadastrar formam um grupo visual único sem misturar destinos; o cadastro usa rótulo curto do contrato. O seletor de idioma fica dentro do painel aberto, identificado e antes dos links, sem uma faixa isolada no cabeçalho fechado.
- [x] A estrutura mobile segue botão disclosure nativo com links comuns. Chrome confirma abertura, `aria-expanded`/`aria-controls`, Escape e retorno de foco. O seletor mantém os nomes nativos “Português” e “English”, sinaliza `lang` em cada opção, acompanha o idioma ativo e funciona dentro do painel. Sem JavaScript, os links permanecem visíveis.
- [x] O runner deriva os pontos de quebra das folhas realmente carregadas por rota (incluindo `@import`) e verifica cada breakpoint e os pixels vizinhos, entre 280 e 2560 px. Foram aprovados 281 pares rota/largura, incluindo a transição do header para duas linhas até 1160 px. CSS da Surface é observado para cobertura, sem alterações.
- [x] Header, navegação, footer e ações foram revistos em onze rotas. `/conta/` preserva seu shell de aplicação; Privacidade/Termos mantêm seus bytes fixados por Identity, com normalização visual pelo runtime. O rodapé público tem owner/estrutura compartilhados; o footer da Conta permanece com o owner da aplicação. Alvos touch estruturais preservam pelo menos 44×44 px.
- [x] Navegação da Conta continua em SSOT: `sections[]` de `site/assets/account-portal.js` é a fonte dos grupos laterais, atalhos móveis e itens em “Mais”; traduções e geometria têm owners únicos. A suíte impede listas paralelas e confirma encaixe dos cinco alvos em PT-BR/en-US.
- [x] Chrome passou 11 rotas × 9 viewports (99 casos), 281 casos de breakpoint, 308 combinações bilíngues (11 × 14 × 2), 77 cenários touch, 22 reflows, 11 textos a 200%, 22 espaçamentos, seis estados sem JavaScript e provas de catálogo/Identity/fragments, sem falhas. Os dez painéis de navegação pública cabem na viewport.
- [x] Contrato/build (`build check`, `build verify`, smoke estático), 76 testes Python e localização com 1.716 mensagens/11 rotas/2 idiomas passaram. O runner mediu 1.798 amostras de texto sobre fundos sólidos: zero falhas e zero valores sólidos não reconhecidos; 189 superfícies com imagem/gradiente foram excluídas da medição automatizada.
- [x] Capturas das onze rotas a 280 px e dos onze rodapés a 390 px foram inspecionadas; também foram vistos header aberto/fechado, ações agrupadas, inglês, Conta e páginas legais. A geometria do painel aberto cabe na viewport após descontar scrollbar. O bundle usa `source_commit=c70d0b611c3d7b2b96b7629db73b301dccf7cd66` e manifesto SHA-256 `7903F00E8D3439D2850DF5BDAD3D2E85469115E421D29B749882DB354EC0DD08`. Relatório e 193 capturas finais: `work/browser-evidence-mobile-shell-ssot-20261029-final4/`; prévia local: `http://127.0.0.1:4218/termos/`.
- [ ] Zoom nativo de 200%/400%, ampliação nativa somente de texto, leitor de tela e contraste completo em fundos compostos permanecem gates manuais. O checklist não declara conformidade WCAG integral; ver [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).

Referências para a decisão do seletor mobile: [NN/g — Language Switching on E-Commerce Sites](https://www.nngroup.com/articles/language-switching-ecommerce/), [WAI-ARIA APG — Disclosure](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e [WAI/W3C — Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow).

Esta verificação é local e não comprova Identity em staging, autorização de produção nem publicação de um deployment. O build está pronto para revisão no branch `codex/site-responsive-polish`; a publicação de produção não faz parte desta atualização.

## Atualização de legibilidade mobile — Licenças (29/10/2026)

- A captura de `/licencas/` a 280 px mostrava o título anterior em sete linhas. O heading foi reduzido para “Transparência por release”; a explicação sobre inventários, componentes e licenças permanece no conteúdo da página. O catálogo i18n atualiza a mesma frase em inglês.
- Candidato `source_commit=e67923e6cf8398ad148eeaa3a64643ea0487e816`; SHA-256 do manifesto `B60F1BE92A215FE140623C6DAD4D847E52C242A60D5566F326AB328682725665`. `build.py check`, 76 testes Python, localização (1.716 mensagens, 11 rotas, 2 idiomas), `build.py verify` e smoke estático (11 rotas) passaram. A prévia em `http://127.0.0.1:4219/licencas/` respondeu HTTP 200; inspeção visual e árvore de acessibilidade confirmaram o heading novo.
- A matriz completa de navegador ainda se refere ao candidato `c70d0b6…` acima. Nesta máquina, `scripts/browser_smoke.py` não iniciou por falta de ChromeDriver; não atribuir aquela matriz ao commit `e67923e`. O CI de navegador executa em `main` ou em pull request.
- Não houve deploy de produção.

## Atualização de layout SSOT — 29/10/2026

- `site/assets/portal.css` agora é o único owner da geometria e tipografia de `.page-shell`, `.page-hero`, `.auth-shell` e `.auth-copy`. `site/assets/site.css` não redefine esses componentes; isso remove a disputa entre os breakpoints de 1050 px do shell geral e 1000 px do portal.
- A imagem fornecida mostrava a prévia antiga servida em `4209` (`site-preview-responsive-final-c6ed577`). A prévia foi apontada para o candidato atual. Em 390 px e 280 px, a marca, as ações de conta agrupadas e o botão do menu ocupam uma linha; idioma aparece no disclosure aberto, antes dos links. Entrar e cadastrar seguem como links distintos para login e registro, dentro do mesmo grupo visual.
- Candidato verificado: `source_commit=31b01e0d9ca7e2ef273c5365e0c2d4a22a54ad31`; SHA-256 do manifesto `A7D054481E3BAC03C53C845B3AA9AC87A9AC6974805ECB3EEB8B15C46010BFB6`.
- `build.py check`, 77 testes Python, localização (1.716 mensagens, 11 rotas e 2 idiomas), `build.py verify` e smoke estático (11 rotas) passaram. Chrome aprovou 11 rotas × 9 viewports (99 casos), 281 verificações de breakpoint, 308 checagens bilíngues, 77 casos touch, 22 reflows, 11 testes de texto a 200%, 22 testes de espaçamento e 6 casos sem JavaScript, sem falhas. Relatório e 132 capturas: `work/browser-evidence-header-layout-ssot-20261029/`.
- Prévia local atual: `http://127.0.0.1:4209/termos/`. Esta checagem é de candidato local; não houve deploy de produção.

## Hierarquia das ações da header — 29/10/2026

- A imagem seguinte do preview motivou simplificar o grupo de conta: “Entrar” é link secundário e “Criar conta” é a ação principal. Os dois destinos continuam explícitos e acessíveis, mas sem moldura dupla. No mobile, marca, as duas ações e o menu mantêm uma única linha; em 280 px os alvos continuam com pelo menos 44 px de altura.
- O idioma permanece dentro do painel acessível aberto pelo menu, junto dos links de navegação. Isso evita uma linha isolada para o seletor e mantém o idioma alcançável no mobile.
- Candidato verificado: `source_commit=1d89509838e30b03601ce3a9602688756a8d11ec`; SHA-256 do manifesto `BCC8880E0461B18865804EFAD131F9862E68C5E24C6C59C13EF41D8EECE30137`. `build.py check`, 77 testes Python, localização (1.716 mensagens, 11 rotas e 2 idiomas), `build.py verify` e smoke estático (11 rotas) passaram. Chrome passou nas 11 rotas × 9 viewports (99 casos), 281 verificações de breakpoint, 308 checagens bilíngues, 77 casos touch, 22 reflows, 11 testes de texto a 200%, 22 testes de espaçamento e 6 casos sem JavaScript, sem falhas. Relatório e 132 capturas: `work/browser-evidence-header-auth-final-20261029/`.
- Preview do candidato: `http://127.0.0.1:4210/licencas/`. É uma verificação local, sem deploy de produção. Os gates manuais de acessibilidade listados em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md) continuam pendentes.

## Header compartilhado e ritmo inicial do conteúdo — 29/10/2026

- `contracts/public-shell.json` continua sendo a fonte de conteúdo e links do shell; `site/i18n/runtime.js` instala o seletor e o disclosure; `site/assets/site.css` é o único owner da geometria responsiva em todas as páginas públicas. Acima de 1160 px, marca, ações, idioma e navegação ficam na faixa horizontal. Em 1160 px e abaixo, marca, ações de conta e menu permanecem na mesma faixa; idioma e links ficam no disclosure. A distinção entre Entrar e Cadastrar é mantida porque são destinos diferentes, com hierarquia visual secundária/principal.
- `site/assets/site.css` define `--public-content-top-space: clamp(32px, 4.4vw, 58px)`. `portal.css` aplica o mesmo ritmo a Licenças, Privacidade e Termos e remove o padding superior duplicado do hero. A prova mediu o início do conteúdo a 58 px em 1440 px, 45 px em 1024 px, 34 px em 768 px e 32 px em 390 px. A imagem fornecida mostrava a prévia antiga em `4210`; a prévia final está em `http://127.0.0.1:4221/licencas/`.
- `/conta/` mantém sua barra de aplicação como owner separado. As páginas públicas restantes usam o shell compartilhado, inclusive Privacidade/Termos após normalização no runtime; os documentos legais continuam byte-idênticos.
- Candidato `source_commit=d485b4b3d7a0408b09aac52b6374edd746067938`; SHA-256 do manifesto público `0BA3F9AC6A0FBC6EF8C59C3A32FFB58C9C7DA6AD0FFB73A3E3E86C8E18F10D07`. `build.py check` (33 arquivos), 78 testes Python, localização (1.716 mensagens, 11 rotas e 2 idiomas), `build.py verify` e smoke estático (11 rotas) passaram. Chrome aprovou 11 rotas × 9 viewports (99 casos), 281 verificações de breakpoint, 308 combinações bilíngues, 77 touch, 22 reflows, 11 textos a 200%, 22 testes de espaçamento e 6 estados sem JavaScript — zero falhas. Evidências e capturas em `work/browser-evidence-header-one-row-20261029/`.
- O teste do novo gutter não encontrou clipping nem overflow nos 22 casos de espaçamento. Zoom nativo, ampliação somente de texto, leitor de tela e contraste completo em fundos compostos permanecem como gates manuais; ver [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md). Não houve deploy de produção.

## Ordem mobile das páginas de identidade — 29/10/2026

- Removi a reordenação visual global do shell de identidade. Login, cadastro e recuperação continuam exibindo o cartão primeiro pela própria ordem do HTML; `/web/` mantém a leitura de introdução, acesso e detalhes, sem divergência entre DOM, teclado e ordem visual.
- Em `/web/`, a introdução curta agora precede o cartão; os benefícios e a nota de segurança vêm depois. No desktop, o CSS próprio de Web mantém a composição em duas colunas com o cartão à direita; em 390 px, o cartão já aparece após o contexto breve, sem exigir rolagem pela lista completa.
- Candidato `source_commit=779a5058826d5b2022182807652cc4469672d310`; SHA-256 do manifesto `B00CD86684C4D3BF04F54FCC948BC72E7F1FED88EF05B2FF6BEE3487E33DC08A`.
- `build.py check` (33 arquivos), 79 testes Python, localização (1.716 mensagens, 11 rotas e 2 idiomas), `build.py verify` e smoke estático (11 rotas) passaram. Chrome passou 11 rotas × 9 viewports (99 casos), 282 verificações de breakpoint, 308 verificações bilíngues, 77 touch, 22 reflows, 11 ampliações simuladas de texto a 200%, 22 verificações de espaçamento e seis estados sem JavaScript; também passaram as provas de catálogo/Identity/JSON, sem falhas.
- Capturas de `/web/` inspecionadas em 390, 768 e 1024 px. Relatório e evidências: `work/browser-evidence-web-order-779a505/`; preview local atualizado: `http://127.0.0.1:4223/web/`.
- Zoom nativo, ampliação nativa somente de texto, leitores de tela e contraste completo em fundos compostos continuam gates manuais. Não houve deploy de produção.

## Revalidação do cabeçalho e ritmo mobile — 29/10/2026

- A captura em `4210` apontava para um bundle anterior. A revisão atual usa `site/assets/site.css` como único owner da geometria do cabeçalho e do token `--public-content-top-space`; no desktop a 1440 px, marca, ações, idioma e navegação ocupam uma faixa. Em telas estreitas, marca, ações e menu permanecem alinhados; idioma e links são revelados no disclosure.
- A inspeção visual de `/licencas/` a 1440 e 390 px confirma que o conteúdo começa com ritmo consistente depois do cabeçalho, sem o grande vazio da captura anterior. A evidência Chrome mede todos os breakpoints e também verifica reflow nas onze rotas.
- Em `/download/`, o hero mobile agora usa `--public-page-gutter`, reduz a área vertical reservada para arte e alinha a legenda ao mesmo gutter. `tests/test_site_contract.py` protege o gutter compartilhado e a altura compacta contra regressões.
- Candidato `source_commit=1dd70972d76a3d2d8684377a645cfb7b7d74bcf5`; manifesto SHA-256 `CF693EAE7133BFA5ABEA628631E8F51167AFF1A1A30D36798DADCA38532E33DA`. Build estrutural, 79 testes Python, localização (1.716 mensagens, 11 rotas, dois idiomas), verify e smoke estático passaram. Chrome aprovou 99 cenários rota/viewports, 282 verificações de breakpoint, 308 combinações localizadas, 77 touch, 22 reflows, 11 ampliações simuladas de texto a 200%, 22 verificações de espaçamento e os estados sem JavaScript; zero falhas.
- Capturas revisadas: `work/browser-evidence-shell-spacing-1dd7097/` (194 arquivos). Preview local em `http://127.0.0.1:4225/licencas/`. O checklist não representa certificação WCAG integral; os gates manuais continuam descritos em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md). Não houve deploy de produção.
