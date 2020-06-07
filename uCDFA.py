'''
Third Project: DataFlow Analysis of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 06/06/2020.
'''

from collections import OrderedDict
from os.path import exists
import re

class uCDFA(object):
    def __init__(self, generator, block_constructor):
        self.generator = generator
        self.cfg = block_constructor
        
    def test(self, data, quiet=False):
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.code = []
        self.generator.generate(data)
        
        if not quiet:
            self.generator.print_code()
            print("\n")

        # Build CFG.
        if self.cfg.first_block:
            self.cfg.delete_cfg()
        self.cfg.build_cfg(self.generator.code)
        
        # Testing.
        print("Reaching Definitions:\n")
        self.reaching_definitions()
        print(self)
        
        self.cfg.clear_sets() # Wipes every block set
        
        print("Liveness Analysis:\n")
        self.liveness_analysis()
        print(self)
        self.cfg.print_blocks()
        
        if not quiet:
            self.cfg.print_code()
            
    def usedef_sets(self, blocks):
        # Create use/def tables
        defs = dict([(num,set()) for num in range(1,self.cfg.lineID+1)])
        uses = dict([(num,set()) for num in range(1,self.cfg.lineID+1)])
        
        # Maps which instruction USES which register (according to tuple position)
        use_map = {
            # Variables & Values
            ('elem'):[1,2],
            ('store','load','get'):[1],
            # Binary Operations
            ('add','sub','mul','div','mod'):[1,2], 
            # Cast Operations
            ('fptosi','sitofp'):[1],
            # Relational/Equality/Logical 
            ('lt','le','ge','gt','eq','ne','and','or','not'):[1,2],
            # Functions & Builtins
            ('param','print','return','cbranch', 'call'):[1] 
            }

        # Maps which instruction DEFINES which register (according to tuple position)
        def_map = {
            # Variables & Values
            ('elem'):[3],
            ('store','load','literal','get'):[2],
            # Binary Operations
            ('add','sub','mul','div','mod'):[3], 
            # Cast Operations
            ('fptosi','sitofp'):[1], 
            # Relational/Equality/Logical 
            ('lt','le','ge','gt','eq','ne','and','or','not'):[3],
            # Functions
            ('call'):[2]
            }

        def get_vars(inst, inst_map):
            '''Get variables mapped from instruction'''
            for keys,vals in inst_map.items():
                local_def = inst[0].split('_')[0]
                if local_def in keys:
                    try:    return [inst[i] for i in vals]
                    except: return []
            return []

        # Store Pointer is a special case (is a use of both temps)
        str_ptr = lambda x: bool(re.match(r'store\w+\*', x[0]))
        is_use = lambda x: [x[1],x[2]] if str_ptr(x) else get_vars(x, use_map)
        is_def = lambda x: [] if str_ptr(x) else get_vars(x, def_map)

        # Find use/def sets for each instruction
        for b in blocks:
            # Get use/def of each instruction in the block
            for num, inst in b.instructions.items():
                uses[num].update(is_use(inst))
                defs[num].update(is_def(inst))

        # Return usedef statement wise sets
        return uses,defs

    def reaching_definitions(self):
        # DFS in CFG
        dfs = self.cfg.dfs_sort()
        
        # Get gen/kill sets.
        self.rd_gen_kill(dfs)
        
        # All blocks in "changed" set.
        changed = set(dfs)
        
        # Main iteration
        while changed:
            b = changed.pop()
            
            # Calculate 'in' set from predecessors 'out' set.
            for p in b.pred:
                b.in_set.update(p.out_set)
            
            # Save old 'out'
            old_out = b.out_set.copy()
            
            # Update 'out'
            new = b.in_set - b.kill
            b.out_set = b.gen | new
            
            # Check changes to 'out'
            # All successors to the 'changed' set.
            if b.out_set != old_out:
                changed.update(b.succ)
        
        return dfs

    def rd_gen_kill(self, dfs):
        defs = dict()
        def_types = ('load', 'store', 'elem', 'literal', 'get', 
                     'add', 'sub', 'mul', 'div', 'mod', 
                     'le', 'lt', 'ge', 'gt', 'eq', 'ne',
                     'and', 'or', 'not',
                     'read')
        
        # Find all definitions and create gen set.
        for b in dfs:

            # Go through all instructions.
            for num,inst in b.instructions.items():
                call_return = (inst[0] == 'call') and (len(inst) == 3)
                local_def = (inst[0].split('_')[0] in def_types)
                
                if local_def or call_return:
                    
                    # Update DEFS.
                    if not defs.get(inst[-1], None):
                        defs[inst[-1]] = set([(b.ID,num)])
                    else:
                        defs[inst[-1]].update([(b.ID,num)])
        
        # Gen/Kill definitions
        for b in dfs:
                        
            # Go through all instructions.
            for num,inst in b.instructions.items():
                call_return = inst[0] == 'call' and len(inst)== 3
                local_def = inst[0].split('_')[0] in def_types
                
                if local_def or call_return:
                    curr_kill = defs[inst[-1]] - set([(b.ID,num)])
                    curr_gen  = set([(b.ID,num)]) | (b.gen - curr_kill)
                    b.kill.update(curr_kill)
                    b.gen.update(curr_gen)

    def liveness_analysis(self):
        # DFS in CFG
        dfs = list(reversed(self.cfg.dfs_sort()))
        
        ### INTRA BLOCK STAGE ###

        # Get genkill sets from usedef sets
        gen,kill = self.usedef_sets(dfs)

        # Unify block instructions gen/kill sets
        for b in dfs:
            # Reverse unify instructions gen/kill sets
            rev_insts = list(reversed(list(b.instructions)))
            for n in rev_insts[:-1]:
                b.gen = gen[n] | (b.gen - kill[n])
                b.kill.update(kill[n])

        # Keep individual inst genkill sets
        for b in dfs:
            for n in b.instructions:
                b.inst_gen[n] = gen[n]
                b.inst_kill[n] = kill[n]
        
        ### INTER BLOCK STAGE ###

        # All blocks in "changed" set.
        changed = set(dfs)
        
        # Reverse data flow iteration
        while changed:
            b = changed.pop()
            
            # Calculate out_set set from successors in_set.
            for succ in b.succ:
                b.out_set.update(succ.in_set)
            
            # Build new in_set from new out_set
            new_in = b.gen | (b.out_set - b.kill)
            
            # Check if there are changes in out_set
            if b.in_set != new_in:
                b.in_set = new_in
                changed.update(b.pred)

        return dfs

    def print_table(self, table, name):
        txt = f"{name}:\n"
        for k,v in table.items():
            txt += f"  {k:3}  {', '.join(map(str,v))}\n"
        print(txt)

    def __str__(self):
        dfs = self.cfg.dfs_sort()
        
        show = lambda x : x if x else '{}'

        txt = '\n'
        for b in dfs:
            txt += f"BLOCK {b.ID}:\n"
            txt += f"   IN: {show(b.in_set)}\n"
            txt += f"   GEN: {show(b.gen)}\n"
            txt += f"   KILL: {show(b.kill)}\n"
            txt += f"   OUT: {show(b.out_set)}\n"
            txt += '\n'
        return txt
