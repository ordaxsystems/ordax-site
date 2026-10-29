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
- [x] Cobertura de breakpoints sem configuração paralela: `scripts/browser_smoke.py` lê as folhas CSS efetivamente carregadas em cada rota, segue `@import` e testa cada limite e pixels vizinhos na faixa de 280 a 2560 px. Foram cobertos 251 casos rota/largura; CSS da Surface é observado somente para cobertura, sem alterações.
- [x] Cada header público mobile mantém marca + ações de conta na primeira linha. Na segunda, idioma + disclosure ficam lado a lado como um único grupo compacto alinhado à direita; a matriz repetida inclui 280 px. O Chrome também confirma que o disclosure abre os links, sincroniza `aria-expanded`/`aria-controls`, fecha com Escape e devolve o foco. Usa botão nativo e links comuns, sem role ARIA `menu`.
- [x] O seletor aparece uma vez, antes dos links. O placeholder vazio foi removido do HTML gerado; “Português” e “English” mantêm seus nomes nativos, cada opção informa seu `lang`, e o nome acessível do seletor/menu vem do catálogo PT-BR/en-US. Os landmarks do header e rodapé acompanham o idioma nas 280 combinações públicas de rota/largura/idioma.
- [x] Sem JavaScript, links de navegação continuam visíveis. `/conta/` mantém o shell da aplicação; Privacidade/Termos mantêm os bytes fixados por Identity e recebem normalização visual via runtime.
- [x] O rodapé público continua gerado pelo mesmo contrato e pela mesma geometria compartilhada. O rodapé da Conta mantém seu owner de aplicação. Links estruturais preservam alvo de 44×44 px nos viewports móveis.
- [x] SSOT da navegação Conta: `sections[]` em `site/assets/account-portal.js` é a única lista de seções; grupos do menu lateral, quatro atalhos móveis e destinos restantes em “Mais” são derivados dos metadados. As traduções permanecem em `site/i18n/catalog.js`, e a geometria mobile tem um único owner em `site/assets/account-dashboard.css`. `test_account_navigation_is_derived_from_section_metadata` impede a volta de uma lista paralela.
- [x] A barra móvel da Conta usa rótulos curtos traduzidos; em 280/320 px, PT-BR/en-US, todos os cinco alvos têm pelo menos 44×44 px, cada texto cabe na própria célula e não invade vizinhos. O runner Chrome confirma essa condição na matriz responsiva e touch.
- [x] Revisão visual do candidato atual: capturas das onze rotas a 280 px e das onze regiões finais de rodapé a 390 px. Marca/ações, grupo idioma/menu, rodapé comum e shell de aplicação da Conta foram inspecionados; os HTML legais continuam byte-idênticos.
- [x] Contrato/build: `python scripts/build.py check`, `python scripts/build.py verify` e `python scripts/smoke_static.py` passaram; o smoke estático validou as 11 rotas e assets. Passaram 76 testes Python e localização com 1.715 mensagens em 11 rotas e dois idiomas.
- [x] Chrome no candidato `c6ed577b9c4689007ba233c7b6d64ac835e4bf3f`, manifesto SHA-256 `AC34B15A261BE1D64BE63F5C8BF3303B900CAFDB5F1944A022D73EFB267073C6`: 11 rotas × 9 larguras representativas, 99 cenários; 251 casos rota/largura de breakpoint derivados do CSS; 308 combinações de rota/largura/idioma (11 × 14 × PT-BR/en-US); 77 cenários touch; sem falhas. Também passaram 22 reflows, 11 ampliações simuladas de texto a 200%, 22 provas de espaçamento, seis estados sem JavaScript e regressões de catálogo/Identity/fragments. A nova regra `publicHeaderBrandContentFits` verifica o conteúdo interno da marca: Download em 280 px passou com marca completa e 9 px entre marca e ações. Evidência: `work/browser-evidence-responsive-final-c6ed577/report.json`.
- [x] A regressão do frame inicial posiciona a animação de entrada do telefone em `currentTime=0` e comprova que o elemento e o documento cabem na viewport antes de restaurar a animação. A prova encontrou e corrigiu overflow horizontal transitório na home; o frame inicial passou nas nove larguras, inclusive em 280, 360 e 430 px.
- [x] Navegação móvel testada em dez headers públicos: estado inicial recolhido, abertura por botão, links visíveis, Escape para fechar e foco retornando ao botão. As provas de layout confirmam idioma/menu na mesma linha até 760px; acima disso o idioma acompanha os links. Marca/ações permanecem na mesma linha.
- [x] Revisão visual das capturas desktop, mobile a 280/320/390 px e da Conta a 768 px, incluindo a rota legal com HTML bloqueado por hash e rodapés no fim das páginas. As capturas de Licenças em 280 px confirmam marca + Entrar/Criar conta na primeira linha e idioma + Menu agrupados na seguinte; os estados em inglês também passaram na matriz responsiva. Prévia local atual: `http://127.0.0.1:4209/licencas/`.
- [x] O padrão foi escolhido conforme a orientação W3C para disclosure: [Disclosure Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/) e [navegação disclosure com links comuns](https://www.w3.org/WAI/ARIA/apg/patterns/disclosure/examples/disclosure-navigation-hybrid/). Reflow a 320 CSS px segue a [WAI/W3C](https://www.w3.org/WAI/WCAG21/Understanding/reflow).
- [ ] Zoom nativo de 200%/400%, aumento nativo somente de texto, leitor de tela e contraste completo em composições permanecem gates manuais; este checklist não declara conformidade WCAG. Protocolo em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).

Este checklist confirma o shell, a navegação SSOT da Conta, o primeiro frame da home e os estados do catálogo no bundle local revisado (`http://127.0.0.1:4209/`). Ele não prova Identity em staging, deployment remoto ou autorização de produção.
