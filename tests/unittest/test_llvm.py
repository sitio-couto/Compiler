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
from uCBuild import uCIRBuilder as Builder
from os.path import exists
from sys import argv

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

print('\n', f'Working Directory: {workdir}','\n')

class TestOpt(unittest.TestCase):
    
    inputs = {
        't1':'tests/llvm/t1.uc',
        't2':'tests/llvm/t2.uc',
        't3':'tests/llvm/t3.uc',
        't4':'tests/llvm/t4.uc',
        't5':'tests/llvm/t5.uc',
        't6':'tests/llvm/t6.uc',
        't7':'tests/llvm/t7.uc',
        't8':'tests/llvm/t8.uc',
        't9':'tests/llvm/t9.uc',
        't10':'tests/llvm/t10.uc',
        't11':'tests/llvm/t11.uc',
        't12':'tests/llvm/t12.uc',
        't13':'tests/llvm/t13.uc',
        't14':'tests/llvm/t14.uc',
        't15':'tests/llvm/t15.uc',
        't16':'tests/llvm/t16.uc',}

    def runNcmp(self, id):
        filename = self.inputs[id]

        tokenizer = Lexer(print_error)
        tokenizer.build()
        parser = Parser(tokenizer)
        parser.build()
        semantic = Semantic(parser)
        generator = Generator(semantic)
        cfg = CFG(generator)
        dfa = DFA(cfg)
        opt = Optimizer(dfa)
        llvm = Builder(opt)

        raw_std,raw_err = StringIO(),StringIO()
        sys.stdout = raw_std
        sys.stderr = raw_err
        llvm.test(filename, True, None)
        
        opt_std,opt_err = StringIO(),StringIO()
        sys.stdout = opt_std
        sys.stderr = opt_err
        llvm.test(filename, True, 'all')

        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__

        print(f'\n{id}=> TRUE - The LLVM code is valid\n')       

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

    def test_t9(self):
        self.runNcmp('t9')
    
    def test_t10(self):
        self.runNcmp('t10')

    def test_t11(self):
        self.runNcmp('t11')
    
    def test_t12(self):
        self.runNcmp('t12')
    
    def test_t13(self):
        self.runNcmp('t13')
    
    def test_t14(self):
        self.runNcmp('t14')
    
    def test_t15(self):
        self.runNcmp('t15')

    def test_t16(self):
        self.runNcmp('t16')

    

if __name__ == '__main__':
    unittest.main()    
