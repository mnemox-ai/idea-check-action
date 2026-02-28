# idea-check-action

Pre-build reality check for your ideas — as a GitHub Action.

Powered by [idea-reality-mcp](https://github.com/mnemox-ai/idea-reality-mcp). Scans GitHub, Hacker News, npm, PyPI, and Product Hunt for existing solutions, then returns a reality signal (0-100) so you know what you're getting into before writing code.

## Quick Start

### Run on every Pull Request

```yaml
name: Idea Check
on:
  pull_request:
    types: [opened]

jobs:
  check:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4

      - uses: mnemox-ai/idea-check-action@main
        id: idea
        with:
          idea: "Real-time collaborative markdown editor with AI suggestions"
          depth: quick

      - name: Post result as PR comment
        uses: actions/github-script@v7
        with:
          script: |
            const score = '${{ steps.idea.outputs.score }}';
            const top = '${{ steps.idea.outputs.top-competitor }}';
            const body = `## Idea Reality Check\n\n` +
              `**Reality Signal:** ${score}/100\n` +
              `**Top Competitor:** ${top}\n\n` +
              `> Powered by [idea-reality-mcp](https://github.com/mnemox-ai/idea-reality-mcp)`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

### Run when an issue is labeled "idea"

```yaml
name: Idea Check from Issue
on:
  issues:
    types: [labeled]

jobs:
  check:
    if: github.event.label.name == 'idea'
    runs-on: ubuntu-latest
    permissions:
      issues: write
    steps:
      - uses: actions/checkout@v4

      - uses: mnemox-ai/idea-check-action@main
        id: idea
        with:
          idea: ${{ github.event.issue.body }}
          depth: deep

      - name: Post result as issue comment
        uses: actions/github-script@v7
        with:
          script: |
            const score = '${{ steps.idea.outputs.score }}';
            const top = '${{ steps.idea.outputs.top-competitor }}';
            const body = `## Idea Reality Check\n\n` +
              `**Reality Signal:** ${score}/100\n` +
              `**Top Competitor:** ${top}\n\n` +
              `> Powered by [idea-reality-mcp](https://github.com/mnemox-ai/idea-reality-mcp)`;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body
            });
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `idea` | Idea description text or path to a proposal file | Yes | — |
| `depth` | `quick` (GitHub + HN) or `deep` (all 5 sources) | No | `quick` |
| `github-token` | GitHub token for API access | No | `${{ github.token }}` |
| `threshold` | Reality signal threshold that triggers a warning | No | `70` |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `score` | Reality signal (0-100). Higher = more competition | `82` |
| `report` | Full JSON report with evidence and pivot hints | `{"reality_signal": 82, ...}` |
| `top-competitor` | Name and star count of the top similar project | `dnscheck (1.2k stars)` |

## Advanced Usage

### Custom threshold with deep scan

```yaml
- uses: mnemox-ai/idea-check-action@main
  id: idea
  with:
    idea: "AI-powered code review bot for GitHub PRs"
    depth: deep
    threshold: "85"
```

### Read idea from a file

```yaml
- uses: mnemox-ai/idea-check-action@main
  with:
    idea: "./docs/proposal.md"
```

### Fail-safe design

The action never breaks your CI pipeline. If the reality check fails (network issues, API rate limits, etc.), it prints a `::warning::` and exits with code 0. Downstream steps will see `score=0` and `report={}` as fallback values.

### Use the full report in subsequent steps

```yaml
- uses: mnemox-ai/idea-check-action@main
  id: idea
  with:
    idea: "Kubernetes cost optimizer with ML predictions"
    depth: deep

- name: Parse report
  run: |
    echo '${{ steps.idea.outputs.report }}' | jq '.pivot_hints'
```

## How it works

1. Extracts keywords from your idea description
2. Searches GitHub repos, Hacker News, npm, PyPI, and Product Hunt in parallel
3. Computes a weighted reality signal based on existing solutions
4. Returns the score, top competitors, and pivot suggestions

## Links

- [idea-reality-mcp](https://github.com/mnemox-ai/idea-reality-mcp) — the core engine (MCP server + Python package)
- [Mnemox AI](https://mnemox.ai) — builder tools for AI-native workflows

## License

MIT License. See [LICENSE](LICENSE).
