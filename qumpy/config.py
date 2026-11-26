"""The ``Qum`` object: global settings + a single entry point to everything.

    from qumpy import Qum

    Qum.shots = 2000          # every .run() now uses 2000 shots
    Qum.precision = 3         # every printed number has 3 decimals
    Qum.backend = "noisy"     # simulate a (fake) real IBM device
    Qum.settings()            # print all settings
    Qum.reset()               # back to defaults

    with Qum.using(shots=10): # temporary settings
        ...

Every QumPy function is also reachable through ``Qum``:

    c = Qum.Circuit(2).h(0).cx(0, 1)
    psi = Qum.ket("01")
"""

from __future__ import annotations

import contextlib
import difflib

import numpy as np

from .errors import QumError

_DEFAULTS = {
    "shots": 1024,
    "precision": 4,
    "seed": None,
    "backend": "ideal",
    "device": "manila",
    "draw": "mpl",
    "auto_measure": True,
}

_HELP = {
    "shots": "number of repetitions used by .run()",
    "precision": "decimals shown when printing states / matrices",
    "seed": "random seed (None = different result each run)",
    "backend": "'ideal' (perfect simulator) or 'noisy' (fake IBM device)",
    "device": "fake device used when backend='noisy' ('manila', 'generic')",
    "draw": "default drawing style: 'mpl', 'text' or 'latex'",
    "auto_measure": "measure all qubits automatically if .run() finds no measurement",
}

_CHOICES = {
    "backend": ("ideal", "noisy"),
    "device": ("manila", "generic"),
    "draw": ("mpl", "text", "latex"),
}


class _Qum:
    """Global settings of QumPy. Use the single instance ``Qum``."""

    def __init__(self):
        object.__setattr__(self, "_values", dict(_DEFAULTS))
        self._apply_precision(_DEFAULTS["precision"])

    # ---------------------------------------------------------------- settings
    def __setattr__(self, name, value):
        if name not in _DEFAULTS:
            raise QumError(
                f"'{name}' is not a QumPy setting.",
                hint=_suggest(name, _DEFAULTS) or f"Available settings: {', '.join(_DEFAULTS)}",
            )
        self._values[name] = self._validate(name, value)
        if name == "precision":
            self._apply_precision(value)

    def __getattr__(self, name):
        values = object.__getattribute__(self, "_values")
        if name in values:
            return values[name]
        if name.startswith("__"):
            raise AttributeError(name)
        import qumpy

        if hasattr(qumpy, name):
            return getattr(qumpy, name)
        raise AttributeError(
            f"Qum has no setting or function called '{name}'. "
            + (_suggest(name, list(values) + qumpy.__all__) or "Try Qum.cheatsheet().")
        )

    def __dir__(self):
        import qumpy

        return sorted(set(_DEFAULTS) | set(qumpy.__all__) | {"settings", "reset", "using"})

    @staticmethod
    def _validate(name, value):
        if name == "shots":
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
                raise QumError(f"Qum.shots must be a positive whole number, got {value!r}.",
                               hint="Example: Qum.shots = 1000")
            return int(value)
        if name == "precision":
            if not isinstance(value, (int, np.integer)) or value < 0:
                raise QumError(f"Qum.precision must be an integer >= 0, got {value!r}.")
            return int(value)
        if name == "seed":
            if value is not None and not isinstance(value, (int, np.integer)):
                raise QumError(f"Qum.seed must be an integer or None, got {value!r}.")
            return value
        if name == "auto_measure":
            return bool(value)
        if name in _CHOICES:
            value = str(value).lower()
            if value not in _CHOICES[name]:
                raise QumError(f"Qum.{name} must be one of {_CHOICES[name]}, got {value!r}.")
        return value

    @staticmethod
    def _apply_precision(p):
        np.set_printoptions(precision=p, suppress=True)

    # ----------------------------------------------------------------- helpers
    def settings(self):
        """Print all settings with their current value."""
        print("QumPy settings")
        print("-" * 72)
        for k in _DEFAULTS:
            print(f"  Qum.{k:<13} = {self._values[k]!r:<10}  # {_HELP[k]}")

    def reset(self):
        """Restore every setting to its default value."""
        for k, v in _DEFAULTS.items():
            setattr(self, k, v)

    @contextlib.contextmanager
    def using(self, **settings):
        """Temporarily change settings::

            with Qum.using(shots=10, seed=1):
                c.run()
        """
        old = {k: getattr(self, k) for k in settings}
        try:
            for k, v in settings.items():
                setattr(self, k, v)
            yield self
        finally:
            for k, v in old.items():
                setattr(self, k, v)

    def __repr__(self):
        body = ", ".join(f"{k}={v!r}" for k, v in self._values.items())
        return f"Qum({body})"


def _suggest(name, options):
    close = difflib.get_close_matches(name, list(options), n=3, cutoff=0.6)
    return f"Did you mean: {', '.join(close)}?" if close else ""


Qum = _Qum()
