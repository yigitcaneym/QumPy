import numpy as np
import pytest
from qiskit import QuantumCircuit
from qiskit import quantum_info as qi
from qiskit.circuit.library import QFTGate

import qumpy as qp
from qumpy import Qum, QumError


@pytest.fixture(autouse=True)
def _reset():
    Qum.reset()
    Qum.seed = 1234
    yield
    Qum.reset()


# ------------------------------------------------------------------ Qum
def test_qum_shots_is_used_by_run():
    Qum.shots = 37
    counts = qp.Circuit(1).h(0).measure().run()
    assert counts.shots == 37 and sum(counts.values()) == 37


def test_qum_validates_and_suggests():
    with pytest.raises(QumError, match="positive"):
        Qum.shots = -5
    with pytest.raises(QumError, match="shots"):
        Qum.shot = 10  # typo -> suggestion
    with pytest.raises(QumError):
        Qum.backend = "quantum-magic"


def test_qum_using_restores():
    Qum.shots = 100
    with Qum.using(shots=7):
        assert Qum.shots == 7
    assert Qum.shots == 100


def test_qum_forwards_functions():
    assert Qum.Circuit is qp.Circuit
    assert qp.equal(Qum.ket("+"), qp.ket([1, 1]))


# --------------------------------------------------------------- states
def test_ket_forms():
    assert qp.ket("01") == qi.Statevector.from_label("01")
    assert qp.ket("|1>") == qi.Statevector.from_label("1")
    assert qp.ket(3, n=2) == qi.Statevector.from_label("11")
    assert np.isclose(qp.norm(qp.ket([1, 1, 0, 1])), 1)
    with pytest.raises(QumError):
        qp.ket("012")
    with pytest.raises(QumError):
        qp.ket(4, n=2)


def test_bell_and_ghz():
    assert qp.equal(qp.bell("phi+"), qp.bell_circuit("phi+").state())
    for w in ("phi-", "psi+", "psi-"):
        assert qp.equal(qp.bell(w), qp.bell_circuit(w).state())
    assert qp.equal(qp.ghz(3), qp.ghz_circuit(3).state())


def test_linalg():
    a, b = qp.ket("0"), qp.ket("+")
    assert np.isclose(qp.inner(a, b), 1 / np.sqrt(2))
    assert np.allclose(qp.outer(a), [[1, 0], [0, 0]])
    w, _ = qp.eig(qp.X)
    assert np.allclose(w, [-1, 1])
    assert np.allclose(qp.commutator(qp.X, qp.Y), 2j * qp.Z.data)
    assert qp.is_hermitian(qp.H) and qp.is_unitary(qp.H)


def test_dirac():
    assert qp.dirac(qp.bell("phi-"), 3) == "0.707|00⟩ - 0.707|11⟩"
    assert qp.dirac(qp.ket("1")) == "|1⟩"


# ----------------------------------------------------------------- gates
def test_gates_and_tensor():
    assert qp.equal(qp.apply(qp.H, "0"), qp.ket("+"))
    assert qp.tensor(qp.X, qp.Z) == qp.X.tensor(qp.Z)
    assert qp.tensor("0", "1") == qp.ket("01")
    U = qp.random_unitary(1)
    assert qp.is_unitary(U)
    assert qp.equal(qp.dagger(U).compose(U), qp.I)


# --------------------------------------------------------------- circuit
def test_circuit_chain_and_unitary():
    c = qp.Circuit(2).h(0).cnot(0, 1)
    assert qp.equal(c.state(), qp.bell("phi+"))
    assert c.unitary().dim == (4, 4)
    assert qp.equal(qp.Circuit(1).x(0).unitary(), qp.X)


def test_measure_creates_bits_and_counts():
    c = qp.Circuit(2).x(1).measure()
    assert c.num_bits == 2
    counts = c.run(shots=100)
    assert counts == {"10": 100}
    assert counts.most_likely() == "10"
    assert counts.as_ints() == {2: 100}
    assert counts.reversed_bits() == {"01": 100}


def test_auto_measure_warns():
    with pytest.warns(UserWarning):
        counts = qp.Circuit(1).x(0).run(shots=10)
    assert counts == {"1": 10}
    Qum.auto_measure = False
    with pytest.raises(QumError):
        qp.Circuit(1).run()


def test_friendly_errors():
    with pytest.raises(QumError, match="hadamard|Did you mean"):
        qp.Circuit(1).hadamrd(0)
    with pytest.raises(QumError, match="qubit"):
        qp.Circuit(2).h(5)
    with pytest.raises(QumError, match="register"):
        qp.Circuit(alice=1).h("bob")


def test_named_registers_and_all():
    c = qp.Circuit(a=2, b=1)
    c.h("a").x("b")
    assert qp.equal(c.state(), qp.ket("1++"))
    d = qp.Circuit(3).h("all")
    assert qp.equal(d.state(), qp.plus(3))


def test_init_and_gate():
    psi = qp.random_state(1)
    c = qp.Circuit(2).init(psi, qubits=1)
    assert qp.fidelity(qp.keep(c.state(), 1), psi) > 0.999
    c2 = qp.Circuit(1).gate(qp.H, 0)
    assert qp.equal(c2.unitary(), qp.H)
    with pytest.raises(QumError):
        c.unitary()  # contains initialize


def test_noisy_backend_runs():
    c = qp.bell_circuit(measure=True)
    counts = c.run(shots=200, backend="noisy")
    assert counts.shots == 200 and counts.backend.startswith("noisy")
    Qum.device = "generic"
    assert qp.ghz_circuit(6, measure=True).run(shots=50, backend="noisy").shots == 50


def test_compile_and_stats_and_qiskit_interop():
    c = qp.Circuit(1).gate(qp.random_unitary(1), 0)
    t = c.compile(basis=["rx", "rz", "cx"])
    assert set(t.qc.count_ops()) <= {"rx", "rz", "cx"}
    assert qp.equal(t.unitary(), c.unitary())
    assert c.stats(show=False)["qubits"] == 1
    raw = QuantumCircuit(1)
    raw.x(0)
    assert qp.equal(qp.state(raw), qp.ket("1"))


def test_add_and_controlled():
    a = qp.Circuit(1).h(0)
    b = qp.Circuit(1).h(0)
    assert qp.equal((a + b).unitary(), qp.I)
    cu = qp.Circuit(1).x(0).controlled()
    c = qp.Circuit(2).x(0)
    c.append(cu, [0, 1])
    assert qp.equal(c.state(), qp.ket("11"))


# --------------------------------------------------------------- density
def test_density_tools():
    rho = qp.density_matrix(qp.bell("phi+"))
    r1 = qp.keep(rho, 1)
    assert np.isclose(qp.purity(r1), 0.5)
    assert qp.is_valid(rho) and qp.is_pure(rho)
    assert qp.is_entangled(qp.bell("psi-"))
    assert not qp.is_entangled(qp.ket("01"))
    assert np.isclose(qp.entropy(r1), 1)
    assert np.isclose(qp.concurrence(qp.bell("phi+")), 1)
    mix = qp.mixed_state(["0", "1"], [0.5, 0.5])
    assert np.allclose(mix.data, np.eye(2) / 2)
    assert np.allclose(qp.bloch_vector("+"), [1, 0, 0])


# ------------------------------------------------------------ algorithms
@pytest.mark.parametrize("n", [1, 2, 3, 4])
def test_qft_matches_qiskit(n):
    assert qp.qft(n).unitary() == qi.Operator(QFTGate(n))
    assert qp.equal(qp.inverse_qft(n).unitary(), qi.Operator(QFTGate(n)).adjoint())


def test_deutsch_jozsa():
    for kind in ("constant", "balanced"):
        c = qp.deutsch_jozsa(4, kind=kind)
        assert qp.dj_answer(c.run(shots=20)) == kind
    c = qp.deutsch_jozsa(3, kind="constant", value=1)
    assert qp.dj_answer(c.run(shots=5)) == "constant"


def test_bernstein_vazirani():
    assert qp.bernstein_vazirani("1011").run(shots=10) == {"1011": 10}


@pytest.mark.parametrize("marked", ["11", "101", ["0110", "1001"]])
def test_grover(marked):
    counts = qp.grover(marked).run(shots=500)
    targets = [marked] if isinstance(marked, str) else marked
    hit = sum(counts.get(t, 0) for t in targets) / 500
    assert hit > 0.8


def test_phase_estimation():
    U = qp.P(2 * np.pi * 0.375)
    c = qp.phase_estimation(U, n_counting=3, eigenstate="1")
    assert np.isclose(qp.estimated_phase(c.run(shots=100)), 0.375)
    # 2-qubit unitary, eigenstate prepared by a circuit
    U2 = qp.tensor(qp.P(2 * np.pi * 0.25), qp.P(2 * np.pi * 0.5))  # |11> -> phase 0.75
    c2 = qp.phase_estimation(U2, 2, eigenstate=qp.Circuit(2).x("all"))
    assert np.isclose(qp.estimated_phase(c2.run(shots=50)), 0.75)


def test_teleportation():
    psi = qp.random_state(1, seed=7)
    for seed in range(4):
        out = qp.teleportation(psi).state(seed=seed)
        assert qp.fidelity(qp.keep(out, 2), psi) > 0.999


# -------------------------------------------------------------- dynamics
def test_hamiltonian_forms():
    H1 = qp.hamiltonian({"ZZ": 1, "XI": -0.1})
    X, Z, I = (qi.SparsePauliOp(p) for p in "XZI")
    H2 = (Z ^ Z) - 0.1 * (X ^ I)
    assert np.allclose(H1.to_matrix(), H2.to_matrix())
    H3 = qp.hamiltonian([(1, "ZZ"), (-0.1, "XI")])
    assert np.allclose(H3.to_matrix(), H2.to_matrix())
    H4 = qp.hamiltonian([("ZZ", [0, 1], 1.0), ("X", [1], -0.1)])
    assert np.allclose(H4.to_matrix(), H2.to_matrix())


def test_trotter_converges_to_exact():
    H = qp.hamiltonian({"ZZ": 1, "XI": -0.1})
    psi0 = qp.ket("00")
    exact = qp.evolve(H, psi0, 2.0)
    c = qp.trotter_circuit(H, time=2.0, steps=20, order=2)
    assert qp.fidelity(c.state(), exact) > 0.999
    assert np.isclose(qp.fidelity(qp.exact_evolution(H, psi0, [2.0])[0], exact), 1)


def test_time_evolution_is_really_trotterized():
    H = qp.ising_chain(3, J=0.5, h=1.0, alpha=0.3)
    coarse = qp.time_evolution(H, "010", time=4, steps=4, order=1)
    fine = qp.time_evolution(H, "010", time=4, steps=200, order=1)
    assert coarse.fidelity() < 0.999          # visible Trotter error
    assert fine.fidelity() > coarse.fidelity()
    # matches the circuit built by trotter_circuit
    c = qp.trotter_circuit(H, time=4, steps=4, order=1, initial="010")
    assert qp.fidelity(c.state(), coarse.states[-1]) > 0.999999


def test_time_evolution_ising():
    L = 4
    H = qp.ising_chain(L, J=0.2, h=1.2, alpha=np.pi / 8)
    res = qp.time_evolution(H, "0110", time=5, steps=50, order=2,
                            observables={"Energy": H, "Magnetization": qp.magnetization(L),
                                         "Correlation": qp.zz_correlation(L)})
    assert res.values["Energy"].shape == (51,)
    assert np.allclose(res.values["Energy"], res.values["Energy"][0], atol=0.05)  # energy ~conserved
    assert res.fidelity() > 0.99
    ex = res.exact(num_points=11)
    assert np.isclose(ex["Magnetization"][0], res.values["Magnetization"][0])


def test_display_does_not_crash(capsys):
    qp.show(qp.ket("+"))
    qp.show(qp.bell("phi+"), style="ket")
    qp.show(qp.H)
    qp.versions()
    qp.cheatsheet("circuits")
    Qum.settings()
    out = capsys.readouterr().out
    assert "QumPy" in out and "qiskit" in out
    assert r"\begin{bmatrix}" in qp.latex(qp.X)
