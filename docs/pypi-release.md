# Published release: SwarmSleuth 0.1.0

Published November 1, 2026 via GitHub Trusted Publishing.

- PyPI: https://pypi.org/project/swarmsleuth/0.1.0/
- Release run: https://github.com/rishiparpyaninortheastern/devswarm/actions/runs/41331826023
- Release source commit: cf0c1f1
- All 66 tests, lint, distribution validation and isolated installation checks passed.
- A fresh local environment installed `swarmsleuth==0.1.0` directly from public PyPI and passed
  demo, deduplication, export, host template, overwrite guard and optional-extra smoke checks.

```sh
pip install swarmsleuth
devswarm demo
```

The CLI and Python import remain `devswarm`. PyPI rejected the original distribution name
as too similar to an existing project. The owner registered the accepted SwarmSleuth publisher
for repository `rishiparpyaninortheastern/devswarm`, workflow `publish.yml`, environment `pypi`.
No static API tokens were needed. Subsequent releases use a new version and manual workflow dispatch.
The first published README describes publication as pending because it was built before upload;
the repository documentation now records the verified release.
