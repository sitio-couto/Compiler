'''
Third Project: DataFlow Analysis of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 21/05/2020.
'''

from collections import OrderedDict
from os.path import exists
import re

class Optimization(object):
    def __init__(self, generator, block_constructor):
        self.generator = generator
        self.blocker = block_constructor
        
        # Gen/Kill sets
        self.gen = dict()
        self.kill = dict()
        
        # In/Out sets
        self.in_set = dict()
        self.out_set = dict()

    def test(self, data, quiet=False):
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.generate(data)
        
        if not quiet:
            self.generator.print_code()
            print("\n")

        # Build CFG.
        self.blocker.build_cfg(self.generator.code)
        
        # Testing... ?
        # self.reaching_definitions(self.blocker.first_block)
        self.liveness_analysis(self.blocker.first_block)
        self.blocker.first_block.show_sets()

    def reaching_definitions(self, cfg):
        # DFS in CFG
        dfs = cfg.dfs_sort()
        
        # Get gen/kill sets.
        # TODO: needs to be here?
        self.rd_gen_kill(dfs)
        print(self)
        # Initialize
        for b in dfs:
            self.out_set[b.ID] = set()
        
        # All blocks in "changed" set.
        changed = set(dfs)
        
        # Main iteration
        while changed:
            b = changed.pop()
            
            # Empty 'in' set
            self.in_set[b.ID] = set()
            
            # Calculate 'in' set from predecessors 'out' set.
            for p in b.pred:
                self.in_set[b.ID].update(self.out_set[p.ID])
            
            # Save old 'out'
            old_out = self.out_set[b.ID].copy()
            
            # Update 'out'
            new = self.in_set[b.ID] - self.kill[b.ID]
            self.out_set[b.ID] = self.gen[b.ID].union(new)
            
            # Check changes to 'out'
            # All successors to the 'changed' set.
            if self.out_set[b.ID] != old_out:
                changed.update(b.succ)

    def map_vars(self, blocks):
        ''' Given a list of basic blocks, maps which variables are 
            referenced by which statements (identified by lineID).
            Param:
                blocks - List of the code's basic blocks
            Return:
                table - dictionary where keys are the vars in the code and
                    values are the lineIDs which reference such variable
        '''
        keys = self.blocker.update_vars()
        vals = [set() for i in range(len(keys))]
        table = dict(zip(keys,vals))
        for b in blocks:
            for lin,inst in b.instructions.items():
                for var in re.findall(r'%\d+', str(inst)):
                    table[var].add(lin)
        return table


    def rd_gen_kill(self, dfs):
        # TODO: any missing def type?
        defs = dict()
        def_types = ['load', 'read', 'elem', 'literal', 'get', 'add', 'sub', 'mul', 'div', 'mod', 'fptosi', 'sitofp']
        
        # Find all definitions and create gen set.
        for b in dfs:
            
            # Go through all instructions.
            for num, inst in b.instructions.items():
                call_return = inst[0] == 'call' and len(inst)== 3
                local_def = inst[0].split('_')[0] in def_types
                
                if local_def or call_return:
                    
                    # Update DEFS.
                    if not defs.get(inst[-1], None):
                        defs[inst[-1]] = set([num])
                    else:
                        defs[inst[-1]].update([num])
        
        # Gen/Kill definitions
        for b in dfs:
            self.gen[b.ID] = set()
            self.kill[b.ID] = set()
            
            # Go through all instructions.
            for num, inst in b.instructions.items():
                call_return = inst[0] == 'call' and len(inst)== 3
                local_def = inst[0].split('_')[0] in def_types
                
                if local_def or call_return:
                    curr_kill = defs[inst[-1]] - set([num])
                    curr_gen  = set([num]).union(self.gen[b.ID] - curr_kill)
                    self.kill[b.ID].update(curr_kill)
                    self.gen[b.ID].update(curr_gen)

    def la_gen_kill(self, dfs):
        # Create use/def tables
        defs = dict([(num,set()) for num in range(1,dfs[0].__lineID__+1)])
        uses = dict([(num,set()) for num in range(1,dfs[0].__lineID__+1)])

        # Maps which instruction DEFINES which register (according to tuple position)
        use_map = {
            # Variables & Values
            ('store','elem'):[1,2],
            ('load','get'):[1],
            # Binary Operations
            ('add','sub','mul','div','mod'):[1,2], 
            # Cast Operations
            ('fptosi','sitofp'):[1],
            # Relational/Equality/Logical 
            ('lt','le','ge','gt','eq','ne','and','or','not'):[1,2],
            # Functions & Builtins
            ('param','print','return'):[1] 
            }
        
        # Maps which instruction DEFINES which register (according to tuple position)
        def_map = {
            # Variables & Values
            ('elem','literal'):[3],
            ('load','get'):[2],
            # Binary Operations
            ('add','sub','mul','div','mod'):[3], 
            # Cast Operations
            ('fptosi','sitofp'):[1], # TODO: is it a use and def simultaneously?
            # Relational/Equality/Logical 
            ('lt','le','ge','gt','eq','ne','and','or','not'):[3],
            # Functions
            ('call','print'):[2]
            }

        def get_vars(inst, inst_map):
            '''Get variables mapped from instruction'''
            for keys,vals in inst_map.items():
                local_def = inst[0].split('_')[0]
                if local_def in keys:
                    if len(inst) <= max(vals): return [] # for optional registers (return,)
                    else: return [inst[i] for i in vals]
            return []

        is_use = lambda x: get_vars(x, use_map)
        is_def = lambda x: get_vars(x, def_map)

        # Find use/def sets for each instruction
        for b in dfs:
            # Get use/def of each instruction in the block
            for num, inst in b.instructions.items():
                uses[num].update(is_use(inst))
                defs[num].update(is_def(inst)) 

        # self.print_table(uses, "USES:")
        # self.print_table(defs, "DEFS:")

        gen = uses
        kill = defs
        # Unify block instructions gen/kill sets
        for b in dfs:
            # Reverse unify instructions gen/kill sets
            rev_insts = list(reversed(list(b.instructions)))
            for n in rev_insts[:-1]:
                b.gen = gen[n].union(b.gen - kill[n])
                b.kill.update(kill[n])
    
    def liveness_analysis(self, cfg):
        # DFS in CFG
        dfs = list(reversed(cfg.dfs_sort()))
        
        # Get gen/kill sets.
        self.la_gen_kill(dfs)
        
        # All blocks in "changed" set.
        changed = set(dfs)
        
        # Reverse data flow iteration
        while changed:
            b = changed.pop()

            # Calculate out_set set from successors in_set.
            for succ in b.succ:
                b.out_set.update(succ.in_set)
            
            # Build new in_set from new out_set
            new_in = b.gen.union(b.out_set - b.kill)
            
            # Check if there are changes in out_set
            if b.in_set != new_in:
                b.in_set = new_in
                changed.update(b.pred)

    def print_table(self, table, name):
        txt = f"{name}:\n"
        for k,v in table.items():
            txt += f"  {k:3}  {', '.join(map(str,v))}\n"
        print(txt)
    
    def optimize(self):
        raise NotImplementedError

    def __str__(self):
        IDs = [b.ID for b in self.blocker.first_block.dfs_sort()]
        
        show = lambda x,i : x[i] if x.get(i,None) else '{}'

        txt = ''
        for idx in IDs:
            txt += f"BLOCK {idx}:\n"
            txt += f"   IN: {show(self.in_set,idx)}\n"
            txt += f"   GEN: {show(self.gen,idx)}\n"
            txt += f"   KILL: {show(self.kill,idx)}\n"
            txt += f"   OUT: {show(self.out_set,idx)}\n"
            txt += '\n'
        return txt
