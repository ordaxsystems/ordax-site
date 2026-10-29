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

## Checklist do shell responsivo — 29/10/2026

- [x] Cabeçalho público centralizado em `site/assets/site.css`; CSS de página mantém tema e tipografia sem reposicionar marca, ações, navegação ou idioma.
- [x] Rodapé público usa a mesma geometria compartilhada e o breakpoint de coluna; `/conta/` continua com o componente próprio da aplicação.
- [x] Testes de contrato impedem que as folhas de página voltem a declarar layout do cabeçalho ou rodapé.
- [x] Build verificado, smoke estático nas onze rotas, 72 testes Python e localização PT-BR/en-US.
- [x] Inspeção visual em desktop do rodapé de `/licencas/` no preview local.
- [ ] Smoke completo de Chrome com 11 rotas, 1440/390/320 px, reflow e alvos do rodapé: não executou neste host, que não tem Chrome e ChromeDriver disponíveis. Rodar no CI ou em host configurado antes de tratar este checklist visual como concluído.

Este checklist cobre regressões estruturais do shell; não declara conformidade WCAG. O gate manual de zoom real, leitor de tela, contraste em composições e estados permanece em [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md).
