import sys, os, filecmp, unittest, re
from io import StringIO 
from difflib import unified_diff as diff
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader

workdir = os.path.dirname(os.path.abspath(__file__))
test_file = workdir + "/test.uc"
workdir = re.sub('.tests.unittest$', '', workdir)
sys.path.append(workdir[:])
import uCCompiler

class TestAST(unittest.TestCase):

    def runNcmp(self, code, err_test=True):
        f = open(test_file, "w")
        f.write(code)
        f.flush()
        f.close()

        sys.argv = sys.argv[:1]+[test_file]
        with self.assertRaises(SystemExit) as cm:
            uCCompiler.run_compiler()
        err = cm.exception.code

        if err_test != err : 
            if err_test : raise Exception("An error should've ocurred\n")
            else : raise Exception("There should be no errors\n")
            
        print("==================")
        
    def test_t1(self):
        self.runNcmp(
        '''
        int main(){
            return;
        }
        '''
        , err_test=True)

    def test_t2(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c);
        int test(int a, float b, char c);
        '''
        , err_test=False)

        

if __name__ == '__main__':
    unittest.main()
