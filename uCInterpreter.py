'''
Second Project: Interpreter for uCIR intermediate code based on uC.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 05/05/2020.
'''

from os.path import exists

class uCIRInterpreter(object):
    '''
    Runs an interpreter on the SSA intermediate code generated for
    your compiler.   The implementation idea is as follows.  Given
    a sequence of instruction tuples such as:

         code = [ 
              ('literal_int', 1, 't_1'),
              ('literal_int', 2, 't_2'),
              ('add_int', 't_1', 't_2, 't_3')
              ('print_int', 't_3')
              ...
         ]

    The class executes methods self.run_opcode(args).  For example:

             self.run_literal_int(1, 't_1')
             self.run_literal_int(2, 't_2')
             self.run_add_int('t_1', 't_2', 't_3')
             self.run_print_int('t_3')

    To store the values of variables created in the intermediate
    language, simply use a dictionary.

    For builtin function declarations, allow specific Python modules
    (e.g., print, input, etc.) to be registered with the interpreter.
    We don't have namespaces in the source language so this is going
    to be a bit of sick hack.
    '''
    def __init__(self, generator=None):
        # Adding IR generator for testing
        self.generator = generator
        
        global M
        M = 10000 * [None]       # Memory for holding data

        self.globals = {}        # Dictionary of address of global vars & constants
        self.vars = {}           # Dictionary of address of local vars relative to sp

        self.offset = 0          # offset (index) of local & global vars. Note that
                                 # each instance of var has absolute address in Memory
        self.stack = []          # Stack to save offset of vars between calls
        self.sp = []             # Stack to save & restore the last offset

        self.params = []         # List of parameters from caller (address)
        self.result = None       # Result Value (address) from the callee

        self.registers = []      # Stack of register names (in the caller) to return value
        self.returns = []        # Stack of return addresses (program counters)

        self.pc = 0              # Program Counter
        self.start = 0           # PC of the main function

    def test(self, data, show_code=None):
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.generate(data)
        
        if show_code:
            self.generator.print_code()
        
        # Run IR code.
        self.run(self.generator.code)

    def _alloc_reg(self, target):
        if target not in self.vars:
            self.vars[target] = self.offset
            self.offset += 1

    def _extract_operation(self, source):
        # Extract the operation & their modifiers
        _modifier = {}
        _aux = source.split('_')
        # ...
        return (_opcode, _modifier)

    def run(self, ircode):
        '''
        Run intermediate code in the interpreter.  ircode is a list
        of instruction tuples.  Each instruction (opcode, *args) is 
        dispatched to a method self.run_opcode(*args)
        '''
        self.pc = 0
        # First, store the global vars & constants in Memory
        # and hold their offsets in self.globals dictionary
        # Also, set the start pc to the main function entry
        self.pc = self.start
        while True:
            try:
                op = ircode[self.pc]
            except IndexError:
                break
            self.pc += 1
            if not op[0].isdigit():
                opcode, modifier = self._extract_operation(op[0])
                if hasattr(self, "run_" + opcode):
                    if not modifier:
                        getattr(self, "run_" + opcode)(*op[1:])
                    else:
                        getattr(self, "run_" + opcode + '_')(*op[1:], **modifier)
                else:
                    print("Warning: No run_" + opcode + "() method")

    # YOU MUST IMPLEMENT methods for different opcodes.  A few sample
    # opcodes are shown below to get you started.

    def run_jump(self, target):
        self.pc = self.vars[target]

    def run_cbranch(self, expr_test, true_target, false_target):
        if M[self.vars[expr_test]]:
            self.pc = self.vars[true_target]
        else:
            self.pc = self.vars[false_target]

    # load literals into registers
    def run_literal_int(self, value, target):
        self._alloc_reg(target)
        M[self.vars[target]] = value

    run_literal_float = run_literal_int
    run_literal_char = run_literal_int

    # perform binary operations
    def run_add_int(self, left, right, target):
        self._alloc_reg(target)
        M[self.vars[target]] = M[self.vars[left]] + M[self.vars[right]]

    run_add_float = run_add_int
    run_add_string = run_add_int

    def run_alloc_int_(self, varname, **kwargs):
        _size = 1
        for arg in kwargs.values():
            if arg.isdigit():
                _size *= int(arg)
        self.vars[varname] = self.offset
        M[self.offset:self.offset + _size] = _size * [0]
        self.offset += _size

    run_alloc_float_ = run_alloc_int_
    run_alloc_char_ = run_alloc_int_

    def run_store_int_(self, source, target, **kwargs):
        _ref = 0
        _size = 1
        for arg in kwargs.values():
            if arg.isdigit():
                _size *= int(arg)
            elif arg == '*':
                _ref += 1
        if _ref == 0:
            self._store_multiple_values(_size, target, source)
        elif _size == 1 and _ref == 1:
            self._store_deref(target, self._get_value(source))
        # ...

    run_store_float_ = run_store_int_
    run_store_char_ = run_store_int_

    # Load/stores
    def run_load_int(self, varname, target):
        self._alloc_reg(target)
        M[self.vars[target]] = self._get_value(varname)

    run_load_float = run_load_int
    run_load_char = run_load_int
    run_load_bool = run_load_int
    
    def run_call(self, source, target):
        self._alloc_reg(target)
        self.registers.append(target)
        # save the return pc
        self.returns.append(self.pc)
        # jump to the function
        self.pc = self.globals[source]

    def run_elem_int(self, source, index, target):
        self._alloc_reg(target)
        _aux = self._get_address(source)
        _idx = self._get_value(index)
        _address = _aux + _idx
        self._store_value(target, _address)

    run_elem_float = run_elem_int
    run_elem_char = run_elem_int

    def run_param_int(self, source):
        self.params.append(self.vars[source])

    run_param_float = run_param_int
    run_param_char = run_param_int
