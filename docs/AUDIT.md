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

## Checklist SSOT e shell responsivo — atualização 29/10/2026

- [x] `contracts/site-routes.json` continua sendo o único inventário de rotas e indexabilidade.
- [x] `contracts/public-shell.json` é o owner do conteúdo e da estrutura pública de header/footer nas oito rotas geradas; os perfis nomeados mantêm ações e navegações repetidas sem cópia por página. `scripts/public_shell.py` expande e valida o contrato.
- [x] Limites de SSOT preservados por responsabilidade: `site/assets/site.css` contém geometria/breakpoints do shell; `site/i18n/runtime.js` contém o comportamento; `site/i18n/catalog.js` contém labels e traduções; `contracts/site-routes.json` permanece owner do inventário de rotas.
- [x] Cada header público mobile mostra marca e ações de conta na primeira linha e idioma + botão na segunda. O disclosure abre os links abaixo, sincroniza `aria-expanded` e `aria-controls`, aceita Escape e devolve o foco ao botão. Usa botão nativo e links comuns; não aplica o role ARIA `menu`.
- [x] O seletor está presente uma vez, antes do primeiro link. O placeholder vazio duplicado foi removido do HTML gerado; labels “Português” e “English” e o nome acessível do botão vêm do catálogo PT-BR/en-US.
- [x] Sem JavaScript, links de navegação continuam visíveis. `/conta/` mantém o shell da aplicação; Privacidade/Termos mantêm os bytes fixados por Identity e recebem normalização visual via runtime.
- [x] O rodapé público continua gerado pelo mesmo contrato e pela mesma geometria compartilhada. O rodapé da Conta mantém seu owner de aplicação. Links estruturais preservam alvo de 44×44 px nos viewports móveis.
- [x] Contrato/build: `python scripts/build.py check` e `python scripts/build.py verify` passaram; `python scripts/smoke_static.py` validou as 11 rotas e seus assets; os 74 testes Python e a localização passaram com 1.715 mensagens em 11 rotas e dois idiomas.
- [x] Chrome local: `SITE_BROWSER_PROOF=PASS`, zero falhas; 11 rotas × 6 larguras (1440, 1024, 768, 760, 390 e 320 px), 66 cenários. A matriz adicional de tablets touch simulou `any-pointer: coarse` em 641, 760, 761, 1100, 1101, 1180 e 1181 px: 77 cenários (11 rotas × 7 larguras), todos sem overflow e com alvos estruturais utilizáveis. Total: 143 estados de layout. Também passaram 22 reflows de desktop, 11 ampliações simuladas de texto a 200%, 22 provas de espaçamento, seis estados sem JavaScript e testes adversariais de catálogo, Identity e fragments. Evidência: `work/browser-evidence-mobile-navigation-20261029-06/report.json`.
- [x] Navegação móvel testada em dez headers públicos: estado inicial recolhido, abertura por botão, links visíveis, Escape para fechar e foco retornando ao botão. As provas de layout confirmam idioma/menu na mesma linha até 760px; acima disso o idioma acompanha os links. Marca/ações permanecem na mesma linha.
- [x] Revisão visual das capturas em 320, 390, 760 e 768 px, incluindo a rota legal com HTML bloqueado por hash. O preview local atualizado está em `http://127.0.0.1:4190/licencas/`.
- [x] O padrão foi escolhido conforme a orientação W3C para disclosure: [Disclosure Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e [navegação disclosure com links comuns](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/examples/disclosure-navigation-hybrid/). Reflow a 320 CSS px segue a [WAI/W3C](https://www.w3.org/WAI/WCAG21/Understanding/reflow).
- [ ] Zoom nativo de 200%/400%, aumento nativo somente de texto, leitor de tela e contraste completo em composições permanecem gates manuais; este checklist não declara conformidade WCAG. Protocolo em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).

Este checklist substitui a prova responsiva anterior de 33 cenários e confirma o shell no estado local revisado. Ele não prova Identity em staging, deployment remoto ou autorização de produção.
