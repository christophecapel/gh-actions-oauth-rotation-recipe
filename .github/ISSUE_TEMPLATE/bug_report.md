---
name: Bug report
about: Something broke: workflow, script, test, or doc
title: "[bug] "
labels: bug
---

## What broke

<!-- Describe the failure. What command/step did you run? What did you expect? What actually happened? -->

## Provider

<!-- Which OAuth provider are you using? Fitbit / Strava / Whoop / Oura / Spotify / other -->

## Relevant logs

<!-- Paste the relevant log lines from the failed run.
     IMPORTANT: redact any token values, client secrets, or PATs before pasting.
     Look for lines starting with [refresh], [secret-update], or [push]. -->

```
(paste here)
```

## Rotation invariant log line

<!-- If your run produced the invariant line, paste it. Looks like:
     [refresh] Rotation invariant: file_persisted=True secret_updated=True
     This single line usually identifies the broken sink. -->

## Environment

- Python version: <!-- e.g. 3.11 -->
- Runner: <!-- GitHub Actions / local / self-hosted -->
- Recipe version / commit: <!-- e.g. v1.0.0 or commit SHA -->

## Anything else

<!-- Workarounds you tried, related issues, anything that might help. -->
