# Releasing QumPy on PyPI

QumPy is uploaded to PyPI by the GitHub workflow
[`.github/workflows/publish.yml`](.github/workflows/publish.yml), using
**trusted publishing**: PyPI trusts this repository's workflow directly, so no
API token or password is stored anywhere.

The workflow builds the sdist and wheel, checks them with `twine check`,
installs the wheel, runs the test suite against it, and only then uploads.

| Trigger | Uploads to |
|---|---|
| Publishing a GitHub release (tag `v0.1.0`, …) | **PyPI** |
| Actions → *Publish to PyPI* → *Run workflow* | **TestPyPI**, for a dry run |

## One-time setup (done by the project owner)

1. **Create accounts** on <https://pypi.org> and <https://test.pypi.org>. They
   are separate sites with separate accounts. Both require two-factor
   authentication.
2. **Register the trusted publisher on TestPyPI.** Go to *Your account →
   Publishing → Add a new pending publisher* and fill in:

   | Field | Value |
   |---|---|
   | PyPI Project Name | `qumpy` |
   | Owner | `yigitcaneym` |
   | Repository name | `QumPy` |
   | Workflow name | `publish.yml` |
   | Environment name | `testpypi` |

3. **Register the trusted publisher on PyPI** the same way, with environment
   name **`pypi`**.

"Pending" means the project doesn't exist yet: the first successful upload
creates it and makes you its owner.

## Dry run on TestPyPI

1. On GitHub: *Actions → Publish to PyPI → Run workflow*.
2. When it is green, install from TestPyPI in a fresh environment. The extra
   index is needed because Qiskit and the other dependencies come from the real
   PyPI:

   ```bash
   pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ "qumpy[noisy]"
   ```

3. Check it: `python -c "import qumpy as qp; qp.versions()"`.

A version number can be uploaded **only once** to each index, even if you
delete it later. For a second dry run, bump the version first (for example
`0.1.0.dev1`).

### If PyPI rejects the name

PyPI refuses new names that are too similar to popular projects, and `qumpy`
is one letter away from `numpy`. If the upload fails with *"too similar to an
existing project"*:

1. Choose another distribution name, for example `qumpy-qc`, and change
   `name = "qumpy"` in `pyproject.toml`. Users then run
   `pip install qumpy-qc`, but the code stays `import qumpy`.
2. Update the trusted publishers on PyPI and TestPyPI to the new name.
3. Update the PyPI project links in `publish.yml` (`https://pypi.org/p/...`).

## Releasing

1. Make sure the **Tests** workflow is green on `main`.
2. Set the version in `qumpy/__init__.py` (`__version__ = "0.1.0"`). It is
   the only place the version is written; `pyproject.toml` reads it from there.
3. Change the install instructions from the GitHub `.zip` link to PyPI, in
   `README.md`, `docs/installation.md`, `docs/index.md` and
   `examples/Simple_Example.ipynb`:

   ```bash
   pip install "qumpy[noisy]"
   ```

4. Commit and push.
5. On GitHub: *Releases → Draft a new release*, create the tag **`v` +
   version** (e.g. `v0.1.0`), write a few lines about what changed, and click
   *Publish release*. The workflow refuses to upload if the tag doesn't match
   `__version__`.
6. Watch *Actions → Publish to PyPI*. When it is green, the package is on
   <https://pypi.org/project/qumpy/> and `pip install qumpy` works.

## Building by hand (optional)

```bash
pip install build twine
```

```bash
python -m build
```

```bash
twine check --strict dist/*
```

This creates `dist/qumpy-<version>.tar.gz` and
`dist/qumpy-<version>-py3-none-any.whl`. Uploading by hand would need a PyPI
API token (`twine upload dist/*`). The workflow above is the recommended way.
