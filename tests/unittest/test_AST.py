import sys, os, filecmp, unittest, re
from io import StringIO 
from difflib import unified_diff as diff
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader

workdir = os.path.dirname(os.path.abspath(__file__))
workdir = re.sub('(.)tests(.)unittest$', '', workdir)
sys.path.append(workdir)
import uCCompiler
print()

@contextmanager
def captured_output():
    new_out, new_err = StringIO(), StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    try:
        sys.stdout, sys.stderr = new_out, new_err
        yield sys.stdout, sys.stderr
    finally:
        sys.stdout, sys.stderr = old_out, old_err

class TestAST(unittest.TestCase):

    inputs = [
        'tests/ast_in/t1.uc',
        'tests/ast_in/t2.uc',
        'tests/ast_in/t3.uc',
        'tests/ast_in/t4.uc',
        'tests/ast_in/t5.uc']
    
    outputs = [
        'tests/ast_in/t1.ast',
        'tests/ast_in/t2.ast',
        'tests/ast_in/t3.ast',
        'tests/ast_in/t4.ast',
        'tests/ast_in/t5.ast']

    targets = [
        'tests/ast_out/t1.ast',
        'tests/ast_out/t2.ast',
        'tests/ast_out/t3.ast',
        'tests/ast_out/t4.ast',
        'tests/ast_out/t5.ast']

    def runNcmp(self, id):
        id -= 1
        i,o,t = self.inputs[id], self.outputs[id], self.targets[id]
        sys.argv = sys.argv[:1]+[i]
        print('\n\n')
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
