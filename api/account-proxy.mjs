// Hosting-only adapter. Authentication logic and policies belong to ordax-os.
// Materialized from the immutable, verified gateway contract at install time.
// Never maintain a second proxy implementation in ordax-site.
export * from "../.gateway-source/api/account-proxy.mjs";
export { default } from "../.gateway-source/api/account-proxy.mjs";
