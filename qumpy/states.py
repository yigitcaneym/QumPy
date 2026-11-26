"""Making quantum states the easy way.

Examples::

    ket("0")            |0>
    ket("01")           |01>   (qubit 1 = '0', qubit 0 = '1' -- Qiskit order)
    ket("+")            (|0> + |1>)/sqrt(2)      also "-", "r" (= |+i>), "l" (= |-i>)
    ket([1, 1])         normalised automatically -> (|0> + |1>)/sqrt(2)
    ket(3, n=2)         basis state number 3 on 2 qubits = |11>
    bell("phi+")        Bell states: "phi+", "phi-", "psi+", "psi-"
    ghz(3)              (|000> + |111>)/sqrt(2)
    random_state(1)     random 1-qubit state

Every function returns a Qiskit ``Statevector``, so everything you learned in
class (``.evolve``, ``.probabilities()``, ``.expectation_value``...) still works.
"""

from __future__ import annotations

import numpy as np
from qiskit import quantum_info as qi

from .config import Qum
from .errors import QumError

_LABEL_CHARS = set("01+-rl")


def ket(state, n=None, normalize=True):
    """Build a state vector |state>.

    Parameters
    ----------
    state : str | int | list | np.ndarray | Statevector
        * ``"0"``, ``"1"``, ``"+"``, ``"-"``, ``"r"``, ``"l"`` or a string of
          them, e.g. ``"01+"``. ``"|01>"`` is accepted too.
        * an integer k together with ``n`` (number of qubits): basis state |k>.
        * a list / array of amplitudes, e.g. ``[1, 1j]``.
    n : int, optional
        Number of qubits (only needed when ``state`` is an integer).
    normalize : bool
        Divide a list of amplitudes by its norm (default True).
    """
    if isinstance(state, qi.Statevector):
        return state
    if isinstance(state, qi.DensityMatrix):
        raise QumError("A density matrix is not a ket.",
                       hint="Use qp.density_matrix(...) for mixed states.")

    if isinstance(state, str):
        label = state.replace("|", "").replace(">", "").replace("⟩", "").replace(" ", "")
        bad = set(label) - _LABEL_CHARS
        if not label or bad:
            raise QumError(f"Cannot read the state label '{state}'.",
                           hint="Use only the characters 0 1 + - r l, e.g. ket('01') or ket('+').")
        return qi.Statevector.from_label(label)

    if isinstance(state, (int, np.integer)) and not isinstance(state, bool):
        if n is None:
            n = max(1, int(state).bit_length())
        if state < 0 or state >= 2**n:
            raise QumError(f"Basis state {state} does not exist for {n} qubit(s).",
                           hint=f"With n={n} qubits the allowed numbers are 0 ... {2**n - 1}.")
        return qi.Statevector.from_int(int(state), dims=2**n)

    vec = np.asarray(state, dtype=complex).flatten()
    if vec.size == 0:
        raise QumError("The state vector is empty.")
    norm = np.linalg.norm(vec)
    if np.isclose(norm, 0):
        raise QumError("The zero vector is not a valid quantum state.")
    if normalize:
        vec = vec / norm
    return qi.Statevector(vec)


def bra(state):
    """The bra <state| as a numpy row vector (conjugate transpose of the ket)."""
    return np.conj(ket(state).data).reshape(1, -1)


def basis(k, n=1):
    """Computational basis state |k> on ``n`` qubits."""
    return ket(int(k), n=n)


def zero(n=1):
    """|00...0> on ``n`` qubits."""
    return ket(0, n=n)


def plus(n=1):
    """|++...+> -- the uniform superposition over all 2**n basis states."""
    return ket("+" * n)


def bell(which="phi+"):
    """One of the four Bell states.

    "phi+" = (|00> + |11>)/sqrt2     "phi-" = (|00> - |11>)/sqrt2
    "psi+" = (|01> + |10>)/sqrt2     "psi-" = (|01> - |10>)/sqrt2
    """
    s = 1 / np.sqrt(2)
    table = {
        "phi+": [s, 0, 0, s],
        "phi-": [s, 0, 0, -s],
        "psi+": [0, s, s, 0],
        "psi-": [0, s, -s, 0],
    }
    key = which.lower().replace("ϕ", "phi").replace("ψ", "psi").replace(" ", "")
    if key not in table:
        raise QumError(f"Unknown Bell state '{which}'.", hint="Choose 'phi+', 'phi-', 'psi+' or 'psi-'.")
    return qi.Statevector(np.array(table[key], dtype=complex))


def ghz(n=3):
    """GHZ state (|00...0> + |11...1>)/sqrt(2) on ``n`` qubits."""
    v = np.zeros(2**n, dtype=complex)
    v[0] = v[-1] = 1 / np.sqrt(2)
    return qi.Statevector(v)


def random_state(n=1, seed=None):
    """A random (Haar distributed) ``n``-qubit pure state."""
    seed = Qum.seed if seed is None else seed
    return qi.random_statevector(2**n, seed=seed)


def num_qubits(state):
    """Number of qubits of a state / operator."""
    obj = ket(state) if not hasattr(state, "num_qubits") else state
    return obj.num_qubits
