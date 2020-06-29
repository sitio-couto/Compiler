'''
Fourth Project: Translation from uCIR to LLVM IR.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 28/06/2020.
'''

from llvmlite import ir

class uCIRTranslator(object):
    def __init__(self, builder):
        self.builder = builder
        self.module  = None
        self.loc     = dict()
        self.types   = dict()
        self.args    = []
        self.init_types()
    
    def init_types(self):
        int_t   = ir.IntType(32)
        float_t = ir.DoubleType()
        char_t  = ir.IntType(8)
        void_t  = ir.VoidType()
        str_t   = ir.PointerType(char_t)
        
        self.types['int']   = int_t
        self.types['float'] = float_t
        self.types['char']  = char_t
        self.types['void']  = void_t
        
        self.types['int_*']   = int_t.as_pointer()
        self.types['float_*'] = float_t.as_pointer()
        self.types['char_*']  = char_t.as_pointer()
        self.types['void_*']  = char_t.as_pointer()
        self.types['string']  = str_t
        return

    def translate(self, module, code):
        ''' Main translation function. '''
        self.module = module
        
        # TODO: initialization
        
        for inst in code:
            opcode, ty, mods = self._extract_operation(inst[0])
            if opcode == 'define':
                self.new_function(inst)
            elif hasattr(self, "build_" + opcode):
                if not mods:
                    getattr(self, "build_" + opcode)(ty, *inst[1:])
                else:
                    getattr(self, "build_" + opcode + '_')(ty, *inst[1:], **mods)
            else:
                print("Warning: No build_" + opcode + "() method", flush=True)

        return
    
    ### Auxiliary functions ###
    def _extract_operation(self, source):
        _modifier = {}
        _type = None
        _aux = source.split('_')
        _opcode = _aux[0]
        if _opcode not in {'fptosi', 'sitofp', 'jump', 'cbranch', 'define', 'call'}:
            _type = _aux[1]
            for i, _val in enumerate(_aux[2:]):
                if _val.isdigit():
                    _modifier['dim' + str(i)] = _val
                elif _val == '*':
                    _modifier['ptr' + str(i)] = _val
                    
        return (_opcode, _type, _modifier)
    
    def _global_constant(self, builder_or_module, name, value, linkage='internal'):
        # Get or create a (LLVM module-)global constant with *name* or *value*.
        if isinstance(builder_or_module, ir.Module):
            mod = builder_or_module
        else:
            mod = builder_or_module.module
        data = ir.GlobalVariable(mod, value.type, name=name)
        data.linkage = linkage
        data.global_constant = True
        data.initializer = value
        data.align = 1
        return data
    
    def make_bytearray(buf):
        # Make a byte array constant from *buf*.
        b = bytearray(buf)
        n = len(b)
        return ir.Constant(ir.ArrayType(ir.IntType(8), n), b)
    
    def _cio(self, fname, format, *target):
        # Make global constant for string format
        mod = self.builder.module
        fmt_bytes = self.make_bytearray((format + '\00').encode('ascii'))
        global_fmt = self._global_constant(mod, mod.get_unique_name('.fmt'), fmt_bytes)
        fn = mod.get_global(fname)
        ptr_fmt = self.builder.bitcast(global_fmt, ir.IntType(8).as_pointer())
        return self.builder.call(fn, [ptr_fmt] + list(target))
    
    def new_function(self, inst):
        ty = inst[0].split('_')[1]
        
        # Get args
        arg_types = list(map(lambda x: x[0], inst[2]))
        arg_types = [self.types[arg] for arg in arg_types]
        
        # Prototype
        func_type = ir.FunctionType(self.types[ty], arg_types)
        
        # Function
        fn = ir.Function(self.module, func_type, name=inst[1][1:])
        
        # Parameter locations
        for i, temp in enumerate(list(map(lambda x: x[1], inst[2]))):
            self.loc[temp] = fn.args[i]

    ### Instruction building functions ###
    # Binary Operations
    def build_add(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fadd(left, right)
        else:
            loc = self.builder.add(left, right)
        self.loc[target] = loc

    def build_sub(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fsub(left, right)
        else:
            loc = self.builder.sub(left, right)
        self.loc[target] = loc

    def build_mul(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fmul(left, right)
        else:
            loc = self.builder.mul(left, right)
        self.loc[target] = loc

    def build_div(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fdiv(left, right)
        else:
            loc = self.builder.sdiv(left, right)
        self.loc[target] = loc

    def build_mod(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.frem(left, right)
        else:
            loc = self.builder.srem(left, right)
        self.loc[target] = loc
    
    # Relational Operations
    def compare(self, op, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp(op, left, right)
        else:
            loc = self.builder.icmp(op, left, right)
        self.loc[target] = loc
        
    def build_gt(self, ty, left, right, target):
        self.compare('>', ty, left, right, target)
    
    def build_ge(self, ty, left, right, target):
        self.compare('>=', ty, left, right, target)
    
    def build_eq(self, ty, left, right, target):
        self.compare('==', ty, left, right, target)
    
    def build_le(self, ty, left, right, target):
        self.compare('<=', ty, left, right, target)
    
    def build_lt(self, ty, left, right, target):
        self.compare('<', ty, left, right, target)
    
    def build_ne(self, ty, left, right, target):
        self.compare('!=', ty, left, right, target)
    
    def build_and(self, _, left, right, target):
        left,right = self.loc[left],self.loc[right]
        loc = self.builder.and_(left, right)
        self.loc[target] = loc
    
    def build_or(self, _, left, right, target):
        left,right = self.loc[left],self.loc[right]
        loc = self.builder.or_(left, right)
        self.loc[target] = loc
    
    def build_not(self, _, left, right, target):
        left,right = self.loc[left],self.loc[right]
        loc = self.builder.neg(left, right)
        self.loc[target] = loc

    # Cast operations
    def build_fptosi(self, _, value, target):
        value = self.loc[value]
        loc = self.builder.fptosi(value, self.types['int'])
        self.loc[target] = loc

    def build_sitofp(self, _, value, target):
        value = self.loc[value]
        loc = self.builder.sitofp(value, self.types['float'])
        self.loc[target] = loc
    
    # Branch Operations
    # TODO: terminators (block operations)?.
    def build_jump(self, _, target):
        target = self.loc[target]
        self.builder.branch(target)
    
    def build_cbranch(self, _, test, true, false):
        test = self.loc[test]
        true, false = self.loc[true], self.loc[false]
        self.builder.cbranch(test, true, false)
    
    # Memory Operations
    # TODO: add global
    def build_alloc(self, ty, target):
        ty = self.types[ty]
        loc = self.builder.alloca(ty, name=target[1:])
        self.loc[target] = loc
    
    def build_alloc_(self, ty, target, **kwargs):
        ty = self.types[ty]
        
        # Modifier
        for mod in reverse(list(kwargs.values())):
            ty = ir.ArrayType(ty, int(mod)) if mod.isdigit() else ir.PointerType(ty)
                
        loc = self.builder.alloca(ty, name=target[1:])
        self.loc[target] = loc
    
    def build_load(self, _, src, target):
        src = self.loc[src]
        if isinstance(src, ir.Constant):
            self.loc[target] = src
        else:
            loc = self.builder.load(src)
            self.loc[target] = loc
    
    def build_load_(self, _, src, target, **kwargs):
        src = self.loc[src]
        loc = self.builder.load(src)
        self.loc[target] = loc
    
    def build_store(self, _, src, target):
        src = self.loc[src]
        loc = self.loc.get(target, None)
        if loc:
            self.builder.store(src, loc)
        else:
            self.loc[target] = src
            
    # TODO: complete with array
    # TODO: pointer correct?
    def build_store_(self, _, src, target, **kwargs):
        src = self.loc[src]
        target = self.loc.get(target, None)
        if isinstance(target.type.pointee, ir.ArrayType):
            size = 1
            for dim in kwargs.values(): size *= int(dim)
            # TODO: someday
        else:
            self.builder.store(src, target.pointee)
    
    def build_literal(self, ty, value, target):
        ty = self.types[ty]
        val = ir.Constant(ty, value)
        loc = self.loc.get(target, None)
        if loc:
            self.builder.store(val, loc)
        else:
            self.loc[target] = val
    
    def build_elem(self, _, src, idx, target):
        src, idx = self.loc[src], self.loc[idx]
        base = ir.Constant(self.types['int'], 0)
        loc = self.builder.gep(src, [base, idx])
        self.loc[target] = loc
    
    # TODO: correct?
    def build_get(self, _, src, target):
        # This function is never called.
        assert False, "Get instruction without *!"
    
    def build_get_(self, _, src, target, **kwargs):
        src = self.loc[src]
        target = self.loc[target]
        self.builder.load(src.pointee, target)
    
    # Function Operations
    def build_param(self, _, src):
        self.args.append(self.loc[src])
    
    def build_call(self, _, fn, target=None):
        fn = self.module.get_global(fn[1:])
        loc = self.builder.call(fn, self.args)
        
        # Check Void
        if not isinstance(fn.type.pointee.return_type, ir.VoidType):
            self.loc[target] = loc
        self.args = []
    
    # TODO: add block operations?.
    def build_return(self, ty, value=None):
        if ty == 'void':
            self.builder.ret_void()
        else:
            value = self.loc[value]
            self.builder.ret(value)
            
    # Builtins
    # TODO: read/scanf?
    def build_print(self, ty, target=None):
        if target:
            # get the object assigned to target
            target = self.loc[target]
            if ty == 'int':
                self._cio('printf', '%d', target)
            elif ty == 'float':
                self._cio('printf', '%.2f', target)
            elif ty == 'char':
                self._cio('printf', '%c', target)
            elif ty == 'string':
                self._cio('printf', '%s', target)
        else:
            self._cio('printf', '\n')
