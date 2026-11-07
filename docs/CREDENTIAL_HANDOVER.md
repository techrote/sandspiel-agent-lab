# Optional API credential handover — Sandspiel Agent Lab

**Status:** policy and integration design only. **No private third-party provider key was supplied or installed**, and the verified Sandspiel gameplay bridge needs no such key. The inherited upstream browser application does contain a public Firebase client API key in `js/api.js`; it is client-side Firebase configuration, not a private provider secret or a credential to use for a new service. The connected GitHub integration and the GitHub Actions job's automatically issued `GITHUB_TOKEN` already provide repository access where authorised. Do not invent a provider or silently add one.

The owner may use a provider offering free, usage-limited credits and 24-hour-expiring API keys. That reduces exposure, but expiry is **not** a substitute for least privilege or bounded spending. Nothing here requires the key to be pasted into ChatGPT.

## Recommended flow: the human enters a short-lived key once

1. **Decide what the key actually authorises**: provider name, specific endpoint, credit/requests cap, creation and expiry time (UTC), and whether it belongs to the agent inference side, a remote browser service or another integration. Keep the game simulation usable with no key.
2. **Owner creates a dedicated sandbox credential** at the provider. Prefer ≤24-hour expiry and the narrowest scope; set provider-side cost/usage caps where available. Do not reuse a personal account's primary key.
3. **Owner enters the value in GitHub**, not chat: repository Settings → Environments → create/choose `agent-lab-credentials` → Environment secrets → Add secret, named provisionally `SANDSPIEL_LAB_PROVIDER_API_KEY`. This is a proposed name, not a currently configured secret. GitHub documents environment-scoped secret injection and approvals. Alternatively use a repository Actions secret for a tiny experiment if environments are unsuitable.
4. **Only after review**, add a dedicated Actions job that declares `environment: agent-lab-credentials` and explicitly maps that secret into a narrow, tested **server-side** client. Keep this separate from the current no-secret physics-build and gameplay smoke workflows. Do not expose the key through `agent.html`, JavaScript bundles, GitHub Pages, session JSON, logs or artifact files.
5. The chat agent submits **typed commands or requests**, not credentials. The credential-bearing job calls the provider, then returns a sanitized result, usage metadata and error category (never full headers/tokens). Prefer dedicated budget and rate limits; fail closed if no key exists, the provider rejects it, or expiry is reached.
6. Rotate or revoke after the session or at the specified expiry. Remove old secrets when no longer needed. Never assume GitHub Actions log masking is a guarantee against deliberate exfiltration.

## Why this distinction matters

- **Chat uses the existing GitHub connection:** no new third-party API key is needed for source edits, workflow-run inspections or artifact retrieval.
- **Actions calls an external provider:** store the provider secret in Actions and run only an allowlisted, reviewed client on GitHub's runner. Chat does not need to see the secret.
- **A future direct ChatGPT plugin/MCP needs the key:** a separately hosted authenticated backend should hold it and expose narrow actions. An encrypted secret in the repository does not magically make that key available to chat tools or to GitHub Pages clients.
- **Provider supports OIDC/federated identity:** prefer job-scoped tokens, avoiding even the 24-hour shared key, if provider support and trust conditions can be verified.

## Security and cost boundaries

- Treat **external key expiry, credit allowance, per-minute request ceiling and total-run cap** as independent controls. A free-credit key can still be abused or leak other account information.
- Only run credential-enabled jobs on explicitly selected, reviewed branches and GitHub environments; do not expose secrets to forked-PR code or untrusted JSON commands.
- Limit HTTP origin and API operations in the server-side client. Do not accept arbitrary URL, shell, JavaScript, function or arbitrary-header inputs from GitHub issue comments or JSON session files.
- Prevent use of `printenv`, `set -x`, header dumps, verbose SDK traces, unredacted exceptions, crash reports and artefact capture of credential variables. Avoid credentials in process arguments.
- Return a safe receipt: provider alias, requested operation, credits/requests used if available, expiry timestamp, accepted/denied result, and a redacted correlation ID. Never return a token or full request header.
- Changes to build code, third-party dependencies, cache keys or executable scripts should not bypass approval for a credential-bearing job. Do not give a general experimental browser session access to secrets simply because its tests pass.
- Never embed credentials in a static site: all HTML, browser JavaScript and Pages assets are public to anyone who can access the site.

## Implementation questions before any key is provisioned

- Which provider and API endpoint is intended? Is this for **model inference**, **browser automation**, **remote session hosting** or something else?
- Does the provider support an API token restricted by origin, endpoint, request count or spend, and automatic 24-hour expiry?
- Must the ChatGPT session directly invoke the service, or is GitHub Actions batch execution sufficient?
- What should happen when a key expires mid-session? Proposed default: stop credentialed operations, preserve safe local gameplay and report `credentials_expired`.
- Are provider request/usage receipts private? Define what can be included in public Actions artifacts.

**Current implementation decision:** document the handover without enabling an external API, inserting placeholder secrets into running workflows or requesting a real credential. The runner already works without one.

## References

- GitHub [Using secrets in Actions](https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets)
- GitHub [Deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- GitHub [OIDC](https://docs.github.com/en/actions/concepts/security/openid-connect)
