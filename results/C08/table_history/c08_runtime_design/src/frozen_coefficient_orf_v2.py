"""Own existing C08 coefficients; validate in bounded tiles without refitting.

Constructor inputs must already be NumPy arrays (memmap is accepted). This
permits a shape/dtype-only budget check before coercion, copies, or full-array
boolean operations. ``maximum_owned_numeric_bytes`` covers the four owned
arrays, reusable validation buffers, and one eigvalsh result. It excludes
caller inputs and NumPy/LAPACK internal workspaces. The reported simultaneous
numeric estimate adds the logical caller input sizes, not their possibly
larger backing allocations. It is not an RSS guarantee. Runtime query arrays,
decompression, and downstream likelihood/native banks need separate budgets.

Endpoints check C0 only, within absolute tolerance. Optional C1 validation is
in x = -beta and defaults off; no coefficient is repaired and no fallback is
used. Representation checks do not establish scientific-response validity.
"""
import math
import numpy as np


def _positive_integer(value, name):
    if (isinstance(value, (bool, np.bool_))
            or not isinstance(value, (int, np.integer)) or value <= 0):
        raise ValueError('Explicit positive integer required: ' + name)
    return int(value)


def loader_memory_estimate(nodes, matrices, coeff, *, validation_tile_size=128):
    """Read array metadata only; no numeric allocation or input coercion."""
    tile = _positive_integer(validation_tile_size, 'validation_tile_size')
    if not all(isinstance(a, np.ndarray) for a in (nodes, matrices, coeff)):
        raise TypeError('Constructor inputs must be existing NumPy arrays')
    n, m, c = nodes, matrices, coeff
    if n.dtype.kind not in 'fiu' or n.ndim != 1 or len(n) < 2:
        raise ValueError('Real node vector with at least two entries required')
    if (m.dtype.kind not in 'fc' or m.ndim != 4 or m.shape[0] != len(n)
            or m.shape[-1] != m.shape[-2] or not m.shape[1] or not m.shape[2]):
        raise ValueError('Floating matrix nodes[N,K,P,P] required')
    if c.dtype.kind not in 'fc' or c.shape != (len(n)-1, 4, *m.shape[1:]):
        raise ValueError('Floating matching cubic coefficients required')
    rows = min(tile, len(n))
    elements = rows * math.prod(m.shape[1:])
    persistent = 2 * len(n) * 8 + (m.size + c.size) * 16
    # Two complex tiles, one real tile and one boolean tile. Their flattened
    # views also supply node/width scratch; there are no separate vector arrays.
    workspace = elements * (2 * 16 + 8 + 1)
    eigenvalues = rows * m.shape[1] * m.shape[2] * 8
    owned_peak = persistent + workspace + eigenvalues
    caller = sum(a.nbytes for a in (n, m, c))
    return dict(
        validation_tile_size=rows,
        persistent_owned_numeric_bytes=int(persistent),
        reusable_validation_workspace_bytes=int(workspace),
        maximum_eigenvalue_result_bytes=int(eigenvalues),
        owned_and_temporary_estimate_bytes=int(owned_peak),
        caller_input_logical_bytes=int(caller),
        simultaneous_loader_numeric_bytes_excluding_backend=int(caller + owned_peak),
        backend_workspace_included=False,
        memory_scope='constructor-owned arrays and explicit tiled buffers; '
                     'caller storage, backend internal workspaces, Python overhead, '
                     'query outputs and downstream banks require separate allowances',
        RSS_guarantee=False,
    )


class FrozenCoefficientORF:
    def __init__(self, nodes, matrices, coeff, *, maximum_owned_numeric_bytes,
                 require_threshold_parity=True, validation_tile_size=128,
                 require_C1=False, C1_absolute_tolerance=1e-7):
        cap = _positive_integer(maximum_owned_numeric_bytes, 'maximum_owned_numeric_bytes')
        for flag in (require_threshold_parity, require_C1):
            if not isinstance(flag, (bool, np.bool_)):
                raise ValueError('Continuity/parity guards must be boolean')
        if (isinstance(C1_absolute_tolerance, (bool, np.bool_))
                or not isinstance(C1_absolute_tolerance, (float, int, np.floating, np.integer))
                or not math.isfinite(C1_absolute_tolerance) or C1_absolute_tolerance <= 0):
            raise ValueError('Positive finite C1 absolute tolerance required')
        estimate = loader_memory_estimate(nodes, matrices, coeff,
                                          validation_tile_size=validation_tile_size)
        if estimate['owned_and_temporary_estimate_bytes'] > cap:
            raise MemoryError('Owned arrays and tiled validation buffers exceed budget; '
                              'caller inputs and backend workspaces need separate allowances')

        # Only now may the loader allocate or inspect numeric values. Keep
        # sources as base-class views, then convert/copy one tile at a time.
        n, m, c = (np.asarray(a) for a in (nodes, matrices, coeff))
        self.nodes = np.empty(n.shape, dtype=np.float64)
        self.matrices = np.empty(m.shape, dtype=np.complex128)
        self.coeff = np.empty(c.shape, dtype=np.complex128)
        self.alpha = np.empty(n.shape, dtype=np.float64)
        self.coordinate_name = 'beta'
        tile = estimate['validation_tile_size']
        shape = (tile, *m.shape[1:])
        work = np.empty(shape, dtype=np.complex128)
        scratch = np.empty(shape, dtype=np.complex128)
        real = np.empty(shape, dtype=np.float64)
        flags = np.empty(shape, dtype=np.bool_)

        def finite(a):
            flag = flags.reshape(-1)[:a.size].reshape(a.shape)
            np.isfinite(a, out=flag)
            if not flag.all():
                raise ValueError('Nonfinite numeric payload or polynomial arithmetic')

        def magnitude(a):
            finite(a)
            target = real[:len(a)]
            np.absolute(a, out=target)
            return float(target.max())

        def hermiticity(a):
            dest = work[:len(a)]
            np.conjugate(a.swapaxes(-1, -2), out=dest)
            np.subtract(a, dest, out=dest)
            return magnitude(dest)

        for start in range(0, len(n), tile):
            end = min(start + tile, len(n))
            nt, xt = self.nodes[start:end], self.alpha[start:end]
            np.copyto(nt, n[start:end], casting='unsafe')
            finite(nt)
            vector = real.reshape(-1)[:len(nt)]
            flag = flags.reshape(-1)[:len(nt)]
            np.less(nt, 0, out=flag)
            if flag.any():
                raise ValueError('Node outside [0,1]')
            np.greater(nt, 1, out=flag)
            if flag.any():
                raise ValueError('Node outside [0,1]')
            np.subtract(1., nt, out=xt)
            np.add(1., nt, out=vector)
            np.multiply(xt, vector, out=xt)
            np.sqrt(xt, out=xt)
            np.negative(xt, out=xt)
            for a in (nt, xt):
                np.less_equal(a[1:], a[:-1], out=flag[:len(a)-1])
                if flag[:len(a)-1].any():
                    raise ValueError('Increasing u and transformed beta nodes required')
            if start and (nt[0] <= self.nodes[start-1] or xt[0] <= self.alpha[start-1]):
                raise ValueError('Increasing u and transformed beta nodes required')
        if self.nodes[0] != 0 or self.nodes[-1] != 1:
            raise ValueError('Full u support [0,1] required')

        herm = 0.
        for source, target in ((m, self.matrices), (c, self.coeff)):
            for start in range(0, len(source), tile):
                end = min(start + tile, len(source))
                # Four coefficient powers are checked separately, so no
                # four-times-larger boolean or conjugation tile is needed.
                powers = (None,) if target.ndim == 4 else range(4)
                for power in powers:
                    src = source[start:end] if power is None else source[start:end, power]
                    dst = target[start:end] if power is None else target[start:end, power]
                    np.copyto(dst, src, casting='unsafe')
                    finite(dst)
                    herm = max(herm, hermiticity(dst))
                    if herm > 1e-12:
                        raise ValueError('Non-Hermitian matrix polynomial')

        endpoint = 0.
        minimum = math.inf
        for start in range(0, len(self.coeff), tile):
            end = min(start + tile, len(self.coeff))
            block = self.coeff[start:end]
            w, s = work[:len(block)], scratch[:len(block)]
            np.subtract(block[:, 0], self.matrices[start:end], out=w)
            endpoint = max(endpoint, magnitude(w))
            np.copyto(w, block[:, 0])
            for power in range(1, 4):
                np.add(w, block[:, power], out=w)
            np.subtract(w, self.matrices[start+1:end+1], out=w)
            endpoint = max(endpoint, magnitude(w))
            if endpoint > 1e-11:
                raise ValueError('Polynomial endpoints do not match stored matrix nodes')

            # Only one Bernstein control exists at any instant. eigvalsh's
            # result is freed before the next call; backend workspace is extra.
            for control in range(4):
                np.copyto(w, block[:, 0])
                if control == 1:
                    np.divide(block[:, 1], 3., out=s)
                    np.add(w, s, out=w)
                elif control == 2:
                    np.multiply(block[:, 1], 2., out=s)
                    np.divide(s, 3., out=s)
                    np.add(w, s, out=w)
                    np.divide(block[:, 2], 3., out=s)
                    np.add(w, s, out=w)
                elif control == 3:
                    for power in range(1, 4):
                        np.add(w, block[:, power], out=w)
                finite(w)
                eigenvalues = np.linalg.eigvalsh(w)
                finite(eigenvalues)
                minimum = min(minimum, float(eigenvalues.min()))
                del eigenvalues
                if minimum < -1e-12:
                    raise ValueError('Bernstein controls not PSD; no clipping or fallback')

        def left_endpoint_derivative(start, end):
            block = self.coeff[start:end]
            w, s = work[:len(block)], scratch[:len(block)]
            np.multiply(block[:, 3], 3., out=w)
            np.multiply(block[:, 2], 2., out=s)
            np.add(w, s, out=w)
            np.add(w, block[:, 1], out=w)
            width = real.reshape(-1)[:len(block)]
            np.subtract(self.alpha[start+1:end+1], self.alpha[start:end], out=width)
            np.divide(w, width[:, None, None, None], out=w)
            return w

        # This is the derivative at t=1 of the left polynomial, in x=-beta.
        last = len(self.coeff)-1
        parity = magnitude(left_endpoint_derivative(last, last+1))
        if require_threshold_parity and parity > 1e-7:
            raise ValueError('Nonzero beta derivative at the tensor threshold')
        c1_error = None
        if require_C1:
            c1_error = 0.
            for start in range(0, len(self.coeff)-1, tile):
                end = min(start+tile, len(self.coeff)-1)
                w = left_endpoint_derivative(start, end)
                s = scratch[:len(w)]
                np.copyto(s, self.coeff[start+1:end+1, 1])
                width = real.reshape(-1)[:len(w)]
                np.subtract(self.alpha[start+2:end+2], self.alpha[start+1:end+1], out=width)
                np.divide(s, width[:, None, None, None], out=s)
                np.subtract(w, s, out=w)
                c1_error = max(c1_error, magnitude(w))
                if c1_error > C1_absolute_tolerance:
                    raise ValueError('C1 derivative continuity guard failed in minus-beta')

        for a in (self.nodes, self.matrices, self.coeff, self.alpha):
            a.flags.writeable = False
        self.representation_checks = estimate | dict(
            maximum_owned_numeric_bytes=cap,
            maximum_Hermiticity_error=herm,
            maximum_endpoint_error=endpoint,
            continuity_order_checked='C1' if require_C1 else 'C0',
            require_C1=bool(require_C1),
            C1_absolute_tolerance=float(C1_absolute_tolerance),
            maximum_C1_derivative_error=c1_error,
            minimum_Bernstein_eigenvalue=minimum,
            threshold_derivative_error=parity,
            threshold_parity_required=bool(require_threshold_parity),
            source_coefficients_used_directly=True,
            spline_fit_performed=False,
            clipping_or_fallback_performed=False,
            scientific_response_validation_claimed=False,
        )

    def coordinate(self, u):
        x = np.asarray(u)
        if (x.dtype.kind not in 'fiu' or x.ndim != 1 or not np.isfinite(x).all()
                or np.any((x < 0) | (x > 1))):
            raise ValueError('Finite real u vector in[0,1] required')
        return -np.sqrt((1-x)*(1+x))

    def location(self, u):
        beta = self.coordinate(u)
        j = np.minimum(np.searchsorted(self.nodes, u, side='right')-1, len(self.nodes)-2)
        fraction = (beta-self.alpha[j])/(self.alpha[j+1]-self.alpha[j])
        return j, fraction

    def __call__(self, u):
        j, f = self.location(u)
        c = self.coeff[j]
        f = f[:, None, None, None]
        return c[:, 0]+f*(c[:, 1]+f*(c[:, 2]+f*c[:, 3]))
