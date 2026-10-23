# OrdaX Site

Repositório de **apresentação pública** do OrdaX. Independente dos builds do kernel, USB, Surface Web, Creator e Identity.

> **Migração em andamento — draft.** A implementação atual no `ordax-os` continua vigente até a prova de cutover. Este repositório **não** publica em produção e não modifica domínios ou segredos.

## O que pertence ao Site

- `site/` — HTML/CSS/JavaScript estático, landing, downloads, login/cadastro/recuperação, UI de Conta, páginas legais, playground read-only e locales `pt-BR`/`en-US`.
- `scripts/` — build de candidato, integridade de bundle, catálogos públicos autorizados.
- `tests/` — regressões de contratos do site e localização.
- `.github/workflows/site-source.yml` — CI isolado, **sem publicação**.
- `docs/` — auditoria, decisões, proveniência e handoff.

Não contém backend próprio, OAuth, identidade, pagamentos, entitlements, banco, releases OS ou Surface compilável.

## Desenvolvimento

```sh
python3 scripts/build.py check
python3 -m unittest discover -s tests -p 'test_*.py' -v
node tests/test_localization.mjs
```

`check` é inspeção de fontes; **não é um pacote pronto para publicação**.

## Build de candidato

O bundle já inclui **todos os arquivos originais do portal**, com os seis binários de imagem preservando seus Git SHAs. O CI usa o snapshot auditado de marca `artifacts/brand/os-migration-70b0f7eb` e gera o candidato estático sem compilar a Surface nem montar o produto Web. Este snapshot de migração **não** é ainda uma publicação oficial da Surface:

```sh
python3 scripts/build.py build \
  --source-commit <SHA40_DO_SITE> \
  --brand-dir artifacts/brand/os-migration-70b0f7eb \
  --out out/site
python3 scripts/build.py verify --out out/site
```

O diretório `brand-dir` deve conter `manifest.json` com `artifact_class=ordax-brand`, `source_commit` e registros `path,size,sha256` para os recursos públicos oficiais. O site jamais cria esse artefato a partir de arquivos internos do OS.

O catálogo de downloads é **vazio** se o publicador não fornecer uma projeção explicitamente autorizada. Um `--publications` aprovado pelo owner real pode ser lido pelo builder, validado e filtrado; a escolha de tornar esse catálogo público pertence ao pipeline autorizado, não ao site. Formulários e Conta dependem de gateway `same-origin` com gates servidor; recuperação/billing não são habilitados por UI.

## Próximos passos e estado preciso

Consultar [Auditoria](docs/AUDIT.md), [Decisões](docs/DECISIONS.md) e [Handoff](docs/HANDOFF.md). As transferências PNG e o build independente com integridade foram comprovados no [CI](https://github.com/ordaxsystems/ordax-site/actions/runs/40039062149). Permanecem pendentes a publicação oficial de marca/demonstração pela Surface, projeção do catálogo de planos, comparação visual/acessibilidade/SEO em staging e a integração/cutover atômicos no `ordax-os`. Nada disso é autorização para deploy.
