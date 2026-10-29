# OrdaX Site — handoff de desenvolvimento

**Estado em 24/10/2026: migração Dev de código, apresentação e artefatos visuais concluída.** Este documento é a referência de estado, não uma nova camada de configuração. O código e os comandos válidos estão no [README](../README.md); os hashes, commits e a origem dos dois pacotes no único [lock Dev](../contracts/dev-artifact-lock.json).

## Ajuste de leitura — 2026-10-29

As páginas de Privacidade e Termos agora limitam o texto corrido a 76ch e usam corpo de 15px com entrelinha 1,8; os textos do painel de licenças, dos estados informativos e das orientações de download também ganharam tamanho e entrelinha. Os hashes SHA-256 e tamanhos em bytes dos arquivos publicados aparecem em 12px, com quebra dos hashes em telas estreitas. Login, cadastro, recuperação e Conta Web receberam texto mais legível nos estados de identidade, avisos, concordância e links de suporte. Em telas estreitas, a navegação e os seletores de idioma das páginas públicas usam texto de 12px; os rodapés públicos usam 12px. Os principais links de suporte e rodapé têm alvos mínimos de 44px. A página inicial e a página de download ampliam os alvos dos links de apoio para 44px em dispositivos de toque; o botão para fechar a demonstração ampliada da página inicial também mede ao menos 44px no celular. Minha Conta mantém botões, abas, breadcrumb, links de ação e o resumo de histórico com alvo mínimo de 44px no celular; status, notas, atalhos, contagens, legendas e rótulos operacionais da Conta usam 12px. Licenças, Privacidade e Termos nomeiam a navegação do rodapé, identificam a rota atual e a destacam visualmente. O conteúdo legal e os contratos de serviço não foram alterados. Como a Conta confere o SHA-256 dos bytes HTML integrais de Privacidade e Termos, alterações de marcação nessas páginas exigem republicar a referência de documento pelo owner de Identity antes de habilitar o consentimento/cadastro; até essa atualização, a validação permanece fechada.

Em dispositivos com ponteiro de toque, os links de navegação do cabeçalho e rodapé, atalhos dos formulários de identidade, controles principais da Conta e ações de integridade/download também mantêm alvo mínimo de 44px, mesmo acima dos breakpoints móveis.

Na página Download, o cabeçalho usa duas linhas entre 761 e 900px para manter ações, navegação e idioma dentro da largura disponível antes do breakpoint móvel.

As versões em inglês de Termos e Privacidade agora traduzem todos os títulos de seção, a data de vigência e o rótulo de contato que ainda apareciam em português. O catálogo i18n está referenciado por fingerprint nas onze rotas para entregar as novas traduções após o deploy. O texto legal em português não foi alterado.

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

## Prova externa do Site Dev — 26/10/2026

O Site Dev `ordax-site-dev` recebeu o **mesmo commit aprovado no CI**: `8ad8037ce2a2d600e621dec5aba2e50f878c3de9` (GitHub Actions `40141425475`). Foi realizada prova HTTPS de leitura do manifesto contra o SHA-256 **obtido do CI independente**, seguida de comparação de bytes/SHA-256 e tamanho de **43/43 arquivos** distribuídos, sem divergências. Em seguida, a Vercel passou a exigir autenticação também no alias do projeto (`ssoProtection=all`); os dois hosts de Dev foram testados novamente sem credenciais e agora retornam `302` para autenticação.

Os dados imutáveis da prova e as ressalvas estão em [`docs/evidence/site-vercel-staging-2026-10-26.json`](evidence/site-vercel-staging-2026-10-26.json). **PASS somente para integridade estática e proteção Dev.** Ainda faltam execução do verificador canônico com CLI autenticado, prova de gateway real em staging, acessibilidade manual e aprovação de identidade/produção; nenhum desses critérios foi marcado como concluído.

## O que continua fora do escopo Dev concluído

1. **Staging externo autorizado:** verificar bytes e commit do bundle real com `scripts/staging_preflight.py`, usando SHA de manifesto proveniente do CI, e testar Identity/Conta com gateway real quando houver autorização.
2. **Acessibilidade:** executar inspeções humanas de zoom nativo/somente texto, leitor de tela, contraste de fundos complexos e estados interativos de acordo com [ACCESSIBILITY-GATES.md](ACCESSIBILITY-GATES.md). Chrome CI é regressão parcial, não conformidade WCAG completa.
3. **Distribuição real:** publicação oficial e atestada de downloads e catálogo comercial pelo owner; somente depois integrar a apresentação de preços, planos e entitlements.
4. **Produção:** avaliação independente do deployment, DNS, domínio, segurança, política de cache e autorização dos owners. Não ativar por alteração de flags do Site.

Esses gates **não reabrem a migração Dev**, que pode evoluir normalmente sem usuários ou clientes em produção.

## Procedimento para a próxima revisão

Alterar apenas o owner correto → criar PR → comprovar CI e Chrome no Site → reconciliar `main` → atualizar o **único** pin do Site no OS se houver mudança de contrato/artefato → testar portal e login Web pela PR do OS → merge protegido. Não usar aliases para `--migration-lock`, cópias de `artifacts/`, fontes visuais no OS nem geradores alternativos.

**Histórico das auditorias e fases anteriores**, preservado exclusivamente como registro e **não** como runbook: [handoff arquivado](history/SITE-CUTOVER-2026-10-24.md) e [auditoria arquivada](history/SITE-AUDIT-2026-10-24.md).
