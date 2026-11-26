"""Real IBM quantum computers (through Qiskit Runtime).

One-time setup (your token is on https://quantum.cloud.ibm.com, it is stored on
your computer by Qiskit, QumPy never sees it):

    from qiskit_ibm_runtime import QiskitRuntimeService
    QiskitRuntimeService.save_account(token="...", channel="ibm_quantum_platform",
                                      set_as_default=True)

Then:

    qp.ibm_backends()                     # names of the devices you can use
    dev = qp.ibm_backend()                # least busy real device
    dev = qp.ibm_backend("ibm_brisbane")  # a specific device
    qp.backend_info(dev)                  # name, qubits, basis gates, queue
    c.compile(backend=dev).draw()         # circuit as the device will run it
    c.run(backend=dev)                    # really runs on the quantum computer
    c.run(backend="ibm")                  # same, on the least busy device

Real devices have a queue: ``run`` waits until the job is done. Jobs use your
IBM Quantum time allowance.
"""

from __future__ import annotations

from .errors import QumError

_SETUP_HINT = (
    "Save your IBM Quantum account once (token from https://quantum.cloud.ibm.com):\n"
    "    from qiskit_ibm_runtime import QiskitRuntimeService\n"
    "    QiskitRuntimeService.save_account(token='YOUR_TOKEN', "
    "channel='ibm_quantum_platform', set_as_default=True)"
)

_SERVICE = {}


def ibm_service():
    """The ``QiskitRuntimeService`` for your saved IBM Quantum account."""
    if "service" in _SERVICE:
        return _SERVICE["service"]
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService
    except ImportError as e:
        raise QumError("Real IBM devices need qiskit-ibm-runtime.",
                       hint="pip install qiskit-ibm-runtime") from e
    try:
        service = QiskitRuntimeService()
    except Exception as e:
        raise QumError(f"Could not connect to IBM Quantum ({type(e).__name__}: {e}).",
                       hint=_SETUP_HINT) from e
    _SERVICE["service"] = service
    return service


def ibm_backends(min_qubits=1):
    """Names of the real IBM devices your account can use."""
    service = ibm_service()
    return sorted(b.name for b in service.backends(simulator=False, operational=True,
                                                   min_num_qubits=min_qubits))


def ibm_backend(name=None, min_qubits=1):
    """A real IBM device: ``name`` if given, otherwise the least busy one."""
    service = ibm_service()
    try:
        if name is not None:
            return service.backend(name)
        return service.least_busy(simulator=False, operational=True, min_num_qubits=min_qubits)
    except Exception as e:
        raise QumError(f"Could not get the IBM device {name or '(least busy)'}: {e}",
                       hint="qp.ibm_backends() lists the devices you can use.") from e


def backend_info(backend, show=True):
    """Name, version, number of qubits, basis gates and queue of a backend.

    Works for real devices and for fake ones (``qp.noisy_backend()``).
    """
    info = {
        "name": getattr(backend, "name", str(backend)),
        "version": getattr(backend, "backend_version", getattr(backend, "version", "?")),
        "qubits": getattr(backend, "num_qubits", "?"),
        "basis gates": sorted(getattr(backend, "operation_names", []) or []),
    }
    status = getattr(backend, "status", None)
    if callable(status):
        try:
            st = status()
            info["operational"] = getattr(st, "operational", "?")
            info["pending jobs"] = getattr(st, "pending_jobs", "?")
        except Exception:
            pass
    if not show:
        return info
    for k, v in info.items():
        print(f"{k:>13}: {v}")
    return None
