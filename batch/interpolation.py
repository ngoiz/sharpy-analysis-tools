from batch.sets import SetOfCases, Actual
from individual.case import Case
import configobj


class Interpolated(Actual):

    def __init__(self, path_to_interpolated_case, parameter_name=None):
        super().__init__(path_to_source=path_to_interpolated_case)

        self.parameter_name = parameter_name

        self.data = configobj.ConfigObj(self.path + 'pmor_summary.txt')

    def load_bulk_cases(self, *args, replace_dir=None, append=False, **kwargs):

        n_loaded_cases = 0
        for ith, case_number in enumerate(self.data):
            # item is the dict where the parameter_name is the key
            # single parameter cases only:
            param_name, param_value = list(self.data[case_number].items())[0]
            self.parameter_name = param_name
            param_value = float(param_value)

            for sys in self.systems:
                case = Case(param_value, sys, parameter_name=param_name, path_to_data=self.path)

                if 'eigs' in args:
                    case.path_to_sys['eigs'] = self.path + '/stability/param_case{:02g}/{:s}/_eigenvalues.dat'.format(ith,
                                                                                                                  sys)
                    case.load_eigs()

                if 'bode' in args:
                    case.path_to_sys[
                        'freqresp'] = self.path + '/frequencyresponse/param_case{:02g}/{:s}/freqresp.h5'.format(ith, sys)
                    case.load_bode()

                if 'ss' in args:
                    case.path_to_sys['ss'] = self.path + '/statespace/param_case{:02g}/{:s}/statespace.h5'.format(ith, sys)

                    case.load_ss()

                self.cases[sys].add_case(param_value, case)

            n_loaded_cases += 1
        print('Loaded {} cases'.format(n_loaded_cases))
