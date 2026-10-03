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
