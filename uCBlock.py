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

class Block(object):
    def __init__(self):
        self.instructions = []   # Instructions in the block
        self.next_block =None    # Link to the next block

    def append(self,instr):
        self.instructions.append(instr)

    def __iter__(self):
        return iter(self.instructions)

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
