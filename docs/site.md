# Public site

[Open Prospector](https://prospector-cosmology.sprajs.chatgpt.site).

`site/` holds the source interface, scientific data projection and abstract loader.
`register/map.html` is the generated local mirror; a plain file server can display
the tree but uses external arXiv links for abstracts. The public Worker provides
the on-demand abstract endpoint.

Connections includes a source-publication timeline using reviewed relationships.
It labels version updates separately; it does not infer idea ancestry from dates.
Paper details show available dated citation/author visibility snapshots, with
unmeasured values and insufficient comparison cohorts explicit. Bibliography
links within this register remain separate from provider-wide citation counts.

Prospect details expose their candidate investigations with equations, conditioning
and unresolved gates. Additional source contracts are associated by an exact
subset of the prospect's registered paper identities. This is navigation, not
an accepted physical component or graph relationship. Both projections exclude
worker records, local source paths and consumer requests.

## Build and preview

```bash
uv run python scripts/build_register.py
python3 scripts/publish_site_assets.py
uv run python scripts/prepare_site.py
node .work/site-hosting/dev.mjs
```

The local preview is `http://127.0.0.1:8892/`. Public source is copied to the ignored
`.work/site-hosting/` checkout and built there. The allowlist is exactly the
registered pinned versions. Runtime requests fetch descriptive metadata from
`export.arxiv.org/abs/<id>vN`; they verify the page's version and title, read at most
256 KiB and time out after 20 seconds. Successful metadata is cached temporarily
for 24 hours. Requests coalesce and serialize within each Worker isolate, with
at least 3.1 seconds between completed acquisitions; this is not a cross-isolate
API rate limiter. The endpoint does not use the legacy API/RSS. It does not retry
failed access, and HTTP 429 imposes a cooldown. The browser always retains the
original arXiv abstract/PDF links. arXiv permits use of descriptive metadata under
its [API terms](https://info.arxiv.org/help/api/tou.html); full paper content is
never served by Prospector.

## Publish the same Site

Use the Sites building/hosting skills. Reuse the exact `project_id` in
`site/.openai/hosting.json`; do not create another Site. For later updates, retrieve
this Site and open its source through the official `site-workflow.mjs` helper
before replacing the exported public files. Preserve advanced remote edits and
resolve divergence rather than overwriting it.

After record and interface checks, copy the current `site/` export with
`prepare_site.py`. Use the helper's returned checkout path. Push source and package
that same commit through `site-workflow.mjs`, with the archive inside `.work/site/`.
Set `TMPDIR` to a directory inside `.work/site/` so packaging intermediates stay
inside Prospector. Supply the short-lived credential only through hidden stdin;
never put it in files, command arguments, commits or logs.

Save a version using the exact pushed SHA and archive, then deploy that saved
version through Sites. Preserve the public audience. Only deployment success
confirms publication. Record the public version/source mapping in `site/publication.json`,
update README if the returned URL changes, and open that URL in the app.
Stop the preview server after successful publication. Repo PRs follow the standing
review/green-CI/merge authorization in [development](development.md).

## Immutable public assets

Sites still serves the HTML and `/api/abstract`. CloudFront serves the exact
public register JSON, stylesheet, interface script and logo from the separate
private `prospector-web-assets-436908790672-eu-west-2` bucket. The research archive
is not a website origin and its policies/retention are not modified.
`site/assets-config.json` identifies the deployed infrastructure;
`infrastructure/site-assets.json` is its CloudFormation definition. CloudFront
uses signed origin access, HTTPS and read-only access to `assets/*`. S3 blocks
public access, enforces bucket ownership and TLS, keeps versions and requires
create-only conditional writes. There is no object expiry or deployment deletion.
The narrowly scoped `prospector-assets-deployer` role trusts only `research-local`,
can list `assets/`, and can read/write assets; it cannot administer infrastructure,
read research data or delete objects. Administrative setup uses the separately
authorized local administrative session, never browser code.

An authorized administrator can recreate/update the stack with:

```bash
aws cloudformation deploy --profile research-admin --region eu-west-2 \
  --stack-name prospector-site-assets --template-file infrastructure/site-assets.json \
  --capabilities CAPABILITY_NAMED_IAM
aws configure set role_arn arn:aws:iam::436908790672:role/prospector-assets-deployer --profile prospector-assets
aws configure set source_profile research --profile prospector-assets
aws configure set region eu-west-2 --profile prospector-assets
```

Check the actual stack outputs against `site/assets-config.json`. These settings
contain no credentials; the role obtains short-lived credentials through the
existing local profile. Do not broaden the restricted cloud research identity.

For each publication, open/fetch the existing hosted source first as described
above, reconcile any changes, then run from the Prospector repository root:

```bash
uv run python scripts/build_register.py
python3 scripts/publish_site_assets.py
uv run python scripts/prepare_site.py --destination /ABSOLUTE/HELPER/CHECKOUT
```

Use the actual opened helper checkout, inside this repository's ignored `.work`.
The uploader selects exactly four generated public files, uses atomic
`If-None-Match: *` writes, reuses only identical objects, downloads every exact
S3 VersionId, checks anonymous CloudFront bytes/CORS/content types/cache headers,
and writes `site/assets-release.json` only after success. The release pins hashes,
lengths, URLs, versions and the register/abstract allowlist input identity. Builds
refuse a stale or missing release; no Site publication should precede verification.
The Worker keeps only paper IDs/titles needed by the abstract allowlist. It does
not serve a second copy of the JSON or external assets.

All asset URLs contain their full SHA256. CloudFront negotiates gzip/Brotli for
eligible files and caches them for one year with `immutable`; unchanged CSS,
JavaScript and images keep the same URLs across register updates. CORS allows
anonymous public reads from any origin, without credentials. CSS/JavaScript use
SRI; register bytes are checked against their SHA256 before rendering. The page
shows loading, an explicit failure and a reload-based Retry. Retain old assets
for old saved Site versions; rollback means redeploying the prior Sites version.
`register/map.html` remains the self-contained offline mirror.

For local-only checks without AWS, use `node site/build.mjs --local-assets` then
`node site/dev.mjs`. Local mode serves exactly the same four generated assets;
production builds require the verified CloudFront release. Add `?performance=1`
to capture browser timing/transfer measurements in the root element's
`data-prospector-performance` attribute without adding interface chrome. Record
cold and repeated loads separately; network timings are environment-specific.
