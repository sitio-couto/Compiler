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

from uCBlock import uCCFG
from uCDFA import uCDFA
from os.path import exists


class Optimizer(object):
    def __init__(self, generator):
        self.generator = generator
        self.cfg = uCCFG(generator)
        self.dfa = uCDFA(generator, self.cfg)

    def optimize(self, dead=True, fold=True, prop=True, single=False):
        ''' This method will run iterativelly all optimizations.
            When executed, it assumes the generator has already 
            created the IR code. The method stops when there's 
            no new enchancements to be done in the code.
            Return:
             - list of tuples: Optimized IR code
        '''
        # Build CFG.
        self.cfg.build_cfg(self.generator.code)
        current_code = self.generator.code.copy()
        new_code = None
        print(f"Raw Size: {len(current_code)}")
        # TODO: Carefully think what needs to be done in the CFG
        # before running a consecutive optimization. As I see, 
        # it doesn't seem to need any special care in between 
        # optimizations, as long as each method ensures the 
        # cohesion of it's changes in the CFG:
        # - deadcode removes some lines, so there will non consecutive 
        #   linesIDs in the new CFG.
        while new_code != current_code:
            current_code = new_code

            if dead: self.deadcode_elimination()

            new_code = self.cfg.retrieve_ir()
            if single: break

        print(f"Opt Size: {len(new_code)}")
        list(map(print, new_code))
        return new_code

    def deadcode_elimination(self):
        # Run dataflow analysis preparing block sets
        blocks = self.dfa.liveness_analysis()

        # Iterate through blocks eliminating code
        for b in blocks:
            # Reverse unify instructions gen/kill sets
            rev_insts = list(reversed(list(b.instructions)))
            alive = b.out_set.copy()
            for n in rev_insts:
                var_def = b.inst_kill[n]
                # Check if there's a definition and if it's alive
                if var_def and not var_def <= alive:
                    print(f"Removing {n} : {b.instructions[n]}")
                    b.remove_inst(n)
                    continue
                alive = b.inst_gen[n] | (alive - b.inst_kill[n])
        self.cfg.view()
    
    def constant_opt(self, cfg):
        binary = ('add', 'sub', 'mul', 'div', 'mod',
                  'le', 'lt', 'ge', 'gt', 'eq', 'ne',
                  'and', 'or', 'not')
        memory = ('load', 'store')
        const = dict()
        
        # Run dataflow analysis preparing block sets
        blocks = self.dfa.reaching_definitions(cfg)
        
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

        op, ty = inst[0].split('_')
        
        # Int or float division
        if op == 'div':
            op += 'i' if ty == 'int' else 'f'
        res = folding[op](left,right)
        return ('literal_'+ty, res, inst[-1])