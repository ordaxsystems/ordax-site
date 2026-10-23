# Decisões arquiteturais — OrdaX Site

**SITE-ADR-001 — Isolamento de repositório (2026-10-23):** HTML/CSS/JS e catálogo local PT-BR/en-US têm owner no Site. Nenhum runtime, backend, código React da Surface ou utilitário de kernel entra no artefato.

**SITE-ADR-002 — Artefatos por digest:** marca e demonstração Meridian entram apenas como artefatos publicados por seu owner, com revisão, manifesto e hashes SHA-256. Snapshot visual local é **somente leitura** e pode ficar temporariamente pinado; não é outro lugar de edição canônica.

**SITE-ADR-003 — Publicação fail-closed:** pipeline de Site nunca autoriza uma release de OS; sem publicação aprovada, gera catálogo vazio. Formulários usam same-origin e readiness do gateway; nenhuma conta de demonstração com credenciais ou checkout fictício.

**SITE-ADR-004 — Cutover atômico:** nenhuma exclusão em `ordax-os` antes de build determinístico, CI, smoke, paridade e atualização de consumidores. Compatibilidade antiga será retirada após substituição, não perpetuada.

**SITE-ADR-005 — Segurança de deployment:** GitHub Actions verifica candidato sem segredos nem deploy. Produção/domínios/credentials exigem autorização independente e serão configurados fora do PR de extração.

**SITE-ADR-006 — Catálogos externos:** contratos oficiais de Identity, entitlements e releases não são copiados como SSOT. Inputs públicos autorizados são projeções versionadas/digestadas. O Site é consumidor, não publicador.


**SITE-ADR-007 — Uma fixture pública, sem serialização inline (2026-10-23):** o playground usa apenas `site/assets/playground-fixture.json` por fetch same-origin; o HTML não guarda uma cópia de ~159 KB. Snapshot vindo de Surface permanece somente leitura, com schema e falha fechada.

**SITE-ADR-008 — Rotas e SEO sem controle de domínio (2026-10-23):** `contracts/site-routes.json` controla indexabilidade e os testes. O build só gera canonical, OpenGraph, sitemap e robots com `--public-origin` explícito vindo do owner de deployment; esse input não transfere ownership de DNS nem publica nada.


**SITE-ADR-009 — Navegação de teclado como contrato do portal (2026-10-23):** todo `main#conteudo` é programaticamente focável por skip link, sem entrar na ordem Tab natural; o handler de Conta pode focar diretamente sem exigir fragmento na URL. Prova usa teclado ChromeDriver e Chrome Accessibility Tree; não basta string estática em HTML. Troca de idioma é testada no seletor real, incluindo persistência.
