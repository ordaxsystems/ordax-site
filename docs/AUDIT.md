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
