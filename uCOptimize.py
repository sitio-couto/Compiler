'''
Third Project: Optimization of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 07/06/2020.
'''

from os.path import exists
import re

class uCIROptimizer(object):
    def __init__(self, dfa):
        self.dfa = dfa
        self.cfg = dfa.cfg
        self.generator = dfa.cfg.generator
        self.code = []
    
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

        # Build CFG.
        self.cfg.build_cfg(self.generator.code)
        
        # Testing.
        self.optimize(quiet=quiet, 
                      dead=dead,
                      prop=prop, 
                      single=single)
    
    def show(self, cfg, buf=None):
        if cfg:
            if buf:
                self.cfg.view(f=buf.name)
            else:
                self.cfg.view()
        else:
            _str = ''
            for _code in self.code:
                _str += f"{_code}\n"
            buf.write(_str)
    
    def optimize(self, quiet, dead, prop, single):
        ''' This method will run iterativelly all optimizations.
            When executed, it assumes the generator has already 
            created the IR code. The method stops when there's 
            no new enchancements to be done in the code.
            Return:
             - list of tuples: Optimized IR code
        '''
        current_code = self.generator.code.copy()
        initial_size = len(current_code)
        new_code = None
        # TODO: Carefully think what needs to be done in the CFG
        # before running a consecutive optimization. As I see, 
        # it doesn't seem to need any special care in between 
        # optimizations, as long as each method ensures the 
        # cohesion of it's changes in the CFG:
        # - deadcode removes some lines, so there will non consecutive 
        #   linesIDs in the new CFG.
        if single:
            self.cfg.print_blocks()
            self.dfa.reaching_definitions()
            self.cfg.print_sets()
            self.show()
            input()

        while new_code != current_code:
            current_code = new_code

            if dead: self.deadcode_elimination()
            self.cfg.clear_sets()

            if prop: self.constant_propagation()
            self.cfg.clear_sets()
            
            self.cfg.clean_cfg()

            new_code = self.cfg.retrieve_ir()
            if single:
                self.cfg.print_blocks()
                self.show()
                input() # wait key
                
        # TODO: change root if empty? Just for view.
        self.clean_allocations()
        # self.cfg.check_cfg()
        new_code = self.cfg.retrieve_ir()

        if not quiet:
            print(f"Raw Size: {initial_size}")
            print(f"Opt Size: {len(new_code)}")
            self.cfg.print_code()
            self.show(True)

        self.code = new_code

    def deadcode_elimination(self):
        # Preparations for Deadcode elimination routine
        blocks = self.dfa.liveness_analysis()
        is_label = lambda str: bool(re.match(r'\d+',str))
        late_kill = []

        # Iterate through blocks eliminating code
        for b in blocks:
            # Reverse unify instructions gen/kill sets
            rev_insts = list(reversed(list(b.instructions)))
            alive = b.out_set.copy()
            for n in rev_insts:
                var_def = b.inst_kill[n]
                # Check if there's a definition and if it's alive
                if var_def and not var_def <= alive:
                    #print(f"Removing {n} : {b.instructions[n]}")
                    late_kill += b.remove_inst(n)
                    continue
                alive = b.inst_gen[n] | (alive - b.inst_kill[n])
        
        # Kill statements which cannot be removed in runtime
        for ID,line in late_kill: 
            self.cfg.index[ID].remove_inst(line)

        # Short circuit CFG
        for b in blocks:
            
            #### COLLAPSE BLOCK SCENARIOS ####
            
            # First Case: single path label-jump block (IR_in/test01.uc)
            single_path = (len(b.pred)==1 and len(b.succ)==1)
            label = b.first_inst() and is_label(b.first_inst()[0]) 
            jump = b.last_inst() and ('jump'==b.last_inst()[0])
            two_insts = (len(b.instructions)==2)
            if single_path and label and jump and two_insts:
                b.collapse_block()
                continue   

            # Second Case: single path label only block (IR_in/test07.uc)
            single_path = (len(b.pred)==1 and len(b.succ)==1)
            label_only  = (len(b.instructions)==1) and is_label(b.first_inst()[0])
            if single_path and label_only:
                b.collapse_block()       
                continue 

            #### COLLAPSE EDGES SCENARIOS ####

            # First Case: Single Unecessary jump-label Edge (IR_in/test01.uc)
            single_edge = (len(b.succ)==1) and (len(b.succ[0].pred)==1)
            jump = b.last_inst() and ('jump'==b.last_inst()[0])
            label = b.succ and b.succ[0].first_inst() and is_label(b.succ[0].first_inst()[0])
            if single_edge and jump and label:
                b.collapse_edge()
                continue

            # NOTE: I might be tripping here. Not sure if it actually happens
            # Second Case: Single Unecessary NOjump-label Edge (IR_in/test07.uc)
            single_edge = (len(b.succ)==1) and (len(b.succ[0].pred)==1)
            label = b.succ and is_label(b.succ[0].first_inst()[0])
            if single_edge and label:
                b.collapse_edge()
                continue
        
    def constant_propagation(self):
        binary = ('add', 'sub', 'mul', 'div', 'mod',
                  'le', 'lt', 'ge', 'gt', 'eq', 'ne',
                  'and', 'or', 'not')
        memory = ('load', 'store')
        other_defs = ('elem', 'get', 'read')
        
        # Run dataflow analysis preparing block sets
        blocks = self.dfa.reaching_definitions()

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
                try: op,ty = inst[0].split('_')
                except: op,ty = inst[0],None

                # Binary operation: fold.
                if op in binary:
                    left,right = inst[1:3]

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
                    if const.get(src,'NAC') != 'NAC' and ty[1] != '*':
                        # Update inst
                        inst = ('literal_'+ty, const[src], inst[2])
                        b.instructions[num] = inst
                        op = 'literal'
                        
                # Branch: check jump optimization and branch elimination.
                elif op == 'cbranch':
                    if const.get(inst[1],'NAC') != 'NAC':
                        # Test and replace.
                        live,dead = inst[2:] if const[inst[1]] else inst[:1:-1]
                        op = 'jump'
                        inst = (op, live)
                        b.instructions[num] = inst
                        for s in b.succ:
                            if s.first_inst()[0] in dead:       
                                #print(f"Removing Edge {b.ID}->{s.ID}")
                                b.succ.remove(s)
                                s.pred.remove(b)
                
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
        functions = []
        program = list(self.cfg.index.values())
        for func in self.cfg.first_block.succ:
            functions.append(self.cfg.dfs_sort(root=func)) 
        functions.append(program)

        # Fetch allocated temps and used temps
        for blocks in functions:
            allc_map = dict()
            allocs = set()
            temps = set()

            for b in blocks:
                for lin,inst in b.instructions.items():
                    if 'alloc' in inst[0]: 
                        allc_map[inst[-1]] = (b,lin)
                        allocs.add(inst[-1])
                    elif 'global' in inst[0]:
                        allc_map[inst[1]] = (b,lin)
                        allocs.add(inst[1])
                    else:
                        temps.update(set(re.findall(r'%\d+|@.str.\d+|@[a-zA-Z_][0-9a-zA-Z_]*', str(inst))))
        
            # Kill any allocated but unused temps
            to_kill = allocs - temps
            for allc in to_kill:
                b,lin = allc_map[allc]
                b.remove_inst(lin)
