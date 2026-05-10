---
name: Provider gotcha
about: A provider-specific quirk that should be documented in adoption.md
title: "[gotcha] <provider>: "
labels: docs, provider-gotcha
---

## Provider

<!-- Fitbit / Strava / Whoop / Oura / Spotify / Notion / Hubspot / other -->

## The quirk

<!-- What's different about this provider's OAuth flow that adopters need to know?
     Examples: client_id/secret in body vs header, refresh-token-doesn't-rotate, scope changes
     break tokens, custom revocation rules, weird rate limits on the token endpoint. -->

## What had to change in the recipe to make it work

<!-- Was it a config tweak (env var)? A code change (Basic auth → body)?
     A workflow yaml change (different secret name)? Be specific. -->

## Suggested addition to docs/adoption.md

<!-- Draft a paragraph or two for the provider-specific gotchas section.
     If you've already used the recipe with this provider successfully, you're
     the best person to write this. PRs welcome. -->

## Working setup (optional)

<!-- If you have a public repo using this recipe with this provider, link it here.
     Other adopters benefit from a reference implementation. -->
