'''
Fourth Project: Building LLVM IR from uCIR.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 09/07/2020.
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
        
        self.setup_translation()
        self._create_execution_engine()

    def setup_translation(self):
        self.module = ir.Module(name=__file__)
        self.module.triple = self.binding.get_default_triple()
        
        # Translator from uCIR to LLVM IR
        self.translator = uCIRTranslator()
        
        # declare external functions
        self._declare_printf_function()
        self._declare_scanf_function()
        
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
        ir.Function(self.module, printf_ty, name="printf")

    def _declare_scanf_function(self):
        voidptr_ty = ir.IntType(8).as_pointer()
        scanf_ty = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg=True)
        ir.Function(self.module, scanf_ty, name="scanf")
        
    ### Utility Functions ###
    def test(self, data, quiet=False, opt=None):
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
        self.setup_translation()
        
        # Translate self.generator.code
        self.build_ir(self.generator.code)
        
        # Execute IR
        self.execute_ir(opt)
        
        if not quiet:
            self.show(False)
            self.view()
    
    def show(self, cfg, buf=None):
        if cfg:
            self.view(buf.name)
        if buf:
            self.save_ir(buf)
        else:
            self.print_ir()
    
    def view(self, filename=None):
        for i,fn in enumerate(self.module.functions):
            if not fn.name.startswith(('printf','scanf','llvm.memcpy')):
                dot = self.binding.get_function_cfg(fn)
                binding.view_dot_graph(dot, filename = filename, view=True)
    
    def print_ir(self):
        print(self.module)
        
    def save_ir(self, output_file):
        output_file.write(str(self.module))
    
    ### IR Construction ###
    def build_ir(self, code):
        self.translator.translate(self.module, code)
    
    ### IR Compilation/Execution Functions ###
    def _compile_ir(self, opt):
        """
        Compile the LLVM IR string with the given engine.
        The compiled module object is returned.
        """
        # Create a LLVM module object from the IR
        llvm_ir = str(self.module)
        mod = self.binding.parse_assembly(llvm_ir)
        mod.verify()

        # Optimize IR
        if opt:
            # apply some optimization passes on module
            pmb = self.binding.create_pass_manager_builder()
            pm = self.binding.create_module_pass_manager()
            pmb.opt_level = 0;
            if opt == 'ctm' or opt == 'all':
                pm.add_constant_merge_pass()
            if opt == 'dce' or opt == 'all':
                pm.add_dead_code_elimination_pass()
            if opt == 'cfg' or opt  == 'all':
                pm.add_cfg_simplification_pass()
            pmb.populate(pm)
            pm.run(mod)
            
        # Now add the module and make sure it is ready for execution
        self.engine.add_module(mod)
        self.engine.finalize_object()
        self.engine.run_static_constructors()
        return mod
    
    def execute_ir(self, opt=None, opt_file=None):
        mod = self._compile_ir(opt)
        
        # Save optimization if needed.
        if opt and opt_file:
            opt_file.write(str(mod))
        
        # Obtain a pointer to the compiled 'main' - it's the address of its JITed code in memory.
        main_ptr = self.engine.get_function_address('main')
        # To convert an address to an actual callable thing we have to use
        # CFUNCTYPE, and specify the arguments & return type.
        main_function = CFUNCTYPE(c_int)(main_ptr)
        # Now 'main_function' is an actual callable we can invoke
        res = main_function()
        print(res)
