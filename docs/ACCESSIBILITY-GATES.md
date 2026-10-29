# Protocolo de validação manual de acessibilidade — OrdaX Site

**Status:** gate **PENDENTE**. Este protocolo não é evidência de execução, nem autoriza merge/cutover/deploy. O owner de implementação é `ordax-site`; o backend Identity, os artefatos Surface e a publicação de releases pertencem a seus owners.

## Escopo e fontes de verdade

- Rotas: iterar o `contracts/site-routes.json` da **mesma revisão** usada para gerar o build candidato; não manter lista duplicada de rotas neste documento.
- Build: usar o bundle estático verificado pelo `scripts/build.py` com `--dev-lock contracts/dev-artifact-lock.json`, usando as duas prereleases Dev assinadas do owner Surface. Verificar o manifesto do próprio candidato e registrar o SHA exato; não confundir o deployment protegido `ordax-site-dev` com autorização de publicação pública.
- Prova automática existente: `scripts/browser_smoke.py` cobre teclado/AX, contraste medível de superfícies planas, reflow, sem JS, `forced-colors`, ampliação **simulada** de texto a 200% e espaçamento WCAG 1.4.12 em PT-BR/EN-US (22 cenários). Os testes `text200` e `spacing` são **regressões parciais de DOM**, não zoom nativo nem aprovação visual/manual.
- Evidência automatizada mais recente (29/10/2026): candidato `758272f6fc744b505db79a3272ea8c59f00e36e7`, SHA-256 do manifesto `315612174C8C18954BA8B246B2051CBADEB0B02C5A184C351F51AB238A47756D`. Chrome 156.0.8078.49/ChromeDriver 156 passou 88 cenários (11 rotas × 8 larguras), 231 casos rota/largura gerados pelos breakpoints das folhas CSS carregadas e 77 cenários touch coarse, sem falhas. A visibilidade e o posicionamento dentro da viewport das regiões do cabeçalho passaram 541 verificações nos dez shells públicos. A suíte mede alvos do Site de pelo menos 24×24 px em layouts regulares e 44×44 px em ponteiro de toque; o cabeçalho da Conta também precisa caber na sua faixa. A matriz bilíngue passou 286 combinações (11 rotas × 13 larguras × pt-BR/en-US). Também passaram 22 reflows, 11 testes text200, 22 testes de espaçamento e seis rotas sem JavaScript. Evidências: `work/browser-evidence-final-758272f/`. Isso **não** fecha os gates de zoom nativo, texto-only nativo, leitor de tela nem inspeção manual de composições complexas.
- Fonte visual de demonstração `.playground`: avalie-a como conteúdo exibido ao usuário, mas encaminhe ajustes de seus artefatos canônicos ao owner Surface. Não introduza CSS espelho no Site.

## Evidência obrigatória por rota

Registre: revisão completa do commit, digest do build candidato, rota do contrato, sistema operacional, navegador/versão, viewport físico, fator de zoom ou configuração de fonte **real**; status PASS/FAIL/BLOCKED, passos de reprodução, captura de tela e referência da issue para toda falha. Nenhuma captura deve conter credenciais, dados pessoais ou sessão real. Resultados parciais não podem fechar o gate.

## 1. Zoom de página nativo — WCAG 1.4.4 e 1.4.10

1. Abrir o build **em ambiente isolado**, com Chrome/Firefox desktop normais, viewport físico `1280 × 900` ou superior. Redefinir o zoom para 100%.
2. Pelo menu do navegador ou pelo controle nativo de zoom, aplicar **200%** e depois **400%**. Não usar `document.body.style.zoom`, `deviceScaleFactor` ou reduzir artificialmente a viewport em lugar do zoom real.
3. Em **todas as rotas**, verificar que navegação, mensagens, idiomas PT-BR/en-US, headings, link de pular conteúdo e foco continuam encontráveis e acionáveis com teclado; que textos relevantes não são cortados, sobrepostos ou escondidos; que não há rolagem horizontal da página em layout equivalente a **320 CSS px** nos conteúdos que devem refluir. Documentar exceções justificadas para conteúdo intrinsecamente bidimensional, em vez de mascará-las.
4. Em páginas Identity/Conta/Web não conectadas a staging, registrar explicitamente o estado **indisponível/fail-closed**. Não tentar substituir por contas/serviços simulados.

## 2. Ampliação nativa somente de texto — WCAG 1.4.4

1. Usar navegador com funcionalidade **somente texto** (por exemplo, Firefox com a opção “Zoom somente no texto”), em sessão isolada. Registrar versão e procedimento exato do navegador.
2. Fixar layout normal e ampliar **somente o texto para 200%**. Não considerar o teste `text200` automatizado como substituto.
3. Conferir que botões, campos, seletores, links, avisos, menus e conteúdo legal mantêm seus rótulos legíveis, distinguíveis e sem sobreposição/truncamento. Usar apenas conteúdo/rotas efetivamente presentes no bundle.
4. Se o navegador escolhido não oferecer zoom somente texto, marcar como **BLOCKED**; não substituir silenciosamente por outro tipo de escala.

## 3. Espaçamento de texto — WCAG 1.4.12

A suíte Chrome aplica esses parâmetros ao texto visível do Site na viewport 390 CSS px e exige métricas computadas, ausência de clipping direto em contêineres de texto e ausência de overflow horizontal ([CI](https://github.com/ordaxsystems/ordax-site/actions/runs/40057544890)). **Esse resultado é parcial**. Na inspeção humana, aplicar os mesmos parâmetros e verificar visualmente todas as rotas, estados e idiomas. Parâmetros: altura de linha de pelo menos 1,5 × tamanho da fonte; espaço após parágrafos de pelo menos 2 × tamanho da fonte; espaçamento entre letras de pelo menos 0,12 × tamanho da fonte; espaçamento entre palavras de pelo menos 0,16 × tamanho da fonte. Verificar perda de conteúdo/funcionalidade, tanto em PT-BR quanto em EN-US. Registrar qualquer incompatibilidade antes de emitir PASS.

## 4. Leitor de tela e teclado

- **Windows:** executar com NVDA e navegador suportado; **macOS:** complementar com VoiceOver e Safari se disponível. Registrar versão de leitor/browser.
- Percorrer landmarks, heading principal, listas, links, idioma, menus, imagens, avisos de erro indisponível e alternância de idiomas por comandos do leitor de tela; confirmar nomes e estado acessíveis, ordem lógica de foco e retorno ao conteúdo após skip link.
- Verificar que nenhum conteúdo do playground se apresenta como heading/documento exterior duplicado, sem suprimir o conteúdo significativo da demonstração.
- Fluxos de Identity autenticados **somente** com gateway real autorizado em staging, depois de autorização do owner; sem staging, marcar BLOCKED, nunca PASS por usar mock.

## Critério de liberação

Este gate é aprovado **somente** com evidências por rota e perfil, bugs bloqueantes resolvidos no owner correto e aprovação humana registrada na PR. A checagem automatizada e este documento não bastam. Permanecem **separados** os gates de artefatos oficiais Surface/Platform, Identity staging, autorização de cutover do OS, domínio e deploy de produção.

Referência de comportamento de zoom do navegador: https://support.google.com/chrome/answer/96810?hl=pt-BR
