# Installation

QumPy is installed straight from GitHub with `pip`. You **don't** need git.

## Requirements

* Python 3.10 or newer. Check with `python --version`.
* `pip`, which comes with Python.

## 1. (Recommended) Create a virtual environment

A virtual environment keeps QumPy and Qiskit separate from your other Python
projects. Skip this step if you already have one for the course.

**Windows (PowerShell)**

```bash
python -m venv .venv
```

```bash
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

Your prompt now starts with `(.venv)`.

## 2. Install QumPy

```bash
pip install "qumpy[noisy] @ https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip"
```

This also installs Qiskit, Qiskit Aer, NumPy, SciPy and Matplotlib.

The `[noisy]` part adds `qiskit-ibm-runtime`, which provides the FakeManila
device used by `backend="noisy"`. Without it you only get the ideal simulator:

```bash
pip install https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip
```

**In a Jupyter notebook**, run the same command with `%pip` in a cell, then
restart the kernel:

```python
%pip install "qumpy[noisy] @ https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip"
```

## 3. Check that it works

```bash
python -c "import qumpy as qp; qp.versions()"
```

You should see a table that starts with `qumpy 0.1.0`.

## Updating

To get the latest version from GitHub:

```bash
pip install --upgrade --force-reinstall --no-deps https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip
```

---

## Common errors

### `Cannot find command 'git'`

```
Cloning https://github.com/yigitcaneym/QumPy.git to ...
  ERROR: Error [WinError 2] The system cannot find the file specified while executing command git version
ERROR: Cannot find command 'git' - do you have 'git' installed and in your PATH?
```

On macOS / Linux the first error line reads
`[Errno 2] No such file or directory: 'git'` instead.

**Why:** the command used a link that starts with `git+https://...`. That kind
of link tells pip to download the code with the `git` program, and git is not
installed on this computer.

**Fix:** use the `.zip` link, which needs no git:

```bash
pip install "qumpy[noisy] @ https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip"
```

Installing git also fixes it: download it from
[git-scm.com](https://git-scm.com/downloads), then close and reopen the
terminal. The `.zip` link is simpler.

### `No module named 'qumpy'` in Jupyter

The notebook is running a different Python than the one where you installed
QumPy. Run this in a notebook cell:

```python
import sys; sys.executable
```

If the path doesn't point into your virtual environment, choose the right
kernel in Jupyter (*Kernel → Change kernel*), or install QumPy from inside the
notebook with `%pip install ...` as shown above and restart the kernel.

### `No module named 'qumpy'` after `pip install -e .` (macOS)

macOS sometimes marks files inside a `.venv` folder as *hidden*, and Python
skips hidden `.pth` files, which an editable install relies on. Use either fix:

```bash
chflags nohidden .venv/lib/python3.*/site-packages/__editable__*.pth
```

```bash
pip install .
```

The second command is a normal (non-editable) install. Re-run it after you
change QumPy's source.

### `Activate.ps1 cannot be loaded because running scripts is disabled` (Windows)

PowerShell blocks activation scripts by default. Allow them for your user
account, then activate again:

```bash
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### `The noisy backend needs qiskit-ibm-runtime`

QumPy was installed without the `[noisy]` extra. Install the missing package:

```bash
pip install qiskit-ibm-runtime
```

---

## For development

To run the tests, build the docs or change the code, clone the repository
(this one needs git):

```bash
git clone https://github.com/yigitcaneym/QumPy.git
```

```bash
cd QumPy
```

```bash
pip install -e ".[noisy,notebook,dev]"
```

```bash
pytest
```
