"""``cheatsheet()``: QumPy commands next to the Qiskit code they replace."""

_SHEET = {
    "settings": [
        ("Qum.shots = 2000", "backend.run(qc, shots=2000)  # every time"),
        ("Qum.precision = 3", "np.set_printoptions(precision=3); array_to_latex(x, precision=3)"),
        ("Qum.seed = 42", "seed_simulator=42, seed_transpiler=42, seed=42 ..."),
        ("Qum.backend = 'noisy'", "backend = FakeManilaV2()"),
        ("Qum.settings() / Qum.reset()", "-"),
        ("with Qum.using(shots=10): ...", "-"),
    ],
    "states": [
        ("ket('0'), ket('01'), ket('+')", "qi.Statevector.from_label('01')"),
        ("ket([1, 1])  # auto-normalised", "qi.Statevector(np.array([1, 1]) / np.sqrt(2))"),
        ("ket(3, n=2)", "qi.Statevector.from_int(3, dims=4)"),
        ("bell('phi+'), ghz(3)", "-"),
        ("random_state(1)", "qi.random_statevector(2)"),
        ("bra(psi)", "vket.T.conj()"),
        ("inner(a, b), outer(a, b), norm(v)", "LA.vecdot / np.outer / LA.norm"),
    ],
    "gates": [
        ("X, Y, Z, H, S, T, I", "qi.Operator(qi.Pauli('X')) ..."),
        ("Rx(t), Ry(t), Rz(t), P(phi), U(t, p, l)", "qi.Operator(RXGate(t)) ..."),
        ("CNOT, CZ, SWAP, TOFFOLI", "qi.Operator(CXGate()) ..."),
        ("tensor(X, Z)", "X.tensor(Z)"),
        ("apply(H, ket('0'))", "sv.evolve(H)"),
        ("dagger(U), is_unitary(U)", "U.adjoint(), U.is_unitary()"),
        ("random_unitary(1)", "qi.random_unitary(2)"),
    ],
    "circuits": [
        ("c = Circuit(2)", "qr = QuantumRegister(2); cr = ClassicalRegister(2); qc = QuantumCircuit(qr, cr)"),
        ("Circuit(alice=1, bob=1, bits={'crx': 1})", "QuantumRegister(1, 'alice') ..."),
        ("c.h(0).cx(0, 1)", "qc.h(qr[0]); qc.cx(qr[0], qr[1])"),
        ("c.h('all') / c.h_all()", "qc.h(qr)"),
        ("c.init('1+') / c.init(psi, qubits=0)", "qc.append(Initialize(psi), qr[:n])"),
        ("c.gate(matrix, [0, 1])", "qc.append(UnitaryGate(matrix), [0, 1])"),
        ("c.measure()", "qc.measure(qr, cr)"),
        ("with c.if_bit('crx', 1): c.x('bob')", "with qc.if_test((crx, 1)): qc.x(qr_B)"),
        ("c.draw()", "qc.draw('mpl', initial_state=True)"),
        ("c.stats()", "qc.depth(); len(qc); qc.num_nonlocal_gates()"),
        ("c.compile(basis=['rx','rz','cx'])", "generate_preset_pass_manager(basis_gates=...).run(qc)"),
        ("c.to_gate('U'), c.controlled(1)", "qc.to_gate(); qc.to_gate().control(1)"),
        ("c.qc", "the raw QuantumCircuit"),
    ],
    "running": [
        ("c.state()", "Aer.get_backend('statevector_simulator').run(qc).result().get_statevector()"),
        ("c.unitary()", "qi.Operator.from_circuit(qc)"),
        ("c.probabilities()", "sv.probabilities_dict()"),
        ("c.run()", "Aer.get_backend('qasm_simulator').run(qc, shots=...).result().get_counts()"),
        ("c.run(backend='noisy')", "FakeManilaV2().run(transpile(qc, backend), shots=...)"),
        ("counts.plot()", "plot_histogram(counts)"),
        ("counts.most_likely()", "max(counts, key=counts.get)"),
    ],
    "show": [
        ("show(x)", "array_to_latex(x, precision=4)"),
        ("show(psi, style='ket') / dirac(psi)", "sv.draw('latex')"),
        ("bloch(psi)  or  bloch(c)", "plot_bloch_multivector(sv)"),
        ("qsphere(psi)", "plot_state_qsphere(sv)"),
        ("histogram(c1, c2)", "plot_histogram([c1, c2])"),
        ("versions()", "import tutorial_magics; %qiskit_version_table"),
    ],
    "density": [
        ("density_matrix(psi)", "qi.DensityMatrix(psi)"),
        ("keep(rho, 2)", "qi.partial_trace(rho, [0, 1])"),
        ("partial_trace(rho, [0, 1])", "qi.partial_trace(rho, [0, 1])"),
        ("purity(rho), is_valid(rho)", "rho.purity(), rho.is_valid()"),
        ("fidelity(a, b), entropy(rho)", "qi.state_fidelity(a, b), qi.entropy(rho)"),
        ("is_entangled(psi)", "-"),
    ],
    "algorithms": [
        ("qft(n), inverse_qft(n)", "qft_rotations(...) + swap_registers(...)"),
        ("deutsch_jozsa(n, kind='balanced')", "~20 lines in Deutsch_Josza.ipynb"),
        ("bernstein_vazirani('1011')", "-"),
        ("grover('101')", "~40 lines in Grover.ipynb"),
        ("phase_estimation(U, 5, eigenstate)", "~30 lines in QPE.ipynb"),
        ("teleportation(psi)", "QCTP_04.ipynb"),
    ],
    "dynamics": [
        ("hamiltonian({'ZZ': 1, 'XI': -0.1})", "(Z ^ Z) - 0.1 * (X ^ I)"),
        ("ising_chain(L, J, h, alpha)", "get_hamiltonian(L, J, h, alpha)"),
        ("trotter_circuit(H, time, steps, order=2)", "PauliEvolutionGate(H, dt, synthesis=SuzukiTrotter()) loop"),
        ("evolve(H, psi, t)", "psi.evolve(sp.linalg.expm(-1j * t * H.to_matrix()))"),
        ("time_evolution(H, psi, T, steps, observables)", "TrotterQRTE(...).evolve(TimeEvolutionProblem(...))"),
        ("expectation(psi, H)", "np.real(psi.expectation_value(H))"),
    ],
}


def cheatsheet(topic=None):
    """Print QumPy commands next to their Qiskit equivalents.

    ``cheatsheet()`` shows everything; ``cheatsheet("circuits")`` one topic.
    Topics: settings, states, gates, circuits, running, show, density,
    algorithms, dynamics.
    """
    topics = [topic] if topic else list(_SHEET)
    for t in topics:
        if t not in _SHEET:
            print(f"Unknown topic '{t}'. Topics: {', '.join(_SHEET)}")
            return
        print(f"\n== {t.upper()} " + "=" * (70 - len(t)))
        width = max(len(q) for q, _ in _SHEET[t]) + 2
        print(f"  {'QumPy':<{width}}Qiskit / numpy")
        for q, k in _SHEET[t]:
            print(f"  {q:<{width}}{k}")
