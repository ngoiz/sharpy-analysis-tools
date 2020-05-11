import numpy as np

class Bode:
    def __init__(self, wv, yfreq):
        self.wv = wv
        self.yfreq = yfreq

        self.mag = 20 * np.log10(yfreq)
        self.phase = np.angle(yfreq)

        self.ss0 = yfreq[:, :, 0]

    def __call__(self, m, p, plot='mag', deg=False):

        if plot == 'mag' or plot == 'm':
            return self.wv, self.mag[p, m, :]
        elif plot == 'pha' or plot == 'p':
            if deg:
                phase = self.phase * 180 / np.pi
            else:
                phase = self.phase
            return self.wv, phase[p, m, :]