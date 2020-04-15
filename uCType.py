'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 15/04/2020.
'''

class uCType(object):
    '''
    Class that represents a type in the uC language.  Types 
    are declared as singleton instances of this type.
    '''
    def __init__(self, name, bin_ops=set(), un_ops=set(), cast_types=set()):
        '''
        You must implement yourself and figure out what to store.
        '''
        self.name = name
        self.bin_ops = bin_ops
        self.un_ops = un_ops
        self.cast_types = cast_types


int_type = uCType("int",
    set(('+', '-', '*', '/', '%',
         'LE', '<', 'EQ', 'UNEQ', '>', 'GE')),
    set(('+', '-')),
    set(('int', 'float', 'char'))
    )
float_type = uCType("float",
    set(('+', '-', '*', '/', '%',
         'LE', '<', 'EQ', 'UNEQ', '>', 'GE')),
    set(('+', '-')),
    set(('int', 'float', 'char'))
    )
string_type = uCType("string",
    set(('+',)),
    set(),
    set()
    )
char_type = uCType("char",
    set(('+',)),
    set(),
    set(('int', 'float', 'char'))
    )
boolean_type = uCType("bool",
    set(('AND', 'OR', 'EQ', 'UNEQ')),
    set(('!',)),
    set()
    )
