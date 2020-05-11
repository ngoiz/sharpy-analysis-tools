import glob
import numpy as np


class Stability:
    def __init__(self, path):

        try:
            file = glob.glob(path + '/velocity*.dat')[-1]
            res = np.loadtxt(file)
        except IndexError:
            print('No velocity data in path {:s}'.format(path))
        self.eigs = res[:, 1:]
        self.v = res[:, 0]

    def flutter(self, vmin=0, use_hz=False):

        conditions = self.v > vmin
        n_vel = np.unique(self.v)[1]
        num_modes = int(self.v.shape[0] // n_vel)

        if np.any(self.eigs[conditions, 0] > 0):

            positive_real = self.eigs[conditions, 0] >= 0

            positive_real_index = np.where(self.eigs[conditions, 0] >= 0)[0][0]

            flutter_vel = self.v[conditions][positive_real_index]

            #             flutter_vel = np.interp(0, [self.eigs[conditions, 0][positive_real_index-num_modes], self.eigs[conditions, 0][positive_real_index]],
            #                                    [self.v[conditions][positive_real_index-num_modes], self.v[conditions][positive_real_index]])

            #             print([self.v[conditions][positive_real_index-num_modes], self.v[conditions][positive_real_index]])

            flutter_freq = np.abs(self.eigs[conditions, 1][positive_real_index])

            if use_hz:
                flutter_freq /= (2 * np.pi)

            #             flutter_vel = self.v[positive_real][0]
            #             flutter_re = self.eigs[positive_real, 0][0]
            #             flutter_im = self.eigs[positive_real, 1][0]

            return flutter_vel, flutter_freq

        else:
            return 0