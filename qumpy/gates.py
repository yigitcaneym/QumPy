"""Gates as matrices (Qiskit ``Operator`` objects).

    X, Y, Z, H, S, T, I          fixed 1-qubit gates
    Rx(t), Ry(t), Rz(t), P(phi)  rotations / phase
    CNOT, CZ, SWAP, TOFFOLI      multi-qubit gates
    tensor(X, Z)                 X (x) Z   (left factor acts on the highest qubit)
    apply(H, ket("0"))           H|0>
    random_unitary(1)            random 1-qubit unitary
"""

from __future__ import annotations

import numpy as np
from qiskit import quantum_info as qi
from qiskit.circuit.library import (
    CCXGate, CXGate, CZGate, PhaseGate, RXGate, RYGate, RZGate, SwapGate, UGate,
)

from .config import Qum
from .errors import QumError
from .linalg import to_array

I = qi.Operator(qi.Pauli("I"))
X = qi.Operator(qi.Pauli("X"))
Y = qi.Operator(qi.Pauli("Y"))
Z = qi.Operator(qi.Pauli("Z"))
H = qi.Operator(np.array([[1, 1], [1, -1]]) / np.sqrt(2))
S = qi.Operator(np.diag([1, 1j]))
T = qi.Operator(np.diag([1, np.exp(1j * np.pi / 4)]))
CNOT = CX = qi.Operator(CXGate())
CZ = qi.Operator(CZGate())
SWAP = qi.Operator(SwapGate())
TOFFOLI = CCX = qi.Operator(CCXGate())


def Rx(theta):
    """Rotation by ``theta`` around the x-axis of the Bloch sphere."""
    return qi.Operator(RXGate(theta))


def Ry(theta):
    """Rotation by ``theta`` around the y-axis of the Bloch sphere."""
    return qi.Operator(RYGate(theta))


def Rz(theta):
    """Rotation by ``theta`` around the z-axis of the Bloch sphere."""
    return qi.Operator(RZGate(theta))


def P(phi):
    """Phase gate diag(1, e^{i phi})."""
    return qi.Operator(PhaseGate(phi))


def U(theta, phi, lam):
    """General 1-qubit gate U(theta, phi, lambda)."""
    return qi.Operator(UGate(theta, phi, lam))


def operator(m):
    """Turn a matrix (list / numpy array / Pauli string) into a Qiskit Operator."""
    if isinstance(m, qi.Operator):
        return m
    if isinstance(m, str):
        return qi.Operator(qi.Pauli(m.upper()))
    if hasattr(m, "to_operator"):
        return m.to_operator()
    from .circuit import Circuit

    if isinstance(m, Circuit):
        return m.unitary()
    a = to_array(m)
    if a.ndim != 2 or a.shape[0] != a.shape[1]:
        raise QumError(f"An operator must be a square matrix, got shape {a.shape}.")
    return qi.Operator(a)


def pauli(label):
    """Pauli string as Operator, e.g. ``pauli("XZ")`` = X (x) Z."""
    return operator(label)


def tensor(*ops):
    """Tensor (Kronecker) product A (x) B (x) ...

    Works for operators *and* states. As in Qiskit, the left-most factor
    belongs to the highest qubit index.
    """
    if not ops:
        raise QumError("tensor() needs at least one argument.")
    from .states import ket

    if all(isinstance(o, (qi.Statevector, str)) for o in ops):
        out = ket(ops[0])
        for o in ops[1:]:
            out = out.tensor(ket(o))
        return out
    out = operator(ops[0])
    for o in ops[1:]:
        out = out.tensor(operator(o))
    return out


def apply(op, state):
    """Apply a gate to a state: returns op|state>."""
    from .states import ket

    return ket(state).evolve(operator(op))


def random_unitary(n=1, seed=None):
    """Random ``n``-qubit unitary (``n=1`` -> 2x2 matrix)."""
    seed = Qum.seed if seed is None else seed
    return qi.random_unitary(2**n, seed=seed)


def equal(a, b, up_to_phase=True):
    """Are two operators (or states) the same? Global phase is ignored by default."""
    if isinstance(a, qi.Statevector) or isinstance(b, qi.Statevector):
        from .states import ket

        a, b = ket(a), ket(b)
        if up_to_phase:
            return bool(np.isclose(abs(np.vdot(a.data, b.data)), 1.0))
        return bool(np.allclose(a.data, b.data))
    a, b = operator(a), operator(b)
    return a.equiv(b) if up_to_phase else a == b
