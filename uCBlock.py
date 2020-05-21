'''
Third Project: Basic Block organization of uCIR code.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

REFERENCES:
    https://en.wikipedia.org/wiki/Basic_block
    https://stackoverflow.com/questions/31305423/how-do-you-include-subroutine-calls-in-a-control-flow-graph

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 19/05/2020.
'''

from collections import OrderedDict
from os.path import exists
import re

class Block(object):
    __blockID__ = 0
    __lineID__ = 0
    __index__ = dict()

    def __init__(self):
        Block.__blockID__ += 1
        self.ID = Block.__blockID__          # Integer to identify block
        self.instructions = OrderedDict()    # Instructions in the block
        self.pred = []                       # Link to parent blocks
        self.succ = []                       # Link to the next block
        Block.__index__[self.ID] = self

    def append(self,instr):
        Block.__lineID__ += 1
        key = Block.__lineID__
        self.instructions[key] = instr

    def concat(self,inst_list):
        base = Block.__lineID__ + 1
        top = base + len(inst_list)
        Block.__lineID__ += len(inst_list)
        new = zip(range(base, top), inst_list)
        self.instructions.update(new)

    def add_pred(self, block):
        self.pred.append(block)

    def add_succ(self, block):
        self.succ.append(block)

    def get_inst(self, idx):
        insts = list(self.instructions.values())
        return insts[idx]

    def __iter__(self):
        return iter(self.instructions.values())

    def dfs_sort(self, visits=[]):
        if self not in visits:
            visits.append(self)
            for b in self.succ:
                visits = b.dfs_sort(visits=visits)
        return visits

    def delete(self):
        for s in self.succ:
            s.pred.remove(self)
        for p in self.pred:
            p.succ.remove(self)
        del Block.__index__[self.ID]

    def __str__(self):
        txt = f"BLOCK {self.ID}:\n"
        
        txt += f"   Preds:"
        for b in self.pred:
            txt += f" {b.ID}"
        txt += '\n\n'
        
        for lin,inst in self.instructions.items():
            txt += f"   {lin} : {inst}\n"
        txt += '\n'
        txt += f"   Succs:"
        
        for b in self.succ:
            txt += f" {b.ID}"
        txt += "\n"

        return txt

class BasicBlock(Block):
    '''
    Class for a simple basic block.  Control flow unconditionally
    flows to the next block.
    '''
    pass

class uCCFG(object):
    def __init__(self, generator):
        self.generator = generator
        self.first_block = None
        
        self.targets = [r'define',r'\d+']              # Possible branch targets
        self.branches = [r'return',r'jump',r'cbranch'] # Possible branching statements

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
        self.build_cfg(self.generator.code)
        
        self.print_blocks()

    def print_blocks(self):
        dfs = self.first_block.dfs_sort()
        ids = []
        for block in dfs:
            print(block)
            ids.append(block.ID)
        
        print('DFS Sequence: ', ids)

    # Lambda functions
    is_target = lambda self, x : bool([True for t in self.targets if re.match(t, x)])
    is_branch = lambda self, x : bool([True for b in self.branches if re.match(b, x)])

    ##### Building the CFG ####
    
    def build_cfg(self, code):
        ''' Given the IR code as a list of tuples, build a CFG.
            The CFG considers subroutines as independent subtrees.
            If there are no global variables, the global block is empty.
            Params:
                code - List of tuples where each tuple is a IR statement
            Return:
                BasicBlock - Return the global basic block (links to every subroutine) 
        '''
        # Get leaders
        leads = self.get_leaders(code)
        blocks = []

        # Create blocks
        for s,t in zip(leads, leads[1:]+[len(code)]):
            new_block = BasicBlock()
            new_block.concat(code[s:t])
            blocks.append(new_block)

        # Split blocks by function
        glob,funcs = self.isolate_functions(blocks) 

        # Link Blocks
        for blocks in funcs: 
            self.link_blocks(glob, blocks)
        self.first_block = glob
                
        # Remove unreachable blocks
        self.clean_cfg()

    def update_vars(self):
        aux = set()
        blocks = list(Block.__index__.values())
        for b in blocks:
            for inst in b.instructions.values():
                aux.update(re.findall(r'%\d+', str(inst)))
        return sorted(list(aux), key=lambda x: int(x[1:]))
    
    def get_leaders(self, code):
        ''' Given a list with IR code instructions, find all leaders indexes.
            Params:
                code - List of tupes where each element is a IR instruction
            Return:
                List - indexes of the leades in the code
        '''
        leaders = set([0])
        for i in range(len(code)):
            prev = code[i-1][0]
            curr = code[i][0]
            if self.is_target(curr) or self.is_branch(prev):
                leaders = leaders.union([i])
        
        return sorted(list(leaders))

    def isolate_functions(self, blocks):
        ''' Given a list of basic blocks, group blocks by enclosing function.
            Functions are sequential instructions in the IR, so we take the 
            blocks and group then until a new 'define' statement is found, or
            until we reach the end of the code.
            Params:
                Blocks - List of unconnected BasicBlocks 
        '''
        # Create the program entry block
        entry = blocks[0].get_inst(0)[0]
        if 'global' in entry:
            globs = blocks.pop(0)    # Separe globals block
        else:
            globs = BasicBlock() # Create dummy block

        aux = []
        funcs = [] # List of lists (each element is the blocks of a function)
        
        # Group blocks by functions
        for b in blocks:
            inst = b.get_inst(0)[0]
            if inst=='define': # Reset every time a define is found
                if aux: funcs.append(aux)
                aux = [b]
            else:
                aux.append(b)
        if aux: funcs.append(aux) # Append rest if eof

        return globs,funcs

    def link_blocks(self, globs, blocks):
        ''' Given the globals block and a list of basic blocks, link them 
            creating a CFG. Subroutines are handled separatedly.
            Every subroutine is connected to the globals block.
            Params:
                globs - Basic block containing global vars (program entrypoint)
                Blocks - List of unconnected BasicBlocks of a subroutine 
        '''
        jumps  = dict() # Block : Label
        labels = dict() # Label : Block

        # Define blocks edges (jumps and labels)
        for i,b in enumerate(blocks):
            jumps[b] = [] # Make some ops easier
            first = b.get_inst(0)
            last = b.get_inst(-1)

            # Save blocks that can be jumped to
            if self.is_target(first[0]):
                # Either a define or a label
                if first[0]=='define':
                    globs.add_succ(b) # Link header to function
                    b.add_pred(globs)
                else:
                    labels[first[0]] = b
            
            # Save where the block jumps to
            if self.is_branch(last[0]):
                if last[0]=="jump":
                    jumps[b] += [last[1][1:]]
                if last[0]=="cbranch":
                    jumps[b] += [last[2][1:], last[3][1:]]

            # Link Consecutive Blocks
            else:
                b.add_succ(blocks[i+1])
                blocks[i+1].add_pred(b)

        # Link successors and predecessors
        for pred in jumps:
            for label in jumps[pred]:
                succ = labels[label]
                pred.add_succ(succ)
                succ.add_pred(pred)

        return 

    def clean_cfg(self):
        ''' Uses a DFS search stargin from the global block to check
            which blocks are unreacheable, and removes then from the instance.
        '''
        # Removing unreachable blocks
        all_ids = list(range(1, 1 + Block.__blockID__))
        reachable = [b.ID for b in self.first_block.dfs_sort()]
        dead = set(all_ids)-set(reachable)
        if dead: print(f"\nRemoving deadblocks: {dead}\n")
        for idx in dead:
            block = Block.__index__[idx]
            block.delete()
