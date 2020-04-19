'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 19/04/2020.
'''

class uCType(object):
    '''
    Class that represents a type in the uC language.  Types 
    are declared as singleton instances of this type.
    '''
    def __init__(self, name, bin_ops=set(), un_ops=set(), rel_ops=set(), assign_ops=set(), cast_types=set()):
        '''
        You must implement yourself and figure out what to store.
        '''
        self.name = name
        self.bin_ops = bin_ops
        self.un_ops = un_ops
        self.rel_ops = rel_ops
        self.assign_ops = assign_ops
        self.cast_types = cast_types


int_type = uCType("int",
    bin_ops = {'+', '-', '*', '/', '%'},
    un_ops = {'+', '-', '--', '++', 'p--', 'p++', '*', '&'},
    rel_ops = {'<=', '<', '==', '!=', '>', '>='},
    assign_ops = {'+=', '-=', '*=', '/=', '%='},
    cast_types = {'int', 'float'}
    )
float_type = uCType("float",
    bin_ops = {'+', '-', '*', '/', '%'},
    un_ops = {'+', '-', '&', '*'},
    rel_ops = {'<=', '<', '==', '!=', '>', '>='},
    assign_ops = {'+=', '-=', '*=', '/=', '%='},
    cast_types = {'int', 'float'}
    )
char_type = uCType("char",
    un_ops = {'*', '&'},
    rel_ops = {'==', '!=', '&&', '||'},
    cast_types = {'char'}
    )
string_type = uCType("string",
    rel_ops = {'==', '!='}
    )
boolean_type = uCType("bool",
    un_ops = {'!', '*', '&'},
    rel_ops = {'&&', '||', '==', '!='}
    )
void_type = uCType("void",
    un_ops = {'*', '&'}
    )
array_type = uCType("array",
    un_ops = {'*', '&'},
    rel_ops = {'==', '!='}
    )
ptr_type = uCType('ptr',
    un_ops = {'*', '&', '++', 'p++', '--', 'p--'},
    rel_ops = {'==', '!='}
    )
