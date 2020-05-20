'''
Compiler for the uC Language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020
'''

from uCLexer import uCLexer as Lexer
from uCParser import uCParser as Parser
from uCSemantic import uCSemanticCheck as Semantic
from uCGenerate import uCIRGenerate as Generator
from uCInterpreter import uCIRInterpreter as Interpreter
from uCBlock import uCCFG as CFG
from uCDFA import Optimization as opt
from os.path import exists
from sys import argv

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

if __name__ == '__main__':
    
    # Building lexer
    tokenizer = Lexer(print_error)
    tokenizer.build()
        
    # Building parser
    parser = Parser(tokenizer)
    parser.build()

    semantic = Semantic(parser)
    generator = Generator(semantic)
    
    # Interpret or optimize IR.
    interpreter = Interpreter(generator)
    cfg = CFG(generator)
    dfa = opt(generator, CFG(generator))
    
    while True:
        # quick testing input file
        if len(argv) > 1 :
            for i in range(1,len(argv)):
                dfa.test(argv[i], False)
            exit(1)

        print('''\nType one of the following keys:
        l - for lexer test 
        p - for parser test 
        s - for semantic test 
        g - for IR Generation test 
        i - for interpreter test 
        b - for basic block test
        d - for dataflow analysis test
        q - to quit
        ''')
        mode = input("Mode: ")

        if mode == 'l':
            while True: 
                try:
                    tokenizer.reset_line_num()
                    tokenizer.test(input("Filename or expression for Lexer: "))
                except EOFError:
                    break
        elif mode == 'p':
            while True:
                try:
                    parser.test(input("Filename or expression for Parser: "))
                except EOFError:
                    break
        elif mode == 's':
            while True:
                try:
                    semantic.test(input("Filename or expression for Semantic Check: "), True)
                except EOFError:
                    break
        elif mode == 'g':
            while True:
                try:
                    generator.test(input("Filename or expression for IR Generation: "), False)
                except EOFError:
                    break
        elif mode == 'i':
            while True:
                try:
                    interpreter.test(input("Filename or expression to run: "), True)
                except EOFError:
                    break
        elif mode == 'b':
            while True:
                try:
                    cfg.test(input("Filename or expression to run: "), True)
                except EOFError:
                    break
        elif mode == 'd':
            while True:
                try:
                    dfa.test(input("Filename or expression to run: "), True)
                except EOFError:
                    break
        elif mode == 'q':
            break
        else:
            print('Invalid mode! Try again.')

