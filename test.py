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
from uCDFA import uCDFA as DFA
from uCOptimize import Optimizer
from os.path import exists
from sys import argv
import argparse

# NOTE: Running tests
# to test some optimization do the following:
# python test.py -f inputfile/path.uc [--dead|--prop|--fold|--single|--quiet]
# if no opt is defined it will run all of then
# The remaining test options can be used by running:
# python test.py -x (where x is the desired test type)

parser = argparse.ArgumentParser(
    description='''Test specific sections of our compiler's pipeline.'''
    )
parser.add_argument('-f','--file', type=str, 
                    help='Path of the uC code input file.')
parser.add_argument('-q','--quiet', action='store_true', 
                    help='No prints or graphs, only output file.')
parser.add_argument('--dead', action='store_true', 
                    help='Run deadcode elimination optimization.')
parser.add_argument('--fold', action='store_true', 
                    help='Run constan folding optimization.')
parser.add_argument('--prop', action='store_true', 
                    help='Run constan propagation optimization.')
parser.add_argument('--single', action='store_true', 
                    help='Run one iteration at a time.')
group = parser.add_mutually_exclusive_group()
group.add_argument('-l','--lexer', action='store_true')
group.add_argument('-p','--parser', action='store_true')
group.add_argument('-s','--semantic', action='store_true')
group.add_argument('-g','--generator', action='store_true')
group.add_argument('-i','--interpreter', action='store_true')
group.add_argument('-b','--basicblocks', action='store_true')
group.add_argument('-d','--dataflow', action='store_true')
group.add_argument('-o','--optimization', action='store_true')
args = parser.parse_args()

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
    dfa = DFA(generator, cfg)
    opt = Optimizer(generator)
    
    while True:
        if args.lexer:
            while True: 
                try:
                    tokenizer.reset_line_num()
                    tokenizer.test(input("Filename or expression for Lexer: "))
                except EOFError:
                    break
        elif args.parser:
            while True:
                try:
                    parser.test(input("Filename or expression for Parser: "))
                except EOFError:
                    break
        elif args.semantic:
            while True:
                try:
                    semantic.test(input("Filename or expression for Semantic Check: "), True)
                except EOFError:
                    break
        elif args.generator:
            while True:
                try:
                    generator.test(input("Filename or expression for IR Generation: "), False)
                except EOFError:
                    break
        elif args.interpreter:
            while True:
                try:
                    interpreter.test(input("Filename or expression to run: "), True)
                except EOFError:
                    break
        elif args.basicblocks:
            while True:
                try:
                    cfg.test(input("Filename or expression to separate: "), True)
                except EOFError:
                    break
        elif args.dataflow:
            while True:
                try:
                    dfa.test(input("Filename or expression to analyze: "), True)
                except EOFError:
                    break
        elif args.optimization:
            while True:
                try:
                    code = opt.test(input("Filename or expression to optimize and run: "), False)
                    interpreter.run(code)
                except EOFError:
                    break
        elif args.file:
            # quick testing input file
            if args.file:
                if not sum([args.dead,args.fold,args.prop]):
                    args.dead,args.fold,args.prop = True,True,True
                opt.test(args.file, args.quiet, args.dead, args.fold, args.prop, args.single)
                exit(1)
        else:
            print("No valid option selected.")
            break


