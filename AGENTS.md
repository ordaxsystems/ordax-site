# OrdaX Site — instruções para agentes

Este repositório é o **owner do código de apresentação do site público** após cutover aprovado, não do OS, Surface Web, Identity, cobranças ou publicação de releases.

## Ordem de leitura
1. `README.md`
2. `docs/AUDIT.md`
3. `docs/DECISIONS.md`
4. `docs/HANDOFF.md`
5. `scripts/build.py`
6. `site/config/public-site.json`

## Autoridades e limites
- `ordax-site/main` é a autoridade do site **somente após conclusão de migração validada**; até lá, o site atual em `ordax-os/main` não deve ser removido.
- Nunca importar `system/surface`, `tools/surface-web` ou código de kernel, USB, Creator ou apps.
- Marca e demos da Surface são **artefatos publicados, imutáveis e verificáveis**, nunca cópias de código para compilar no site.
- Backend de Identity, sessão, autorização, pagamentos e banco pertence a seus respectivos owners (`ordax-platform` / serviços canônicos). Browser só consome APIs autorizadas de mesma origem.
- Não versionar secrets, chaves ou tokens. Não fabricar Conta, sincronização, assinatura, download, release ou produtos publicados.
- Não alterar domínio, deploy de produção nem credenciais sem aprovação específica.
- Recuperação e Conta continuam fail-closed enquanto seus gates reais não estiverem aprovados.
- O catálogo público vem exclusivamente de projeção autorizada do publicador de releases; sem publicação, catálogo vazio.
- Não alterar API/comportamento de `ordax-os` sem reconciliação das PRs da Surface.
- Preservar commits da `main`; não usar force-push/rebase da main.

## Fluxo
Branch -> auditoria de diffs e conflitos -> testes de rotas/i18n/segurança -> pacote com provenance SHA-256 -> CI -> PR review -> cutover OS só depois de prova de paridade -> publicação sob autorização separada. Registrar atualizações em `docs/HANDOFF.md`.

## Status
Extração é **candidata em draft**; ainda faltam duas imagens originais e artefato publicado de marca. Nenhum build de produção aprovado.
