"""Measurement results."""

from __future__ import annotations


class Counts(dict):
    """Measurement counts, e.g. ``{'00': 507, '11': 517}``.

    It is a normal dict, plus a few helpers:

        counts.plot()           histogram
        counts.probabilities()  {'00': 0.495, '11': 0.505}
        counts.most_likely()    '11'
        counts.shots            1024

    Bit order (Qiskit convention): in ``'01'`` the RIGHT-most character is
    qubit 0 / classical bit 0.
    """

    def __init__(self, data, shots=None, backend="ideal"):
        super().__init__(sorted(data.items()))
        self.shots = int(shots if shots is not None else sum(data.values()))
        self.backend = backend

    def probabilities(self):
        return {k: v / self.shots for k, v in self.items()}

    def probability(self, bitstring):
        return self.get(bitstring, 0) / self.shots

    def most_likely(self):
        return max(self, key=self.get)

    def top(self, k=5):
        """The ``k`` most frequent outcomes, as a list of (bitstring, count)."""
        return sorted(self.items(), key=lambda kv: -kv[1])[:k]

    def as_ints(self):
        """Keys as integers: ``{'11': 3}`` -> ``{3: 3}``."""
        return {int(k.replace(" ", ""), 2): v for k, v in self.items()}

    def reversed_bits(self):
        """Keys written with qubit 0 on the LEFT (textbook order)."""
        return Counts({k[::-1]: v for k, v in self.items()}, self.shots, self.backend)

    def plot(self, title=None, **kwargs):
        from .display import histogram

        return histogram(self, title=title, **kwargs)

    def __repr__(self):
        return f"Counts({dict.__repr__(self)}, shots={self.shots})"
