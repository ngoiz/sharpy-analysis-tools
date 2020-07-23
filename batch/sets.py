from individual.case import Case
from linear.stability import Stability
import glob
import configobj
import numpy as np


class Actual:
    def __init__(self, path_to_source):
        self.path = path_to_source
        self.systems = ['aeroelastic', 'aerodynamic', 'structural']

        self.cases = dict()
        for sys in self.systems:
            self.cases[sys] = SetOfCases()

        self.structural = self.cases['structural']
        self.aerodynamic = self.cases['aerodynamic']
        self.aeroelastic = self.cases['aeroelastic']

    def load_bulk_cases(self, *args, replace_dir=None, append=False, **kwargs):

        source_cases_name = glob.glob(self.path)

        eigs_legacy = kwargs.get('eigs_legacy', True)

        n_loaded_cases = 0
        for source in source_cases_name:
            try:
                param_file = glob.glob(source + '/*.pmor.sharpy')[0]
            except IndexError:
                print('Unable to find source case .pmor.sharpy at {:s}'.format(source))
                continue

            case_info = configobj.ConfigObj(param_file)

            self.param_name, param_value = list(case_info['parameters'].items())[0]

            param_value = float(param_value)

            if replace_dir is not None:
                path_to_source_case = case_info['sim_info']['path_to_data'].replace('/home/ng213/sharpy_cases/',
                                                                                    '/home/ng213/2TB/')
            else:
                path_to_source_case = case_info['sim_info']['path_to_data']

            for sys in self.systems:
                if param_value in self.cases[sys].parameter_values and append:
                    continue

                case = Case(param_value, sys, parameter_name=self.param_name, path_to_data=path_to_source_case)
                case.name = case_info['sim_info']['case']

                if eigs_legacy: # asymtotic stability in dev_pmor has an extra setting to save aeroelastic_eigenvalues.dat
                    case.path_to_sys['eigs'] = case.path + '/stability/eigenvalues.dat'
                else:
                    case.path_to_sys['eigs'] = case.path + '/stability/{:s}_eigenvalues.dat'.format(sys)

                case.path_to_sys['freqresp'] = case.path + '/frequencyresponse/{:s}.freqresp.h5'.format(sys)
                case.path_to_sys['ss'] = case.path + '/statespace/{:s}.statespace.dat'.format(sys)
                try:
                    case.alpha = float(list(case_info['parameters'].items())[1][1])
                except IndexError:
                    pass
                if 'eigs' in args:
                    case.load_eigs()
                if 'bode' in args:
                    case.load_bode()
                case.path_to_sys['WriteVariablesTime'] = case.path + '/WriteVariablesTime/*'

                if 'deflection' in args:
                    case.load_deflection()

                if sys == 'aeroelastic' and 'stability' in args:
                    case.stability = Stability(case.path + '/stability/')

                case.path_to_sys['beam_modal_analysis'] = case.path + '/beam_modal_analysis'
                if 'beam_modal_analysis' in args:
                    case.load_beam_modal_analysis()
                self.cases[sys].add_case(param_value, case)
                n_loaded_cases += 1
        print('Loaded {} cases'.format(n_loaded_cases))

    def eigs(self, sys):
        param_array = []
        eigs = []
        for case in self.cases[sys]:
            eigs.append(case.eigs)
            param_array.append(np.ones_like(case.eigs[:, 0]) * case.parameter_value)

        return np.concatenate(param_array), np.concatenate(eigs)

    def wing_tip_deflection(self, frame='a', alpha=0):
        param_array = []
        deflection = []

        if frame == 'g':
            try:
                import sharpy.utils.algebra as algebra
            except ModuleNotFoundError:
                raise(ModuleNotFoundError('Please load sharpy'))
            else:
                cga = algebra.quat2rotation(algebra.euler2quat(np.array([0, alpha * np.pi / 180, 0])))

        for case in self.cases['aeroelastic']:
            param_array.append(case.parameter_value)
            if frame == 'a':
                deflection.append(case.deflection[-1, -3:])
            elif frame == 'g':
                deflection.append(cga.dot(case.deflection[-1, -3:]))

        param_array = np.array(param_array)
        order = np.argsort(param_array)
        param_array = param_array[order]
        deflection = np.array([deflection[ith] for ith in order])

        return param_array, deflection



class SetIterator:

    def __init__(self, set_of_cases):
        self._set_cases = set_of_cases
        self._index = 0

    def __next__(self):
        if self._index < self._set_cases.n_cases:
            res = self._set_cases(self._index)
            self._index += 1
            return res

        raise StopIteration


class SetOfCases:
    def __init__(self):
        self.cases = list()
        self.parameter_values = list()
        self.id_list = list()

        self._n_cases = 0

    def add_case(self, parameter_value, case):
        case.case_id = self.n_cases + 1

        self.cases.append(case)
        self.parameter_values.append(parameter_value)
        self.id_list.append(case.case_id)

    def __call__(self, i):
        return self.cases[i]

    @property
    def n_cases(self):
        self.n_cases = len(self.cases)
        return self._n_cases

    @n_cases.setter
    def n_cases(self, number):
        self._n_cases = number

    def __iter__(self):
        return SetIterator(self)

    def find_parameter_value(self, param_value, return_idx=False):
        ind = self.parameter_values.index(param_value)
        if not return_idx:
            return self(ind)
        else:
            return ind