# The drift check warns; it never fails the build

When a pull request makes an API Change, the drift check posts a comment that lists each affected Page, and its check stays green. Many API Changes are intentional, and the matching docs fix often lands in a follow-up PR, so a red check would mostly train people to ignore it or bypass it. Snippets that no longer run are a different case: the snippet runner fails the build for those.

## Considered Options

- **Fail unless the PR acknowledges the Drift**, either by touching every affected Page or by carrying a `docs-not-needed` label. This is stricter and could come later, but it adds a labelling ritual before we know whether the warnings are noisy.
