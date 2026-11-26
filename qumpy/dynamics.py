"""Hamiltonians and time evolution (Trotterization).

    H = hamiltonian({"ZZ": 1, "XI": -0.1})       # = Z(x)Z - 0.1 X(x)I
    H = ising_chain(L=6, J=0.2, h=1.2, alpha=pi/8)
    c = trotter_circuit(H, time=20, steps=10, order=2)
    exact = evolve(H, ket("00"), time=20)        # exact e^{-iHt}|psi>
    res = time_evolution(H, ket("001100"), time=30, steps=60,
                         observables={"Energy": H, "Magnetization": magnetization(6)})
    res.plot(exact=True)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from qiskit import quantum_info as qi
from qiskit.circuit.library import PauliEvolutionGate
from qiskit.quantum_info import SparsePauliOp
from qiskit.synthesis import LieTrotter, SuzukiTrotter

from .circuit import Circuit
from .errors import QumError


def hamiltonian(terms, num_qubits=None):
    """Build a Hamiltonian (``SparsePauliOp``) in a readable way.

    * ``hamiltonian({"ZZ": 1.0, "XI": -0.1})``
    * ``hamiltonian([(1.0, "ZZ"), (-0.1, "XI")])``
    * ``hamiltonian("ZZ")``
    * ``hamiltonian([("ZZ", [0, 1], -1.0), ("X", [2], 0.5)], num_qubits=3)``
      (sparse form: Pauli string, qubits, coefficient -- as in the course)
    * a numpy matrix is converted with ``SparsePauliOp.from_operator``
    """
    if isinstance(terms, SparsePauliOp):
        return terms
    if isinstance(terms, str):
        return SparsePauliOp(terms.upper())
    if isinstance(terms, dict):
        return SparsePauliOp.from_list([(k.upper(), v) for k, v in terms.items()]).simplify()
    if isinstance(terms, (list, tuple)) and terms and isinstance(terms[0], tuple):
        first = terms[0]
        if len(first) == 3:
            if num_qubits is None:
                num_qubits = 1 + max(max(q) for _, q, _ in terms)
            return SparsePauliOp.from_sparse_list(
                [(p.upper(), list(q), c) for p, q, c in terms], num_qubits=num_qubits).simplify()
        if len(first) == 2:
            pairs = [(t[1], t[0]) if isinstance(t[1], str) else (t[0], t[1]) for t in terms]
            return SparsePauliOp.from_list([(p.upper(), c) for p, c in pairs]).simplify()
    arr = np.asarray(terms.data if hasattr(terms, "data") else terms, dtype=complex)
    if arr.ndim == 2:
        return SparsePauliOp.from_operator(qi.Operator(arr))
    raise QumError("Could not understand this Hamiltonian.",
                   hint='Example: hamiltonian({"ZZ": 1, "XI": -0.1})')


def ising_chain(L, J=1.0, h=1.0, alpha=0.0):
    """Transverse/longitudinal field Ising chain (course notebook QCTP_09).

    H = -J sum Z_i Z_{i+1} - h sin(alpha) sum Z_i - h cos(alpha) sum X_i
    """
    zz = [("ZZ", [i, i + 1], -J) for i in range(L - 1)]
    z = [("Z", [i], -h * np.sin(alpha)) for i in range(L)]
    x = [("X", [i], -h * np.cos(alpha)) for i in range(L)]
    return SparsePauliOp.from_sparse_list([*zz, *z, *x], num_qubits=L).simplify()


def magnetization(L):
    """M = sum_i Z_i"""
    return SparsePauliOp.from_sparse_list([("Z", [i], 1.0) for i in range(L)], num_qubits=L)


def zz_correlation(L):
    """Mean nearest-neighbour correlation (1/(L-1)) sum_i Z_i Z_{i+1}"""
    return SparsePauliOp.from_sparse_list(
        [("ZZ", [i, i + 1], 1.0) for i in range(L - 1)], num_qubits=L) / (L - 1)


def _synthesis(order):
    if order == 1:
        return LieTrotter()
    if order in (2, 4, 6, 8):
        return SuzukiTrotter(order=order)
    raise QumError(f"Trotter order must be 1, 2, 4, 6 or 8, got {order}.")


def trotter_step(H, dt, order=1):
    """One Trotter step e^{-i H dt} as a gate."""
    return PauliEvolutionGate(hamiltonian(H), dt, synthesis=_synthesis(order))


def trotter_circuit(H, time, steps, order=1, initial=None, decompose=True):
    """Circuit approximating e^{-iHt} with ``steps`` Trotter steps."""
    H = hamiltonian(H)
    n = H.num_qubits
    c = Circuit(n, name=f"Trotter (order {order})")
    if initial is not None:
        c.init(initial)
    step = trotter_step(H, time / steps, order)
    for _ in range(steps):
        c.qc.append(step, range(n))
        c.qc.barrier()
    if decompose:
        c = c.decompose(reps=2)
    return c


def evolution_operator(H, time):
    """Exact U(t) = e^{-iHt} as an Operator."""
    import scipy.linalg

    m = hamiltonian(H).to_matrix()
    return qi.Operator(scipy.linalg.expm(-1j * time * m))


def evolve(H, state, time):
    """Exact e^{-iHt}|state> (a Statevector)."""
    from .states import ket

    return ket(state).evolve(evolution_operator(H, time))


def exact_evolution(H, state, times):
    """Exact states at every time in ``times`` (diagonalises H once)."""
    from .states import ket

    psi = ket(state)
    w, v = np.linalg.eigh(hamiltonian(H).to_matrix())
    c0 = v.conj().T @ psi.data
    return [qi.Statevector(v @ (np.exp(-1j * w * t) * c0)) for t in np.atleast_1d(times)]


def expectation(state, op):
    """<state| op |state> as a real number (imaginary part dropped if ~0)."""
    from .states import ket

    if not isinstance(state, (qi.Statevector, qi.DensityMatrix)):
        state = ket(state)
    if isinstance(op, (str, dict)):
        op = hamiltonian(op)
    val = complex(state.expectation_value(op))
    return val.real if abs(val.imag) < 1e-10 else val


@dataclass
class EvolutionResult:
    """Output of ``time_evolution``: ``times``, ``values[name]``, ``states``."""

    times: np.ndarray
    values: dict
    states: list
    H: SparsePauliOp
    initial: qi.Statevector
    order: int
    exact_values: dict = field(default_factory=dict)

    def exact(self, num_points=200):
        """Exact curves of the same observables (computed once and cached)."""
        if not self.exact_values:
            t = np.linspace(self.times[0], self.times[-1], num_points)
            states = exact_evolution(self.H, self.initial, t)
            self.exact_values = {"times": t}
            for name, op in self._ops.items():
                self.exact_values[name] = np.array([expectation(s, op) for s in states])
        return self.exact_values

    def fidelity(self):
        """Fidelity between the final Trotter state and the exact final state."""
        exact = exact_evolution(self.H, self.initial, [self.times[-1]])[0]
        return float(qi.state_fidelity(self.states[-1], exact))

    def plot(self, exact=True, figsize=None):
        import matplotlib.pyplot as plt

        names = list(self.values)
        fig, axes = plt.subplots(len(names), sharex=True,
                                 figsize=figsize or (8, 2.6 * len(names)), squeeze=False)
        ex = self.exact() if exact else None
        for ax, name in zip(axes[:, 0], names):
            ax.plot(self.times, self.values[name], marker="x", ls="-", lw=0.8,
                    c="darkmagenta", label=f"Trotter (order {self.order})")
            if ex is not None:
                ax.plot(ex["times"], ex[name], c="k", ls="--", lw=1, label="Exact")
            ax.set_ylabel(name)
        axes[-1, 0].set_xlabel("Time")
        axes[0, 0].legend(loc="best")
        fig.suptitle("Observable evolution")
        fig.tight_layout()
        return fig


def time_evolution(H, initial, time, steps, observables=None, order=2):
    """Trotterized time evolution and observables at every step.

    ``observables``: dict ``{"name": operator}`` (default: the energy).
    Returns an :class:`EvolutionResult` (use ``.plot()``).
    """
    from .states import ket

    H = hamiltonian(H)
    psi0 = ket(initial)
    if psi0.num_qubits != H.num_qubits:
        raise QumError(f"The initial state has {psi0.num_qubits} qubits but H acts on {H.num_qubits}.")
    obs = observables if observables is not None else {"Energy": H}
    if not isinstance(obs, dict):
        obs = {f"O{i}": o for i, o in enumerate(obs)}
    obs = {k: hamiltonian(v) if not isinstance(v, (qi.Operator,)) else v for k, v in obs.items()}

    from qiskit import QuantumCircuit

    import warnings

    step_qc = QuantumCircuit(H.num_qubits)
    step_qc.append(trotter_step(H, time / steps, order), range(H.num_qubits))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")   # scipy sparse-efficiency chatter
        # decompose first: Operator(PauliEvolutionGate) would be the EXACT exponential
        U = qi.Operator(step_qc.decompose(reps=2))

    states = [psi0]
    for _ in range(steps):
        states.append(states[-1].evolve(U))
    times = np.linspace(0, time, steps + 1)
    values = {k: np.array([expectation(s, o) for s in states]) for k, o in obs.items()}
    res = EvolutionResult(times, values, states, H, psi0, order)
    res._ops = obs
    return res
