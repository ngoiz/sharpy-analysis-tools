from linear.statespace import Bode
import numpy as np
import glob
import os
import h5py as h5
import sharpy.utils.h5utils as h5utils
import sharpy.linear.src.libss as libss
import sharpy.utils.algebra as algebra


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
        self.crv = None

        self.aero_forces = None

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
            try:
                path = self.path_to_sys['freqresp']
            except KeyError:
                path = glob.glob(self.path + 'frequencyresponse/{}.freqresp.h5'.format(self.system))[0]

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

    def load_deflection(self, refresh=None, path=None, reference_line=0):
        if path is None:
            try:
                path = self.path_to_sys['WriteVariablesTime']
            except KeyError:
                return None
        node_files = glob.glob(path + 'pos*')

        if len(node_files) == 0:
            print('No displacement files found at {}'.format(path))
            return None
        res = []
        for file in node_files:
            try:
                res.append(np.loadtxt(file)[-1, :])
            except IndexError:
                res.append(np.loadtxt(file))  # single entry case in WriteVariablesTime

        res = np.vstack(res)
        try:
            order = res[:, 2].argsort()
            res = res[order] # sort by spanwise index
        except IndexError:
            print(res.shape)
            print(self.parameter_value)
            print('Unable to order deflection by span')
            return None

        self.deflection = res

        # load crv if available
        crv = np.zeros((self.deflection.shape[0], 3))
        crv_files = glob.glob(path + 'psi*')
        if len(crv_files) == 0:
            return None
        else:
            crv_list = [] # same order of nodes as position - we'll use that to order these
            for ith, crv_file in enumerate(crv_files):
                try:
                    crv_list.append(np.loadtxt(crv_file)[-1, 1:])
                except IndexError:
                    crv_list.append(np.loadtxt(crv_file)[1:])

        for i in range(crv.shape[0]):
            crv[i, :] = crv_list[order[i]]

        self.crv = crv

    def load_beam_modal_analysis(self, refresh=None, path=None):
        if path is None:
            try:
                path = self.path_to_sys['beam_modal_analysis']
            except KeyError:
                return None

        frequencies = np.loadtxt(path + '/frequencies.dat')

        self.beam_eigs = np.zeros((len(frequencies), 2))
        self.beam_eigs[:, 1] = frequencies

    def get_deflection_at_line(self, reference_line=np.array([0, 0, 0.])):
        if self.crv is None:
            return self.deflection

        def_at_line = np.zeros((self.deflection.shape[0], 3))
        for i_node in range(def_at_line.shape[0]):
            def_at_line[i_node] = self.deflection[i_node, -3:] + algebra.crv2rotation(self.crv[i_node]).dot(reference_line)

        return def_at_line

    def load_forces(self, path=None):
        if path is None:
            try:
                path = self.path_to_sys['AeroForcesCalculator']
            except KeyError:
                return None

        self.aero_forces = np.loadtxt(path, skiprows=1, delimiter=',')

