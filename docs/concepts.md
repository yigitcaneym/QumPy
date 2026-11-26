# Concepts

The parts of quantum programming that confuse beginners most, and how QumPy
deals with each.

## The `Qum` object

Plain Qiskit makes you pass the same options again and again: `shots=` in
every `backend.run`, `precision=` in every `array_to_latex`, seeds in three
different places. QumPy keeps them in one place:

```python
from qumpy import Qum
Qum.shots = 4000
Qum.precision = 3
Qum.seed = 42          # same random numbers every time
```

Any function argument still wins over the global setting:
`c.run(shots=10)` uses 10 shots whatever `Qum.shots` says.

`Qum` also forwards to every QumPy function, so if you only want one name in
your notebook, you can write `Qum.Circuit(2)`, `Qum.ket("0")`,
`Qum.grover("11")`.

Settings are checked as you set them: `Qum.shots = -1` or `Qum.backend = "ibm"`
raise a `QumError` that explains what is allowed.

## Qubit order

Qiskit (and therefore QumPy) is **little-endian**: in a bitstring or a label,
the **rightmost** character is qubit 0.

```python
qp.ket("01")                       # qubit 1 = 0, qubit 0 = 1
qp.Circuit(2).x(0).measure().run() # {'01': 1024}
```

The same rule applies to tensor products. In `qp.tensor(A, B)` (= `A ⊗ B`),
`A` acts on the higher qubit and `B` on qubit 0.

Textbooks (Nielsen & Chuang) usually write qubit 0 on the left. To read results
that way, call:

```python
counts.reversed_bits()      # {'10': 1024}
```

## `state()` vs `run()`

| | `c.state()` | `c.run()` |
|---|---|---|
| What you get | the exact state vector | measurement counts |
| Shots | none, it's exact | `Qum.shots` |
| Real hardware possible? | no | yes, the physical experiment |
| Measurements in the circuit | allowed (one random collapse is simulated) | needed (added automatically if missing) |

Use `state()`, `unitary()` and `probabilities()` to understand a circuit, and
`run()` to see what an experiment would give.

If you call `run()` on a circuit without measurements, QumPy measures every
qubit and prints a warning. Set `Qum.auto_measure = False` to get an error
instead.

## `unitary()`

`c.unitary()` returns the matrix of the circuit. Measurements at the very end
are ignored. A circuit containing `init()`, a mid-circuit measurement or
`if_bit()` has no single unitary, and QumPy says so instead of returning
something wrong.

## Ideal vs noisy

```python
c.run()                    # perfect simulator (AerSimulator)
c.run(backend="noisy")     # imitation of a real 5-qubit IBM chip (FakeManilaV2)
Qum.backend = "noisy"      # make it the default
Qum.device = "generic"     # bigger noisy device (GenericBackendV2), any size
```

The noisy backend shows the effects you see on real hardware: readout errors,
imperfect gates, and circuits being rewritten for the chip's native gates and
connectivity. You can also pass any Qiskit backend object:
`c.run(backend=my_backend)`.

`c.run(backend="ibm")` (or `backend=qp.ibm_backend("ibm_brisbane")`) runs on
a **real** IBM quantum computer. IBM removed `backend.run()` for real devices,
so QumPy sends the job through the `SamplerV2` primitive and converts the
answer back into ordinary `Counts`, in the same format as the simulators. A
real job waits in a queue and uses your IBM Quantum time.

## Classical bits are created for you

`Circuit(3)` starts without classical bits. The first `measure()` adds a
register `c` with one bit per qubit, and qubit *i* goes to bit *i*. You only
need to think about bits when you want something special:

```python
qp.Circuit(3, bits=1).measure(2, 0)    # qubit 2 -> bit 0
```

## Named registers

Naming registers makes protocols readable:

```python
c = qp.Circuit(psi=1, alice=1, bob=1, bits={"crz": 1, "crx": 1})
c.h("alice")             # a name means the whole register
c.measure("psi", "crz")
```

The qubits are numbered in the order you wrote them: psi = 0, alice = 1,
bob = 2. Use those numbers for `keep(state, 2)` and similar functions.

## It is still Qiskit

QumPy never hides Qiskit:

* `c.qc` is the underlying `QuantumCircuit`.
* `Circuit.from_qiskit(qc)` wraps a circuit you built in Qiskit.
* States are `Statevector`, gates are `Operator`, density matrices are
  `DensityMatrix`, Hamiltonians are `SparsePauliOp`.
* `qp.run`, `qp.state` and `qp.unitary` accept plain `QuantumCircuit`s too.

So you can mix course code and QumPy in the same notebook.

## Friendly errors

Every QumPy error is a `QumError` that says what went wrong and, where it can,
how to fix it:

```
>>> qp.Circuit(2).h(5)
QumError: h(): Index 5 out of range for size 2.
  Hint: This circuit has 2 qubit(s) (0 ... 1) and 0 bit(s).

>>> qp.Circuit(1).hadamrd(0)
QumError: Circuit has no gate or method called 'hadamrd'.
  Hint: Did you mean: hadamard?
```
