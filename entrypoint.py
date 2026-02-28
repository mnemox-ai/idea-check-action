#!/usr/bin/env python3
"""
Idea Reality Check — GitHub Action entrypoint.

Scans GitHub, HN, npm, PyPI & Product Hunt for existing solutions,
then computes a reality signal (0-100) for the given idea.
"""

import asyncio
import json
import os
import sys
from pathlib import Path


def write_output(name: str, value: str) -> None:
    """Write a key=value pair to GITHUB_OUTPUT (multiline-safe)."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        delimiter = "EOF_IDEA_CHECK"
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(f"{name}<<{delimiter}\n{value}\n{delimiter}\n")
    else:
        # Local testing fallback
        print(f"::set-output name={name}::{value}")


def write_fallback_outputs() -> None:
    """Write safe fallback outputs so downstream steps don't break."""
    write_output("score", "0")
    write_output("report", "{}")
    write_output("top-competitor", "N/A")


async def run() -> None:
    idea_raw = os.environ.get("INPUT_IDEA", "").strip()
    depth = os.environ.get("INPUT_DEPTH", "quick").strip().lower()
    github_token = os.environ.get("INPUT_GITHUB_TOKEN", "").strip()
    threshold = int(os.environ.get("INPUT_THRESHOLD", "70"))

    if not idea_raw:
        print("::error::No idea provided. Set the 'idea' input.")
        sys.exit(1)

    # If the idea looks like a file path and the file exists, read it
    idea_text = idea_raw
    if len(idea_raw) < 260 and not "\n" in idea_raw:
        candidate = Path(idea_raw)
        if candidate.is_file():
            print(f"Reading idea from file: {candidate}")
            idea_text = candidate.read_text(encoding="utf-8").strip()

    if not idea_text:
        print("::error::Idea text is empty (file was empty or input was blank).")
        sys.exit(1)

    # Expose GitHub token for the GitHub search API adapter
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    print(f"Idea: {idea_text[:120]}{'...' if len(idea_text) > 120 else ''}")
    print(f"Depth: {depth}")
    print(f"Threshold: {threshold}")
    print("---")

    try:
        from idea_reality_mcp.scoring.engine import compute_signal, extract_keywords
        from idea_reality_mcp.sources.github import search_github_repos
        from idea_reality_mcp.sources.hn import search_hn

        keywords = extract_keywords(idea_text)
        print(f"Keywords: {keywords}")

        # Parallel source queries
        if depth == "deep":
            from idea_reality_mcp.sources.npm import search_npm
            from idea_reality_mcp.sources.producthunt import search_producthunt
            from idea_reality_mcp.sources.pypi import search_pypi

            github_results, hn_results, npm_results, pypi_results, ph_results = (
                await asyncio.gather(
                    search_github_repos(keywords),
                    search_hn(keywords),
                    search_npm(keywords),
                    search_pypi(keywords),
                    search_producthunt(keywords),
                )
            )

            report = compute_signal(
                idea_text,
                keywords,
                github_results,
                hn_results,
                depth,
                npm_results=npm_results,
                pypi_results=pypi_results,
                ph_results=ph_results,
            )
        else:
            github_results, hn_results = await asyncio.gather(
                search_github_repos(keywords),
                search_hn(keywords),
            )

            report = compute_signal(
                idea_text,
                keywords,
                github_results,
                hn_results,
                depth,
            )

        score = report.get("reality_signal", 0)
        top_similars = report.get("top_similars", [])

        # Build top-competitor string
        if top_similars:
            top = top_similars[0]
            top_name = top.get("name", "unknown")
            top_stars = top.get("stars", 0)
            top_competitor = f"{top_name} ({top_stars} stars)"
        else:
            top_competitor = "None found"

        # Write outputs
        write_output("score", str(score))
        write_output("report", json.dumps(report, ensure_ascii=False))
        write_output("top-competitor", top_competitor)

        # Summary
        print(f"\nReality Signal: {score}/100")
        print(f"Duplicate Likelihood: {report.get('duplicate_likelihood', 'N/A')}")
        print(f"Top Competitor: {top_competitor}")

        if top_similars:
            print("\nTop Similar Projects:")
            for i, proj in enumerate(top_similars[:5], 1):
                name = proj.get("name", "?")
                stars = proj.get("stars", 0)
                url = proj.get("url", "")
                print(f"  {i}. {name} ({stars} stars) — {url}")

        pivot_hints = report.get("pivot_hints", [])
        if pivot_hints:
            print("\nPivot Hints:")
            for hint in pivot_hints:
                print(f"  - {hint}")

        # Threshold warning
        if score > threshold:
            print(
                f"\n::warning::Reality signal {score} exceeds threshold {threshold}. "
                f"High competition detected — consider pivoting or differentiating."
            )

    except Exception as exc:
        print(f"\n::warning::Idea reality check failed: {exc}")
        print("Continuing gracefully — CI pipeline will not be blocked.")
        write_fallback_outputs()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(run())
