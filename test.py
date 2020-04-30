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
    
    while True:
        # quick testing input file
        if len(argv) > 1 :
            for i in range(1,len(argv)):
                code = generator.test(argv[i], False)
                out = ''
                for inst in code: out += str(inst)+'\n'
                f = open(argv[i][:-2]+'in', 'w')
                f.write(out)
                f.close()
            exit(1)

        print("\nSend 'l' for lexer test, 'p' for parser test, 's' for semantic test and 'i' for IR test ('q' to quit)")
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
        elif mode == 'i':
            while True:
                try:
                    generator.test(input("Filename or expression for IR Generation: "), True)
                except EOFError:
                    break
        elif mode == 'q':
            break
        else:
            print('Invalid mode! Try again.')

