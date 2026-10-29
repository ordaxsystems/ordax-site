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
- [x] Em celular, marca, entrar/cadastro e botão do menu ficam juntos na primeira faixa. O cadastro usa rótulo curto vindo do contrato. O seletor de idioma fica dentro do painel aberto, identificado e antes dos links; a pessoa não encontra um seletor solto em outra linha do cabeçalho fechado. Isso mantém idioma acessível sem competir com as ações principais em larguras de 280 px.
- [x] A estrutura mobile segue botão disclosure nativo com links comuns. Chrome confirma abertura, `aria-expanded`/`aria-controls`, Escape e retorno de foco. O seletor mantém os nomes nativos “Português” e “English”, sinaliza `lang` em cada opção, acompanha o idioma ativo e funciona dentro do painel. Sem JavaScript, os links permanecem visíveis.
- [x] O runner deriva os pontos de quebra das folhas realmente carregadas por rota (incluindo `@import`) e verifica cada breakpoint e os pixels vizinhos, entre 280 e 2560 px. Foram aprovados 278 pares rota/largura. CSS da Surface é observado para cobertura, sem alterações.
- [x] Header, navegação, footer e ações foram revistos em onze rotas. `/conta/` preserva seu shell de aplicação; Privacidade/Termos mantêm seus bytes fixados por Identity, com normalização visual pelo runtime. O rodapé público tem owner/estrutura compartilhados; o footer da Conta permanece com o owner da aplicação. Alvos touch estruturais preservam pelo menos 44×44 px.
- [x] Navegação da Conta continua em SSOT: `sections[]` de `site/assets/account-portal.js` é a fonte dos grupos laterais, atalhos móveis e itens em “Mais”; traduções e geometria têm owners únicos. A suíte impede listas paralelas e confirma encaixe dos cinco alvos em PT-BR/en-US.
- [x] Chrome passou 11 rotas × 9 viewports (99 casos), 278 casos de breakpoint, 308 combinações bilíngues (11 × 14 × 2), 77 cenários touch, 22 reflows, 11 textos a 200%, 22 espaçamentos, seis estados sem JavaScript e provas de catálogo/Identity/fragments, sem falhas.
- [x] Contrato/build (`build check`, `build verify`, smoke estático), 76 testes Python e localização com 1.716 mensagens/11 rotas/2 idiomas passaram. O runner mediu 1.803 amostras de texto sobre fundos sólidos: zero falhas e zero valores sólidos não reconhecidos; 192 superfícies com imagem/gradiente foram excluídas da medição automatizada.
- [x] Capturas das onze rotas a 280 px e dos onze rodapés a 390 px foram inspecionadas; também foram vistos header aberto/fechado, inglês, Conta e páginas legais. A geometria do painel aberto também é conferida e deve caber na viewport após descontar scrollbar. O bundle usa `source_commit=db02f97150f3bf9b065c00791d05871f2e64cc83` e manifesto SHA-256 `3976F529C674B08232E229CD72E82EC921B27618CBD8E56D5CCB3094DF5B50C4`. Relatório e capturas finais: `work/browser-evidence-mobile-shell-ssot-20261029-final2/`; prévia local: `http://127.0.0.1:4216/licencas/`.
- [ ] Zoom nativo de 200%/400%, ampliação nativa somente de texto, leitor de tela e contraste completo em fundos compostos permanecem gates manuais. O checklist não declara conformidade WCAG integral; ver [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).

Referências para a decisão do seletor mobile: [NN/g — Language Switching on E-Commerce Sites](https://www.nngroup.com/articles/language-switching-ecommerce/), [WAI-ARIA APG — Disclosure](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e [WAI/W3C — Reflow](https://www.w3.org/WAI/WCAG21/Understanding/reflow).

Esta verificação é local e não comprova Identity em staging, autorização de produção nem publicação de um deployment. O build está pronto para revisão no branch `codex/site-responsive-polish`; a publicação de produção não faz parte desta atualização.
