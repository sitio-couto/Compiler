'''
Third Project: Optimization of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 02/06/2020.
'''

from uCDFA import Optimization
from os.path import exists

class DeadCodeElimination(Optimization):
    def optimize(self, cfg):
        # Run dataflow analysis preparing block sets
        blocks = self.liveness_analysis(cfg)

        # Iterate through blocks eliminating code
        for b in blocks:
            # Reverse unify instructions gen/kill sets
            rev_insts = list(reversed(list(b.instructions)))
            alive = b.out_set.copy()
            for n in rev_insts:
                var_def = b.inst_kill[n]
                if var_def and var_def in alive:
                    print("OK")
                    b.remove_inst(n)
                alive = b.inst_gen[n] | (alive - b.inst_kill[n])

class ConstantPropagation(Optimization):
    def optimize(self, cfg):
        raise NotImplementedError
