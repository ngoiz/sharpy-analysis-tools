import glob
import numpy as np


class Stability:
    def __init__(self, path):

        try:
            file = glob.glob(path + '/velocity*.dat')[-1]
            res = np.loadtxt(file)
        except IndexError:
            print('No velocity data in path {:s}'.format(path))
            raise FileNotFoundError('Unable to find velocity file data')
        self.eigs = res[:, 1:]
        self.v = res[:, 0]  # raw speeds
        self.damp = None
        self.v_f = None  # filtered for any freq limits specified
        self.frequency = None
        self.flutter_speed = None

    def process(self, **kwargs):
        self.v_f, self.damp, self.frequency = modes(self.v, self.eigs, **kwargs)
        self.flutter_speed = find_flutter_speed(self.v_f, self.damp)

    def save_to_file(self, output_folder):
        save_to_file(output_folder, self.v_f, self.damp, self.frequency, self.flutter_speed)
        np.savetxt(output_folder + '/vel_eigs.txt', np.column_stack((self.v, self.eigs)))


def modes(v, eigs, **kwargs):
    hz = kwargs.get('use_hz', False)

    wn = np.sqrt(eigs[:, 0] ** 2 + eigs[:, 1] ** 2)
    damp = eigs[:, 0] / wn

    if hz:
        wn /= (2 * np.pi)

    vmin = kwargs.get('vmin', 0)
    vmax = kwargs.get('vmax', 1000)

    wdmax = kwargs.get('wdmax', 10000)
    wdmin = kwargs.get('wdmin', -1)

    conditions = (eigs[:, 0] > -50) * (eigs[:, 1] > wdmin) * (eigs[:, 1] < wdmax) * (v >= vmin) * (v <= vmax)

    vc = v[conditions]
    dampc = damp[conditions]
    wnc = wn[conditions]
    return vc, dampc, wnc


def max_mode(v, damp):
    vels = np.unique(v)
    max_damp = np.zeros(len(vels))
    for ith, vel in enumerate(vels):
        max_damp[ith] = np.max(damp[v == vel])

    return vels, max_damp


def find_flutter_speed(v, damp):
    vu, max_damp = max_mode(v, damp)
    stable = max_damp >= 0
    flutter_speeds = []
    for i in range(1, len(vu)):
        axis_crossed = int(stable[i-1]) + int(stable[i])
        if axis_crossed == 1:
            x = np.array(max_damp[i-1:i+1])
            order = np.argsort(x)
            x = x[order]
            y = np.array(vu[i-1:i+1])[order]
            v = np.interp(0, x, y, right=0, left=0)
            flutter_speeds.append(v)

    return flutter_speeds


def save_to_file(output_folder, vel, damp, fn, flutter_speed):
    np.savetxt(output_folder + '/stability_analysis.txt', np.column_stack((vel, damp, fn)))

    with open(output_folder + '/flutter.txt', 'w') as fid:
        if type(flutter_speed) is list:
            for speed in flutter_speed:
                fid.write('Flutter speed = {:.4f} m/s'.format(speed))
        else:
            fid.write('Flutter speed = {:.4f} m/s'.format(flutter_speed))
