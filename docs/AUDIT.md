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
- [x] `contracts/public-shell.json` é o owner único dos fragmentos e do conteúdo do cabeçalho/rodapé nas oito rotas comuns; o build os gera com `scripts/public_shell.py`.
- [x] `site/assets/site.css` é o owner da geometria e dos breakpoints; `site/i18n/catalog.js`/`runtime.js` são os owners de idioma e traduções.
- [x] O mobile mantém marca e ações de identidade na mesma linha; o seletor é inserido junto aos links da navegação, sem fila de idioma separada.
- [x] Exceções são declaradas no contrato: `/conta/` usa shell de aplicação próprio; Privacidade/Termos preservam seus bytes por hash de Identity e o runtime normaliza a apresentação.
- [x] Testes de contrato cobrem HTML gerado, separação de CSS, conteúdo localizado e preservação dos HTML legais.
- [ ] Build final, smoke estático e suíte completa: registrar resultados do candidato desta revisão antes do push.
- [ ] Smoke Chrome com 11 rotas, 1440/390/320 px, alinhamento header, idioma junto à navegação, reflow e rodapé: pendente nesta revisão até execução em host com ChromeDriver.

Este checklist cobre regressões estruturais do shell; não declara conformidade WCAG. O gate manual de zoom real, leitor de tela, contraste em composições e estados permanece em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).
