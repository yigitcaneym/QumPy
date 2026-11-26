"""Density matrices, entanglement and mixed states.

    rho = density_matrix(bell("phi+"))
    keep(rho, 1)                 reduced state of qubit 1   (what you KEEP)
    partial_trace(rho, [0])      same thing, Qiskit style   (what you TRACE OUT)
    purity(rho)                  Tr(rho^2): 1 = pure, 1/2^n = maximally mixed
    entropy(rho)                 von Neumann entropy (bits)
    is_entangled(state)          True for a Bell state, False for |00>
    fidelity(a, b)               how close two states are (1 = identical)
"""

from __future__ import annotations

import numpy as np
from qiskit import quantum_info as qi

from .errors import QumError


def _to_rho(x):
    from .circuit import Circuit
    from .states import ket

    if isinstance(x, qi.DensityMatrix):
        return x
    if isinstance(x, Circuit):
        return qi.DensityMatrix(x.state())
    if isinstance(x, qi.Statevector):
        return qi.DensityMatrix(x)
    if isinstance(x, str):
        return qi.DensityMatrix(ket(x))
    a = np.asarray(x.data if hasattr(x, "data") else x, dtype=complex)
    if a.ndim == 1 or (a.ndim == 2 and 1 in a.shape):
        return qi.DensityMatrix(ket(a.flatten()))
    return qi.DensityMatrix(a)


def density_matrix(x):
    """rho = |psi><psi| for a state, or wrap a matrix as a DensityMatrix."""
    return _to_rho(x)


def mixed_state(states, probabilities):
    """rho = sum_i p_i |psi_i><psi_i|  (e.g. ``mixed_state(["0", "1"], [0.5, 0.5])``)."""
    if len(states) != len(probabilities):
        raise QumError("You need one probability per state.")
    p = np.asarray(probabilities, dtype=float)
    if np.any(p < 0) or not np.isclose(p.sum(), 1):
        raise QumError(f"Probabilities must be >= 0 and add up to 1 (they add up to {p.sum():.4g}).")
    rhos = [_to_rho(s) for s in states]
    out = rhos[0] * p[0]
    for r, pi in zip(rhos[1:], p[1:]):
        out = out + r * pi
    return out


def partial_trace(x, trace_out):
    """Trace out the qubits in ``trace_out`` (Qiskit convention)."""
    rho = _to_rho(x)
    trace_out = [trace_out] if isinstance(trace_out, int) else list(trace_out)
    n = rho.num_qubits
    for q in trace_out:
        if not 0 <= q < n:
            raise QumError(f"Qubit {q} does not exist (the state has {n} qubits).")
    return qi.partial_trace(rho, trace_out)


def keep(x, qubits):
    """Reduced state of the qubits you want to KEEP (everything else is traced out)."""
    rho = _to_rho(x)
    qubits = [qubits] if isinstance(qubits, int) else list(qubits)
    others = [q for q in range(rho.num_qubits) if q not in qubits]
    return partial_trace(rho, others) if others else rho


reduced_state = keep


def purity(x):
    """Tr(rho^2). 1 for a pure state, smaller for mixed states."""
    return float(np.real(_to_rho(x).purity()))


def is_pure(x, atol=1e-8):
    return bool(np.isclose(purity(x), 1.0, atol=atol))


def is_valid(x):
    """Is this a valid density matrix (Hermitian, trace 1, positive)?"""
    return bool(_to_rho(x).is_valid())


def entropy(x, base=2):
    """Von Neumann entropy S(rho) = -Tr(rho log rho)."""
    return float(qi.entropy(_to_rho(x), base=base))


def fidelity(a, b):
    """State fidelity between two states / density matrices (1 = identical)."""
    from .states import ket

    def conv(s):
        if isinstance(s, (qi.Statevector, qi.DensityMatrix)):
            return s
        if isinstance(s, str):
            return ket(s)
        return _to_rho(s) if np.ndim(getattr(s, "data", s)) == 2 else ket(s)

    return float(qi.state_fidelity(conv(a), conv(b)))


def is_entangled(state, qubits=(0,)):
    """For a PURE state: are ``qubits`` entangled with the rest?

    It checks whether the reduced state of ``qubits`` is mixed.
    """
    rho = _to_rho(state)
    if not is_pure(rho):
        raise QumError("is_entangled() only works for pure states.",
                       hint="For mixed states entanglement is much harder to decide.")
    return not is_pure(keep(rho, list(qubits)))


def concurrence(state):
    """Concurrence of a 2-qubit state (0 = not entangled, 1 = maximally entangled)."""
    rho = _to_rho(state)
    if rho.num_qubits != 2:
        raise QumError("Concurrence is defined here for 2-qubit states only.")
    return float(qi.concurrence(rho))


def bloch_vector(x):
    """(<X>, <Y>, <Z>) of a single qubit."""
    rho = _to_rho(x)
    if rho.num_qubits != 1:
        raise QumError("bloch_vector() needs a 1-qubit state.", hint="Use keep(state, qubit) first.")
    return np.real([rho.expectation_value(qi.Pauli(p)) for p in "XYZ"])
