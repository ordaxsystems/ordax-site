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

## Checklist SSOT e shell responsivo — 29/10/2026

- [x] `contracts/site-routes.json` continua sendo o único inventário de rotas e indexabilidade.
- [x] `contracts/public-shell.json` é o owner único dos fragmentos e do conteúdo do cabeçalho/rodapé nas oito rotas comuns; perfis nomeados mantêm em um só lugar ações de login repetidas, navegação simples e rodapés de autenticação/recuperação; `scripts/public_shell.py` valida e resolve os perfis no build.
- [x] `site/assets/site.css` é o owner da geometria e dos breakpoints; `site/i18n/catalog.js`/`runtime.js` são os owners de idioma e traduções.
- [x] O mobile mantém marca e ações de identidade na mesma linha; o seletor é inserido junto aos links da navegação, sem fila de idioma separada.
- [x] Exceções são declaradas no contrato: `/conta/` usa shell de aplicação próprio; Privacidade/Termos preservam seus bytes por hash de Identity e o runtime normaliza a apresentação.
- [x] O runtime reaproveita a marca do cabeçalho para padronizar também o rodapé legal; os documentos de origem continuam byte-idênticos aos hashes de Identity.
- [x] Testes de contrato cobrem HTML gerado, separação de CSS, conteúdo localizado e preservação dos HTML legais.
- [x] Build do candidato, verificação do bundle, smoke estático nas 11 rotas, 74 testes Python, localização PT-BR/en-US e contrato legal.
- [x] Playwright local com navegação nova por amostra: 11 rotas × 13 larguras (320, 360, 390, 430, 600, 641, 768, 980, 1024, 1100, 1180, 1280 e 1440 px). Os 143 cenários não apresentaram overflow horizontal nem shell fora da viewport. Até 600 px, marca e ações ficam na mesma linha; até 430 px, o idioma divide a linha da navegação com ao menos um link. Links estruturais dos rodapés público e da Conta, mais atalhos de perfil/retorno visíveis em dispositivos coarse, respeitam 44×44 px. Links inline em texto continuam fora da regra de alvo do rodapé.
- [x] Revisão visual da header em 320 e 390 px: logo e ações de conta na primeira linha; idioma integrado à linha de navegação. Em 320 px o último link reflui para a linha seguinte com o restante do cabeçalho dentro da tela.
- [x] A escolha de mobile segue a recomendação da [NN/g para o seletor de idioma](https://www.nngroup.com/articles/language-switching-ecommerce/): mantê-lo visível acima da dobra ou dentro da navegação, que libera o canto superior para ações prioritárias. O critério de reflow a 320 CSS px está descrito pela [WAI/W3C](https://www.w3.org/WAI/WCAG21/Understanding/reflow). O alvo 44×44 px é uma meta adotada pelo Site alinhada ao [critério enhanced 2.5.5](https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced).
- [ ] `scripts/browser_smoke.py` completo e capturas de evidência no runner CI: o comando `chromedriver` não está disponível no PATH deste host. A auditoria Playwright direcionada acima não substitui os cenários completos de teclado, console, recursos e estados sem JavaScript.

Este checklist cobre regressões estruturais do shell; não declara conformidade WCAG. O gate manual de zoom real, leitor de tela, contraste em composições e estados permanece em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).
