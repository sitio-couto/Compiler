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
from os.path import exists
from sys import argv

def print_error(msg, x, y):
    print("Lexical error: %s at %d:%d" % (msg, x, y))

print('\n', f'Working Directory: {workdir}','\n')

class TestAST(unittest.TestCase):

    inputs = [
        'tests/IR_in/test01.uc',
        'tests/IR_in/test02.uc',
        'tests/IR_in/test03.uc',
        'tests/IR_in/test04.uc',
        'tests/IR_in/test05.uc',
        'tests/IR_in/test06.uc',
        'tests/IR_in/test07.uc',
        'tests/IR_in/test08.uc',
        'tests/IR_in/test09.uc',
        'tests/IR_in/test10.uc',
        'tests/IR_in/test11.uc',
        'tests/IR_in/test12.uc',
        'tests/IR_in/test13.uc']
    
    outputs = [
        'tests/IR_in/test01.in',
        'tests/IR_in/test02.in',
        'tests/IR_in/test03.in',
        'tests/IR_in/test04.in',
        'tests/IR_in/test05.in',
        'tests/IR_in/test06.in',
        'tests/IR_in/test07.in',
        'tests/IR_in/test08.in',
        'tests/IR_in/test09.in',
        'tests/IR_in/test10.in',
        'tests/IR_in/test11.in',
        'tests/IR_in/test12.in',
        'tests/IR_in/test13.in']

    targets = [
        'tests/IR_out/test01.out',
        'tests/IR_out/test02.out',
        'tests/IR_out/test03.out',
        'tests/IR_out/test04.out',
        'tests/IR_out/test05.out',
        'tests/IR_out/test06.out',
        'tests/IR_out/test07.out',
        'tests/IR_out/test08.out',
        'tests/IR_out/test09.out',
        'tests/IR_out/test10.out',
        'tests/IR_out/test11.out',
        'tests/IR_out/test12.out',
        'tests/IR_out/test13.out']

    def runNcmp(self, id):
        i,o,t = self.inputs[id], self.outputs[id], self.targets[id]
        sys.argv = sys.argv[:1]+[i]
        
        tokenizer = Lexer(print_error)
        tokenizer.build()
        parser = Parser(tokenizer)
        parser.build()
        semantic = Semantic(parser)
        generator = Generator(semantic)
        generator.test(i, False, out_file=o, quiet=True)

        print(f'Comparing: {o} == {t} ?')
        try:
            assert filecmp.cmp(o, t, shallow=True)
        except:
            fo = open(o)
            ft = open(t)
            for l in diff(
                fo.read().splitlines(), 
                ft.read().splitlines(),
                fromfile='output',
                tofile='expected',
                lineterm=''):
                print(l)
            fo.close()
            ft.close()
            print('FALSE - The Files Differ\n')
        else:
            print('TRUE - The Output Is Correct\n')

    def test_t0(self):
        self.runNcmp(0)

    # def test_t1(self):
    #     self.runNcmp(1)

    # def test_t2(self):
    #     self.runNcmp(2)

    # def test_t3(self):
    #     self.runNcmp(3)

    # def test_t4(self):
    #     self.runNcmp(4)

    # def test_t5(self):
    #     self.runNcmp(5)

    # def test_t6(self):
    #     self.runNcmp(6)

    # def test_t7(self):
    #     self.runNcmp(7)

    # def test_t8(self):
    #     self.runNcmp(8)

    # def test_t9(self):
    #     self.runNcmp(9)

    # def test_t10(self):
    #     self.runNcmp(10)

    # def test_t11(self):
    #     self.runNcmp(11)
    
    # def test_t12(self):
    #     self.runNcmp(12)
    
    # def test_t13(self):
    #     self.runNcmp(13)

if __name__ == '__main__':
    unittest.main()    
