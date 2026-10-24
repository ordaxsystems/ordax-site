# OrdaX Site — handoff de desenvolvimento

**Estado em 24/10/2026: migração Dev de código, apresentação e artefatos visuais concluída.** Este documento é a referência de estado, não uma nova camada de configuração. O código e os comandos válidos estão no [README](../README.md); os hashes, commits e a origem dos dois pacotes no único [lock Dev](../contracts/dev-artifact-lock.json).

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

## O que continua fora do escopo Dev concluído

1. **Staging externo autorizado:** verificar bytes e commit do bundle real com `scripts/staging_preflight.py`, usando SHA de manifesto proveniente do CI, e testar Identity/Conta com gateway real quando houver autorização.
2. **Acessibilidade:** executar inspeções humanas de zoom nativo/somente texto, leitor de tela, contraste de fundos complexos e estados interativos de acordo com [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md). Chrome CI é regressão parcial, não conformidade WCAG completa.
3. **Distribuição real:** publicação oficial e atestada de downloads e catálogo comercial pelo owner; somente depois integrar a apresentação de preços, planos e entitlements.
4. **Produção:** avaliação independente do deployment, DNS, domínio, segurança, política de cache e autorização dos owners. Não ativar por alteração de flags do Site.

Esses gates **não reabrem a migração Dev**, que pode evoluir normalmente sem usuários ou clientes em produção.

## Procedimento para a próxima revisão

Alterar apenas o owner correto → criar PR → comprovar CI e Chrome no Site → reconciliar `main` → atualizar o **único** pin do Site no OS se houver mudança de contrato/artefato → testar portal e login Web pela PR do OS → merge protegido. Não usar aliases para `--migration-lock`, cópias de `artifacts/`, fontes visuais no OS nem geradores alternativos.

**Histórico das auditorias e fases anteriores**, preservado exclusivamente como registro e **não** como runbook: [handoff arquivado](history/SITE-CUTOVER-2026-10-24.md) e [auditoria arquivada](history/SITE-AUDIT-2026-10-24.md).
