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

import re

class Block(object):
    __count__ = 0

    def __init__(self):
        Block.__count__ += 1
        self.ID = Block.__count__
        self.instructions = []   # Instructions in the block
        self.pred = [] # Link to parent blocks
        self.succ = [] # Link to the next block

    def append(self,instr):
        self.instructions.append(instr)

    def concat(self,inst_list):
        self.instructions += inst_list

    def add_pred(self, block):
        self.pred.append(block)

    def add_succ(self, block):
        self.succ.append(block)

    def __iter__(self):
        return iter(self.instructions)

    def dfs_search(self, func):
        pass

    def __str__(self):
        txt = f"Block {self.ID}:\n"
        for i,b in enumerate(self.pred):
            txt += f"   Pred{i+1}: {b.ID}\n"
        txt += '\n'
        for inst in self.instructions:
            txt += f"   {inst}\n"
        txt += '\n'
        for i,b in enumerate(self.succ):
            txt += f"   Succ{i+1}: {b.ID}\n"

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

targets = ['define','\d+'] # Possible branch targets
# NOTE: not including 'call'
branches = ['return','jump','cbranch'] # Possible branching statements
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

def link_blocks(blocks):
    ''' Given a list of basic blocks, link then creating a CFG.
        Subroutines are handled as ambigous statements.
        Every subroutine is connected to the header block (global statements).
        Params:
            Blocks - List of unconnected BasicBlocks 
    '''
    jumps  = dict() # Block : Label
    labels = dict() # Label : Block

    # Separate global variables from funcs
    glob_vars = blocks[0]
    code_blocks = blocks[1:]

    # Define blocks edges (jumps and labels)
    for i,b in enumerate(code_blocks):
        first = b.instructions[0]
        last = b.instructions[-1]

        # Save blocks that can be jumped to
        if is_target(first[0]):
            # Either a define or a label
            if first[0]=='define':
                glob_vars.add_succ(b) # Link header to function
                b.add_pred(glob_vars)
            else:
                labels[first[0]] = b
        
        # Save where the block jumps to
        if is_branch(last[0]):
            if last[0]=="jump":
                jumps[b] = [last[1][1:]]
            if last[0]=="cbranch":
                jumps[b] = [last[2][1:], last[3][1:]]

        # Link Consecutive Blocks
        # NOTE: Seems like it's never used for our code
        if not is_branch(last[0]):
            b.add_succ(code_blocks[i+1])

    # Link successors and predecessors
    for pred in jumps.keys():
        for label in jumps[pred]:
            succ = labels[label]
            pred.add_succ(succ)
            succ.add_pred(pred)

    return 

def build_cfg(code):
    # Get leaders
    leads = get_leaders(code)
    blocks = []

    # Create blocks
    for s,t in zip(leads, leads[1:]+[len(code)]):
        new_block = BasicBlock()
        new_block.concat(code[s:t])
        blocks.append(new_block)
    
    # Link Blocks
    link_blocks(blocks)
    
    list(map(print, blocks))
    return blocks[0]

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
    