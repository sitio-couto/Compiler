'''
Fourth Project: Translation from uCIR to LLVM IR.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 09/07/2020.
'''

from llvmlite import ir
import re

class uCIRTranslator(object):
    def __init__(self):
        self.builder = None
        self.module  = None
        self.loc     = dict()
        self.types   = dict()
        self.blocks  = dict()
        self.globals = dict()
        self.args    = []
        self.init_types()
    
    def init_types(self):
        int_t   = ir.IntType(32)
        float_t = ir.DoubleType()
        char_t  = ir.IntType(8)
        bool_t  = ir.IntType(1)
        void_t  = ir.VoidType()
        str_t   = ir.PointerType(char_t)
        
        self.types['int']    = int_t
        self.types['float']  = float_t
        self.types['char']   = char_t
        self.types['void']   = void_t
        self.types['bool']   = bool_t
        self.types['int_64'] = ir.IntType(64)
        
        self.types['int_*']   = int_t.as_pointer()
        self.types['float_*'] = float_t.as_pointer()
        self.types['char_*']  = char_t.as_pointer()
        self.types['void_*']  = char_t.as_pointer()
        self.types['string']  = str_t
        return

    def translate(self, module, code):
        ''' Main translation function. '''
        self.module = module

        # Fix code.
        code = self.label_collapse(code)
        
        # Pass through code.
        for line,inst in enumerate(code):
            opcode, ty, mods = self._extract_operation(inst[0])
            if opcode == 'label':
                self.builder.position_at_start(self.blocks[inst[0]])
            elif opcode == 'define':
                self.new_function(line, inst, code)
            elif hasattr(self, "build_" + opcode):
                if not mods:
                    getattr(self, "build_" + opcode)(ty, *inst[1:])
                else:
                    getattr(self, "build_" + opcode + '_')(ty, *inst[1:], **mods)
            else:
                print("Warning: No build_" + opcode + "() method", flush=True)

        return
    
    ### Auxiliary functions ###
    def label_collapse(self, code):
        pairs = []

        # Find all consecutive labels
        for line,inst in enumerate(code[:-1]):
            A = self.is_label(code[line])
            B = self.is_label(code[line+1])
            if A and B: pairs.append([line,'%'+code[line][0],'%'+code[line+1][0]])

        # Replace labels
        for l,o,n in pairs:
            code[l] = ('jump', n) # every block must end in a terminator instruction
            for line,inst in enumerate(code):
                if o in inst:
                    aux = list(inst)
                    aux[aux.index(o)] = n
                    code[line] = tuple(aux)

        # Add jump (terminator) after function calls
        line = 0
        while line < len(code)-1:
            inst = code[line]
            A = not re.match(r'cbranch|jump', inst[0])
            B = self.is_label(code[line+1])
            if A and B:
                label = '%'+code[line+1][0]
                code = code[:line+1]+[('jump',label)]+code[line+1:]
            line += 1

        return code

    def is_label(self, inst):
        if type(inst) in {tuple,list}: 
            return bool(re.match(r'^\d+$', inst[0]))
        else: 
            return bool(re.match(r'^\d+$', inst))

    def _extract_operation(self, source):
        if self.is_label(source): return 'label',None,None
        _modifier = {}
        _type = None
        _aux = source.split('_')
        _opcode = _aux[0]
        if _opcode not in {'fptosi', 'sitofp', 'jump', 'cbranch', 'define'}:
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
    
    def make_bytearray(self,buf):
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
    
    def new_function(self, line, inst, code):
        try:
            fn = self.module.get_global(inst[1][1:])
        except KeyError:
            ty = inst[0].split('_')[1]
            
            # Get args
            arg_types = list(map(lambda x: x[0], inst[2]))
            arg_types = [self.types[arg] for arg in arg_types]
            
            # Prototype
            func_type = ir.FunctionType(self.types[ty], arg_types)
            
            # Function
            fn = ir.Function(self.module, func_type, name=inst[1][1:])
        
        # Function's Basic Blocks
        self.blocks = dict()
        self.builder = ir.IRBuilder(fn.append_basic_block(name="entry"))
        for i in map(lambda x: x[0], code[line+1:]):
            if 'define' in i: break # Until reaches other function
            if self.is_label(i):
                self.blocks[i] = fn.append_basic_block(name=i)
        
        # Parameters and Globals Variables
        self.loc = dict()
        self.loc.update(self.globals)
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
            loc = self.builder.fcmp_signed(op, left, right)
        else:
            loc = self.builder.icmp_signed(op, left, right)
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
    def build_jump(self, _, target):
        if self.builder.block.is_terminated: return
        target = self.blocks[target[1:]]
        self.builder.branch(target)
    
    def build_cbranch(self, _, test, true, false):
        if self.builder.block.is_terminated: return
        test = self.loc[test]
        true, false = self.blocks[true[1:]], self.blocks[false[1:]]
        self.builder.cbranch(test, true, false)
    
    # Memory Operations
    # NOTE: the global variables might need alignment
    def build_global(self, ty, target, source=None):
        # If is a function signature, nothing to be done (TODO: fn ptr)
        if type(source)==list: return

        # Check string
        if ty == 'string':
            source = self.make_bytearray((source+'\00').encode('utf-8')) # get byte array for string
            glb = ir.GlobalVariable(self.module, source.type, target[1:])
            glb.initializer = source
            glb.global_constant = True
            
        # Others
        else:
            if source and ty=='char':
                source = ord(source[1]) # Get ascii for char 
                
            ty = self.types[ty]
            glb = ir.GlobalVariable(self.module, ty, target[1:])
            
            # Initializer
            if source:
                glb.initializer = ir.Constant(ty, source)
            
        self.globals[target] = glb

    def build_global_(self, ty, target, source=None, **kwargs):

        # Array/Pointer
        width = 1
        ty_str = ty
        ty = self.types[ty]
        for mod in reversed(list(kwargs.values())):
            if mod.isdigit():
                width *= int(mod)
                ty = ir.ArrayType(ty, int(mod))
            else:
                ty = ir.PointerType(ty)
        glb = ir.GlobalVariable(self.module, ty, target[1:])
        
        # Initializer.
        if source:
            if ty_str=='char': source = self.make_bytearray((source+'\00').encode('utf-8'))
            glb.initializer = ir.Constant(ty, source)
            
        # Global consts.
        if target[1:].startswith('.const'):
            glb.global_constant=True
        self.globals[target] = glb

    def build_alloc(self, ty, target):
        ty = self.types[ty]
        loc = self.builder.alloca(ty, name=target[1:])
        self.loc[target] = loc
    
    def build_alloc_(self, ty, target, **kwargs):
        ty = self.types[ty]
        
        # Modifier
        for mod in reversed(list(kwargs.values())):
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
        pointee = src.type.pointee
        
        # Pointers or array references.
        if isinstance(pointee, ir.PointerType):
            if isinstance(pointee.pointee, ir.FunctionType):
                loc = self.builder.load(src)
            else:
                temp = self.builder.load(src)
                loc = self.builder.load(temp)
        else:
            loc = self.builder.load(src)
        
        self.loc[target] = loc
    
    def build_store(self, _, src, target):
        src = self.loc[src]
        loc = self.loc.get(target, None)
        if loc:
            self.builder.store(src, loc)
        else:
            self.loc[target] = src
            
    def build_store_(self, ty, src, target, **kwargs):
        src = self.loc[src]
        target = self.loc.get(target, None)
        if isinstance(target.type.pointee, ir.ArrayType):
            
            # Get array size in bytes.
            size = 1
            for dim in kwargs.values(): size *= int(dim)
            if ty == 'float': size *= 8
            elif ty == 'int': size *= self.types['int'].width//8
            
            # Getting needed types.
            char_ptr = self.types['char_*']
            i64 = self.types['int_64']
            false = ir.Constant(self.types['bool'], False)
            
            # Memcpy and cast to char pointer
            cp = self.module.declare_intrinsic('llvm.memcpy', [char_ptr, char_ptr, i64])
            src = self.builder.bitcast(src, char_ptr)
            target = self.builder.bitcast(target, char_ptr)
            self.builder.call(cp, [target, src, ir.Constant(i64, size), false])
        else:
            double_pointer = isinstance(target.type.pointee, ir.PointerType)
            temp = self.builder.load(target) if double_pointer else target
            self.builder.store(src, temp)
    
    def build_literal(self, ty, value, target):
        # NOTE: Variables that were not allocated are sprouting in self.loc
        if ty=='char': value = ord(value[1])
        ty = self.types[ty]
        val = ir.Constant(ty, value)
        loc = self.loc.get(target, None)
        if loc:
            self.builder.store(val, loc)
        else:
            self.loc[target] = val
    
    def build_elem(self, _, src, idx, target):
        int_t = self.types['int']
        src, idx = self.loc[src], self.loc[idx]
        base = ir.Constant(idx.type, 0)
        
        # Matrix
        # TODO: generalize to N-dimensional arrays. Currently only 1 or 2.
        if isinstance(src.type.pointee.element, ir.ArrayType):
            n = src.type.pointee.element.count
            if isinstance(idx, ir.Constant):
                i = ir.Constant(int_t, idx.constant // n)
                j = ir.Constant(int_t, idx.constant % n)
            else:
                n = ir.Constant(int_t, n)
                i = self.builder.sdiv(idx, n)
                j = self.builder.srem(idx, n)
            
            temp = self.builder.gep(src, [base, i])
            loc = self.builder.gep(temp, [base, j])
            
        # Array
        else:
            loc = self.builder.gep(src, [base, idx])
        self.loc[target] = loc
    
    def build_get(self, _, src, target):
        # This function is never called.
        assert False, "Get instruction without '*'!"
    
    def build_get_(self, _, src, target, **kwargs):
        src = self.loc[src]
        target = self.loc[target]
        self.builder.store(src, target)
    
    # Function Operations
    def build_param(self, _, src):
        self.args.append(self.loc[src])
    
    def build_call(self, ty, name, target=None):
        try:
            fn = self.module.get_global(name[1:])
        except KeyError:
            # Get args
            arg_types = [arg.type for arg in self.args]
            
            # Prototype
            func_type = ir.FunctionType(self.types[ty], arg_types)
            fn = ir.Function(self.module, func_type, name=name[1:])

        loc = self.builder.call(fn, self.args)
        
        # Check Void
        if target:
            self.loc[target] = loc
        self.args = []
    
    def build_return(self, ty, value=None):
        if ty == 'void':
            self.builder.ret_void()
        else:
            value = self.loc[value]
            self.builder.ret(value)
            
    # Builtins
    def build_print(self, ty, target=None):
        types = {'int':'%d', 'float':'%.2f', 'char':'%c', 'string':'%s'}
        if target:
            # get the object assigned to target
            target = self.loc[target]
            self._cio('printf', types[ty], target)
        else:
            self._cio('printf', '\n')
            
    def build_read(self, ty, target):
        types = {'int':'%d', 'float':'%lf', 'char':'%c', 'string':'%s'}
        target = self.loc[target]
        self._cio('scanf', types[ty], target)
    
    def build_read_(self, ty, target, **kwargs):
        self.build_read(ty, target)
