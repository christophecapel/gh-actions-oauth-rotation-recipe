# Banner brief: gh-actions-oauth-rotation-recipe

> Spec for `banner.png` (repo header image). The current `banner.png` was generated 2026-05-11, **before** the v1.0.0 durable-provider reframe: verify it against this brief before launch, regenerate if it leads with Fitbit.

## Format

- **Dimensions:** 1280 × 640 (matches the `claude-mechanisms` / `claude-mechanisms-tools` pair visual template)
- **File:** `banner.png` at repo root, referenced as `![Banner](banner.png)` at top of README
- **Tool:** ChatGPT image mode (preferred for hero/cinematic art per house style; cinematic-composition-first prompt)

## Thesis the banner must carry

Single-use OAuth refresh-token rotation for GitHub Actions: **provider-agnostic**, durable. NOT a Fitbit banner. The reframe moved Fitbit to "origin incident" only; the banner should not headline Fitbit (it is the deprecation target).

## Content rules

- **No tier-anchor or concrete counts** on the banner (durable surface: no "10 tests", "3 failure modes", "20+"). House rule: counts live on dated artifacts, not durable surfaces.
- Lead with the pattern, not a provider logo. If any provider is implied, keep it generic (a rotating-token / chain-of-custody visual), not a Fitbit/Google Health logo.
- Visual family must read as a sibling of the `claude-mechanisms` pair (same palette / type treatment) so the profile pins look like a set.
- MIT-licensed, open-source drop tone: clean, technical, confident. No stock-photo cliché.

## Suggested subtitle (if text used)

> Single-use OAuth token rotation for GitHub Actions: atomic persistence, push retry, fallback instrumentation.

## Pre-launch check

- [ ] Existing `banner.png` does NOT headline Fitbit (or regenerate)
- [ ] No concrete counts baked into the image
- [ ] Reads as a sibling to the claude-mechanisms pair banners
- [ ] 1280 × 640, renders cleanly at GitHub README width
