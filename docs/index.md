# QumPy

**Quantum computing for beginners: one import, short commands, friendly errors.**

QumPy brings together the tools of the Quantum Computing course (Qiskit,
Qiskit Aer, `quantum_info`, the visualization helpers, fake and real IBM
devices, Trotter evolution) behind one simple interface. It sits on top of
Qiskit, so every object it returns is a normal Qiskit object.

```python
import qumpy as qp
from qumpy import Qum

Qum.shots = 2000                         # one setting, used everywhere

c = qp.Circuit(2).h(0).cx(0, 1)          # Bell state, gates chain
c.draw()                                 # circuit picture
qp.dirac(c.state())                      # '0.7071|00⟩ + 0.7071|11⟩'
c.measure().run().plot()                 # 2000 shots -> histogram
```

Install it (no git needed):

```bash
pip install "qumpy[noisy] @ https://github.com/yigitcaneym/QumPy/archive/refs/heads/main.zip"
```

Then start with [Getting started](getting-started.md), or print every command
with `qp.cheatsheet()`.

```{toctree}
:maxdepth: 1
:caption: User guide

installation
getting-started
concepts
qiskit-migration
```

```{toctree}
:maxdepth: 1
:caption: Examples

examples/Simple_Example
examples/QumPy_Tutorial
```

```{toctree}
:maxdepth: 1
:caption: Reference

api-reference
reference/index
```
