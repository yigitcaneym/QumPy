# QumPy

**Quantum computing for beginners: one import, short commands, friendly errors.**

QumPy brings together the tools used in the Quantum Computing course (Qiskit,
Qiskit Aer, `quantum_info`, the visualization helpers, FakeManila and Trotter
evolution) behind one simple interface. It sits on top of Qiskit, so every
object it returns is a normal Qiskit object, and you can switch back to plain
Qiskit at any time.

```python
import qumpy as qp
from qumpy import Qum

Qum.shots = 2000                         # one setting, used everywhere

c = qp.Circuit(2).h(0).cx(0, 1)          # Bell state, gates chain
c.draw()                                 # circuit picture
qp.dirac(c.state())                      # '0.7071|00⟩ + 0.7071|11⟩'
c.measure().run().plot()                 # 2000 shots -> histogram
```

The same thing in plain Qiskit, as written in the course notebooks:

```python
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit_aer import Aer
from qiskit.visualization import plot_histogram

qr = QuantumRegister(2); cr = ClassicalRegister(2)
qc = QuantumCircuit(qr, cr)
qc.h(qr[0]); qc.cx(qr[0], qr[1])
psi = Aer.get_backend('statevector_simulator').run(qc).result().get_statevector()
qc.measure(qr, cr)
counts = Aer.get_backend('qasm_simulator').run(qc, shots=2000).result().get_counts()
plot_histogram(counts)
```

---

## Installation

You need Python ≥ 3.10. You **don't** need git. Install straight from GitHub:

```bash
pip install "qumpy[noisy] @ https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip"
```

Then check that it works:

```bash
python -c "import qumpy as qp; qp.versions()"
```

> **Got `Cannot find command 'git'`?** You used a link starting with
> `git+https://`, which needs git. Use the `.zip` command above instead.

The [installation guide](https://yigitcaneym.github.io/QumPy/installation.html) covers virtual environments,
Jupyter, updating to a new version, development installs and fixes for
common errors.

## The `Qum` object

`Qum` holds every global setting, and it is also a shortcut to every QumPy
function.

| Setting            | Default    | Meaning                                                |
|--------------------|------------|--------------------------------------------------------|
| `Qum.shots`        | `1024`     | repetitions used by `.run()`                           |
| `Qum.precision`    | `4`        | decimals when printing states and matrices (also numpy) |
| `Qum.seed`         | `None`     | random seed, for reproducible results                  |
| `Qum.backend`      | `"ideal"`  | `"ideal"` simulator, `"noisy"` fake device or `"ibm"` real device |
| `Qum.device`       | `"manila"` | noisy device: `"manila"` (5 qubits) or `"generic"`     |
| `Qum.draw`         | `"mpl"`    | drawing style: `"mpl"`, `"text"`, `"latex"`            |
| `Qum.auto_measure` | `True`     | measure all qubits automatically if you forgot to      |

```python
Qum.shots = 500
Qum.settings()               # print every setting
Qum.reset()                  # back to the defaults

with Qum.using(shots=10, backend="noisy"):
    c.run()                  # temporary settings

Qum.Circuit(1).h(0)          # Qum.<anything> == qp.<anything>
```

A typo gets a suggestion instead of failing silently:

```
>>> Qum.shot = 100
QumError: 'shot' is not a QumPy setting.
  Hint: Did you mean: shots?
```

## What's inside

| Topic         | Main commands |
|---------------|---------------|
| States        | `ket("01+")`, `ket([1, 1j])`, `ket(3, n=2)`, `bell("phi+")`, `ghz(3)`, `random_state(1)`, `bra` |
| Linear algebra | `inner`, `outer`, `norm`, `dagger`, `eig`, `commutator`, `expm`, `is_unitary`, `is_hermitian` |
| Gates         | `X Y Z H S T I`, `Rx Ry Rz P U`, `CNOT CZ SWAP TOFFOLI`, `tensor`, `apply`, `random_unitary`, `equal` |
| Circuits      | `Circuit(n)`, named registers, `.init()`, `.gate()`, `.measure()`, `.if_bit()`, `.draw()`, `.stats()`, `.compile()` |
| Running       | `.state()`, `.unitary()`, `.probabilities()`, `.run()`, `backend="noisy"`, real IBM devices (`backend="ibm"`) |
| Showing       | `show`, `dirac`, `latex`, `bloch`, `qsphere`, `histogram`, `versions` |
| Density matrices | `density_matrix`, `keep`, `partial_trace`, `purity`, `entropy`, `fidelity`, `is_entangled`, `concurrence` |
| Algorithms    | `qft`, `inverse_qft`, `teleportation`, `deutsch_jozsa`, `bernstein_vazirani`, `grover` (also with your own oracle), `sat_oracle`, `phase_estimation` |
| Parameters    | `Parameter("theta")`, `c.assign(theta=...)` |
| Dynamics      | `hamiltonian`, `ising_chain`, `trotter_circuit`, `evolve`, `time_evolution`, `expectation` |

Run `qp.cheatsheet()` to print every QumPy command next to the Qiskit code it
replaces.

## Documentation

**Website: <https://yigitcaneym.github.io/QumPy/>** (searchable, with an API
reference generated from the code). The same pages are in [`docs/`](https://github.com/yigitcaneym/QumPy/tree/main/docs):

| Page | What's in it |
|------|--------------|
| [Installation](https://yigitcaneym.github.io/QumPy/installation.html) | installing, updating, and fixing common errors |
| [Getting started](https://yigitcaneym.github.io/QumPy/getting-started.html) | a 15-minute tour, from a ket to Grover |
| [Concepts](https://yigitcaneym.github.io/QumPy/concepts.html) | qubit order, `state()` vs `run()`, ideal vs noisy, the `Qum` object |
| [API reference](https://yigitcaneym.github.io/QumPy/api-reference.html) | every function and method |
| [Coming from Qiskit](https://yigitcaneym.github.io/QumPy/qiskit-migration.html) | course notebook code → QumPy, side by side |
| [Simple example](https://yigitcaneym.github.io/QumPy/examples/Simple_Example.html) | draw a Bell circuit, measure it, plot a histogram |
| [Tutorial notebook](https://yigitcaneym.github.io/QumPy/examples/QumPy_Tutorial.html) | runnable version of the course TPs |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The tests check QumPy against Qiskit itself: the QFT against `QFTGate`, Trotter
against exact evolution, teleportation fidelity, Grover success rate, and so on.

## Building the docs

The website is built with [Sphinx](https://www.sphinx-doc.org/) and published
to GitHub Pages automatically on every push to `main`
(`.github/workflows/docs.yml`). To build it on your computer:

```bash
pip install -e ".[docs]"
```

```bash
sphinx-build -b html docs docs/_build/html
```

Then open `docs/_build/html/index.html`.

## Troubleshooting

See [Common errors](https://yigitcaneym.github.io/QumPy/installation.html#common-errors) in the installation
guide: missing git, `No module named 'qumpy'` in Jupyter or on macOS,
PowerShell blocking activation scripts, and the noisy backend.

## License

Apache 2.0, the same license as Qiskit.
