from sharpytools.individual.case import Case
from sharpytools.linear.stability import Stability
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

        self.database = dict()

    def load_bulk_cases(self, *args, replace_dir=None, append=False, **kwargs):

        verbose = kwargs.get('verbose', False)

        if kwargs.get('rom_library'):
            source_cases_name = [entry['path_to_data'] for entry in kwargs['rom_library'].library]
        else:
            source_cases_name = glob.glob(self.path)

        eigs_legacy = kwargs.get('eigs_legacy', True)

        n_loaded_cases = 0
        for source in source_cases_name:
            try:
                param_file = glob.glob(source + '/*.pmor.sharpy')[0]
            except IndexError:
                if verbose:
                    print('Unable to find source case .pmor.sharpy at {:s}'.format(source))
                continue

            case_info = configobj.ConfigObj(param_file)

            self.param_name = []
            param_value = []
            for k, v in case_info['parameters'].items():
                self.param_name.append(k)
                param_value.append(v)

            if replace_dir is not None:
                path_to_source_case = case_info['sim_info']['path_to_data'].replace('/home/ng213/sharpy_cases/',
                                                                                    '/home/ng213/2TB/')
            else:
                path_to_source_case = case_info['sim_info']['path_to_data']

            for sys in self.systems:
                if param_value in self.cases[sys].parameter_values and append:
                    continue

                case = Case(case_info['parameters'].values(), sys, parameter_name=self.param_name,
                            path_to_data=path_to_source_case, case_info=case_info['parameters'],
                            verbose=verbose)
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

                if 'forces' in args:
                    case.load_forces(case.path + '/forces/aeroforces.txt')

                if 'ss' in args:
                    case.load_ss(path=case.path)
                self.cases[sys].add_case(param_value, case, case_info['parameters'])
            n_loaded_cases += 1
        print('Loaded {} cases'.format(n_loaded_cases))
        if n_loaded_cases == 0:
            print(source_cases_name)

    def eigs(self, sys):
        param_array = []
        eigs = []
        for case in self.cases[sys]:
            try:
                param_array.append(np.ones((case.eigs.shape[0], len(case.parameter_value))) * case.parameter_value)
                eigs.append(case.eigs)
            except TypeError:
                param_array.append(np.ones_like(case.eigs[:, 0]) * case.parameter_value)
            except AttributeError:
                continue

        if len(eigs) == 0:
            raise FileNotFoundError('No eigenvalue data was found.')
        return np.concatenate(param_array), np.concatenate(eigs)

    def wing_tip_deflection(self, frame='a', alpha=0, reference_line=np.array([0, 0, 0], dtype=float)):
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
                deflection.append(case.get_deflection_at_line(reference_line)[-1, -3:])
            elif frame == 'g':
                deflection.append(cga.dot(case.get_deflection_at_line(reference_line)[-1, -3:]))

        param_array = np.array(param_array)
        order = np.argsort(param_array)
        param_array = param_array[order]
        deflection = np.array([deflection[ith] for ith in order])

        return param_array, deflection

    def forces(self, frame='g'):
        param_array = []
        forces = []
        for case in self.cases['aeroelastic']:
            param_array.append(case.parameter_value)
            if frame == 'g':
                forces.append(case.aero_forces[1:4])
            elif frame == 'a':
                forces.append(case.aero_forces[7:10])
            else:
                raise NameError('Frame can only be A or G')

        param_array = np.array(param_array)
        order = np.argsort(param_array)
        param_array = param_array[order]
        forces = np.vstack(([forces[ith] for ith in order]))

        return param_array, forces

    def moments(self, frame='g'):
        param_array = []
        moments = []
        for case in self.cases['aeroelastic']:
            param_array.append(case.parameter_value)
            if frame == 'g':
                moments.append(case.aero_moments[1:4])
            elif frame == 'a':
                moments.append(case.aero_moments[7:10])
            else:
                raise NameError('Frame can only be A or G')

        param_array = np.array(param_array)
        order = np.argsort(param_array)
        param_array = param_array[order]
        moments = np.vstack(([moments[ith] for ith in order]))

        return param_array, moments


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
        self.id_list = dict()

        self.database = dict()

        self._n_cases = 0

    def add_case(self, parameter_value, case, param_dict=None):
        case.case_id = self.n_cases + 1

        self.cases.append(case)
        self.parameter_values.append(parameter_value)
        self.id_list[case.case_id] = case
        if param_dict is None:
            import pdb; pdb.set_trace()
        self.database[case.case_id] = {k: float(v) for k, v in param_dict.items()}

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

    def find_param(self, param_value, return_idx=False):
        for case_id, entry_values in self.database.items():
            if entry_values == param_value:
                if not return_idx:
                    try:
                        return self.id_list[case_id]
                    except KeyError:
                        msg = f'Unable to find case with {case_id}'
                else:
                    return case_id
