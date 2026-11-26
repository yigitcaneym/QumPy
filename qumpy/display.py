"""Showing things: LaTeX, Dirac notation, Bloch spheres, histograms.

Examples::

    show(x)        pretty matrix / vector (LaTeX in Jupyter, text elsewhere)
    dirac(state)   "0.7071|00⟩ + 0.7071|11⟩"
    bloch(state)   Bloch sphere of every qubit
    histogram(c)   bar chart of measurement counts
    qsphere(state) Q-sphere picture
    versions()     the version table (replaces tutorial_magics)
"""

from __future__ import annotations

import platform

import numpy as np
from qiskit import quantum_info as qi

from .config import Qum


def in_notebook():
    """True when running inside Jupyter."""
    try:
        from IPython import get_ipython

        ip = get_ipython()
        return ip is not None and "IPKernelApp" in ip.config
    except Exception:
        return False


def _fmt_complex(c, p):
    re, im = round(c.real, p), round(c.imag, p)
    if abs(im) < 10**-p:
        return f"{re:.{p}f}"
    if abs(re) < 10**-p:
        return f"{im:.{p}f}i"
    sign = "+" if im >= 0 else "-"
    return f"({re:.{p}f}{sign}{abs(im):.{p}f}i)"


def dirac(state, precision=None):
    """A state written in Dirac notation, e.g. ``0.7071|00⟩ + 0.7071|11⟩``."""
    from .states import ket

    sv = ket(state)
    p = Qum.precision if precision is None else precision
    n = sv.num_qubits
    terms = []
    for i, amp in enumerate(sv.data):
        if abs(amp) < 10 ** (-p) / 2:
            continue
        label = format(i, f"0{n}b") if n is not None else str(i)
        coef = _fmt_complex(complex(amp), p)
        if np.isclose(amp, 1):
            coef = ""
        elif np.isclose(amp, -1):
            coef = "-"
        terms.append(f"{coef}|{label}⟩")
    if not terms:
        return "0"
    out = terms[0]
    for t in terms[1:]:
        out += f" - {t[1:]}" if t.startswith("-") else f" + {t}"
    return out


def show(obj, precision=None, prefix=None, style="vector", max_size=16):
    """Display a state, operator, density matrix, counts or numpy array nicely.

    ``style="ket"`` writes a state in Dirac notation instead of a column vector.
    In Jupyter you get LaTeX; in a plain script it prints text.
    """
    from .circuit import Circuit
    from .results import Counts

    p = Qum.precision if precision is None else precision
    if isinstance(obj, Circuit):
        return obj.draw()
    if isinstance(obj, Counts):
        print(obj)
        return None

    if isinstance(obj, qi.Statevector) and style == "ket":
        text = dirac(obj, p)
        if in_notebook():
            from IPython.display import Math, display

            pre = prefix if prefix is not None else r"|\psi\rangle = "
            display(Math(pre + text.replace("⟩", r"\rangle")))
            return None
        print((prefix or "|ψ⟩ = ") + text)
        return None

    if hasattr(obj, "to_matrix") and not isinstance(obj, (qi.Operator, qi.DensityMatrix)):
        obj = obj.to_matrix()

    if in_notebook():
        from IPython.display import display
        from qiskit.visualization import array_to_latex

        pre = prefix
        if pre is None and isinstance(obj, qi.Statevector):
            pre = r"|\psi\rangle = "
        data = obj.data if hasattr(obj, "data") and not isinstance(obj, np.ndarray) else obj
        display(array_to_latex(np.asarray(data), precision=p, prefix=pre or "", max_size=max_size))
        return None

    data = np.asarray(obj.data if hasattr(obj, "data") and not isinstance(obj, np.ndarray) else obj)
    if isinstance(obj, qi.Statevector):
        data = data.reshape(-1, 1)
    text = np.array2string(data, precision=p, suppress_small=True)
    print(f"{prefix}\n{text}" if prefix else text)
    return None


def latex(obj, precision=None, prefix=""):
    """LaTeX source string of a vector / matrix (for copying into a report)."""
    from qiskit.visualization import array_to_latex

    p = Qum.precision if precision is None else precision
    data = obj.data if hasattr(obj, "data") and not isinstance(obj, np.ndarray) else obj
    return array_to_latex(np.asarray(data), precision=p, prefix=prefix, source=True)


def _as_state(x):
    from .circuit import Circuit
    from .states import ket

    if isinstance(x, Circuit):
        return x.state()
    if hasattr(x, "num_qubits") and hasattr(x, "data") and not isinstance(x, qi.Operator):
        return x
    if x.__class__.__name__ == "QuantumCircuit":
        return Circuit.from_qiskit(x).state()
    return ket(x)


def bloch(state, title="", **kwargs):
    """Bloch sphere for each qubit of a state (or circuit)."""
    from qiskit.visualization import plot_bloch_multivector

    return plot_bloch_multivector(_as_state(state), title=title, **kwargs)


def qsphere(state, **kwargs):
    """Q-sphere picture of a state (or circuit)."""
    from qiskit.visualization import plot_state_qsphere

    return plot_state_qsphere(_as_state(state), **kwargs)


def histogram(*counts, legend=None, title=None, **kwargs):
    """Histogram of one or more measurement results (``histogram(c1, c2)`` compares)."""
    from qiskit.visualization import plot_histogram

    data = [dict(c) for c in counts]
    if len(data) == 1:
        data = data[0]
    return plot_histogram(data, legend=legend, title=title, **kwargs)


def versions():
    """Print the versions of QumPy, Qiskit and friends (for reproducibility)."""
    import qumpy

    rows = [("qumpy", qumpy.__version__)]
    for mod in ("qiskit", "qiskit_aer", "qiskit_ibm_runtime", "numpy", "scipy", "matplotlib"):
        try:
            m = __import__(mod)
            rows.append((mod, getattr(m, "__version__", "?")))
        except ImportError:
            rows.append((mod, "not installed"))
    rows += [("python", platform.python_version()), ("system", f"{platform.system()} {platform.machine()}")]
    width = max(len(r[0]) for r in rows) + 2
    print("Version information")
    print("-" * (width + 14))
    for name, v in rows:
        print(f"  {name:<{width}}{v}")
