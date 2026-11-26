# API reference

Everything below is available as `qp.<name>` after `import qumpy as qp`, and as
`Qum.<name>` after `from qumpy import Qum`. Every function also has a
docstring: `help(qp.grover)`.

Contents: [Settings](#settings-qum) · [States](#states) ·
[Linear algebra](#linear-algebra) · [Gates](#gates) · [Circuit](#circuit) ·
[Counts](#counts) · [Display](#display) · [Density matrices](#density-matrices) ·
[Algorithms](#algorithms) · [Dynamics](#dynamics) ·
[Real IBM devices](#real-ibm-devices) · [Errors](#errors)

---

## Settings: `Qum`

| Attribute / method | Description |
|---|---|
| `Qum.shots` | default number of shots for `run()` (positive int, default 1024) |
| `Qum.precision` | decimals for `show`, `dirac` and numpy printing (default 4) |
| `Qum.seed` | random seed for simulators, transpiler and random states (`None` = random) |
| `Qum.backend` | `"ideal"`, `"noisy"` or `"ibm"` (least busy real device) |
| `Qum.device` | noisy device: `"manila"` (FakeManilaV2, 5 qubits) or `"generic"` (GenericBackendV2) |
| `Qum.draw` | default style for `Circuit.draw()`: `"mpl"`, `"text"`, `"latex"` |
| `Qum.auto_measure` | `run()` measures all qubits when the circuit has no measurement |
| `Qum.settings()` | print every setting |
| `Qum.reset()` | restore the defaults |
| `Qum.using(**settings)` | context manager for temporary settings |

---

## States

All of these return a Qiskit `Statevector`.

| Function | Description |
|---|---|
| `ket(state, n=None, normalize=True)` | `"0"`, `"1"`, `"+"`, `"-"`, `"r"`, `"l"` or strings of them (`"01+"`, `"\|01>"`); an int with `n` qubits; a list or array of amplitudes (normalised by default) |
| `bra(state)` | the conjugate row vector ⟨state\| (numpy) |
| `basis(k, n=1)` | \|k⟩ on `n` qubits |
| `zero(n=1)` | \|0…0⟩ |
| `plus(n=1)` | \|+…+⟩ |
| `bell(which="phi+")` | `"phi+"`, `"phi-"`, `"psi+"`, `"psi-"` |
| `ghz(n=3)` | (\|0…0⟩ + \|1…1⟩)/√2 |
| `random_state(n=1, seed=None)` | Haar-random pure state |
| `num_qubits(x)` | number of qubits of a state or operator |

---

## Linear algebra

Inputs can be lists, numpy arrays, `Statevector`, `Operator` or `DensityMatrix`.

| Function | Description |
|---|---|
| `inner(a, b)` | ⟨a\|b⟩ (conjugates `a`) |
| `outer(a, b=None)` | \|a⟩⟨b\|; `outer(a)` is the projector \|a⟩⟨a\| |
| `norm(v)`, `normalize(v)` | length, unit vector |
| `column(*entries)` | column vector, e.g. `column(1, 1j)` |
| `dagger(m)` | conjugate transpose (keeps `Operator` type) |
| `is_hermitian(m)`, `is_unitary(m)` | checks |
| `eig(m)` | sorted eigenvalues and eigenvectors (columns); uses `eigh` for Hermitian matrices |
| `eigenvectors(m)` | eigenvectors as a list |
| `commutator(a, b)`, `anticommutator(a, b)` | AB − BA, AB + BA |
| `expm(m)` | matrix exponential |
| `trace(m)` | trace |
| `to_array(x)` | any of the above as a numpy array |

---

## Gates

Constants (Qiskit `Operator`): `I X Y Z H S T`, `CNOT` (= `CX`), `CZ`, `SWAP`,
`TOFFOLI` (= `CCX`).

| Function | Description |
|---|---|
| `Rx(t)`, `Ry(t)`, `Rz(t)` | rotations |
| `P(phi)` | phase gate diag(1, e^{iφ}) |
| `U(theta, phi, lam)` | general 1-qubit gate |
| `pauli("XZ")` | Pauli string as an operator |
| `operator(m)` | matrix, Pauli string, `Circuit` or gate → `Operator` |
| `tensor(*ops)` | A ⊗ B ⊗ …, for operators or states (left factor = highest qubit) |
| `apply(op, state)` | op\|state⟩ |
| `random_unitary(n=1, seed=None)` | random n-qubit unitary |
| `equal(a, b, up_to_phase=True)` | compare operators or states |

---

## Circuit

```python
Circuit(qubits=None, bits=None, name=None, **named_qubits)
```

* `Circuit(3)`: 3 qubits in register `q`.
* `Circuit(3, bits=2)`: 2 classical bits in register `c`.
* `Circuit(alice=1, bob=1, bits={"crx": 1})`: named registers.

**Qubit arguments** can be an int, a list, a `range`, a register name such as
`"alice"`, or `"all"`.

### Gates

Every `QuantumCircuit` gate method works and returns the circuit, so calls
chain: `h x y z s sdg t tdg rx ry rz p u cx cy cz cp crx cry crz ch swap ccx
cswap mcx mcp id barrier reset append`, and the rest. Aliases: `cnot`,
`toffoli`, `fredkin`, `hadamard`, `phase`, `cphase`, `identity`.

| Method | Description |
|---|---|
| `h_all()`, `x_all()` | gate on every qubit |
| `init(state, qubits=None, label="init")` | prepare qubits in any state `ket()` accepts |
| `gate(matrix, qubits, label=None)` | add any unitary matrix as a gate |
| `add(other, qubits=None, bits=None)` | append another Circuit, QuantumCircuit or gate |
| `a + b`, `a.then(b)` | new circuit: `a` followed by `b` |
| `measure(qubits=None, bits=None)` | measure (all qubits by default); creates bits if needed |
| `with c.if_bit(bits, value=1):` | classical control, e.g. teleportation corrections |

### Simulation

| Method | Description |
|---|---|
| `state(seed=None)` | final `Statevector` |
| `unitary()` | `Operator` of the circuit (final measurements ignored) |
| `probabilities(decimals=None)` | exact outcome probabilities |
| `density_matrix()` | `DensityMatrix` of the final state |
| `run(shots=None, backend=None, seed=None, use_sampler=None)` | `Counts`; backend `"ideal"`, `"noisy"`, `"ibm"` or a backend object. Real IBM devices are run through `SamplerV2` automatically |

### Parameters

| Method | Description |
|---|---|
| `Parameter("theta")` | a free parameter (Qiskit's `Parameter`, also `qp.Parameter`) |
| `assign(values=None, **by_name)` | set parameter values in place: `c.assign(theta=qp.pi)`, `c.assign({th: 0})`, `c.assign({"lambda": 0})` |

`state()`, `unitary()` and `run()` raise a `QumError` naming the parameters
that still have no value.

### Inspection and display

| Method | Description |
|---|---|
| `draw(style=None, initial_state=True, scale=None)` | picture; `style` defaults to `Qum.draw` |
| `bloch()` | Bloch spheres of the final state |
| `show_state(style="vector")`, `show_unitary()` | pretty print |
| `stats(show=True)` | qubits, bits, depth, gate count, non-local gates, ops |
| `depth()`, `len(c)` | depth and number of instructions |
| `num_qubits`, `num_bits`, `registers` | properties |
| `has_measurements()` | bool |
| `print(c)` | text drawing |

### Transformations

| Method | Description |
|---|---|
| `inverse()` | U† |
| `decompose(reps=1)` | expand composite gates |
| `compile(basis=("rx","rz","cx"), optimization_level=1, backend=None)` | transpile to a basis or a backend |
| `to_gate(label=None)`, `controlled(num_controls=1)` | reusable gates |
| `copy()` | independent copy |
| `qasm()`, `Circuit.from_qasm(text)` | OpenQASM 2 |
| `Circuit.from_qiskit(qc)`, `c.qc` | convert to and from `QuantumCircuit` |

### Functional shortcuts

`run(circuit, shots=None, backend=None)`, `state(circuit)`, `unitary(circuit)`
accept a `Circuit` or a plain `QuantumCircuit`. `noisy_backend(device=None,
num_qubits=5)` returns the noisy backend object.

---

## Counts

`run()` returns `Counts`, a `dict` subclass such as `{'00': 507, '11': 517}`.

| Member | Description |
|---|---|
| `shots`, `backend` | shots used, backend label |
| `plot(title=None)` | histogram |
| `probabilities()` | dict of frequencies |
| `probability(bitstring)` | one frequency |
| `most_likely()` | most frequent bitstring |
| `top(k=5)` | k most frequent `(bitstring, count)` |
| `as_ints()` | keys as integers |
| `reversed_bits()` | keys with qubit 0 on the left |

---

## Display

| Function | Description |
|---|---|
| `show(x, precision=None, prefix=None, style="vector")` | LaTeX in Jupyter, text elsewhere; `style="ket"` for Dirac notation |
| `dirac(state, precision=None)` | string such as `'0.7071\|00⟩ + 0.7071\|11⟩'` |
| `latex(x, precision=None, prefix="")` | LaTeX source string |
| `bloch(x)` | Bloch spheres; accepts a state, a `Circuit` or a `QuantumCircuit` |
| `qsphere(x)` | Q-sphere |
| `histogram(*counts, legend=None, title=None)` | one or several results side by side |
| `versions()` | version table (replaces `tutorial_magics`) |
| `cheatsheet(topic=None)` | QumPy commands next to the Qiskit equivalents |
| `in_notebook()` | True inside Jupyter |

---

## Density matrices

Inputs can be a state, a label, a `Circuit` or a matrix.

| Function | Description |
|---|---|
| `density_matrix(x)` | ρ = \|ψ⟩⟨ψ\| |
| `mixed_state(states, probabilities)` | Σ pᵢ \|ψᵢ⟩⟨ψᵢ\| |
| `keep(x, qubits)` (= `reduced_state`) | reduced state of the qubits you keep |
| `partial_trace(x, trace_out)` | trace out these qubits (Qiskit convention) |
| `purity(x)`, `is_pure(x)`, `is_valid(x)` | checks |
| `entropy(x, base=2)` | von Neumann entropy |
| `fidelity(a, b)` | state fidelity |
| `is_entangled(state, qubits=(0,))` | pure states: are `qubits` entangled with the rest? |
| `concurrence(state)` | 2-qubit entanglement measure |
| `bloch_vector(x)` | (⟨X⟩, ⟨Y⟩, ⟨Z⟩) of one qubit |

---

## Algorithms

All of these return a `Circuit`.

| Function | Description |
|---|---|
| `qft(n, swaps=True, inverse=False)`, `inverse_qft(n)` | Quantum Fourier Transform (identical to Qiskit's `QFTGate`) |
| `bell_circuit(which="phi+", measure=False)`, `ghz_circuit(n, measure=False)` | entangled states |
| `teleportation(psi=None, seed=None)` | registers psi, alice, bob and crz, crx; `.input_state` holds ψ |
| `dj_oracle(n, kind="balanced", value=0, a=None)` | Deutsch–Jozsa oracle on n+1 qubits |
| `deutsch_jozsa(n=3, kind="balanced", oracle=None, ...)` | full circuit; `dj_answer(counts)` → `"constant"` / `"balanced"` |
| `bernstein_vazirani(secret)` | measurement returns `secret` |
| `grover(marked=None, iterations=None, measure=True, oracle=None, n=None, num_solutions=None)` | search for `marked` bitstring(s), **or** use your own `oracle` on the first `n` qubits: a phase oracle with exactly `n` qubits, or a bit-flip oracle whose qubit `n` is the output (prepared in \|−⟩) and the rest are ancillas |
| `sat_oracle(formula, exactly_one=True)` | bit-flip oracle for a CNF formula such as `[[1, 2, -3], [-1, -2, -3], [-1, 2, 3]]` (`-3` = NOT x3); registers `fin`, `fout`, `aux`; `.solutions` lists the satisfying bitstrings |
| `grover_oracle(marked)`, `diffuser(n)`, `grover_iterations(n, M)` | building blocks |
| `phase_estimation(U, n_counting=3, eigenstate=None)` | QPE; `eigenstate` may be a label, vector or `Circuit` |
| `estimated_phase(counts, n_counting=None)` | φ from the most likely outcome |

---

## Dynamics

| Function | Description |
|---|---|
| `hamiltonian(terms, num_qubits=None)` | from a dict `{"ZZ": 1}`, a list `[(1, "ZZ")]`, the sparse form `[("ZZ", [0, 1], 1)]`, a Pauli string or a matrix → `SparsePauliOp` |
| `ising_chain(L, J=1, h=1, alpha=0)` | −J ΣZZ − h sin α ΣZ − h cos α ΣX |
| `magnetization(L)`, `zz_correlation(L)` | observables |
| `trotter_step(H, dt, order=1)` | one `PauliEvolutionGate` |
| `trotter_circuit(H, time, steps, order=1, initial=None)` | Trotterized evolution circuit (order 1, 2, 4, 6 or 8) |
| `evolution_operator(H, t)` | exact e^{−iHt} |
| `evolve(H, state, time)` | exact e^{−iHt}\|ψ⟩ |
| `exact_evolution(H, state, times)` | exact states at many times |
| `expectation(state, op)` | ⟨ψ\|O\|ψ⟩ |
| `time_evolution(H, initial, time, steps, observables=None, order=2)` | returns `EvolutionResult` with `.times`, `.values`, `.states`, `.plot(exact=True)`, `.exact()`, `.fidelity()` |

---

## Real IBM devices

Needs `qiskit-ibm-runtime` and an IBM Quantum account saved once with
`QiskitRuntimeService.save_account(token=..., channel="ibm_quantum_platform", set_as_default=True)`.
QumPy never handles your token.

| Function | Description |
|---|---|
| `ibm_backends(min_qubits=1)` | names of the real devices your account can use |
| `ibm_backend(name=None, min_qubits=1)` | a device by name, or the least busy one |
| `backend_info(backend, show=True)` | name, version, qubits, basis gates, operational, pending jobs (also works for fake backends) |
| `ibm_service()` | the underlying `QiskitRuntimeService` |

`c.run(backend=dev)` or `c.run(backend="ibm")` sends the job, prints its ID,
and waits for the result. IBM removed `backend.run()` for real devices, so
QumPy uses the `SamplerV2` primitive and returns ordinary `Counts`.

---

## Errors

`QumError` is raised for every mistake QumPy can explain. It has a message
and an optional `.hint`. Unknown circuit methods raise `QumAttributeError`,
which is both a `QumError` and an `AttributeError`, so `hasattr()` works.
