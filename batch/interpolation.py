from batch.sets import SetOfCases
from individual.case import Case
import configobj


class Interpolated:

    def __init__(self, path_to_interpolated_case, parameter_name=None):
        self.systems = ['aeroelastic', 'aerodynamic', 'structural']
        self.path = path_to_interpolated_case

        self.parameter_name = parameter_name

        self.data = configobj.ConfigObj(self.path + 'pmor_summary.txt')

        self.cases = dict()
        for sys in self.systems:
            self.cases[sys] = SetOfCases()

        self.structural = self.cases['structural']
        self.aerodynamic = self.cases['aerodynamic']
        self.aeroelastic = self.cases['aeroelastic']

    def load_bulk_cases(self):

        for ith, case_number in enumerate(self.data):
            # item is the dict where the parameter_name is the key
            # single parameter cases only:
            param_name, param_value = list(self.data[case_number].items())[0]
            self.parameter_name = param_name
            param_value = float(param_value)

            for sys in self.systems:
                case = Case(param_value, sys, parameter_name=param_name, path_to_data=self.path)
                case.path_to_sys['eigs'] = self.path + '/stability/param_case{:02g}/{:s}/_eigenvalues.dat'.format(ith,
                                                                                                                  sys)
                case.path_to_sys[
                    'freqresp'] = self.path + '/frequencyresponse/param_case{:02g}/{:s}/freqresp.h5'.format(ith, sys)
                case.path_to_sys['ss'] = self.path + '/statespace/param_case{:02g}/{:s}/statespace.h5'.format(ith, sys)

                case.load_bode()
                case.load_ss()
                case.load_eigs()

                self.cases[sys].add_case(param_value, case)