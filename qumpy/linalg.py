"""Linear algebra helpers (bra-ket maths) -- the numpy part of the course.

    inner(a, b)        <a|b>
    outer(a, b)        |a><b|
    norm(v)            ||v||
    dagger(M)          M^dagger  (conjugate transpose)
    eig(M)             eigenvalues and eigenvectors (sorted)
    is_hermitian(M)    M == M^dagger ?
    commutator(A, B)   AB - BA
"""

from __future__ import annotations

import numpy as np
import scipy.linalg
from qiskit import quantum_info as qi

from .errors import QumError


def to_array(x):
    """Turn a Statevector / Operator / DensityMatrix / list into a numpy array."""
    if isinstance(x, (qi.Statevector, qi.DensityMatrix)):
        return np.asarray(x.data)
    if isinstance(x, qi.Operator):
        return np.asarray(x.data)
    if isinstance(x, (qi.SparsePauliOp, qi.Pauli)):
        return np.asarray(x.to_matrix())
    if hasattr(x, "to_matrix"):
        return np.asarray(x.to_matrix())
    return np.asarray(x, dtype=complex)


def column(*entries):
    """A column vector: ``column(1, 1j)`` -> [[1], [1j]]."""
    if len(entries) == 1 and np.ndim(entries[0]) > 0:
        entries = entries[0]
    return np.asarray(entries, dtype=complex).reshape(-1, 1)


def _vec(x):
    return to_array(x).flatten()


def inner(a, b):
    """<a|b>  (the first argument is complex-conjugated)."""
    a, b = _vec(a), _vec(b)
    if a.shape != b.shape:
        raise QumError(f"Vectors have different sizes ({a.size} and {b.size}).")
    return complex(np.vdot(a, b))


def outer(a, b=None):
    """|a><b| ; ``outer(a)`` gives the projector |a><a|."""
    a = _vec(a)
    b = a if b is None else _vec(b)
    return np.outer(a, np.conj(b))


def norm(v):
    """Length of a vector ||v|| = sqrt(<v|v>)."""
    return float(np.linalg.norm(_vec(v)))


def normalize(v):
    """v / ||v||"""
    v = _vec(v)
    n = np.linalg.norm(v)
    if np.isclose(n, 0):
        raise QumError("Cannot normalise the zero vector.")
    return v / n


def dagger(m):
    """Conjugate transpose M^dagger. Keeps Qiskit types (Operator -> Operator)."""
    if isinstance(m, qi.Operator):
        return m.adjoint()
    if isinstance(m, qi.Statevector):
        return np.conj(m.data).reshape(1, -1)
    return np.conj(to_array(m)).T


def is_hermitian(m, atol=1e-10):
    a = to_array(m)
    return a.shape[0] == a.shape[-1] and np.allclose(a, a.conj().T, atol=atol)


def is_unitary(m, atol=1e-10):
    a = to_array(m)
    return a.shape[0] == a.shape[-1] and np.allclose(a.conj().T @ a, np.eye(a.shape[0]), atol=atol)


def eig(m):
    """Eigenvalues (sorted) and eigenvectors (as columns) of a matrix.

    Hermitian matrices use ``numpy.linalg.eigh`` (real eigenvalues),
    other matrices use ``numpy.linalg.eig``.
    """
    a = to_array(m)
    if is_hermitian(a):
        w, v = np.linalg.eigh(a)
        return w, v
    w, v = np.linalg.eig(a)
    order = np.argsort(w)
    return w[order], v[:, order]


def eigenvectors(m):
    """Eigenvectors as a list of 1D arrays (same order as ``eig``)."""
    _, v = eig(m)
    return [v[:, i] for i in range(v.shape[1])]


def commutator(a, b):
    """[A, B] = AB - BA"""
    a, b = to_array(a), to_array(b)
    return a @ b - b @ a


def anticommutator(a, b):
    """{A, B} = AB + BA"""
    a, b = to_array(a), to_array(b)
    return a @ b + b @ a


def expm(m):
    """Matrix exponential e^M."""
    return scipy.linalg.expm(to_array(m))


def trace(m):
    return complex(np.trace(to_array(m)))
