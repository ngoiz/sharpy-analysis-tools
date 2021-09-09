import numpy as np
import matplotlib.pyplot as plt

class Bode:
    def __init__(self, wv, yfreq):
        self.wv = wv
        self.yfreq = yfreq

        self.mag = 20 * np.log10(np.abs(yfreq))
        self.phase = np.angle(yfreq)

        self.ss0 = yfreq[:, :, 0]

    def __call__(self, m, p, plot='mag', deg=False):

        if plot == 'mag' or plot == 'm':
            return self.wv, self.mag[p, m, :]
        elif plot == 'pha' or plot == 'p' or plot == 'phase':
            if deg:
                phase = self.phase * 180 / np.pi
            else:
                phase = self.phase

            return self.wv, phase[p, m, :]

    def plot(self, ax, m, p, deg=True, **kwargs):
        ax[0].semilogx(*self(m, p, plot='mag'), **kwargs)
        ax[1].semilogx(*self(m, p, plot='phase', deg=deg), **kwargs)


class Statistics:

    def __init__(self, input_psd, aircraft_frf, omega_vec):

        self.input_psd = input_psd
        self.aircraft_frf = aircraft_frf
        self.omega_vec = omega_vec

        self.output_psd = None
        self.output_covariance = None
        self.output_rms = None
        self.correlation = None

    def psd(self):
        self.output_psd = psd(self.input_psd, self.aircraft_frf)
        return self.output_psd

    def covariance(self):
        self.output_covariance, self.output_rms = covariance(self.output_psd, self.omega_vec)

    def correlation_coefficient(self):
        self.correlation = correlation_matrix(self.output_covariance, self.output_rms)

    def run(self):
        self.psd()
        self.covariance()
        self.correlation_coefficient()

    def probabillity_ellipse(self, output1, output2, x, y):
        return joint_gaussian_probability(x, y, self.output_rms[output1], self.output_rms[output2],
                                          self.correlation[output1, output2])


def psd(input_psd, yfreq):
    """
    Output Power Spectral Density from Input PSD and aircraft Frequency Response Function

    Args:
        input_psd (np.array): Power spectral density of input ``wv x 1``
        yfreq (np.array): FRF with dimensions ``p, m, wv``.

    Returns:
        np.array: Output PSD
    """

    psd_matrix = np.zeros((yfreq.shape[0], yfreq.shape[0], yfreq.shape[-1]), dtype=float)
    for i_omega in range(yfreq.shape[-1]):
        psd_matrix[:, :, i_omega] = input_psd[i_omega] * yfreq[:, :, i_omega].dot(np.conj(yfreq[:, :, i_omega].T))

    return psd_matrix


def covariance(psd, omega_vec):
    r"""
    Computes the covariance matrix and the Root Mean Square

    .. math::
        \Sigma_y = \frac{1}{2} \int_0^\infty (\Phi_y(\omega) + \Phi^\top(\omega)) d\omega

    Args:
        psd (np.ndarray): PSD of shape ``p x p x wv``
        omega_vec: Frequency Vector

    Returns:
        tuple: Tuple containing the covariance and RMS
    """
    d_omega_covariance = np.array([psd[:, :, i] + psd[:, :, i].T for i in range(psd.shape[-1])])
    print(d_omega_covariance.shape)
    covariance = np.zeros((psd.shape[0], psd.shape[0]))
    for i in range(psd.shape[0]):
        for j in range(psd.shape[0]):
            covariance[i, j] = 0.5 * np.trapz(d_omega_covariance[:, i, j], omega_vec)
    rms = np.sqrt(np.diag(covariance))
    print(rms)

    return covariance, rms


def correlation_matrix(covariance_matrix, rms):
    """
    Provides the correlation coefficients from the covariance matrix and the RMS.

    Args:
        covariance_matrix (np.array): Covariance matrix
        rms (np.array): Vector of RMS

    Returns:
        np.array: Correlation coefficient matrix
    """
    corr_coeff = np.zeros_like(covariance_matrix)
    for i in range(covariance_matrix.shape[0]):
        for j in range(covariance_matrix.shape[0]):
            corr_coeff[i, j] = covariance_matrix[i, j] / rms[i] / rms[j]

    return corr_coeff


def joint_gaussian_probability(x, y, rms_x, rms_y, corr_coeff):
    """
    Joint probability function density

    Args:
        x:
        y:
        rms_x:
        rms_y:
        corr_coeff:

    Returns:

    """
    mult = 1 / (2 * np.pi * rms_x * rms_y * np.sqrt(1 - corr_coeff))
    exponent = -1 / (2 * (1 - corr_coeff ** 2)) * (
                x ** 2 / rms_x ** 2 + y ** 2 / rms_y ** 2 - 2 * corr_coeff * x * y / rms_x / rms_y)
    return mult * np.exp(exponent)
