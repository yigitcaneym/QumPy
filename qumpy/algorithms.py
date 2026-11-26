"""Ready-made circuits for the algorithms of the course.

    qft(n), inverse_qft(n)              Quantum Fourier Transform
    bell_circuit(), ghz_circuit(n)      entangled states
    teleportation(psi)                  quantum teleportation
    deutsch_jozsa(n, kind=...)          constant or balanced?
    bernstein_vazirani("1011")          find the secret string
    grover("101")                       search for marked bitstrings
    phase_estimation(U, n, eigenstate)  QPE

Each function returns a ``Circuit``: you can ``.draw()``, ``.run()`` or
modify it before running.
"""

from __future__ import annotations

import math

import numpy as np
from qiskit import QuantumCircuit

from .circuit import Circuit
from .config import Qum
from .errors import QumError
from .results import Counts

# ----------------------------------------------------------------- QFT


def _qft_rotations(qc, n):
    """The recursive construction from the course notebook (no swaps)."""
    if n == 0:
        return
    n -= 1
    qc.h(n)
    for qubit in range(n):
        qc.cp(math.pi / 2 ** (n - qubit), qubit, n)
    _qft_rotations(qc, n)


def qft(n, swaps=True, inverse=False):
    """Quantum Fourier Transform on ``n`` qubits, as a Circuit.

    |j>  ->  1/sqrt(2^n) sum_k e^{2 pi i j k / 2^n} |k>
    """
    c = Circuit(n, name="QFT†" if inverse else "QFT")
    _qft_rotations(c.qc, n)
    if swaps:
        for q in range(n // 2):
            c.qc.swap(q, n - q - 1)
    if inverse:
        c = c.inverse()
        c.qc.name = "QFT†"
    return c


def inverse_qft(n, swaps=True):
    """Inverse QFT on ``n`` qubits."""
    return qft(n, swaps=swaps, inverse=True)


# ------------------------------------------------------- entangled states


def bell_circuit(which="phi+", measure=False):
    """Circuit preparing a Bell state ('phi+', 'phi-', 'psi+', 'psi-')."""
    which = which.lower()
    if which not in ("phi+", "phi-", "psi+", "psi-"):
        raise QumError(f"Unknown Bell state '{which}'.", hint="Choose 'phi+', 'phi-', 'psi+' or 'psi-'.")
    c = Circuit(2, name=f"Bell {which}")
    if which.startswith("psi"):
        c.x(1)
    if which.endswith("-"):
        c.x(0)
    c.h(0).cx(0, 1)
    return c.measure() if measure else c


def ghz_circuit(n=3, measure=False):
    """Circuit preparing (|0...0> + |1...1>)/sqrt(2)."""
    c = Circuit(n, name="GHZ")
    c.h(0)
    for q in range(n - 1):
        c.cx(q, q + 1)
    return c.measure() if measure else c


# ------------------------------------------------------------ teleportation


def teleportation(psi=None, seed=None):
    """Teleport the 1-qubit state ``psi`` from qubit "psi" to qubit "bob".

    Registers: psi (qubit 0), alice (qubit 1), bob (qubit 2);
    classical bits crz, crx. If ``psi`` is None a random state is used.
    The input state is stored as ``circuit.input_state``.
    """
    from .states import ket, random_state

    psi = random_state(1, seed=seed) if psi is None else ket(psi)
    if psi.num_qubits != 1:
        raise QumError("Teleportation sends a single qubit; give a 1-qubit state.")
    c = Circuit(psi=1, alice=1, bob=1, bits={"crz": 1, "crx": 1}, name="teleport")
    c.init(psi, "psi")
    c.barrier()
    c.h("alice").cx("alice", "bob")          # shared Bell pair
    c.barrier()
    c.cx("psi", "alice").h("psi")            # Alice's Bell measurement
    c.barrier()
    c.measure("psi", "crz").measure("alice", "crx")
    with c.if_bit("crx", 1):
        c.x("bob")
    with c.if_bit("crz", 1):
        c.z("bob")
    c.input_state = psi
    return c


# ---------------------------------------------------------- Deutsch-Jozsa


def dj_oracle(n, kind="balanced", value=0, a=None, seed=None):
    """Oracle for Deutsch-Jozsa on n input qubits + 1 output qubit (qubit n).

    kind="constant": f(x) = value (0 or 1)
    kind="balanced": f(x) = a . x (mod 2) for a hidden non-zero integer ``a``
    """
    c = Circuit(n + 1, name="oracle")
    kind = kind.lower()
    if kind == "constant":
        if value not in (0, 1):
            raise QumError("A constant oracle returns 0 or 1.")
        if value == 1:
            c.x(n)
    elif kind == "balanced":
        if a is None:
            rng = np.random.default_rng(Qum.seed if seed is None else seed)
            a = int(rng.integers(1, 2**n))
        if not 0 < a < 2**n:
            raise QumError(f"The hidden parameter a must be between 1 and {2**n - 1}.")
        for i in range(n):
            if a & (1 << i):
                c.cx(i, n)
        c.hidden = a
    else:
        raise QumError(f"Unknown oracle kind '{kind}'.", hint="Use 'constant' or 'balanced'.")
    c.kind = kind
    return c


def deutsch_jozsa(n=3, kind="balanced", oracle=None, value=0, a=None, seed=None):
    """Full Deutsch-Jozsa circuit (with measurement).

    Give your own ``oracle`` (a Circuit on n+1 qubits) or let QumPy make one.
    Run it once: all zeros -> constant, anything else -> balanced
    (``dj_answer(counts)`` tells you).
    """
    if oracle is None:
        oracle = dj_oracle(n, kind=kind, value=value, a=a, seed=seed)
    if oracle.num_qubits != n + 1:
        raise QumError(f"The oracle must act on n+1 = {n + 1} qubits.")
    c = Circuit(n + 1, bits=n, name="Deutsch-Jozsa")
    c.h(range(n)).x(n).h(n).barrier()
    c.add(oracle)
    c.barrier().h(range(n)).barrier()
    c.measure(range(n))
    c.oracle = oracle
    return c


def dj_answer(counts):
    """'constant' if the result is all zeros, otherwise 'balanced'."""
    outcome = Counts(counts).most_likely() if not isinstance(counts, str) else counts
    return "constant" if set(outcome.replace(" ", "")) == {"0"} else "balanced"


# ----------------------------------------------------- Bernstein-Vazirani


def bernstein_vazirani(secret):
    """Circuit that reveals the secret bitstring ``secret`` in ONE query.

    Measuring gives ``secret`` back (Qiskit bit order: rightmost = qubit 0).
    """
    if not secret or set(secret) - {"0", "1"}:
        raise QumError("The secret must be a string of 0s and 1s, e.g. '1011'.")
    n = len(secret)
    c = Circuit(n + 1, bits=n, name="Bernstein-Vazirani")
    c.h(range(n)).x(n).h(n).barrier()
    for i, bit in enumerate(reversed(secret)):
        if bit == "1":
            c.cx(i, n)
    c.barrier().h(range(n)).measure(range(n))
    return c


# --------------------------------------------------------------- Grover


def _mcz(qc, qubits):
    *controls, target = qubits
    qc.h(target)
    qc.mcx(controls, target)
    qc.h(target)


def grover_oracle(marked, n=None):
    """Phase oracle: flips the sign of each marked bitstring."""
    marked = [marked] if isinstance(marked, str) else list(marked)
    n = n or len(marked[0])
    for m in marked:
        if len(m) != n or set(m) - {"0", "1"}:
            raise QumError(f"Marked item '{m}' must be a {n}-bit string of 0s and 1s.")
    c = Circuit(n, name="oracle")
    for m in marked:
        zeros = [i for i, b in enumerate(reversed(m)) if b == "0"]
        if zeros:
            c.x(zeros)
        _mcz(c.qc, list(range(n)))
        if zeros:
            c.x(zeros)
    return c


def diffuser(n):
    """Grover's 'inversion about the average' on n qubits."""
    c = Circuit(n, name="diffuser")
    c.h(range(n)).x(range(n))
    _mcz(c.qc, list(range(n)))
    c.x(range(n)).h(range(n))
    return c


def grover_iterations(n, num_marked=1):
    """Best number of Grover iterations: floor(pi/4 * sqrt(N/M))."""
    return max(1, int(math.floor(math.pi / 4 * math.sqrt(2**n / num_marked))))


def _literal_true_flips(qc, clause):
    """X on the qubits of negative literals, so that qubit = 1 <=> literal true."""
    for lit in clause:
        if lit < 0:
            qc.x(-lit - 1)


def _clause_check(qc, clause, target, exactly_one):
    """Flip ``target`` iff the clause is satisfied (reversible, no garbage)."""
    qubits = [abs(lit) - 1 for lit in clause]
    if exactly_one:
        # exactly one literal true  <=>  odd number true AND not all three true
        _literal_true_flips(qc, clause)
        for q in qubits:
            qc.cx(q, target)
        if len(qubits) == 3:
            qc.mcx(qubits, target)
        _literal_true_flips(qc, clause)
    else:
        # at least one literal true  <=>  NOT (all literals false)
        positives = [abs(lit) - 1 for lit in clause if lit > 0]
        if positives:
            qc.x(positives)              # now qubit = 1 <=> literal false
        qc.mcx(qubits, target)
        qc.x(target)
        if positives:
            qc.x(positives)


def sat_oracle(formula, exactly_one=True):
    """Bit-flip oracle for a SAT formula in conjunctive normal form.

    ``formula`` is a list of clauses; each clause is a list of literals:
    ``3`` means variable x3, ``-3`` means NOT x3 (as in the course's Grover
    notebook). ``exactly_one=True`` gives the course's exactly-1 3-SAT (every
    clause must have exactly one true literal); ``False`` gives ordinary SAT.

    Registers: ``fin`` (one qubit per variable, x1 = qubit 0), ``fout`` (the
    output qubit, flipped when the formula is satisfied), ``aux`` (one per
    clause, returned to |0>). ``oracle.solutions`` lists the satisfying
    assignments as bitstrings (Qiskit order: x1 is the rightmost bit).
    """
    if not formula or not all(clause for clause in formula):
        raise QumError("The formula needs at least one non-empty clause.",
                       hint="Example: [[1, 2, -3], [-1, -2, -3], [-1, 2, 3]]")
    for clause in formula:
        if any(not isinstance(lit, (int, np.integer)) or lit == 0 for lit in clause):
            raise QumError(f"Literals must be non-zero integers, got clause {clause}.")
        if len({abs(lit) for lit in clause}) != len(clause):
            raise QumError(f"Clause {clause} uses the same variable twice.")
        if exactly_one and len(clause) > 3:
            raise QumError(f"Exactly-one clauses may have at most 3 literals, got {clause}.")
    n = max(abs(lit) for clause in formula for lit in clause)
    m = len(formula)
    c = Circuit(fin=n, fout=1, aux=m, name="SAT oracle")
    qc = c.qc
    aux = list(range(n + 1, n + 1 + m))
    for clause, target in zip(formula, aux):
        _clause_check(qc, clause, target, exactly_one)
    qc.mcx(aux, n)                               # all clauses satisfied -> flip fout
    for clause, target in reversed(list(zip(formula, aux))):
        _clause_check(qc, clause, target, exactly_one)   # uncompute aux

    def satisfied(bits):
        for clause in formula:
            truth = [bits[abs(lit) - 1] == (lit > 0) for lit in clause]
            if (sum(truth) != 1) if exactly_one else (not any(truth)):
                return False
        return True

    c.solutions = [format(k, f"0{n}b") for k in range(2**n)
                   if satisfied([(k >> i) & 1 == 1 for i in range(n)])]
    c.num_inputs = n
    return c


def grover(marked=None, iterations=None, measure=True, oracle=None, n=None, num_solutions=None):
    """Grover search.

    * ``grover("101")`` or ``grover(["0110", "1001"])``: search for these
      bitstrings (QumPy builds the oracle).
    * ``grover(oracle=my_oracle, n=3)``: use your own oracle on the first ``n``
      qubits. If the oracle has exactly ``n`` qubits it must be a *phase* oracle
      (it flips the sign of the solutions). If it has more, qubit ``n`` is taken
      as the *output* qubit of a bit-flip oracle (prepared in |->, as in the
      course) and the remaining qubits are ancillas that the oracle must
      return to |0>.
    * ``grover(oracle=qp.sat_oracle(formula))``: the course's 3-SAT example.

    ``iterations`` defaults to the optimal number for ``num_solutions``
    solutions (taken from ``oracle.solutions`` when it exists, else 1).
    """
    if (marked is None) == (oracle is None):
        raise QumError("Give either the marked bitstrings or an oracle (not both).",
                       hint="grover('101')  or  grover(oracle=my_oracle, n=3)")

    if marked is not None:
        marked = [marked] if isinstance(marked, str) else list(marked)
        n = len(marked[0])
        if n < 2:
            raise QumError("Grover search needs at least 2 qubits.")
        oracle = grover_oracle(marked, n)
        num_solutions = len(marked) if num_solutions is None else num_solutions
    else:
        if isinstance(oracle, QuantumCircuit):
            oracle = Circuit.from_qiskit(oracle)
        if not isinstance(oracle, Circuit):
            raise QumError("The oracle must be a Circuit or a QuantumCircuit.")
        n = getattr(oracle, "num_inputs", None) if n is None else n
        if n is None:
            raise QumError("Tell grover() how many qubits are searched.",
                           hint="grover(oracle=my_oracle, n=3)")
        if not 2 <= n <= oracle.num_qubits:
            raise QumError(f"n must be between 2 and the oracle's {oracle.num_qubits} qubits, got {n}.")
        if num_solutions is None:
            num_solutions = len(getattr(oracle, "solutions", [None])) or 1

    iterations = grover_iterations(n, num_solutions) if iterations is None else iterations
    total = oracle.num_qubits
    c = Circuit(total, bits=n if measure else None, name="Grover")
    c.h(range(n))
    if total > n:                                   # bit-flip oracle: output qubit in |->
        c.x(n).h(n)
    diff = diffuser(n)
    for _ in range(iterations):
        c.barrier()
        c.add(oracle)
        c.add(diff, qubits=range(n))
    c.iterations = iterations
    c.oracle = oracle
    if measure:
        c.barrier()
        c.measure(range(n))
    return c


# ---------------------------------------------------- Phase estimation


def phase_estimation(unitary, n_counting=3, eigenstate=None):
    """Quantum Phase Estimation of ``unitary`` (matrix / Operator / gate / Circuit).

    If U|u> = e^{2 pi i phi}|u>, measuring the counting register gives
    phi * 2^n_counting. Use ``estimated_phase(counts)`` to read phi.
    """
    from qiskit.circuit.library import UnitaryGate

    from .gates import operator

    U = operator(unitary).data
    m = int(round(math.log2(U.shape[0])))
    c = Circuit(counting=n_counting, target=m, bits={"c": n_counting}, name="QPE")
    if eigenstate is not None:
        if isinstance(eigenstate, Circuit):
            c.add(eigenstate, qubits="target")
        else:
            c.init(eigenstate, "target")
    c.h("counting")
    target = [n_counting + i for i in range(m)]
    power = U.copy()                       # U^(2^k), squared at every step
    for k in range(n_counting):            # counting qubit k controls U^(2^k)
        gate = UnitaryGate(power, label=f"U^{2**k}").control(1)
        c.qc.append(gate, [k, *target])
        power = power @ power
    c.barrier()
    c.add(inverse_qft(n_counting), qubits="counting")
    c.barrier()
    c.measure("counting", "c")
    c.n_counting = n_counting
    return c


def estimated_phase(counts, n_counting=None):
    """phi estimated from QPE counts (most likely outcome / 2^n)."""
    best = Counts(counts).most_likely().replace(" ", "")
    n = n_counting or len(best)
    return int(best, 2) / 2**n
