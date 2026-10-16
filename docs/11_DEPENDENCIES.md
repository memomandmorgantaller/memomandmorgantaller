# Dependencies and supply-chain record

Python 3.12; runtime dependencies are pypdf and defusedxml only. SQLite is supplied
by Python. No model weights, external inference, telemetry or upload credentials.
The universal-wheel `baseline/rfp_registry_m1/requirements.lock` includes exact versions
and SHA-256 hashes for runtime, tests and build backend (including Windows colorama).
Fresh installation used `--require-hashes`, then `--no-deps --no-build-isolation`
for this local source. TLS/checksum verification was never disabled.
Installation needs approved PyPI/artifact hosts or an approved verified internal mirror.
Processing is offline. See the operator README for failure modes and safe defaults.

Licenses from downloaded distribution metadata (full notices remain in installed
packages; organizational license approval is still a deployment gate):

| Distribution | Version | Declared license |
|---|---|---|
| colorama | 0.4.6 | License :: OSI Approved :: BSD License |
| defusedxml | 0.7.1 | PSFL |
| iniconfig | 2.3.1 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.7.0 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pypdf | 6.21.0 | BSD-3-Clause |
| pytest | 9.1.1 | MIT |
| setuptools | 84.0.0 | MIT |
| wheel | 0.46.2 | MIT |

Ruff 0.17.1 (MIT), mypy 2.4.0 (MIT) and pip-audit 2.10.1 (Apache-2.0) ran in a separate
tooling venv. CI's Ruff/mypy are version-pinned, outside the universal-wheel hash lock.

## Advisory result

2026-10-16: `pip-audit 2.10.1 --no-deps --disable-pip -r requirements.lock` using PyPI
advisories found **no known vulnerabilities in the final lock**. Initial wheel 0.45.1
was rejected for CVE-2026-24049 and replaced with fixed 0.46.2 before fresh validation.
No application artifacts depend on the rejected version. This point-in-time result
is not a guarantee: repeat before release. Review version/license/advisory changes,
obtain authenticated approved artifacts and rerun regressions when refreshing hashes;
never replace a hash merely to bypass a verification failure.
