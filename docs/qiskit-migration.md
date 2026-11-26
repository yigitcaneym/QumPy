# Coming from Qiskit (course notebooks → QumPy)

Each block shows a short excerpt of typical Qiskit code, in the style of the
course notebooks, next to the QumPy version of it.
You don't have to convert everything: QumPy objects are Qiskit objects, so
both styles mix freely.

## Imports

```python
# Qiskit
import numpy as np
from numpy import linalg as LA
from qiskit import QuantumRegister, ClassicalRegister, QuantumCircuit
from qiskit import quantum_info as qi
from qiskit_aer import Aer
from qiskit.visualization import array_to_latex, plot_bloch_multivector, plot_histogram
from qiskit.circuit.library import Initialize
from qiskit.compiler import transpile
np.set_printoptions(precision=4)
```

```python
# QumPy
import qumpy as qp
from qumpy import Qum
```

## TP 1: vectors and operators

```python
# Qiskit
vket = np.array([[1.], [1j]]);  vbra = vket.T.conj();  vbra.dot(vket)
sv = qi.Statevector(np.array([1., 0.]));  array_to_latex(sv)
U = qi.random_unitary(2, seed=123456);  U.compose(U.adjoint())
X = qi.Operator(qi.Pauli('X'));  Z = qi.Operator(qi.Pauli('Z'));  X.tensor(Z)
qi.Statevector(np.array([1., 0.])).evolve(X)
```

```python
# QumPy
v = qp.ket([1, 1j], normalize=False);  qp.inner(v, v)
qp.show(qp.ket("0"))
U = qp.random_unitary(1, seed=123456);  qp.equal(U.compose(qp.dagger(U)), qp.I)
qp.tensor(qp.X, qp.Z)
qp.apply(qp.X, "0")
```

## TP 2: single-qubit circuits

```python
# Qiskit
qr = QuantumRegister(1, "qreg");  qc = QuantumCircuit(qr)
qc.ry(np.pi/4, qr[0])
qc.draw('mpl', initial_state=True)
psi_f = Aer.get_backend('statevector_simulator').run(qc).result().get_statevector()
U = qi.Operator.from_circuit(qc)
plot_bloch_multivector(psi_f)
```

```python
# QumPy
c = qp.Circuit(1).ry(qp.pi / 4, 0)
c.draw()
psi_f = c.state()
U = c.unitary()
c.bloch()
```

## TP 3: two qubits, density matrices, noisy device

```python
# Qiskit
rho_f = qi.DensityMatrix(psi_f)
rho_f_q1 = qi.partial_trace(rho_f, [0])
rho_f.purity(), rho_f_q1.purity()

qc.measure(qr, cr)
counts = Aer.get_backend('qasm_simulator').run(qc, shots=10000).result().get_counts(qc)
plot_histogram(counts)

from qiskit_ibm_runtime.fake_provider import FakeManilaV2
counts = FakeManilaV2().run(qc, shots=10000).result().get_counts(qc)

pm = generate_preset_pass_manager(basis_gates=['rx', 'rz', 'cx'])
qc_t = pm.run(qc)
```

```python
# QumPy
rho = qp.density_matrix(c)
rho_q1 = qp.keep(rho, 1)          # or qp.partial_trace(rho, [0])
qp.purity(rho), qp.purity(rho_q1)

Qum.shots = 10000
c.measure().run().plot()
c.run(backend="noisy").plot()

c_t = c.compile(basis=["rx", "rz", "cx"])
```

## TP 4: teleportation

```python
# Qiskit: ~25 lines (registers, Initialize, Bell pair, Bell measurement, if_test)
```

```python
# QumPy
t = qp.teleportation(psi)
t.draw()
qp.fidelity(qp.keep(t.state(), 2), psi)   # 1.0
```

Or build it step by step with named registers; see
[Getting started §7](getting-started.md#7-named-registers-and-teleportation).

## TP 5: oracles, Deutsch–Jozsa

```python
# Qiskit
psi = qi.Statevector.from_int(k, dims=N)
init_gate = Initialize(psi);  qc.append(init_gate, qr[:n])
for i in range(n):
    if (a & (1 << i)):
        qc.cx(qr[i], qr[n])
```

```python
# QumPy
c = qp.Circuit(n + 1).init(qp.ket(k, n=n), qubits=range(n))
c.add(qp.dj_oracle(n, kind="balanced", a=a))

dj = qp.deutsch_jozsa(n, kind="balanced")
qp.dj_answer(dj.run(shots=1))
```

## QFT, QPE, Grover

```python
# Qiskit: qft_rotations(...), swap_registers(...), inverse_qft(...),
#         black_box_u_f(...), n_controlled_Z(...), inversion_about_average(...)
```

```python
# QumPy
qp.qft(4);  qp.inverse_qft(4)
qp.phase_estimation(U, n_counting=5, eigenstate=psi)
qp.grover("101");  qp.grover(["0110", "1001"])
```

QPE with a Hamiltonian, as in `QPE.ipynb`:

```python
U = qp.evolution_operator(A, t)          # e^{-iAt}
c = qp.phase_estimation(U, n_counting=5, eigenstate=psi_0)
```

## TP 8–9: Trotterization

```python
# Qiskit
X = SparsePauliOp("X"); Z = SparsePauliOp("Z"); I = SparsePauliOp("I")
H = (Z ^ Z) - 0.1 * (X ^ I)
step = PauliEvolutionGate(H, dt, synthesis=SuzukiTrotter())
circuit = QuantumCircuit(H.num_qubits)
for i in range(num_timesteps):
    circuit.append(step, range(H.num_qubits)); circuit.barrier()
circuit = circuit.decompose(reps=2)
final_state = Aer.get_backend('statevector_simulator').run(circuit).result().get_statevector()
exact = initial_state.evolve(sp.linalg.expm(-1j * final_time * H.to_matrix()))
qi.state_fidelity(final_state, exact)

trotter = TrotterQRTE(SuzukiTrotter(order=2), num_timesteps=60, estimator=StatevectorEstimator())
problem = TimeEvolutionProblem(H, initial_state=..., time=30, aux_operators=[...])
result = trotter.evolve(problem)
# ...plus 20 lines of matplotlib
```

```python
# QumPy
H = qp.hamiltonian({"ZZ": 1, "XI": -0.1})
c = qp.trotter_circuit(H, time=20, steps=10, order=2)
qp.fidelity(c.state(), qp.evolve(H, "00", 20))

res = qp.time_evolution(qp.ising_chain(6, 0.2, 1.2, qp.pi / 8), "001100",
                        time=30, steps=60, order=2,
                        observables={"Magnetization": qp.magnetization(6)})
res.plot(exact=True)
```

`time_evolution` does not need `qiskit-algorithms`.

## Qiskit.ipynb: parameters and real devices

```python
# Qiskit
from qiskit.circuit import Parameter
th_par = Parameter("theta"); ph_par = Parameter("phi"); la_par = Parameter("lambda")
qc.u(th_par, ph_par, la_par, qreg[0])
qc.assign_parameters({th_par: np.pi, ph_par: 0, la_par: np.pi}, inplace=True)

from qiskit_ibm_runtime import QiskitRuntimeService
service = QiskitRuntimeService()
print(service.backends())
backend = service.backend("ibm_brisbane")
backend.status(); backend.num_qubits; backend.basis_gates
# backend.run(...) no longer works on real devices -> SamplerV2 code needed
```

```python
# QumPy
th, ph, la = qp.Parameter("theta"), qp.Parameter("phi"), qp.Parameter("lambda")
c = qp.Circuit(1).u(th, ph, la, 0)
c.assign(theta=qp.pi, phi=0, **{"lambda": qp.pi})   # 'lambda' is a Python keyword

qp.ibm_backends()
dev = qp.ibm_backend("ibm_brisbane")
qp.backend_info(dev)
c.measure().run(backend=dev)                       # SamplerV2 under the hood
```

## Grover.ipynb: the 3-SAT oracle

```python
# Qiskit: black_box_u_f(...), n_controlled_Z(...), inversion_about_average(...),
#         input_state(...), registers fin / fout / aux, T = 2 iterations
```

```python
# QumPy
oracle = qp.sat_oracle([[1, 2, -3], [-1, -2, -3], [-1, 2, 3]])
oracle.draw()                      # same fin / fout / aux layout as the course
g = qp.grover(oracle=oracle)       # 2 iterations, chosen automatically
g.run().plot()                     # '101'
```

The course's `black_box_u_f` only works when every clause uses exactly the
variables x1, x2, x3. `sat_oracle` works for any number of variables and
clauses, and `exactly_one=False` gives ordinary SAT.

## Version table

```python
# Qiskit
import tutorial_magics
%qiskit_version_table
```

```python
# QumPy
qp.versions()
```
