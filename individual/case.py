from linear.statespace import Bode
import numpy as np
import glob
import os
import h5py as h5
import sharpy.utils.h5utils as h5utils
import sharpy.linear.src.libss as libss


class Case:
    """The basic element"""

    def __init__(self, parameter_value, system, path_to_data, **kwargs):
        self._name = ''
        self.parameter_value = parameter_value  #: dict with parameter information (or a simple float)
        self.parameter_name = kwargs.get('parameter_name', 'param')
        self.system = system  #: system name (aeroelastic, aerodynamic or structural)
        self.path = path_to_data

        self.eigs = None
        self.bode = None
        self.ss = None

        self.deflection = None

        self.path_to_eigs = kwargs.get('eigs', None)
        self.path_to_sys = dict()

        self._case_id = -1

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def case_id(self):
        return self._case_id

    @case_id.setter
    def case_id(self, number):
        if self.case_id == -1:
            self._case_id = number
        else:
            print('Case id already set and should not be changed')

    def load_eigs(self, refresh=False, path=None):

        if path is None:
            try:
                path = self.path_to_sys['eigs']
            except KeyError:
                if self.path_to_eigs is None:
                    print('No path to eigs has been given')
                    return

                path = self.path_to_eigs

        if self.eigs is None or refresh:
            try:
                self.eigs = np.loadtxt(path)
            except OSError:
                print('Unable to find eigenvalues at file {:s}'.format(os.path.abspath(path)))

    def load_bode(self, refresh=False, path=None):
        if path is None:
            path = self.path_to_sys['freqresp']

        try:
            with h5.File(path, 'r') as freq_file_handle:
                # store files in dictionary
                freq_dict = h5utils.load_h5_in_dict(freq_file_handle)
        except OSError:
            print('No frequency data - %s' % path)
            return
        # Could create a Bode object with ss gain, max gain etc
        self.bode = Bode(wv=freq_dict['frequency'], yfreq=freq_dict['response'])

    def load_ss(self, refresh=None, path=None):
        if path is None:
            path = self.path_to_sys['ss']

        with h5.File(path, 'r') as f:
            data = h5utils.load_h5_in_dict(f)

        self.ss = libss.ss(data['a'], data['b'], data['c'], data['d'], dt=data.get('dt', None))

    def load_deflection(self, refresh=None, path=None):
        if path is None:
            try:
                path = self.path_to_sys['WriteVariablesTime']
            except KeyError:
                return None

        node_files = glob.glob(path)

        if len(node_files) == 0:
            return None
        res = []
        for file in node_files:
            try:
                res.append(np.loadtxt(file)[-1, :])
            except IndexError:
                res.append(np.loadtxt(file))

        res = np.vstack(res)
        #         print(res)
        try:
            res = res[res[:, 2].argsort()]
        except IndexError:
            print(res.shape)
            print(self.parameter_value)

        self.deflection = res

    def load_beam_modal_analysis(self, refresh=None, path=None):
        if path is None:
            try:
                path = self.path_to_sys['beam_modal_analysis']
            except KeyError:
                return None

        frequencies = np.loadtxt(path + '/frequencies.dat')

        self.beam_eigs = np.zeros((len(frequencies), 2))
        self.beam_eigs[:, 1] = frequencies