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
    
    inputs = {
        't00':('tests/IR_in/test.uc',1000),
        't01':('tests/IR_in/test01.uc',1000),
        't02':('tests/IR_in/test02.uc',1000),
        't03':('tests/IR_in/test03.uc',1000),
        't04':('tests/IR_in/test04.uc',1000),
        't05':('tests/IR_in/test05.uc',1000),
        't06':('tests/IR_in/test06.uc',1000),
        't07':('tests/IR_in/test07.uc',1000),
        't08':('tests/IR_in/test08.uc',1000),
        't09':('tests/IR_in/test09.uc',1000),
        't10':('tests/IR_in/test10.uc',1000),
        't11':('tests/IR_in/test11.uc',1000),
        't12':('tests/IR_in/test12.uc',1000),
        't13':('tests/IR_in/test13.uc',1000),
        'e1':('tests/opt_in/e1.uc',100),
        'e2':('tests/opt_in/e2.uc',38),
        'e3':('tests/opt_in/e3.uc',9)}

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

    #### NOTE: Some tests are commented because they require input.

    def test_t0(self):
        self.runNcmp('t00')

    def test_t1(self):
        self.runNcmp('t01')

    def test_t2(self):
        self.runNcmp('t02')
    
    def test_t3(self):
        self.runNcmp('t03')

    def test_t4(self):
        self.runNcmp('t04')

    def test_t5(self):
        self.runNcmp('t05')
    
    def test_t6(self):
        self.runNcmp('t06')

    # def test_t7(self):
    #     self.runNcmp('t07')

    def test_t8(self):
        self.runNcmp('t08')
    
    def test_t9(self):
        self.runNcmp('t09')

    def test_t10(self):
        self.runNcmp('t10')

    def test_t11(self):
        self.runNcmp('t11')
    
    # def test_t12(self):
    #     self.runNcmp('t12')

    # def test_t13(self):
    #     self.runNcmp('t13')

    def test_e1(self):
        self.runNcmp('e1')

    def test_e2(self):
        self.runNcmp('e2')

    def test_e3(self):
        self.runNcmp('e3')

if __name__ == '__main__':
    unittest.main()    
