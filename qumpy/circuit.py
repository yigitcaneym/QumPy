"""``Circuit``: a beginner friendly wrapper around Qiskit's ``QuantumCircuit``.

    c = Circuit(2)            # 2 qubits, classical bits are added when needed
    c.h(0).cx(0, 1)           # gates can be chained
    c.draw()                  # picture of the circuit
    c.state()                 # final state vector (no shots, exact)
    c.unitary()               # matrix of the whole circuit
    c.measure()               # measure every qubit
    c.run()                   # Qum.shots repetitions -> Counts
    c.run().plot()            # histogram

Named registers (e.g. for teleportation):

    c = Circuit(psi=1, alice=1, bob=1, bits={"crz": 1, "crx": 1})
    c.h("alice").cx("alice", "bob")
    c.measure("psi", "crz")
    with c.if_bit("crx", 1):
        c.x("bob")

Every Qiskit gate method works (``c.ry(theta, 0)``, ``c.mcx([0, 1], 2)``...),
and ``c.qc`` is the plain ``QuantumCircuit`` if you ever need it.
"""

from __future__ import annotations

import contextlib
import difflib
import warnings

import numpy as np
from qiskit import ClassicalRegister, QuantumCircuit, QuantumRegister, transpile
from qiskit import quantum_info as qi
from qiskit.circuit import CircuitInstruction, Clbit, InstructionSet, Qubit
from qiskit.circuit.exceptions import CircuitError
from qiskit.circuit.library import Initialize, UnitaryGate

from .config import Qum
from .errors import QumError
from .results import Counts

_ALIASES = {
    "hadamard": "h",
    "cnot": "cx",
    "toffoli": "ccx",
    "fredkin": "cswap",
    "phase": "p",
    "cphase": "cp",
    "identity": "id",
    "i": "id",
    "not_": "x",
}

_NON_UNITARY = {"measure", "reset", "if_else", "while_loop", "for_loop", "switch_case", "initialize"}


class Circuit:
    """A quantum circuit.

    Parameters
    ----------
    qubits : int
        Number of qubits (named ``q``). Leave it out if you use named registers.
    bits : int or dict, optional
        Classical bits. An int creates a register ``c``; a dict such as
        ``{"crz": 1, "crx": 1}`` creates named registers. If omitted, bits are
        created automatically by ``measure()``.
    name : str, optional
        Name shown in drawings.
    **named_qubits
        Named quantum registers, e.g. ``Circuit(alice=1, bob=1)``.
    """

    def __init__(self, qubits=None, bits=None, name=None, **named_qubits):
        regs = []
        if qubits is not None:
            if isinstance(qubits, QuantumCircuit):
                raise QumError("Use Circuit.from_qiskit(qc) to wrap an existing QuantumCircuit.")
            if not isinstance(qubits, (int, np.integer)) or qubits < 1:
                raise QumError(f"Number of qubits must be a positive integer, got {qubits!r}.")
            regs.append(QuantumRegister(int(qubits), "q"))
        for reg_name, size in named_qubits.items():
            regs.append(QuantumRegister(int(size), reg_name))
        if not regs:
            raise QumError("A circuit needs at least one qubit.",
                           hint="Circuit(2) or Circuit(alice=1, bob=1)")
        if bits is not None:
            if isinstance(bits, dict):
                regs += [ClassicalRegister(int(s), n) for n, s in bits.items()]
            elif bits > 0:
                regs.append(ClassicalRegister(int(bits), "c"))
        self.qc = QuantumCircuit(*regs, name=name)

    # ------------------------------------------------------------ construction
    @classmethod
    def from_qiskit(cls, qc):
        """Wrap an existing Qiskit ``QuantumCircuit`` (no copy is made)."""
        if isinstance(qc, Circuit):
            return qc
        obj = cls.__new__(cls)
        obj.qc = qc
        return obj

    @classmethod
    def from_qasm(cls, text):
        """Build a circuit from an OpenQASM 2 string."""
        return cls.from_qiskit(QuantumCircuit.from_qasm_str(text))

    def copy(self):
        return Circuit.from_qiskit(self.qc.copy())

    # ---------------------------------------------------------------- basics
    @property
    def num_qubits(self):
        return self.qc.num_qubits

    @property
    def num_bits(self):
        return self.qc.num_clbits

    @property
    def registers(self):
        """All registers by name."""
        return {r.name: r for r in (*self.qc.qregs, *self.qc.cregs)}

    def __len__(self):
        return len(self.qc.data)

    def __repr__(self):
        return str(self.qc.draw("text"))

    # -------------------------------------------------------- name resolution
    def _resolve(self, arg):
        if isinstance(arg, str):
            if arg == "all":
                return list(self.qc.qubits)
            regs = self.registers
            if arg in regs:
                return regs[arg]
            raise QumError(f"There is no register called '{arg}'.",
                           hint=f"Registers in this circuit: {', '.join(regs)}")
        if isinstance(arg, range):
            return list(arg)
        if isinstance(arg, (list, tuple)) and any(isinstance(a, str) for a in arg):
            out = []
            for a in arg:
                r = self._resolve(a)
                out.extend(r if isinstance(r, (list, QuantumRegister, ClassicalRegister)) else [r])
            return out
        return arg

    def _qubit_indices(self, spec):
        """Turn any qubit spec (int, list, register, name) into a list of ints."""
        spec = self._resolve(spec)
        if isinstance(spec, (int, np.integer)):
            spec = [spec]
        elif isinstance(spec, (Qubit, Clbit)):
            spec = [spec]
        out = []
        for s in spec:
            if isinstance(s, (int, np.integer)):
                if not 0 <= s < self.num_qubits:
                    raise self._index_error(s)
                out.append(int(s))
            else:
                out.append(self.qc.find_bit(s).index)
        return out

    def _index_error(self, idx):
        return QumError(f"Qubit {idx} does not exist.",
                        hint=f"This circuit has {self.num_qubits} qubit(s): 0 ... {self.num_qubits - 1}.")

    # ------------------------------------------------- forwarding Qiskit gates
    def __getattr__(self, name):
        if name == "qc" or name.startswith("__"):
            raise AttributeError(name)
        real = _ALIASES.get(name, name)
        try:
            attr = getattr(self.qc, real)
        except AttributeError:
            options = [m for m in dir(QuantumCircuit) if not m.startswith("_")] + list(_ALIASES)
            close = difflib.get_close_matches(name, options, n=3)
            raise QumError(f"Circuit has no gate or method called '{name}'.",
                           hint=f"Did you mean: {', '.join(close)}?" if close else
                           "See qp.cheatsheet('gates') for the list of gates.") from None
        if not callable(attr):
            return attr

        def method(*args, **kwargs):
            args = [self._resolve(a) for a in args]
            try:
                out = attr(*args, **kwargs)
            except (CircuitError, IndexError) as e:
                msg = str(e).strip("'\"")
                if "out of range" in msg or "index" in msg.lower():
                    raise QumError(f"{real}(): {msg}",
                                   hint=f"This circuit has {self.num_qubits} qubit(s) (0 ... "
                                        f"{self.num_qubits - 1}) and {self.num_bits} bit(s).") from e
                raise QumError(f"{real}(): {msg}") from e
            if out is None or isinstance(out, (InstructionSet, CircuitInstruction)) or out is self.qc:
                return self
            if isinstance(out, QuantumCircuit):
                return Circuit.from_qiskit(out)
            return out

        method.__name__ = real
        method.__doc__ = getattr(attr, "__doc__", None)
        return method

    def __dir__(self):
        return sorted(set(super().__dir__()) | {m for m in dir(QuantumCircuit) if not m.startswith("_")}
                      | set(_ALIASES))

    # ------------------------------------------------------------ extra gates
    def init(self, state, qubits=None, label="init"):
        """Prepare qubits in a given state (anything ``qp.ket`` accepts).

        ``c.init("1+")`` or ``c.init([1, 1j], qubits=0)``.
        """
        from .states import ket

        sv = ket(state)
        n = sv.num_qubits
        targets = list(range(n)) if qubits is None else self._qubit_indices(qubits)
        if len(targets) != n:
            raise QumError(f"The state has {n} qubit(s) but you gave {len(targets)} target qubit(s).")
        gate = Initialize(sv)
        gate.label = label
        self.qc.append(gate, targets)
        return self

    def gate(self, matrix, qubits, label=None):
        """Add any unitary matrix (numpy array / Operator / Circuit) as a gate."""
        from .gates import operator

        op = operator(matrix)
        targets = self._qubit_indices(qubits)
        if 2 ** len(targets) != op.dim[0]:
            raise QumError(f"A {op.dim[0]}x{op.dim[0]} matrix acts on {op.num_qubits} qubit(s), "
                           f"but you gave {len(targets)} qubit(s).")
        self.qc.append(UnitaryGate(op, label=label), targets)
        return self

    def add(self, other, qubits=None, bits=None):
        """Append another Circuit / QuantumCircuit / gate onto (some of) these qubits."""
        if isinstance(other, Circuit):
            other = other.qc
        if isinstance(other, QuantumCircuit):
            q = list(range(other.num_qubits)) if qubits is None else self._qubit_indices(qubits)
            if bits is None and other.num_clbits:
                bits = list(range(other.num_clbits))
                self._ensure_bits(other.num_clbits)
            self.qc.compose(other, qubits=q, clbits=bits, inplace=True)
            return self
        q = list(range(other.num_qubits)) if qubits is None else self._qubit_indices(qubits)
        self.qc.append(other, q)
        return self

    def __add__(self, other):
        out = self.copy()
        return out.add(other)

    def then(self, other):
        """``a.then(b)``: new circuit = a followed by b."""
        return self + other

    def h_all(self):
        """Hadamard on every qubit."""
        self.qc.h(range(self.num_qubits))
        return self

    def x_all(self):
        self.qc.x(range(self.num_qubits))
        return self

    # ------------------------------------------------------------ measurement
    def _ensure_bits(self, needed):
        if self.num_bits < needed:
            if self.num_bits == 0:
                self.qc.add_register(ClassicalRegister(self.num_qubits if needed <= self.num_qubits
                                                       else needed, "c"))
            else:
                raise QumError(
                    f"This measurement needs classical bit {needed - 1}, but the circuit has only "
                    f"{self.num_bits} bit(s).",
                    hint="Pass the bits explicitly: c.measure(qubits, bits=...)")

    def measure(self, qubits=None, bits=None):
        """Measure qubits into classical bits.

        * ``c.measure()``          every qubit i -> bit i
        * ``c.measure([0, 2])``    qubit 0 -> bit 0, qubit 2 -> bit 2
        * ``c.measure(2, 0)``      qubit 2 -> bit 0
        * ``c.measure("psi", "crz")`` named registers
        Classical bits are created automatically when there are none.
        """
        q = self._qubit_indices("all" if qubits is None else qubits)
        if bits is None:
            self._ensure_bits(max(q) + 1)
            b = q
        else:
            b = self._resolve(bits)
            if isinstance(b, (int, np.integer)):
                b = [b]
            if isinstance(b, (list, tuple)) and b and all(isinstance(x, (int, np.integer)) for x in b):
                self._ensure_bits(max(b) + 1)
            n_b = len(b) if not isinstance(b, Clbit) else 1
            if n_b != len(q):
                raise QumError(f"You measure {len(q)} qubit(s) into {n_b} bit(s); they must match.")
        self.qc.measure(q, b)
        return self

    @contextlib.contextmanager
    def if_bit(self, bits, value=1):
        """Classical control: ``with c.if_bit("crx", 1): c.x("bob")``."""
        target = self._resolve(bits)
        if isinstance(target, (int, np.integer)):
            target = self.qc.clbits[target]
        with self.qc.if_test((target, value)):
            yield self

    def has_measurements(self):
        return any(inst.operation.name == "measure" for inst in self.qc.data)

    # ------------------------------------------------------------- simulation
    def _clean_for_unitary(self):
        qc = self.qc.remove_final_measurements(inplace=False)
        bad = {inst.operation.name for inst in qc.data} & _NON_UNITARY
        if bad:
            raise QumError(
                f"This circuit contains {', '.join(sorted(bad))}, so it has no single unitary matrix.",
                hint="Remove init()/measure()/if_bit() or use .state() instead.")
        return qc

    def unitary(self):
        """The matrix U of the whole circuit (as a Qiskit ``Operator``)."""
        return qi.Operator.from_circuit(self._clean_for_unitary())

    def state(self, seed=None):
        """Final state vector after the circuit (exact, no shots).

        Mid-circuit measurements are simulated once (the state collapses
        randomly, exactly like the course's ``statevector_simulator``).
        """
        from qiskit_aer import AerSimulator

        if "statevector" not in _BACKEND_CACHE:
            _BACKEND_CACHE["statevector"] = AerSimulator(method="statevector")
        backend = _BACKEND_CACHE["statevector"]
        seed = Qum.seed if seed is None else seed
        qc = self.qc.copy()
        qc.save_statevector()
        qc = transpile(qc, backend, **({} if seed is None else {"seed_transpiler": seed}))
        opts = {} if seed is None else {"seed_simulator": seed}
        return qi.Statevector(backend.run(qc, shots=1, **opts).result().get_statevector())

    def probabilities(self, decimals=None):
        """Exact outcome probabilities, e.g. ``{'00': 0.5, '11': 0.5}``."""
        d = Qum.precision if decimals is None else decimals
        probs = self.state().probabilities_dict(decimals=d)
        return {k: v for k, v in probs.items() if v > 0}

    def density_matrix(self):
        return qi.DensityMatrix(self.state())

    def bloch(self, title="", **kwargs):
        """Bloch sphere of every qubit of the final state."""
        from .display import bloch

        return bloch(self.state(), title=title, **kwargs)

    def show_state(self, style="vector", **kwargs):
        """Display the final state (``style="ket"`` for Dirac notation)."""
        from .display import show

        return show(self.state(), style=style, **kwargs)

    def show_unitary(self, **kwargs):
        """Display the matrix of the circuit."""
        from .display import show

        return show(self.unitary(), **kwargs)

    def run(self, shots=None, backend=None, seed=None):
        """Run the circuit ``shots`` times and count the results.

        shots   : default ``Qum.shots``
        backend : ``"ideal"`` (default ``Qum.backend``), ``"noisy"`` (fake IBM
                  device ``Qum.device``) or any Qiskit backend object.
        """
        shots = Qum.shots if shots is None else shots
        Qum._validate("shots", shots)
        seed = Qum.seed if seed is None else seed
        qc = self.qc
        if not self.has_measurements():
            if not Qum.auto_measure:
                raise QumError("The circuit has no measurement, so there is nothing to count.",
                               hint="Call c.measure() first (or set Qum.auto_measure = True).")
            warnings.warn("No measurement found: measuring all qubits automatically.", stacklevel=2)
            qc = qc.copy()
            qc.measure_all(add_bits=True)

        be, label = _get_backend(backend, self.num_qubits)
        tkw = {} if seed is None else {"seed_transpiler": seed}
        rkw = {} if seed is None else {"seed_simulator": seed}
        compiled = transpile(qc, be, **tkw)
        counts = be.run(compiled, shots=shots, **rkw).result().get_counts()
        return Counts(counts, shots=shots, backend=label)

    # ------------------------------------------------------------ inspection
    def draw(self, style=None, initial_state=True, scale=None, **kwargs):
        """Draw the circuit. style: 'mpl' (default ``Qum.draw``), 'text' or 'latex'."""
        style = style or Qum.draw
        if scale is not None:
            kwargs["scale"] = scale
        try:
            return self.qc.draw(style, initial_state=initial_state, **kwargs)
        except Exception as e:  # missing pylatexenc / latex
            if style == "text":
                raise
            warnings.warn(f"Could not draw with '{style}' ({e}); falling back to text.", stacklevel=2)
            return self.qc.draw("text", initial_state=initial_state)

    def stats(self, show=True):
        """Depth, number of gates, number of 2+ qubit gates, gate counts."""
        info = {
            "qubits": self.num_qubits,
            "bits": self.num_bits,
            "depth": self.qc.depth(),
            "gates": len(self.qc.data),
            "nonlocal gates": self.qc.num_nonlocal_gates(),
            "ops": dict(self.qc.count_ops()),
        }
        if show:
            for k, v in info.items():
                print(f"{k:>15}: {v}")
            return None
        return info

    def depth(self):
        return self.qc.depth()

    # ----------------------------------------------------------- transforms
    def inverse(self):
        return Circuit.from_qiskit(self.qc.inverse())

    def decompose(self, reps=1):
        return Circuit.from_qiskit(self.qc.decompose(reps=reps))

    def compile(self, basis=("rx", "rz", "cx"), optimization_level=1, backend=None):
        """Rewrite the circuit using only the gates in ``basis`` (or for a backend)."""
        from qiskit.transpiler import generate_preset_pass_manager

        if backend is not None:
            be, _ = _get_backend(backend, self.num_qubits)
            pm = generate_preset_pass_manager(optimization_level=optimization_level, backend=be)
        else:
            pm = generate_preset_pass_manager(optimization_level=optimization_level,
                                              basis_gates=list(basis))
        return Circuit.from_qiskit(pm.run(self.qc))

    def to_gate(self, label=None):
        """Turn this circuit into a reusable gate (no measurements allowed)."""
        g = self._clean_for_unitary().to_gate()
        if label:
            g.label = label
        return g

    def controlled(self, num_controls=1, label=None):
        """Controlled version of this circuit, as a gate."""
        return self.to_gate(label).control(num_controls)

    def qasm(self):
        """OpenQASM 2 text of the circuit."""
        from qiskit import qasm2

        return qasm2.dumps(self.qc)


# ---------------------------------------------------------------- backends
_BACKEND_CACHE = {}


def _get_backend(backend, num_qubits):
    backend = Qum.backend if backend is None else backend
    if not isinstance(backend, str):
        return backend, getattr(backend, "name", str(backend))
    key = backend.lower()
    if key in ("ideal", "qasm", "simulator", "aer"):
        from qiskit_aer import AerSimulator

        if "ideal" not in _BACKEND_CACHE:
            _BACKEND_CACHE["ideal"] = AerSimulator()
        return _BACKEND_CACHE["ideal"], "ideal"
    if key in ("noisy", "fake", "device"):
        return noisy_backend(Qum.device, num_qubits), f"noisy ({Qum.device})"
    raise QumError(f"Unknown backend '{backend}'.", hint="Use 'ideal' or 'noisy'.")


def noisy_backend(device=None, num_qubits=5):
    """A simulator that imitates a real IBM device (with noise).

    ``"manila"`` -> ``FakeManilaV2`` (5 qubits, used in the course);
    ``"generic"`` -> ``GenericBackendV2`` with ``num_qubits`` qubits.
    """
    device = (device or Qum.device).lower()
    if device == "manila":
        if num_qubits > 5:
            raise QumError(f"FakeManila has only 5 qubits, your circuit has {num_qubits}.",
                           hint="Set Qum.device = 'generic' for bigger noisy circuits.")
        try:
            from qiskit_ibm_runtime.fake_provider import FakeManilaV2
        except ImportError as e:
            raise QumError("The noisy backend needs qiskit-ibm-runtime.",
                           hint="pip install qiskit-ibm-runtime") from e
        if "manila" not in _BACKEND_CACHE:
            _BACKEND_CACHE["manila"] = FakeManilaV2()
        return _BACKEND_CACHE["manila"]
    if device == "generic":
        from qiskit.providers.fake_provider import GenericBackendV2

        key = ("generic", num_qubits, Qum.seed)
        if key not in _BACKEND_CACHE:
            _BACKEND_CACHE[key] = GenericBackendV2(num_qubits=max(num_qubits, 2), seed=Qum.seed)
        return _BACKEND_CACHE[key]
    raise QumError(f"Unknown device '{device}'.", hint="Use 'manila' or 'generic'.")


# ------------------------------------------------- functional shortcuts
def _wrap(c):
    if isinstance(c, Circuit):
        return c
    if isinstance(c, QuantumCircuit):
        return Circuit.from_qiskit(c)
    raise QumError(f"Expected a Circuit or QuantumCircuit, got {type(c).__name__}.")


def run(circuit, shots=None, backend=None, seed=None):
    """``qp.run(c)`` == ``c.run()``; also accepts a plain Qiskit QuantumCircuit."""
    return _wrap(circuit).run(shots=shots, backend=backend, seed=seed)


def state(circuit, seed=None):
    """Final state vector of a Circuit / QuantumCircuit."""
    return _wrap(circuit).state(seed=seed)


def unitary(circuit):
    """Unitary matrix of a Circuit / QuantumCircuit."""
    return _wrap(circuit).unitary()
