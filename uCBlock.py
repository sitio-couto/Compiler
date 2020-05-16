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

import re

class Block(object):
    def __init__(self):
        self.instructions = []   # Instructions in the block
        self.next_block = []   # Link to the next block

    def append(self,instr):
        self.instructions.append(instr)

    def concat(self,inst_list):
        self.instructions += inst_list

    def add_succ(self, block):
        self.next_block.append(block)

    def __iter__(self):
        return iter(self.instructions)

    def __str__(self):
        txt = "New Block:\n"
        for inst in self.instructions:
            txt += f"   {inst}\n"
        txt += '\n'
        for i,n in enumerate(self.next_block):
            txt += f"   Branch{i+1}: {n.instructions[0]}\n"

        return txt

class BasicBlock(Block):
    '''
    Class for a simple basic block.  Control flow unconditionally
    flows to the next block.
    '''
    pass

class IfBlock(Block):
    '''
    Class for a basic-block representing an if-else.  There are
    two branches to handle each possibility.
    '''
    def __init__(self):
        super(IfBlock,self).__init__()
        self.if_branch = None
        self.else_branch = None
        self.test = None

class WhileBlock(Block):
    def __init__(self):
        super(WhileBlock, self).__init__()
        self.test = None
        self.body = None

class BlockVisitor(object):
    '''
    Class for visiting basic blocks.  Define a subclass and define
    methods such as visit_BasicBlock or visit_IfBlock to implement
    custom processing (similar to ASTs).
    '''
    def visit(self,block):
        while isinstance(block,Block):
            name = "visit_%s" % type(block).__name__
            if hasattr(self,name):
                getattr(self,name)(block)
            block = block.next_block

#### Auxiliary Functions ####

targets = ['define','\d+'] # Possible branch targets
branches = ['return','call','jump','cbranch'] # Possible branching statements
is_target = lambda x : bool([True for t in targets if re.match(t, x)])
is_branch = lambda x : bool([True for b in branches if re.match(b, x)])

def get_leaders(code):
    leaders = set([0])
    for i in range(len(code)):
        prev = code[i-1][0]
        curr = code[i][0]
        if is_target(curr) or is_branch(prev):
            leaders = leaders.union([i])
    
    return sorted(list(leaders))

def link_blocks(blocks):
    jumps  = dict() # Block : Label
    labels = dict() # Label : Block

    for i,b in enumerate(blocks):
        first = b.instructions[0]
        last = b.instructions[-1]

        # Save Blocks Which Can be Jumped to
        if is_target(first[0]):
            if first[0]!="define":
                labels[first[0]] = b # get label
        
        # Save Which Blocks Jumps Where
        if is_branch(last[0]):
            if last[0]=="jump":
                jumps[b] = [last[1][1:]]
            if last[0]=="cbranch":
                jumps[b] = [last[2][1:], last[3][1:]]

        # Link Consecutive Blocks
        if not is_branch(last[0]) or last[0]=='call':
            b.add_succ(blocks[i+1])

    for b in jumps.keys():
        for label in jumps[b]:
            b.add_succ(labels[label])

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

    for b in blocks: print(b)

    return None

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