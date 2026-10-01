# Development and publication

Read [contributing](../CONTRIBUTING.md), [AGENTS.md](../AGENTS.md) and the current
README. This follows Irreducible's coherent branches, checkpoint backup,
independent review and verified cleanup. Prospector's tests should reflect its
literature/provenance responsibilities rather than Irreducible's native CI matrix.

## Validate the actual change

For literature changes, check paper identity/version, primary-source locators,
source hashes, actual reading coverage, review provenance and overlap/data
relationships. Run implemented record/schema/reference validators and regenerate
browsing views as their instructions require. Structural validation does not
verify scientific truth, complete reading or licensing. Preserve corrections,
failed access and provisional/blocked candidates.

For tooling changes, exercise malformed, duplicated, changed-source and missing
records where relevant. For documentation-only changes, check local links and
truthful examples; do not start a new paper-reading campaign just to check prose.
CI is applicable when configured; do not claim that an absent check passed.

## Publish through a PR

Use a `codex/` branch for agent work. Preserve unrelated local changes and use an
isolated checkout if another worker owns the active tree. Stage explicit coherent
paths and review the staged diff. Commit meaningful checkpoints and push work
branches promptly for backup. Open a PR describing final behavior, source/check
evidence and limitations; drafts are useful for dependencies but not required for
backup. Attach created PRs to the Codex chat.

Explain dependencies on record formats or sibling repositories. Review and check
the latest integrated candidate after dependencies change. Obtain independent
review, resolve conversations and inspect all applicable CI for the current
head/base before an authorized merge. Use merge commits when checkpoint ancestry
matters; do not assume GitHub settings enforce a policy. Direct `main` pushes and
force pushes require a specific request. Branch/PR publication does not itself
authorize external messages or a merge.

## Verify a merge and preserve work

After an authorized merge, verify PR state, exact head and merge SHA. Wait for
applicable post-merge CI on that exact `main` commit. Inspect status and worktrees,
fetch/prune, prove local `main` is an ancestor of `origin/main` and update it
fast-forward-only. Before `git branch -d`, prove the feature tip equals the
verified PR head and is an ancestor of fetched `origin/main`. Preserve dirty
checkouts, extra commits and branches in active worktrees; never force-delete.
Remote branch deletion depends on repository settings. Report deferred cleanup.

If `main` fails, stop new merges, preserve evidence and repair or revert through
a focused PR under the same review/fresh-check gates. Do not weaken checks or
bypass the failure with a direct push.
