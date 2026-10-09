# Development and publication

Read [contributing](../CONTRIBUTING.md), [AGENTS.md](../AGENTS.md) and the current
README. [The roadmap](roadmap.md) is the sole active priority plan;
[the gaps](gaps.md) are evidence. This follows Irreducible's coherent branches, checkpoint backup,
deliberate review and verified cleanup. Prospector's tests should reflect its
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
the latest integrated candidate after dependencies change. The owner gives
standing authorization for agents to review their own PRs in a separate deliberate
pass and merge ready changes without asking again. Inspect the complete final
diff, fix actionable findings, resolve conversations and require applicable green
CI on the latest integrated head and up-to-date base. No separate human reviewer
is required. Record the review conclusion and actual checks; scientific evidence
remains a separate gate. Verify the exact head and use a merge commit directly
once ready; GitHub's auto-merge setting need not be enabled. Direct `main` pushes,
force pushes and external messages still require specific authorization.

## Coordinate a consumer handoff

One owner integrates each repository; the coordinator controls shared interfaces
and independent final review. Pin Prospector candidate/reference hashes in the
Reproducible experiment, then pin its inputs and Irreducible revision/build.
Keep source review, numerical acceptance, PR review and exact-main CI distinct.
The shared roadmap programme shares four local compiler/compute jobs across all
chats and worktrees, with at most one light job in Prospector. It adds no worker
launch entitlement. Preserve the bounded research queue and existing alternatives.
Publish this task's Site changes only after the reviewed repository merge.

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
