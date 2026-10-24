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

**SITE-ADR-010 — Artefato de apresentação externa pinado sem JSON redundante (2026-10-23/24):** o snapshot JSON separado equivalia integralmente a `fixture.surface`, por isso não é distribuído. CSS+fixture migraram para artefato read-only manifestado com SHA-256/ Git blob e pin explícito fornecido no build; o Site não edita nem recompila Surface. CSS distribuído só rebasa URL da fonte Inter para o brand externo verificado, sem alterar arquivo-fonte. Produção requer futura release oficial do owner e gate de proveniência não autoafirmado. [ordax-surface#3](https://github.com/ordaxsystems/ordax-surface/issues/3).

**SITE-ADR-011 — Lock de confiança único e releases inacessíveis sem evidência externa (2026-10-23/24):** `contracts/migration-artifact-lock.json` reúne hashes SHA-256/paths dos três materiais de migração temporários e define status exclusivamente dev; builder recusa overrides e valida cada manifesto contra seu pin antes de qualquer declaração interna. Brand/preview/offers compartilham revisão OS. Entradas de download `--publications` arbitrárias não podem habilitar catálogo: somente artefato imutável com autoridade externa de publicação poderá abrir esse gate futuramente. O lock não equivale a assinatura ou autorização de produção.

**SITE-ADR-012 — Auditabilidade de recursos renderizados (2026-10-23/24):** CSS emitido deve apontar apenas a arquivos reais do bundle ou imagens/data/fragmentos embutidos, sem `@import` implícito; o Chrome captura erros de runtime/rede a partir de antes dos scripts. O favicon é uma apresentação do símbolo do pacote brand validado, injetado no HTML apenas quando ausente, nunca outra fonte de asset. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40048444731).

**SITE-ADR-013 — Reflow sem mascarar conteúdo, sem autenticação inventada (2026-10-23):** regressões Chrome separam 33 viewports usuais, 22 provas adicionais de reflow em CSS (larguras 640/320 no desktop) e seis rotas Identity/Conta/Web sem JavaScript. O reflow encontrou quebra de navegação por seletor de idioma dinâmico; a correção foi permitir wrapping e linha dedicada no CSS Site, não cortar o scroll horizontal globalmente. Fluxos sem scripts preservam avisos e bloqueiam credenciais/sessão/Web. Zoom real, contraste e leitor de tela permanecem gates próprios. [CI PASS](https://github.com/ordaxsystems/ordax-site/actions/runs/40051704031).
