# Contributing

This repository uses **Conventional Commits** and automated semantic releases.

## Why

We use Conventional Commits so that:

- commit history is easier to understand
- changelogs can be generated automatically
- version bumps happen consistently based on the type of change

This repository uses automated releases based on commit history:

- `fix:` changes trigger a **patch** release (`0.0.X`)
- `feat:` changes trigger a **minor** release (`0.X.0`)
- commits marked as **breaking changes** trigger a **major** release (`X.0.0`)

---

## Commit message format

Use this format:

    <type>[optional scope][optional !]: <description>

    [optional body]

    [optional footer(s)]

### Parts of the format

- **type**: the kind of change being made
- **scope**: optional area of the repo affected, such as `terraform`, `gcp`, `docs`, `network`, `ci`, etc.
- **!**: optional marker for a breaking change
- **description**: short summary of the change
- **body**: optional longer explanation
- **footer**: optional metadata, notes, or breaking change details

Example:

    feat(terraform): add partner logging sink module

Example with scope and breaking change:

    feat(terraform)!: rename module inputs for partner deployment

Example with body and footer:

    fix(gcp): correct firewall rule target tags

    The previous target tags prevented the health check rule from applying
    to the intended instances.

    Refs: #42

---

## Supported commit types

This repository allows the following commit types.

### `feat`
A new feature or capability.

    feat(terraform): add support for partner log export

### `fix`
A bug fix.

    fix(gcp): correct firewall target tag for health checks

### `docs`
Documentation-only changes.

    docs(readme): clarify partner setup steps

### `style`
Formatting, whitespace, or other non-functional style-only changes.

    style(terraform): reformat module locals

### `refactor`
A code change that is neither a feature nor a fix.

    refactor(network): simplify VPC module variable handling

### `perf`
A performance improvement.

    perf(terraform): reduce redundant provider lookups

### `test`
Adding or updating tests.

    test(terraform): add validation test coverage for subnet inputs

### `build`
Changes to the build system, packaging, or dependencies.

    build(actions): pin action versions

### `ci`
Changes to CI/CD workflows or automation.

    ci(release): add release-please workflow

### `chore`
General maintenance or housekeeping that does not fit another category.

    chore(repo): update contributing guide

### `revert`
Reverting a previous commit.

    revert: revert "feat(terraform): add partner logging sink module"

---

## Optional scope values

The scope is optional, but recommended when it helps clarify the affected area.

Common examples for this repository may include:

- `terraform`
- `gcp`
- `aws`
- `cos`
- `network`
- `partner`
- `logging`
- `monitoring`
- `docs`
- `readme`
- `ci`
- `release`
- `github-actions`
- `security`

Examples:

    feat(terraform): add new partner module
    fix(logging): correct sink destination
    docs(security): clarify IAM requirements
    ci(github-actions): enforce conventional commits

You are not strictly limited to the examples above. Use a short, meaningful scope when helpful.

---

## Breaking changes

Breaking changes indicate a change that is not backward compatible.

A breaking change causes a **major version bump**.

You can mark a breaking change in either of these ways.

### Option 1: add `!` after the type or scope

    feat(terraform)!: rename partner module inputs

    refactor(network)!: remove legacy subnet variable format

### Option 2: add a `BREAKING CHANGE:` footer

    feat(terraform): redesign partner deployment inputs

    BREAKING CHANGE: renamed `partner_region` to `region`

Use the footer when the change needs more explanation.

---

## Optional body

Use the body to explain:

- why the change was needed
- important implementation details
- migration considerations
- context that would help reviewers

Example:

    fix(logging): correct log sink filter

    The previous filter excluded startup messages that are still needed
    for debugging partner node initialization.

---

## Optional footers

Footers can be used for references and metadata.

Examples:

    fix(gcp): correct backend health check port

    Refs: #101

    docs(readme): add release workflow documentation

    Closes: #87

    feat(terraform): add new module inputs

    Reviewed-by: @example-user

The most important footer is:

    BREAKING CHANGE: <description>

That footer triggers a major release.

---

## Good commit examples

    feat(terraform): add module for partner logging
    fix(cos): correct container restart policy
    docs(contributing): add conventional commit guidance
    ci(release): configure release-please
    refactor(network): simplify subnet variable usage
    test(terraform): add validation for partner input variables
    build(actions): pin workflow dependencies
    perf(logging): reduce duplicate log processing
    chore(repo): clean up old workflow files
    revert: revert "feat(terraform): add temporary debug outputs"

---

## Bad commit examples

    updated stuff
    fix stuff
    changes
    WIP
    misc
    terraform updates
    another change

These are too vague and will usually fail linting.

---

## Pull request requirements

All pull requests to `main` must pass the commit lint check before they can be merged.

If your pull request contains multiple commits, **each commit** should follow the Conventional Commit format.

If the repository uses **squash merge**, the **pull request title** should also follow Conventional Commits, because the final squash commit message may be based on the PR title.

Good PR title examples:

    feat(terraform): add partner log export support
    fix(ci): correct release workflow permissions
    docs(readme): document deployment prerequisites

---

## Release behavior

Releases are created automatically from merged commits on `main`.

Version bumps are determined from commit history:

### Patch release
For backward-compatible bug fixes:

    fix(network): correct subnet route propagation

Result:

    0.0.X

### Minor release
For backward-compatible new features:

    feat(gcp): add support for partner log export

Result:

    0.X.0

### Major release
For breaking changes:

    feat(api)!: remove legacy partner config format

or

    feat(api): redesign partner config format

    BREAKING CHANGE: removed support for legacy config fields

Result:

    X.0.0

---

## Quick reference

### Small bug fix
    fix(terraform): correct variable default

### New feature
    feat(logging): add partner sink support

### Docs only
    docs(readme): add conventional commit examples

### CI update
    ci(actions): add commitlint workflow

### Breaking change
    feat(terraform)!: rename partner deployment variables

---

## Summary

When in doubt, use:

    <type>(<scope>): <description>

Most common examples:

    feat(terraform): add new feature
    fix(gcp): correct broken behavior
    docs(readme): improve documentation
    ci(release): update automation

If the change breaks compatibility, add `!` or a `BREAKING CHANGE:` footer.