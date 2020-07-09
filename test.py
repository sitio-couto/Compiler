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
from uCGenerate import uCIRGenerator as Generator
from uCInterpreter import uCIRInterpreter as Interpreter
from uCBlock import uCIRCFG as CFG
from uCDFA import uCIRDFA as DFA
from uCOptimize import uCIROptimizer as Optimizer
from uCBuild import uCIRBuilder as Builder
from os.path import exists
from sys import argv
import argparse

# NOTE: Running tests
# to test some optimization do the following:
# python test.py -f inputfile/path.uc [--dead|--prop|--single|--quiet]
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
parser.add_argument('--prop', action='store_true', 
                    help='Run constant propagation optimization.')
parser.add_argument('--single', action='store_true', 
                    help='Run one iteration at a time.')
parser.add_argument('--optimize', action='store_true', 
                    help='Use optimized code (only in full compilation).')
group = parser.add_mutually_exclusive_group()
group.add_argument('-l','--lexer', action='store_true')
group.add_argument('-p','--parser', action='store_true')
group.add_argument('-s','--semantic', action='store_true')
group.add_argument('-g','--generator', action='store_true')
group.add_argument('-i','--interpreter', action='store_true')
group.add_argument('-b','--basicblocks', action='store_true')
group.add_argument('-d','--dataflow', action='store_true')
group.add_argument('-o','--optimization', action='store_true')
group.add_argument('-c','--compilation', action='store_true')
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
    dfa = DFA(cfg)
    opt = Optimizer(dfa)
    llvm = Builder(opt) if args.optimize else Builder(generator)
    
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
                semantic.test(input("Filename or expression for Semantic Check: "), args.quiet)
            except EOFError:
                break
    elif args.generator:
        while True:
            try:
                generator.test(input("Filename or expression for IR Generation: "), args.quiet)
            except EOFError:
                break
    elif args.interpreter:
        while True:
            try:
                interpreter.test(input("Filename or expression to run: "), args.quiet)
            except EOFError:
                break
    elif args.basicblocks:
        while True:
            try:
                cfg.test(input("Filename or expression to separate: "), args.quiet)
            except EOFError:
                break
    elif args.dataflow:
        while True:
            try:
                dfa.test(input("Filename or expression to analyze: "), args.quiet)
            except EOFError:
                break
    elif args.optimization:
        while True:
            try:
                opt.test(input("Filename or expression to optimize and run: "), args.quiet, args.dead, args.prop, args.single)
                interpreter.run(opt.code)
            except EOFError:
                break
    elif args.compilation:
        while True:
            try:
                llvm.test(input("Filename or expression to compile and run: "), args.quiet, 'all')
            except EOFError:
                break
    elif args.file:
        # quick testing input file
        llvm.test(args.file, args.quiet, 'all')
    else:
        print("No valid option selected.")
