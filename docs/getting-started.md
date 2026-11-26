# Getting started

Install QumPy first: see [Installation](installation.md).

This tour takes about 15 minutes and follows the order of the course: vectors
and kets, gates, circuits, measurement, entanglement, algorithms, and time
evolution. Run it in a Jupyter notebook so the pictures and LaTeX show up.

```python
import qumpy as qp
from qumpy import Qum
```

## 1. Kets and bras

```python
psi = qp.ket("0")          # |0>
psi = qp.ket("+")          # (|0> + |1>)/√2
psi = qp.ket("01")         # |01>
psi = qp.ket([1, 1j])      # normalised for you: (|0> + i|1>)/√2
psi = qp.ket(3, n=2)       # basis state number 3 on 2 qubits = |11>

qp.show(psi)               # column vector (LaTeX in Jupyter)
qp.show(psi, style="ket")  # Dirac notation
qp.dirac(psi)              # same, as a string: '|11⟩'
psi.num_qubits             # 2: psi is a normal Qiskit Statevector
```

Inner products and friends:

```python
a, b = qp.ket("0"), qp.ket("+")
qp.inner(a, b)     # <a|b> = 0.7071
qp.outer(a)        # |a><a|, the projector
qp.bra(b)          # row vector <b|
qp.norm([3, 4])    # 5.0
```

## 2. Gates as matrices

```python
qp.show(qp.H)                     # Hadamard matrix
qp.apply(qp.H, "0")               # H|0> = |+>
qp.tensor(qp.X, qp.Z)             # X ⊗ Z (4x4)
qp.Rx(qp.pi / 2)                  # rotation gate
U = qp.random_unitary(1)
qp.is_unitary(U)                  # True
qp.equal(qp.dagger(U).compose(U), qp.I)   # U†U = I  -> True
```

## 3. Circuits

```python
c = qp.Circuit(2)        # 2 qubits; classical bits get added when you measure
c.h(0).cx(0, 1)          # gates chain
c.draw()                 # picture (Qum.draw sets the style)
```

Every Qiskit gate works: `c.ry(qp.pi / 4, 0)`, `c.cp(qp.pi / 2, 0, 1)`,
`c.ccx(0, 1, 2)`, `c.mcx([0, 1, 2], 3)`, `c.swap(0, 1)`, `c.barrier()`, and so
on. There are also readable aliases: `c.cnot`, `c.toffoli`, `c.hadamard`.

Apply a gate to every qubit with `"all"`:

```python
qp.Circuit(3).h("all")
```

Without running anything, you can look at:

```python
c.state()           # final Statevector, exact
c.unitary()         # the 4x4 matrix of the circuit
c.probabilities()   # {'00': 0.5, '11': 0.5}
c.bloch()           # Bloch spheres of each qubit
qp.bloch(c)         # same
```

## 4. Measuring

```python
Qum.shots = 1000
c.measure()                # every qubit i -> classical bit i
counts = c.run()           # Counts({'00': 497, '11': 503}, shots=1000)
counts.plot()              # histogram
counts.most_likely()       # '11'
counts.probabilities()     # {'00': 0.497, '11': 0.503}
```

To see what a real (noisy) device does:

```python
c.run(backend="noisy")     # FakeManila: a few '01' and '10' appear
```

> **Bit order.** As in Qiskit, the rightmost character of `'01'` is qubit 0.
> `counts.reversed_bits()` gives you the textbook order if you prefer it.
> [Concepts](concepts.md#qubit-order) explains why.

## 5. Preparing a state

```python
psi = qp.random_state(1)
c = qp.Circuit(2)
c.init(psi, qubits=0)      # replaces Initialize(psi) + qc.append(...)
```

## 6. Entanglement and density matrices

```python
bell = qp.bell("phi+")
rho = qp.density_matrix(bell)
rho_B = qp.keep(rho, 1)        # reduced state of qubit 1
qp.purity(rho), qp.purity(rho_B)   # 1.0, 0.5
qp.is_entangled(bell)          # True
qp.entropy(rho_B)              # 1.0 bit
```

`keep(rho, 1)` names the qubits you keep. `partial_trace(rho, [0])` names the
qubits you remove, as Qiskit does. Both give the same result here.

## 7. Named registers and teleportation

```python
c = qp.Circuit(psi=1, alice=1, bob=1, bits={"crz": 1, "crx": 1})
c.init(qp.random_state(1), "psi")
c.h("alice").cx("alice", "bob")
c.cx("psi", "alice").h("psi")
c.measure("psi", "crz").measure("alice", "crx")
with c.if_bit("crx", 1):
    c.x("bob")
with c.if_bit("crz", 1):
    c.z("bob")
c.draw()
```

The same circuit is ready-made:

```python
t = qp.teleportation(psi)
qp.fidelity(qp.keep(t.state(), 2), psi)    # 1.0
```

## 8. Algorithms

```python
qp.qft(3).draw()                                   # Quantum Fourier Transform

dj = qp.deutsch_jozsa(4, kind="balanced")
qp.dj_answer(dj.run(shots=1))                      # 'balanced'

qp.bernstein_vazirani("1011").run()                # {'1011': 1024}

qp.grover("101").run().plot()                      # '101' dominates

U = qp.P(2 * qp.pi * 0.375)                        # eigenphase 0.375 on |1>
qpe = qp.phase_estimation(U, n_counting=3, eigenstate="1")
qp.estimated_phase(qpe.run())                      # 0.375
```

Grover also takes your own oracle. The 3-SAT problem from the course's Grover
notebook is built in:

```python
formula = [[1, 2, -3], [-1, -2, -3], [-1, 2, 3]]   # -3 means NOT x3
oracle = qp.sat_oracle(formula)                   # exactly-1 3-SAT
oracle.solutions                                  # ['101']
qp.grover(oracle=oracle).run().plot()
```

Each of these returns a `Circuit`, so you can draw it, inspect it with
`.stats()` or add gates before running it.

## 9. Hamiltonians and Trotterization

```python
H = qp.hamiltonian({"ZZ": 1, "XI": -0.1})          # Z⊗Z − 0.1 X⊗I
c = qp.trotter_circuit(H, time=20, steps=10, order=2)
c.stats()
exact = qp.evolve(H, "00", time=20)
qp.fidelity(c.state(), exact)
```

Observables over time, compared with the exact solution (course notebook
QCTP_09):

```python
L = 6
H = qp.ising_chain(L, J=0.2, h=1.2, alpha=qp.pi / 8)
res = qp.time_evolution(
    H, "001100", time=30, steps=60, order=2,
    observables={"Energy": H,
                 "Magnetization": qp.magnetization(L),
                 "Mean spin correlation": qp.zz_correlation(L)},
)
res.plot(exact=True)
```

## 10. Parameters

```python
theta = qp.Parameter("theta")
c = qp.Circuit(1).ry(theta, 0)
c.draw()                         # shows θ
c.assign(theta=qp.pi / 2)        # give it a value
qp.dirac(c.state())              # '0.7071|0⟩ + 0.7071|1⟩'
```

## 11. Real IBM quantum computers

After saving your IBM Quantum account once (see the
[API reference](api-reference.md#real-ibm-devices)):

```python
qp.ibm_backends()                    # devices you can use
dev = qp.ibm_backend()               # the least busy one
qp.backend_info(dev)
c = qp.bell_circuit(measure=True)
c.compile(backend=dev).draw()        # the circuit as the chip will run it
c.run(backend=dev).plot()            # waits in IBM's queue, then plots
```

## Next steps

* `qp.cheatsheet()` prints every command.
* [Concepts](concepts.md) explains the parts that confuse people.
* The [API reference](api-reference.md) lists every function.
* [`examples/QumPy_Tutorial.ipynb`](../examples/QumPy_Tutorial.ipynb) is this
  tour as a runnable notebook.
