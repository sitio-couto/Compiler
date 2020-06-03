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
                # Check if there's a definition and if it's alive
                if var_def and not var_def <= alive:
                    b.remove_inst(n)
                    continue
                alive = b.inst_gen[n] | (alive - b.inst_kill[n])

class ConstantPropagation(Optimization):
    folding = {
        'add' : lambda self,a,b: a + b,
        'sub' : lambda self,a,b: a - b,
        'mul' : lambda self,a,b: a * b,
        'divi': lambda self,a,b: a // b,
        'divf': lambda self,a,b: a / b,
        'mod' : lambda self,a,b: a % b,
        'or'  : lambda self,a,b: int(a or b), # a | b?
        'and' : lambda self,a,b: int(a and b), # a & b?
        'gt'  : lambda self,a,b: int(a > b),
        'ge'  : lambda self,a,b: int(a >= b),
        'lt'  : lambda self,a,b: int(a < b),
        'le'  : lambda self,a,b: int(a <= b),
        'eq'  : lambda self,a,b: int(a == b),
        'ne'  : lambda self,a,b: int(a != b),
    }
    
    binary = ('add', 'sub', 'mul', 'div', 'mod',
              'le', 'lt', 'ge', 'gt', 'eq', 'ne',
              'and', 'or', 'not')
    
    memory = ('load', 'store')
    
    def optimize(self, cfg):
        const = dict()
        
        # Run dataflow analysis preparing block sets
        blocks = self.reaching_definitions(cfg)
        
        # Pass through all blocks.
        # TODO: Figure out the best solution for CONST
        for b in blocks:
            
            # Initialize const dictionary.
            # NAC: not a constant
            for inst in b:
                # TODO: ?? Maybe use RD here.
                target = inst[-1] # ?
                # Check DRAGON BOOK for algorithm.
                op = inst[0].split('_')[0]
                if op == 'literal':
                    if target not in const:
                        const[target] = inst[1]
                    elif const[target] != inst[1]:
                        const[target] = 'NAC'
                elif target in const:
                    const[target] = 'NAC'
            
            # Propagate/fold.
            for num, inst in b.instructions.items():
                op,ty = inst[0].split('_')
                
                # Binary operation: fold.
                if op in binary:
                    left,right = inst[1:3]
                    both_exist = all(x in const for x in (left,right))
                    both_const = all(const[x] != 'NAC' for x in (left,right))
                    
                    # If are both in 'const' dict and are not NAC, fold.
                    if both_exist and both_const:
                        l,r = const[left], const[right]
                        inst = self.fold_constants(inst, l, r)
                        b.instructions[num] = inst
                        op = inst[0].split('_')[0]
                
                # Memory operation: replace with literal
                elif op in memory:
                    src = inst[1]
                    if src in const and const[src] != 'NAC':
                        # Update inst
                        inst = ('literal_'+ty, const[src], inst[2])
                        b.instructions[num] = inst
                        op = inst[0].split('_')[0]
                
                target = inst[-1]
                if op == 'literal':
                    if target not in ctes:
                        # TODO: ?? 
                        continue
                    
        raise NotImplementedError

    def fold_constants(self, inst, left, right):
        ''' Fold constant: apply binary function to two constants. '''
        op, ty = inst[0].split('_')
        
        # Int or float division
        if op == 'div':
            op += 'i' if ty == 'int' else 'f'
        res = folding[op](left,right)
        return ('literal_'+ty, res, inst[-1])
