'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 07/04/2020.
'''

import uCType
from uCAST import NodeVisitor

class SymbolTable(object):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self):
        self.symtab = {}
    def lookup(self, a):
        return self.symtab.get(a)
    def add(self, a, v):
        self.symtab[a] = v

class CheckProgramVisitor(NodeVisitor):
    '''
    Program checking class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self):
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.symtab.add("int",uCType.int_type)
        self.symtab.add("float",uCType.float_type)
        self.symtab.add("char",uCType.char_type)
        self.symtab.add("bool",uCType.boolean_type)

    def visit_Program(self,node):
        # 1. Visit all of the statements
        # 2. Record the associated symbol table
        self.visit(node.program)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        # 2. Make sure the operation is supported
        # 3. Assign the result type
        self.visit(node.left)
        self.visit(node.right)
        node.type = node.left.type

    def visit_Assignment(self,node):
        ## 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.location)
        assert sym, "Assigning to unknown sym"
        ## 2. Check that the types match
        self.visit(node.value)
        assert sym.type == node.value.type, "Type mismatch in assignment"
