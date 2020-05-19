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
        
        # Build CFG.
        self.blocker.build_cfg(self.generator.code)
        
        # Testing... ?

    def reaching_definitions(self, cfg):
        # TODO: gen/kill
        
        # DFS in CFG
        dfs = cfg.dfs_sort()
        
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

    def liveness_analysis(self, cfg):
        pass
    
    def optimize(self):
        raise NotImplementedError
