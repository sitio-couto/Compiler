'''
Compiler for the uC Language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020
'''

from lexer import uCLexer as Lexer
from parser import uCParser as Parser

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

if __name__ == '__main__':
    tokenizer = Lexer(print_error)
    tokenizer.build()

    while True: 
        try:
            tokenizer.test(input("Filename or expression: "))
            tokenizer.reset_line_num()
        except EOFError:
            break

