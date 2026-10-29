# OrdaX Site — handoff de desenvolvimento

**Estado em 24/10/2026: migração Dev de código, apresentação e artefatos visuais concluída.** Este documento é a referência de estado, não uma nova camada de configuração. O código e os comandos válidos estão no [README](../README.md); os hashes, commits e a origem dos dois pacotes no único [lock Dev](../contracts/dev-artifact-lock.json).

## Ajuste de leitura — 2026-10-29

Na Minha Conta, tablets com ponteiro de toque (641–1180px) usam a barra inferior com nomes visíveis para Resumo, Assinatura, Consumo, Segurança e Mais. Isso substitui a faixa lateral de ícones compacta nesse perfil de entrada; teclado/leitores mantêm os nomes acessíveis e o menu Mais abre as demais seções.

O cabeçalho público mobile agora usa uma faixa: marca, ações de conta e botão de navegação. O painel aberto mostra primeiro o seletor de idioma com o rótulo “Idioma/Language” e depois os links; não há seletor solto numa linha própria. Os nomes das opções continuam nativos (“Português” e “English”). O botão disclosure sincroniza `aria-expanded`/`aria-controls`, fecha com Escape e devolve o foco; sem JavaScript, os links permanecem visíveis.

As páginas de Privacidade e Termos agora limitam o texto corrido a 76ch e usam corpo de 15px com entrelinha 1,8; os textos do painel de licenças, dos estados informativos e das orientações de download também ganharam tamanho e entrelinha. Os hashes SHA-256 e tamanhos em bytes dos arquivos publicados aparecem em 12px, com quebra dos hashes em telas estreitas. Login, cadastro, recuperação e Conta Web receberam texto mais legível nos estados de identidade, avisos, concordância e links de suporte. Em telas estreitas, a navegação e os seletores de idioma das páginas públicas usam texto de 12px; os rodapés públicos usam 12px. Os principais links de suporte e rodapé têm alvos mínimos de 44px. A página inicial e a página de download ampliam os alvos dos links de apoio para 44px em dispositivos de toque; o botão para fechar a demonstração ampliada da página inicial também mede ao menos 44px no celular. Minha Conta mantém botões, abas, breadcrumb, links de ação e o resumo de histórico com alvo mínimo de 44px no celular; status, notas, atalhos, contagens, legendas e rótulos operacionais da Conta usam 12px. Licenças, Privacidade e Termos nomeiam a navegação do rodapé, identificam a rota atual e a destacam visualmente. O conteúdo legal e os contratos de serviço não foram alterados. Como a Conta confere o SHA-256 dos bytes HTML integrais de Privacidade e Termos, alterações de marcação nessas páginas exigem republicar a referência de documento pelo owner de Identity antes de habilitar o consentimento/cadastro; até essa atualização, a validação permanece fechada.

Em dispositivos com ponteiro de toque, os links de navegação do cabeçalho e rodapé, atalhos dos formulários de identidade, controles principais da Conta e ações de integridade/download também mantêm alvo mínimo de 44px, mesmo acima dos breakpoints móveis.

Entre 761 e 1160px, o cabeçalho conserva a composição de duas linhas, com ações junto à marca e navegação fluida na linha seguinte. Até 760px, a lista de links é controlada pelo disclosure; ao abrir o painel, o seletor de idioma aparece primeiro, com rótulo visível, antes dos links. O estado fechado mantém marca, ações e botão do menu juntos, sem uma faixa isolada para idioma.

As versões em inglês de Termos e Privacidade agora traduzem todos os títulos de seção, a data de vigência e o rótulo de contato que ainda apareciam em português. O catálogo i18n está referenciado por fingerprint nas onze rotas para entregar as novas traduções após o deploy. O texto legal em português não foi alterado.

Na revisão atual do shell, o contrato `contracts/public-shell.json` continua como owner do conteúdo e das exceções de cabeçalho/rodapé; `site/assets/site.css` contém a geometria e os breakpoints do header mobile; `site/i18n/runtime.js` mantém a interação e `site/i18n/catalog.js` mantém os rótulos. `scripts/public_shell.py` não gera um placeholder vazio para o idioma: o runtime insere um seletor antes dos links e compartilha a mesma melhoria entre shells gerados e HTML legal com hash fixo. O runner Chrome deriva os breakpoints das folhas CSS vinculadas a cada rota, sem segunda lista de transições, e exige que os elementos do cabeçalho realmente apareçam dentro da viewport. O checklist atualizado cobre 11 rotas × nove larguras (a partir de 280 px), 281 casos rota/largura de breakpoint e 11 rotas × 14 larguras × dois idiomas; os resultados estão em [AUDIT.md](AUDIT.md).

Em 29/10, a cópia do estado vazio de downloads foi corrigida no owner i18n: a interface não afirma mais que o catálogo está ativo nem que releases falharam gates de publicação; informa que downloads aparecem quando uma publicação for autorizada. Também foram aumentados para 24×24 px quatro links de desktop antes abaixo do mínimo AA, mantendo 44×44 px em ponteiro de toque. A suíte protege esse mínimo em todas as rotas e exige que as regiões do cabeçalho estejam realmente visíveis dentro da viewport. **Revisão anterior da Conta**: candidato `168bd646aadcec4826eb2e3087123de63fe92916` (manifesto SHA-256 `357F4C011D6A4459FC475813C9F62A0EADC5AC8B5F860109ADA5B45A6631A1B6`), 76 testes Python, localização com 1.715 mensagens, Chrome (99 viewports, 251 breakpoints CSS, 77 touch e 308 combinações bilíngues), sem falhas. Evidências em `work/browser-evidence-account-mobile-shell-168bd64/`. Os gates manuais e de Identity/staging/produção permanecem conforme [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).

## Propriedade e fronteiras

- **`ordax-site`**: HTML/CSS/JS público, onze rotas, apresentação de login/Conta, SEO, i18n, build e testes independentes.
- **`ordax-surface`**: tokens, símbolo, imagem, fonte e demonstração Meridian. Publica os dois arquivos assinados de **desenvolvimento**, sem duplicar fontes no Site.
- **`ordax-os`**: projeção canônica de aplicativos/atalhos da demonstração, integração do portal e login Web, serviços e contratos do OS. O pin do Site pertence a [`docs/contracts/public-site-source.json`](https://github.com/ordaxsystems/ordax-os/blob/main/docs/contracts/public-site-source.json) e tem `production_deployment_activated=false`.
- **Owners de Identity, releases e comércio**: autorizam separadamente autenticação, downloads, planos, cobrança e distribuição. O Site não implementa esses backends.

Nenhum dos três snapshots antigos do OS (brand, preview ou ofertas) permanece em `ordax-site/main`. O pacote de marca e a demo vêm de duas **prereleases Dev do owner Surface** com assinatura verificável e SHA-256 externo. A mensagem comercial é apenas *Planos em preparação — contratação indisponível*; não há catálogo oficial de downloads.

## Evidências integradas

| Responsabilidade | Evidência |
| --- | --- |
| Extração do Site e remoção do portal antigo | [Site #1](https://github.com/ordaxsystems/ordax-site/pull/1), [OS #2229](https://github.com/ordaxsystems/ordax-os/pull/2229) |
| Projeção canônica de apps/atalhos OS | [OS #2234](https://github.com/ordaxsystems/ordax-os/pull/2234) |
| Demonstração Meridian Dev assinada | [Surface #13](https://github.com/ordaxsystems/ordax-surface/pull/13) |
| Marca Dev assinada | [Surface #14](https://github.com/ordaxsystems/ordax-surface/pull/14) |
| Site consome Meridian e remove snapshot OS | [Site #7](https://github.com/ordaxsystems/ordax-site/pull/7) |
| Eliminação de ofertas históricas, sem compra simulada | [Site #9](https://github.com/ordaxsystems/ordax-site/pull/9) |
| Site consome a marca Surface e elimina arquivos históricos | [Site #10](https://github.com/ordaxsystems/ordax-site/pull/10) |
| OS utiliza o Site com os dois artefatos Surface assinados | [OS #2238](https://github.com/ordaxsystems/ordax-os/pull/2238) — cinco workflows aprovados |

A revisão do Site integrada no OS nesta entrega é `8f8e0b33d9418a2ca6d256630d440ca43e4abe47`. Para revisões futuras, **não copie esse hash**: leia o contrato canônico do OS e o lock atual do Site.

## Prova externa do Site Dev — 26/10/2026

O Site Dev `ordax-site-dev` recebeu o **mesmo commit aprovado no CI**: `8ad8037ce2a2d600e621dec5aba2e50f878c3de9` (GitHub Actions `40141425475`). Foi realizada prova HTTPS de leitura do manifesto contra o SHA-256 **obtido do CI independente**, seguida de comparação de bytes/SHA-256 e tamanho de **43/43 arquivos** distribuídos, sem divergências. Em seguida, a Vercel passou a exigir autenticação também no alias do projeto (`ssoProtection=all`); os dois hosts de Dev foram testados novamente sem credenciais e agora retornam `302` para autenticação.

Os dados imutáveis da prova e as ressalvas estão em [`docs/evidence/site-vercel-staging-2026-10-26.json`](evidence/site-vercel-staging-2026-10-26.json). **PASS somente para integridade estática e proteção Dev.** Ainda faltam execução do verificador canônico com CLI autenticado, prova de gateway real em staging, acessibilidade manual e aprovação de identidade/produção; nenhum desses critérios foi marcado como concluído.

## O que continua fora do escopo Dev concluído

1. **Staging externo autorizado:** verificar bytes e commit do bundle real com `scripts/staging_preflight.py`, usando SHA de manifesto proveniente do CI, e testar Identity/Conta com gateway real quando houver autorização.
2. **Acessibilidade:** executar inspeções humanas de zoom nativo/somente texto, leitor de tela, contraste de fundos complexos e estados interativos de acordo com [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md). Chrome CI é regressão parcial, não conformidade WCAG completa.
3. **Distribuição real:** publicação oficial e atestada de downloads e catálogo comercial pelo owner; somente depois integrar a apresentação de preços, planos e entitlements.
4. **Produção:** avaliação independente do deployment, DNS, domínio, segurança, política de cache e autorização dos owners. Não ativar por alteração de flags do Site.

Esses gates **não reabrem a migração Dev**, que pode evoluir normalmente sem usuários ou clientes em produção.

## Procedimento para a próxima revisão

Alterar apenas o owner correto → criar PR → comprovar CI e Chrome no Site → reconciliar `main` → atualizar o **único** pin do Site no OS se houver mudança de contrato/artefato → testar portal e login Web pela PR do OS → merge protegido. Não usar aliases para `--migration-lock`, cópias de `artifacts/`, fontes visuais no OS nem geradores alternativos.

**Histórico das auditorias e fases anteriores**, preservado exclusivamente como registro e **não** como runbook: [handoff arquivado](history/SITE-CUTOVER-2026-10-24.md) e [auditoria arquivada](history/SITE-AUDIT-2026-10-24.md).

## Polimento visual responsivo — 29/10/2026

### Cabeçalho público com fonte única de layout

O cabeçalho das rotas públicas usa uma composição única: marca, ações de identidade e navegação. `site/assets/site.css` é a única fonte de geometria responsiva do shell e do seletor de idioma; folhas de página podem definir cor e acabamento, mas não repetem grid, espaçamento estrutural ou breakpoints do cabeçalho. `site/i18n/catalog.js` e `site/i18n/runtime.js` continuam sendo a fonte única de idiomas e rótulos. O contrato de rotas permanece em `contracts/site-routes.json`.

No celular, marca, ações de entrar/cadastro e disclosure ficam na mesma faixa. O idioma aparece identificado no painel expandido, antes dos links, sem uma faixa utilitária separada no estado fechado. Essa ordem também é a ordem do DOM e do teclado. Em `Privacidade` e `Termos`, o runtime normaliza a estrutura durante a execução sem alterar os HTML legais protegidos por hash. `/conta/` conserva sua barra de aplicação própria.

Esta composição substitui as notas anteriores deste handoff que descreviam o seletor sozinho numa linha estreita. O conteúdo legal, os hashes usados por Identity e os contratos de serviço permanecem intactos.

### Primeiro frame da página inicial — 29/10/2026

O texto e as ações do hero da home não aguardam mais a animação de entrada para atingir opacidade total. A prova de 29/10/2026 encontrou também um deslocamento horizontal na entrada do telefone, que causava overflow nos primeiros instantes; `phone-enter` agora mantém apenas o movimento vertical e a rotação. `scripts/browser_smoke.py` verifica o estado inicial em todas as oito larguras, incluindo 360 e 430 px. O candidato `df3f6f0ca75d9ce7de435f8c87cf83a9ae379fc8` passou build, verify, smoke estático, 74 testes Python, localização, 88 estados principais e 77 touch coarse; Playwright passou 286 combinações bilíngues. Evidência: `work/browser-evidence-phone-animation-fit/` e `work/responsive-audit-bilingual-final.json`; SHA-256 do manifesto `4432187B0DC54A14D077FCD8BF374D5EB0FE3C87574F2E655E64A842E893E911`.

- Na Conta em tablets touch, cada destino de “Mais” ocupa uma linha completa dentro do diálogo; a regra também evita que folhas de estilo do portal façam links inline em grupos com vários destinos.
- O nome acessível “Fechar diálogo” da Conta agora tem tradução inglesa no catálogo compartilhado, para que leitores de tela recebam o idioma correto após a troca para en-US.
- Em telas touch, as marcas clicáveis de cabeçalho/rodapé e o link de pular conteúdo agora mantêm alvos de pelo menos 44 px; a Conta segue o mesmo tamanho para a marca do topbar.
- Em touch, a demonstração compacta da home sai da ordem de teclado até ser ampliada; os diálogos do notebook e telefone mantêm alvos utilizáveis.
- Nos cabeçalhos de identidade, o seletor de idioma agora reserva espaço para exibir por inteiro “Português (Brasil)” e “English (US)” em desktop; o tamanho móvel continua controlado pelo breakpoint existente.
- Acessibilidade manual, Identity real, catálogo oficial, staging e produção continuam nos estados descritos acima; este ajuste é somente de apresentação.

### Shell público com geometria centralizada — 29/10/2026

`site/assets/site.css` é agora a única fonte de layout responsivo do cabeçalho e do rodapé públicos. O CSS do portal deixou de redefinir largura, posição, espaçamento ou quebra do cabeçalho; folhas de página podem manter cores, bordas visuais e tipografia. O rodapé segue o mesmo grid móvel em todas as rotas que usam `.site-footer` e preserva alvos de link de 44 px. O contrato em `tests/test_site_contract.py` impede que a geometria volte a ser copiada para CSS de página; `scripts/browser_smoke.py` verifica presença, reflow, limites da viewport e tamanho dos links em todas as rotas.

`/conta/` mantém `.page-footer` e seu CSS próprio por ser a barra do aplicativo Conta, sem usar o shell público. Os HTML de Privacidade e Termos seguem byte-idênticos e a validação de documento continua fechada conforme os hashes publicados por Identity.

### SSOT do shell e header mobile — 29/10/2026

O contrato `contracts/public-shell.json` agora concentra marca, ações, navegação e rodapé por rota. Perfis nomeados reutilizam ações de autenticação, navegação simples e rodapés de autenticação/recuperação; cada rota mantém apenas seus desvios. As oito rotas comuns têm somente marcadores no HTML-fonte; `scripts/public_shell.py` valida e expande o contrato durante o build. O CSS responsivo vive em `site/assets/site.css`; conteúdo traduzido continua usando `site/i18n/catalog.js` e `runtime.js`. O build mantém os recursos da marca vindos do artifact verificado da Surface.

Na revisão anterior da navegação, o idioma ficou junto ao disclosure na faixa abaixo da marca/ações. A orientação da [NN/g](https://www.nngroup.com/articles/language-switching-ecommerce/) permite manter a troca de idioma dentro da navegação móvel. Privacidade/Termos são exceções por hash de Identity: seus arquivos permanecem intactos, e o runtime os normaliza para a mesma apresentação. Minha Conta mantém seu shell de aplicação. Build candidato anterior (`source_commit=90e966971f1a2a08e5b41e1a344eb0bf3a9046df`, manifest SHA-256 `36E353600AE4B7C0343792BFA1BC53CD8EF6E5A3D705FB3D646708D5E99FB34A`), verificação do bundle, smoke estático, localização, contrato legal e 74 testes passaram. Chrome 156.0.8078.49 no Windows 10 Pro confirmou 143 combinações de layout: 66 na matriz principal e 77 cenários touch coarse em tablets, cobrindo 11 rotas e 12 larguras distintas, sem falhas. O relatório e capturas estão em `work/browser-evidence-mobile-navigation-20261029-06/`. Zoom nativo, ampliação nativa somente de texto e leitor de tela seguem pendentes conforme [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).


## SSOT da navegação da Conta e header estreito — 29/10/2026

A lista `sections[]` em `site/assets/account-portal.js` agora é a fonte dos IDs, grupos, rótulos móveis e páginas de overflow. A barra inferior, o menu lateral e “Mais” derivam dessa lista; a fonte de tradução continua no catálogo i18n. `site/assets/account-dashboard.css` mantém uma única regra de geometria para a navegação touch, protegida por teste de contrato.

A revisão visual anterior em 280 px revelou que, em Download, o CTA longo comprimia o link da marca embora os retângulos externos parecessem separados. `site/assets/site.css` compacta a marca e o padding do CTA em até 320 px; o Chrome passou a conferir também o conteúdo interno da marca. Os documentos de Privacidade/Termos continuam intactos conforme o hash de Identity.

Naquela revisão anterior da Conta, o candidato `168bd646aadcec4826eb2e3087123de63fe92916`, manifesto `357F4C011D6A4459FC475813C9F62A0EADC5AC8B5F860109ADA5B45A6631A1B6`, passou o checklist Chrome completo sem falhas. Evidência histórica: `work/browser-evidence-account-mobile-shell-168bd64/`; preview daquela revisão: `http://127.0.0.1:4181/`. Não houve deploy de produção. Zoom nativo, ampliação somente de texto, leitor de tela e contraste de composições permanecem gates manuais.

O runner passou a reconhecer as serializações CSS `color(srgb …)` e `color(srgb-linear …)` que antes deixavam texto de algumas páginas sem medição. Na nova prova foram medidas 188 combinações de texto/fundo sólido nas onze rotas a 1440 px, sem falhas ou cores sólidas não reconhecidas; 25 superfícies com imagens/gradientes continuam no gate de inspeção visual. Essa correção melhora o teste e não altera o bundle do Site.

Na Conta, removi regras de espaçamento e posicionamento mobile que já eram sobrescritas e consolidei a geometria do diálogo “Mais” em um único owner para celular. O contrato estático protege esse owner e o padding de fim de página. A matriz Chrome confirmou a folga entre rodapé e navegação fixa em 280–430 px e em tablets touch; por teclado, Enter abre o diálogo com foco dentro, e Escape fecha, atualiza `aria-expanded` e devolve o foco ao botão. Relatório: `work/browser-evidence-account-mobile-shell-168bd64/report.json`.

## Header, footer e SSOT — revisão final 29/10/2026

O commit de código `c70d0b611c3d7b2b96b7629db73b301dccf7cd66` consolida o shell público responsivo. Em celular, marca, grupo Entrar/Cadastrar e menu ficam na mesma faixa. As duas ações conservam destinos separados, mas agora aparecem juntas dentro de um controle visual; o rótulo compacto vem do contrato/catálogo. O idioma fica identificado dentro do painel expandido, antes dos links. A partir de 1160 px para baixo, o header usa duas linhas para preservar espaço da navegação; até 760 px os links recolhem no disclosure. Privacidade/Termos recebem a estrutura normalizada pelo runtime sem alterar bytes fixados por Identity. Owners seguem únicos: CSS compartilhado para geometria, `contracts/public-shell.json` para conteúdo, `runtime.js` para comportamento e `catalog.js` para traduções.

O footer público continua derivado do contrato/CSS compartilhados; `/conta/` mantém o footer da aplicação. Build, verify, smoke estático, 76 testes Python e localização (1.716 mensagens) passaram. Chrome passou sem falhas: 99 cenários principais, 281 pontos de quebra derivados do CSS, 308 verificações bilíngues, 77 touch, 22 reflows, 11 ampliações simuladas de texto a 200%, 22 verificações de espaçamento, seis estados sem JavaScript e os dez painéis públicos dentro da viewport. Foram medidas 1.798 amostras de texto em superfícies sólidas sem falhas; 189 superfícies com imagem/gradiente ficam fora dessa medição automática.

Bundle final `source_commit=c70d0b611c3d7b2b96b7629db73b301dccf7cd66`; manifesto SHA-256 `7903F00E8D3439D2850DF5BDAD3D2E85469115E421D29B749882DB354EC0DD08`. Relatório e 193 capturas: `work/browser-evidence-mobile-shell-ssot-20261029-final4/`. Preview: `http://127.0.0.1:4218/termos/`. Não houve deploy de produção; leitores de tela, zoom nativo, aumento nativo somente de texto e contraste em composições permanecem nos gates manuais de [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).
