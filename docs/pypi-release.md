# First PyPI release

The user authorized a public PyPI release on November 1, 2026. The devswarm JSON endpoint
returned 404 at the availability check. No package name has been reserved or registered yet.
Publication is currently blocked only by owner-account setup: the user does not have a PyPI account.
No token is configured locally, and no package upload has been attempted.

## Install now, without a PyPI account

```sh
pip install "git+https://github.com/rishiparpyaninortheastern/devswarm.git"
devswarm demo
```

This uses the public GitHub source and needs Python 3.11+ and Git. It is distinct from publishing
to the PyPI index; `pip install devswarm` will work only after the first successful PyPI upload.

## One-time owner setup

1. The owner registers at https://pypi.org/account/register/, verifies their email, and completes
   PyPI's required authentication/2FA setup. The owner handles passwords, recovery codes and terms.
2. Open https://pypi.org/manage/account/publishing/ and add a pending GitHub publisher:

   | Field | Value |
   |---|---|
   | PyPI project name | `devswarm` |
   | GitHub owner | `rishiparpyaninortheastern` |
   | Repository | `devswarm` |
   | Workflow filename | `publish.yml` |
   | Environment | `pypi` |

3. Confirm the publisher under the intended owner account. This grants only the named workflow
   identity permission to create/publish this PyPI project. Never paste credentials into the chat
   or commit an API token. No static GitHub/PyPI secret is required for Trusted Publishing.
4. Open GitHub Actions, choose **Publish to PyPI**, select **Run workflow** on `main`, and set
   version `0.1.0`. The workflow validates the version, runs the regression suite, builds and checks
   distributions, and tests a clean wheel install before its publish job can run.
5. The publish job uses the `pypi` environment and short-lived OIDC credentials. The first successful
   upload creates the project. If additional environment approvals are configured, the owner must
   approve that run. Recheck name availability immediately before the first release.

## Completion verification

After the workflow succeeds, verify https://pypi.org/project/devswarm/ and, in a fresh environment:

```sh
pip install --index-url https://pypi.org/simple/ devswarm==0.1.0
devswarm --version
devswarm demo
```

Update public installation instructions only after this verification. A failed upload is not a release;
inspect the Actions error before retrying. Uploaded filenames/versions cannot be silently replaced.

References:
- https://docs.pypi.org/trusted-publishers/creating-a-project-through-oidc/
- https://docs.pypi.org/trusted-publishers/using-a-publisher/
