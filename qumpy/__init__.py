"""QumPy -- quantum computing for beginners, on top of Qiskit.

    import qumpy as qp
    from qumpy import Qum

    Qum.shots = 1000
    c = qp.Circuit(2).h(0).cx(0, 1).measure()
    c.run().plot()

Everything is also available through ``Qum`` (``Qum.Circuit``, ``Qum.ket``...).
Type ``qp.cheatsheet()`` for the full list of commands.
"""

__version__ = "0.1.0"

from .config import Qum
from .errors import QumError
from .states import ket, bra, basis, zero, plus, bell, ghz, random_state, num_qubits
from .linalg import (
    to_array, column, inner, outer, norm, normalize, dagger, is_hermitian, is_unitary,
    eig, eigenvectors, commutator, anticommutator, expm, trace,
)
from .gates import (
    I, X, Y, Z, H, S, T, CNOT, CX, CZ, SWAP, TOFFOLI, CCX,
    Rx, Ry, Rz, P, U, operator, pauli, tensor, apply, random_unitary, equal,
)
from .results import Counts
from .circuit import Circuit, run, state, unitary, noisy_backend
from .display import show, dirac, latex, bloch, qsphere, histogram, versions, in_notebook
from .density import (
    density_matrix, mixed_state, partial_trace, keep, reduced_state, purity, is_pure, is_valid,
    entropy, fidelity, is_entangled, concurrence, bloch_vector,
)
from .algorithms import (
    qft, inverse_qft, bell_circuit, ghz_circuit, teleportation, dj_oracle, deutsch_jozsa,
    dj_answer, bernstein_vazirani, grover_oracle, diffuser, grover_iterations, grover,
    phase_estimation, estimated_phase,
)
from .dynamics import (
    hamiltonian, ising_chain, magnetization, zz_correlation, trotter_step, trotter_circuit,
    evolution_operator, evolve, exact_evolution, expectation, time_evolution, EvolutionResult,
)
from .cheatsheet import cheatsheet

from numpy import pi  # handy: qp.pi

__all__ = [n for n in dir() if not n.startswith("_") and n not in {
    "config", "errors", "states", "linalg", "gates", "results", "circuit", "display",
    "density", "algorithms", "dynamics",
}]
