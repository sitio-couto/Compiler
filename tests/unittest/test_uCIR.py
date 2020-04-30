import sys, os, filecmp, unittest, re
from io import StringIO 
from difflib import unified_diff as diff
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader

workdir = os.path.dirname(os.path.abspath(__file__))
workdir = re.sub('.tests.unittest$', '', workdir)
sys.path.append(workdir)
import uCCompiler

print('\n', f'Working Directory: {workdir}','\n')

class TestAST(unittest.TestCase):

    inputs = [
        'tests/IR_in/test01.uc',
        'tests/IR_in/test02.uc',
        'tests/IR_in/test03.uc',
        'tests/IR_in/test04.uc',
        'tests/IR_in/test04.uc',
        'tests/IR_in/test05.uc',
        'tests/IR_in/test06.uc',
        'tests/IR_in/test07.uc',
        'tests/IR_in/test08.uc',
        'tests/IR_in/test09.uc',
        'tests/IR_in/test10.uc',
        'tests/IR_in/test11.uc']
    
    outputs = [
        'tests/IR_in/test01.in',
        'tests/IR_in/test02.in',
        'tests/IR_in/test03.in',
        'tests/IR_in/test04.in',
        'tests/IR_in/test04.in',
        'tests/IR_in/test05.in',
        'tests/IR_in/test06.in',
        'tests/IR_in/test07.in',
        'tests/IR_in/test08.in',
        'tests/IR_in/test09.in',
        'tests/IR_in/test10.in',
        'tests/IR_in/test11.in']

    targets = [
        'tests/IR_in/test01.out',
        'tests/IR_in/test02.out',
        'tests/IR_in/test03.out',
        'tests/IR_in/test04.out',
        'tests/IR_in/test04.out',
        'tests/IR_in/test05.out',
        'tests/IR_in/test06.out',
        'tests/IR_in/test07.out',
        'tests/IR_in/test08.out',
        'tests/IR_in/test09.out',
        'tests/IR_in/test10.out',
        'tests/IR_in/test11.out']

    def runNcmp(self, id):
        id -= 1
        i,o,t = self.inputs[id], self.outputs[id], self.targets[id]
        sys.argv = sys.argv[:1]+[i]
        with self.assertRaises(SystemExit) as cm:
            uCCompiler.run_compiler()
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

    def test_t1(self):
        self.runNcmp(1)

    def test_t2(self):
        self.runNcmp(2)

    def test_t3(self):
        self.runNcmp(3)

    def test_t4(self):
        self.runNcmp(4)

    def test_t5(self):
        self.runNcmp(5)
        

if __name__ == '__main__':
    unittest.main()    
