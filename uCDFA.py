'''
Third Project: DataFlow Analysis of uCIR code.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 19/05/2020.
'''

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
        self.reaching_definitions(self.blocker.first_block)
        print(self)

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
        # TODO: PROBLEM! MULTIPLE FUNCTIONS AND SCOPE
        print(self.map_vars(dfs))

        defs = dict()
        def_types = ['load', 'elem', 'literal', 'get', 'add', 'sub', 'mul', 'div', 'mod', 'fptosi', 'sitofp']
        
        # Find all definitions and create gen set.
        for b in dfs:
            self.gen[b.ID] = set()
            
            # Go through all instructions.
            for num, inst in b.instructions.items():
                call_return = inst[0] == 'call' and len(inst)== 3
                local_def = inst[0].split('_')[0] in def_types
                
                # if inst[0].split('_')[0] == 'store':
                if local_def or call_return:
                    self.gen[b.ID].update([num])
                    
                    # Update DEFS.
                    if not defs.get(inst[-1], None):
                        defs[inst[-1]] = set([num])
                    else:
                        defs[inst[-1]].update([num])
        
        # Kill definitions
        for b in dfs:
            self.kill[b.ID] = set()
            
            # Go through all instructions.
            for inst in b:
                call_return = inst[0] == 'call' and len(inst)== 3
                local_def = inst[0].split('_')[0] in def_types
                
                # if inst[0].split('_')[0] == 'store':
                if local_def or call_return:
                    self.kill[b.ID].update(defs[inst[-1]])

    def liveness_analysis(self, cfg):
        pass
    
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
        
        
