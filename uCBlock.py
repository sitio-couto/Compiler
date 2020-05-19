'''
Third Project: Basic Block organization of uCIR code.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 14/05/2020.
'''

# HOW TO RUN:
# get IR: python tests/unittest/test_uCIR.py
# pass IR: python tests/IR_in/test.in
# REFERENCES:
# https://en.wikipedia.org/wiki/Basic_block
# https://stackoverflow.com/questions/31305423/how-do-you-include-subroutine-calls-in-a-control-flow-graph

from collections import OrderedDict
import re

class Block(object):
    __blockID__ = 0
    __lineID__ = 0

    def __init__(self):
        Block.__blockID__ += 1
        self.ID = Block.__blockID__   # Iteger to identify block
        self.instructions = OrderedDict()    # Instructions in the block
        self.pred = []              # Link to parent blocks
        self.succ = []              # Link to the next block

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
        if self.ID not in visits:
            visits.append(self.ID)
            for b in self.succ:
                visits = b.dfs_sort(visits=visits)
        return visits
        
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

# class IfBlock(Block):
#     '''
#     Class for a basic-block representing an if-else.  There are
#     two branches to handle each possibility.
#     '''
#     def __init__(self):
#         super(IfBlock,self).__init__()
#         self.if_branch = None
#         self.else_branch = None
#         self.test = None

# class WhileBlock(Block):
#     def __init__(self):
#         super(WhileBlock, self).__init__()
#         self.test = None
#         self.body = None

# class BlockVisitor(object):
#     '''
#     Class for visiting basic blocks.  Define a subclass and define
#     methods such as visit_BasicBlock or visit_IfBlock to implement
#     custom processing (similar to ASTs).
#     '''
#     def visit(self,block):
#         while isinstance(block,Block):
#             name = "visit_%s" % type(block).__name__
#             if hasattr(self,name):
#                 getattr(self,name)(block)
#             block = block.next_block

#### Auxiliary Functions ####

targets = [r'define',r'\d+'] # Possible branch targets
branches = [r'return',r'jump',r'cbranch'] # Possible branching statements
is_target = lambda x : bool([True for t in targets if re.match(t, x)])
is_branch = lambda x : bool([True for b in branches if re.match(b, x)])

##### Building the CFG ####

def get_leaders(code):
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
        if is_target(curr) or is_branch(prev):
            leaders = leaders.union([i])
    
    return sorted(list(leaders))

def isolate_functions(blocks):
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

def link_blocks(globs, blocks):
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
        if is_target(first[0]):
            # Either a define or a label
            if first[0]=='define':
                globs.add_succ(b) # Link header to function
                b.add_pred(globs)
            else:
                labels[first[0]] = b
        
        # Save where the block jumps to
        if is_branch(last[0]):
            if last[0]=="jump":
                jumps[b] += [last[1][1:]]
            if last[0]=="cbranch":
                jumps[b] += [last[2][1:], last[3][1:]]

        # Link Consecutive Blocks
        if not is_branch(last[0]):
            b.add_succ(blocks[i+1])
            blocks[i+1].add_pred(b)

    # Link successors and predecessors
    for pred in jumps:
        for label in jumps[pred]:
            succ = labels[label]
            pred.add_succ(succ)
            succ.add_pred(pred)

    return 

def build_cfg(code):
    ''' Given the IR code as a list of tuples, build a CFG.
        The CFG considers subroutines as independent subtrees.
        If there are no global variables, the global block is empty.
        Params:
            code - List of tuples where each tuple is a IR statement
        Return:
            BasicBlock - Return the global basic block (links to every subroutine) 
    '''
    # Get leaders
    leads = get_leaders(code)
    blocks = []

    # Create blocks
    for s,t in zip(leads, leads[1:]+[len(code)]):
        new_block = BasicBlock()
        new_block.concat(code[s:t])
        blocks.append(new_block)

    # Split blocks by function
    glob,funcs = isolate_functions(blocks) 

    # Link Blocks
    for blocks in funcs: 
        link_blocks(glob, blocks)
    
    ### DEBBUGING
    print(glob)
    for blocks in funcs:
        list(map(print, blocks))

    print(glob.dfs_sort())

    return glob

### TESTING STUB ###

from sys import argv
from os.path import exists
from ast import literal_eval

if __name__ == "__main__":
    # Scan and parse
    if exists(argv[1]):
        with open(argv[1], 'r') as content_file :
            code = content_file.readlines()
        code = list(map(literal_eval,code))

    cfg = build_cfg(code)
    