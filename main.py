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
from parser import *
from os.path import exists

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

if __name__ == '__main__':

    while True:
        print("\nSend 'l' for lexer test, and 'p' for parser test ('q' to quit)")
        mode = input("Mode: ")

        if mode == 'l':
            while True: 
                try:
                    tokenizer = Lexer(print_error)
                    tokenizer.build()
                    
                    tokenizer.test(input("Filename or expression: "))
                    tokenizer.reset_line_num()
                except EOFError:
                    break
        elif mode == 'p':
            while True:
                try:
                    print('Coming soon!')
                    raise EOFError
                    #parser = uCParser()
                    #parser = yacc(write_tables=False)
                    
                    #parser.parse(input("Filename or expression for Parser: "))
                except EOFError:
                    break
        elif mode == 'q':
            break
        else:
            print('Invalid mode! Try again.')

