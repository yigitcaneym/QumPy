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

You need Python ≥ 3.10. Install straight from GitHub:

```bash
pip install "qumpy[noisy] @ git+https://github.com/yigitcaneym/QumPy.git"
```

The `noisy` extra installs `qiskit-ibm-runtime`, which provides the FakeManila
device used by `backend="noisy"`. Leave out `[noisy]` if you only need the
ideal simulator:

```bash
pip install git+https://github.com/yigitcaneym/QumPy.git
```

To update to the latest version later:

```bash
pip install --upgrade --force-reinstall --no-deps git+https://github.com/yigitcaneym/QumPy.git
```

In a Jupyter notebook, use `%pip install ...` with the same text, then restart
the kernel.

**For development** (tests, docs, editing the code), clone the repository
instead:

```bash
git clone https://github.com/yigitcaneym/QumPy.git
cd QumPy
pip install -e ".[noisy,notebook,dev]"
```

Check the installation:

```python
import qumpy as qp
qp.versions()
```

## The `Qum` object

`Qum` holds every global setting, and it is also a shortcut to every QumPy
function.

| Setting            | Default    | Meaning                                                |
|--------------------|------------|--------------------------------------------------------|
| `Qum.shots`        | `1024`     | repetitions used by `.run()`                           |
| `Qum.precision`    | `4`        | decimals when printing states and matrices (also numpy) |
| `Qum.seed`         | `None`     | random seed, for reproducible results                  |
| `Qum.backend`      | `"ideal"`  | `"ideal"` simulator or `"noisy"` fake IBM device       |
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
| Running       | `.state()`, `.unitary()`, `.probabilities()`, `.run()`, `backend="noisy"` |
| Showing       | `show`, `dirac`, `latex`, `bloch`, `qsphere`, `histogram`, `versions` |
| Density matrices | `density_matrix`, `keep`, `partial_trace`, `purity`, `entropy`, `fidelity`, `is_entangled`, `concurrence` |
| Algorithms    | `qft`, `inverse_qft`, `teleportation`, `deutsch_jozsa`, `bernstein_vazirani`, `grover`, `phase_estimation` |
| Dynamics      | `hamiltonian`, `ising_chain`, `trotter_circuit`, `evolve`, `time_evolution`, `expectation` |

Run `qp.cheatsheet()` to print every QumPy command next to the Qiskit code it
replaces.

## Documentation

| Page | What's in it |
|------|--------------|
| [Getting started](docs/getting-started.md) | a 15-minute tour, from a ket to Grover |
| [Concepts](docs/concepts.md) | qubit order, `state()` vs `run()`, ideal vs noisy, the `Qum` object |
| [API reference](docs/api-reference.md) | every function and method |
| [Coming from Qiskit](docs/qiskit-migration.md) | course notebook code → QumPy, side by side |
| [Simple example](examples/Simple_Example.ipynb) | draw a Bell circuit, measure it, plot a histogram |
| [Tutorial notebook](examples/QumPy_Tutorial.ipynb) | runnable version of the course TPs |

## Tests

```bash
pip install -e ".[dev]"
pytest
```

The tests check QumPy against Qiskit itself: the QFT against `QFTGate`, Trotter
against exact evolution, teleportation fidelity, Grover success rate, and so on.

## Troubleshooting

**`ModuleNotFoundError: No module named 'qumpy'` after `pip install -e .` (macOS).**
macOS sometimes marks files inside a `.venv` folder as *hidden*, and Python
then skips the hidden `.pth` file that an editable install relies on. Use one
of these fixes:

```bash
chflags nohidden .venv/lib/python3.*/site-packages/__editable__*.pth
```

```bash
pip install .
```

The second command makes a regular, non-editable install, which doesn't need a
`.pth` file. Re-run it after you change QumPy's source.

**Jupyter can't find QumPy.** Make sure the notebook kernel is the Python
environment where QumPy is installed. In a notebook, run
`import sys; sys.executable` and compare.

## Türkçe özet

QumPy, Quantum Computing dersinde kullandığımız Qiskit, Aer, `quantum_info`,
görselleştirme ve Trotter araçlarını tek bir `import qumpy as qp` altında
toplar. Tüm ayarlar `Qum` nesnesindedir (`Qum.shots = 1000`,
`Qum.precision = 3`, `Qum.backend = "noisy"`). Kapılar zincirlenebilir
(`Circuit(2).h(0).cx(0, 1)`), hatalar ne yapmanız gerektiğini söyler, ve
Grover, QFT, QPE, Deutsch–Jozsa ve teleportation hazır fonksiyon olarak
gelir. Döndürülen her şey normal bir Qiskit nesnesidir, yani dersteki Qiskit
kodunuzla birlikte kullanabilirsiniz. Başlamak için
[docs/getting-started.md](docs/getting-started.md) ve `qp.cheatsheet()`.

## License

Apache 2.0, the same license as Qiskit.
