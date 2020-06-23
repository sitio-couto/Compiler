'''
Fourth Project: Building LLVM IR from uCIR.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 22/06/2020.
'''

from os.path import exists
from llvmlite import ir, binding
from ctypes import CFUNCTYPE, c_int
from uCTranslate import uCIRTranslator

class uCIRBuilder(object):
    # This class accepts 2 generator classes: uCIRGenerate or uCIROptimizer.
    ### Init Functions ###
    def __init__(self, generator):
        self.generator = generator
        
        self.binding = binding
        self.binding.initialize()
        self.binding.initialize_native_target()
        self.binding.initialize_native_asmprinter()
        
        self.module = ir.Module(name=__file__)
        self.module.triple = self.binding.get_default_triple()
        self.builder = ir.IRBuilder()
        
        self._create_execution_engine()
        
        # Translator from uCIR to LLVM IR
        self.translator = uCIRTranslator(self.builder)
        
        # declare external functions
        self._declare_printf_function()
        self._declare_scanf_function()
        
        self.create_optimizator()

    def _create_execution_engine(self):
        """
        Create an ExecutionEngine suitable for JIT code generation on
        the host CPU.  The engine is reusable for an arbitrary number of
        modules.
        """
        target = self.binding.Target.from_default_triple()
        target_machine = target.create_target_machine()
        # And an execution engine with an empty backing module
        backing_mod = binding.parse_assembly("")
        engine = binding.create_mcjit_compiler(backing_mod, target_machine)
        self.engine = engine

    def _declare_printf_function(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        printf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        printf = ir.Function(self.module, printf_ty, name="printf")
        self.printf = printf

    def _declare_scanf_function(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        scanf = ir.Function(self.module, scanf_ty, name="scanf")
        self.scanf = scanf
        
    def create_optimizator(self):
        self.pm = binding.create_module_pass_manager()
        pmb = binding.create_pass_manager_builder()
        pmb.opt_level = 3  # -O3
        pmb.populate(self.pm)
    
    ### Utility Functions ###
    def test(self, data, quiet=False, opt=False):
        # Generating code
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.code = []
        self.generator.generate(data)
        
        if not quiet:
            self.generator.print_code()
            print("\n")
        
        # Reset translator.
        self.module = ir.Module(name=__file__)
        self.module.triple = self.binding.get_default_triple()
        
        # Translate self.generator.code
        self.translator.translate(self.module, self.generator.code)
        
        # Execute IR
        self.execute_ir(opt)
        
        if not quiet:
            self.view()
    
    def show(self, cfg, buf=None):
        if cfg:
            self.view(buf)
        elif buf:
            self.save_ir(buf)
        else:
            self.print_ir()
    
    def view(self, filename=None):
        for fn in self.module.functions:
            dot = self.binding.get_function_cfg(fn)
            llvm.view_dot_graph(dot, filename = filename)
    
    def print_ir(self):
        print(self.module)
        
    def save_ir(self, filename):
        with open(filename, 'w') as output_file:
            output_file.write(str(self.module))
    
    ### IR Compilation/Execution Functions ###
    def _compile_ir(self, opt):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """
        # Create a LLVM module object from the IR
        self.builder.ret_void()
        llvm_ir = str(self.module)
        mod = self.binding.parse_assembly(llvm_ir)
        mod.verify()
        # Optimize IR
        if opt: self.pm.run(mod)
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod
    
    def execute_ir(self, opt):
        mod = self._compile_ir(opt)
        # Obtain a pointer to the compiled 'main' - it's the address of its JITed code in memory.
        main_ptr = self.engine.get_pointer_to_function(mod.get_function('main'))
        # To convert an address to an actual callable thing we have to use
        # CFUNCTYPE, and specify the arguments & return type.
        main_function = CFUNCTYPE(c_int)(main_ptr)
        # Now 'main_function' is an actual callable we can invoke
        res = main_function()
        print(res)
