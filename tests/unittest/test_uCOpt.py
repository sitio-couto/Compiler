import sys, os, filecmp, unittest, re
from io import StringIO 
from difflib import unified_diff as diff
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader

workdir = os.path.dirname(os.path.abspath(__file__))
workdir = re.sub('.tests.unittest$', '', workdir)
sys.path.append(workdir)

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

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

print('\n', f'Working Directory: {workdir}','\n')

class TestOpt(unittest.TestCase):

    inputs = [
        ('tests/opt_in/e1.uc',100),
        ('tests/opt_in/e2.uc',38),
        ('tests/opt_in/e3.uc',9)]

    def runNcmp(self, id):
        filename,goal = self.inputs[id]

        tokenizer = Lexer(print_error)
        tokenizer.build()
        parser = Parser(tokenizer)
        parser.build()
        semantic = Semantic(parser)
        generator = Generator(semantic)
        interpreter = Interpreter(generator)
        cfg = CFG(generator)
        dfa = DFA(generator, cfg)
        opt = Optimizer(generator,cfg=cfg,dfa=dfa)
        opt.test(filename, True, True, True, False)

        raw = generator.code
        opt = cfg.retrieve_ir()

        raw_std,raw_err = StringIO(),StringIO()
        sys.stdout = raw_std
        sys.stderr = raw_err
        with self.assertRaises(SystemExit) as cm:
            interpreter.run(raw)

        opt_std,opt_err = StringIO(),StringIO()
        sys.stdout = opt_std
        sys.stderr = opt_err
        with self.assertRaises(SystemExit) as cm:
            interpreter.run(opt)

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        raw_std,raw_err = raw_std.getvalue(),raw_err.getvalue()
        opt_std,opt_err = opt_std.getvalue(),opt_err.getvalue()

        A,B,C = raw_std==opt_std,raw_err==opt_err,len(opt)<=goal
        if A and B and C:
            print('TRUE - The Output Is Correct\n')
        elif not (A and B):
            print("\n===>Achived:")
            print(opt_std)
            print(opt_err)
            print("\n===>Excpected:")
            print(raw_std)
            print(raw_err)
            assert False, "FALSE - Optimization altered the code's output\n"
        elif not C:
            assert False, f"FALSE - Not enough optimzations (got {len(opt)}, needs {len(raw)})\n"

    def test_t0(self):
        self.runNcmp(0)

    def test_t1(self):
        self.runNcmp(1)

    def test_t2(self):
        self.runNcmp(2)

if __name__ == '__main__':
    unittest.main()    
