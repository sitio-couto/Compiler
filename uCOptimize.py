'''
Third Project: Optimization of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 04/06/2020.
'''

import re
from uCBlock import uCCFG
from uCDFA import uCDFA
from os.path import exists

class Optimizer(object):
    def __init__(self, generator, cfg=None, dfa=None):
        self.generator = generator
        self.cfg = uCCFG(generator) if not cfg else cfg
        self.dfa = uCDFA(generator, self.cfg) if not dfa else dfa
    
    def test(self, data, quiet=False, dead=True, prop=True, single=False):
        # Generating code
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.code = []
        self.generator.generate(data)
        
        # Pre-testing steps
        if not quiet:
            self.generator.print_code()
            print("\n")

        # Testing.
        self.optimize(quiet=quiet, 
                      dead=dead,
                      prop=prop, 
                      single=single)
        
        # Post processing
        if not quiet:
            self.cfg.print_blocks()
            self.cfg.print_code()
        
        return self.cfg.retrieve_ir()

    def optimize(self, quiet, dead, prop, single):
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
        initial_size = len(current_code)
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
            self.cfg.clear_sets()

            if prop: self.constant_propagation()
            self.cfg.clear_sets()

            new_code = self.cfg.retrieve_ir()
            if single: 
                # print stuff
                input() # wait key

        self.clean_allocations()

        if not quiet:
            print(f"Raw Size: {initial_size}")
            print(f"Opt Size: {len(new_code)}")
            self.cfg.view()

        return self.cfg.retrieve_ir()

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

        # Short circuit CFG
        for b in blocks:
            # First Case: Relax Edges
            single_edge = (len(b.pred)==1) and (len(b.pred[0].succ)==1)
            not_root = (self.cfg.first_block not in b.pred)
            if single_edge and not_root:
                self.cfg.collapse_edge(b.pred[0], b.pred[0].succ[0])                

            # allow = [r'\d+','jump']
            # expendable = True
            # for _,inst in b.instructions.items():
            #     if 'alloc' in inst[0]: 
            #         allc_map[inst[-1]] = (b,lin)
            #         allocs.add(inst[-1])
            #     else:
            #         temps.update(set(re.findall(r'%\d+', str(inst))))

    def constant_propagation(self):
        binary = ('add', 'sub', 'mul', 'div', 'mod',
                  'le', 'lt', 'ge', 'gt', 'eq', 'ne',
                  'and', 'or', 'not')
        memory = ('load', 'store')
        other_defs = ('elem', 'get', 'read')
        
        # Run dataflow analysis preparing block sets
        blocks = self.dfa.reaching_definitions(self.cfg)
        
        self.cfg.print_blocks()

        # Pass through all blocks.
        for b in blocks:
            const = dict()
            
            # Initialize const dictionary.
            # NAC: not a constant
            for in_bl,num in b.in_set:
                
                # Get instruction target and op
                inst_block = b.meta.index[in_bl]
                inst = inst_block.instructions[num]
                target = inst[-1]
                op = inst[0].split('_')[0]
                
                # Const dict.
                if op == 'literal':
                    if target not in const:
                        const[target] = inst[1]
                    elif const[target] != inst[1]:
                        const[target] = 'NAC'
                else:
                    const[target] = 'NAC'
            
            # Propagate/fold.
            for num, inst in b.instructions.items():
                if 'define' in inst[0]: continue
                op,ty = inst[0].split('_')
                
                # Binary operation: fold.
                if op in binary:
                    left,right = inst[1:3]
                    # both_exist = all(x in const for x in (left,right))
                    # NOTE: if doesnt exists, return NAC and, therefore, False
                    valid = all(const.get(x,'NAC') != 'NAC' for x in (left,right))
                    
                    # If are both in 'const' dict and are not NAC, fold.
                    if valid:
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
                        
                # Branch: check jump optimization and branch elimination.
                elif op == 'cbranch':
                    if inst[1] in const and const[inst[1]] != 'NAC':
                        
                        # Test and replace.
                        result = inst[3] if not inst[1] else inst[2]
                        op = 'jump'
                        inst = (op, result)
                        b.instructions[num] = inst

                        # TODO: update blocks (pred of other block, succ of this block)
                        # TODO: short_circuit? Maybe do in in dead code elimination.
                
                # Update const dictionary within block
                target = inst[-1]
                if op == 'literal':
                    if target not in const:
                        const[target] = inst[1]
                    elif const[target] != inst[1]:
                        const[target] = 'NAC'
                elif op in (binary+memory+other_defs):
                    if target in const:
                        const[target] = 'NAC'

    def fold_constants(self, inst, left, right):
        ''' Fold constant: apply binary function to two constants. '''
        folding = {
            'add' : lambda a,b: a + b,
            'sub' : lambda a,b: a - b,
            'mul' : lambda a,b: a * b,
            'divi': lambda a,b: a // b,
            'divf': lambda a,b: a / b,
            'mod' : lambda a,b: a % b,
            'or'  : lambda a,b: a | b,
            'and' : lambda a,b: a & b,
            'gt'  : lambda a,b: int(a > b),
            'ge'  : lambda a,b: int(a >= b),
            'lt'  : lambda a,b: int(a < b),
            'le'  : lambda a,b: int(a <= b),
            'eq'  : lambda a,b: int(a == b),
            'ne'  : lambda a,b: int(a != b)
        }

        op, ty = inst[0].split('_')
        
        # Int or float division
        if op == 'div':
            op += 'i' if ty == 'int' else 'f'
        res = folding[op](left,right)
        return ('literal_'+ty, res, inst[-1])

    # NOTE: executing this every time deadcode was called
    # would create a unnecessary overhead. Only call after
    # all optimizations are done
    def clean_allocations(self):
        '''Eliminates any unused temporary allocations'''
        allc_map = dict()
        allocs = set()
        temps = set()
        
        # Fetch allocated temps and used temps
        for b in self.cfg.index.values():
            for lin,inst in b.instructions.items():
                if 'alloc' in inst[0]: 
                    allc_map[inst[-1]] = (b,lin)
                    allocs.add(inst[-1])
                else:
                    temps.update(set(re.findall(r'%\d+', str(inst))))
        
        # Kill any allocated but unused temps
        to_kill = allocs - temps
        for allc in to_kill:
            b,lin = allc_map[allc]
            b.remove_inst(lin)

