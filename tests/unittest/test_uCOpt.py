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
from uCGenerate import uCIRGenerator as Generator
from uCInterpreter import uCIRInterpreter as Interpreter
from uCBlock import uCIRCFG as CFG
from uCDFA import uCIRDFA as DFA
from uCOptimize import uCIROptimizer as Optimizer
from os.path import exists
from sys import argv

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

print('\n', f'Working Directory: {workdir}','\n')

class TestOpt(unittest.TestCase):
    
    inputs = {
        'i00':('tests/IR_in/test.uc',1000),
        'i01':('tests/IR_in/test01.uc',1000),
        'i02':('tests/IR_in/test02.uc',1000),
        'i03':('tests/IR_in/test03.uc',1000),
        'i04':('tests/IR_in/test04.uc',1000),
        'i05':('tests/IR_in/test05.uc',1000),
        'i06':('tests/IR_in/test06.uc',1000),
        'i07':('tests/IR_in/test07.uc',1000),
        'i08':('tests/IR_in/test08.uc',1000),
        'i09':('tests/IR_in/test09.uc',1000),
        'i10':('tests/IR_in/test10.uc',1000),
        'i11':('tests/IR_in/test11.uc',1000),
        'i12':('tests/IR_in/test12.uc',1000),
        'i13':('tests/IR_in/test13.uc',1000),
        'c01':('tests/complete_codes/armstrong.uc',1000),
        'c02':('tests/complete_codes/fatorial.uc',1000),
        'c03':('tests/complete_codes/gcd.uc',1000),
        'c04':('tests/complete_codes/primes.uc',1000),
        'c05':('tests/complete_codes/simple1.uc',1000),
        'c06':('tests/complete_codes/simple2.uc',1000),
        'c07':('tests/complete_codes/simple3.uc',1000),
        'c08':('tests/complete_codes/simple4.uc',1000),
        'c09':('tests/complete_codes/simple6.uc',1000),
        'c10':('tests/complete_codes/PTR_simple5.uc',1000),
        't0': ('tests/opt_in/t0.uc',100),
        't1': ('tests/opt_in/t1.uc',1000),
        't2': ('tests/opt_in/t2.uc',1000),
        't3': ('tests/opt_in/t3.uc',1000),
        't4': ('tests/opt_in/t4.uc',1000),
        't5': ('tests/opt_in/t5.uc',1000),
        't6': ('tests/opt_in/t6.uc',1000),
        't7': ('tests/opt_in/t7.uc',1000),
        't8': ('tests/opt_in/t8.uc',1000)}

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
        dfa = DFA(cfg)
        opt = Optimizer(dfa)
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

    def test_i0(self):
        self.runNcmp('i00')

    def test_i1(self):
        self.runNcmp('i01')

    def test_i2(self):
        self.runNcmp('i02')
    
    def test_i3(self):
        self.runNcmp('i03')

    def test_i4(self):
        self.runNcmp('i04')

    def test_i5(self):
        self.runNcmp('i05')
    
    def test_i6(self):
        self.runNcmp('i06')

    # def test_i7(self):
    #     self.runNcmp('i07')

    def test_i8(self):
        self.runNcmp('i08')
    
    def test_i9(self):
        self.runNcmp('i09')

    def test_i10(self):
        self.runNcmp('i10')

    def test_i11(self):
        self.runNcmp('i11')
    
    # def test_i12(self):
    #     self.runNcmp('i12')

    # def test_i13(self):
    #     self.runNcmp('i13')

    # def test_c1(self):
    #     self.runNcmp('c01')
    
    def test_c2(self):
        self.runNcmp('c02')
    
    # def test_c3(self):
    #     self.runNcmp('c03')
    
    # def test_c4(self):
    #     self.runNcmp('c04')
    
    def test_c5(self):
        self.runNcmp('c05')
    
    def test_c6(self):
        self.runNcmp('c06')
    
    def test_c7(self):
        self.runNcmp('c07')
    
    def test_c8(self):
        self.runNcmp('c08')
    
    # def test_c9(self):
    #     self.runNcmp('c09')
    
    def test_c10(self):
        self.runNcmp('c10')

    def test_t0(self):
        self.runNcmp('t0')
    
    def test_t1(self):
        self.runNcmp('t1')
    
    def test_t2(self):
        self.runNcmp('t2')
    
    def test_t3(self):
        self.runNcmp('t3')
    
    def test_t4(self):
        self.runNcmp('t4')
    
    def test_t5(self):
        self.runNcmp('t5')

    def test_t6(self):
        self.runNcmp('t6')
    
    def test_t7(self):
        self.runNcmp('t7')
    
    def test_t8(self):
        self.runNcmp('t8')

if __name__ == '__main__':
    unittest.main()    
