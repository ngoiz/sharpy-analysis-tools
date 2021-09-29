import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt


def plot_damping_contour(dataset, **kwargs):
    """

    Args:
        dataset (sharpytools.batch.sets.Actual):

    Returns:

    """
    param_info = {}
    eigs = {}
    for ith, case in enumerate(dataset.aeroelastic):
        param_info[ith] = case.case_info
        eigs[ith] = case.eigs
    x = []
    y = []
    z = []
    for ith, entry in enumerate(eigs.keys()):
        x.append(param_info[entry]['alpha'])
        y.append(param_info[entry]['u_inf'])
        z.append(eigs[entry])

    max_damping = []
    for eigs_array in z:
        # filter eigs...
        fn = np.sqrt(eigs_array[:, 0] ** 2 + eigs_array[:, 1] ** 2)
        damp = eigs_array[:, 0] / fn

        conditions = (fn < kwargs.get('max_fn', 500)) * (damp < kwargs.get('max_damp', 0.4))
        max_damping.append(np.max(damp[conditions]))
    plot_contour(x, y, max_damping, x_label='Angle of Attack, deg', y_label='Free Stream Velocity, m/s')


def plot_contour(x, y, z, **kwargs):
    ngridx = 100
    ngridy = 100
    xi = np.linspace(np.min(x), np.max(x), ngridx)
    yi = np.linspace(np.min(y), np.max(y), ngridy)

    # Linearly interpolate the data (x, y) on a grid defined by (xi, yi).
    triang = mpl.tri.Triangulation(x, y)
    interpolator = mpl.tri.LinearTriInterpolator(triang, z)
    Xi, Yi = np.meshgrid(xi, yi)
    zi = interpolator(Xi, Yi)

    fig, ax = plt.subplots()
    ax.contour(xi, yi, zi, levels=11, linewidths=0.5, colors='k')
    cntr = ax.contourf(xi, yi, zi, levels=11, linewidths=0.5)
    ax.scatter(x, y, s=2)

    fig.colorbar(cntr, ax=ax)
    ax.set_xlabel(kwargs.get('x_label'), None)
    ax.set_ylabel(kwargs.get('y_label'), None)
