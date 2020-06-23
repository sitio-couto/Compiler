'''
Fourth Project: Translation from uCIR to LLVM IR.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 22/06/2020.
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
        float_t = ir.FloatType()
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
        self.types['string']  = str_t.as_pointer()
        return

    def translate(self, module, code):
        ''' Main translation function. '''
        self.module = module
        pass
    
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
    def build_gt(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('>', left, right)
        else:
            loc = self.builder.icmp('>', left, right)
        self.loc[target] = loc
    
    def build_ge(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('>=', left, right)
        else:
            loc = self.builder.icmp('>=', left, right)
        self.loc[target] = loc
    
    def build_eq(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('==', left, right)
        else:
            loc = self.builder.icmp('==', left, right)
        self.loc[target] = loc
    
    def build_le(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('<=', left, right)
        else:
            loc = self.builder.icmp('<=', left, right)
        self.loc[target] = loc
    
    def build_le(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('<', left, right)
        else:
            loc = self.builder.icmp('<', left, right)
        self.loc[target] = loc
    
    def build_ne(self, ty, left, right, target):
        left,right = self.loc[left],self.loc[right]
        if ty == 'float':
            loc = self.builder.fcmp('!=', left, right)
        else:
            loc = self.builder.icmp('!=', left, right)
        self.loc[target] = loc
    
    # TODO: correct?
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
    # TODO: Probably incorrect atm.
    # TODO: terminators (block operations).
    def build_jump(self, _, target):
        target = self.loc[target]
        self.builder.branch(target)
    
    def build_cbranch(self, _, test, true, false):
        test = self.loc[test]
        true, false = self.loc[true], self.loc[false]
        self.builder.cbranch(test, true, false)
    
    # Memory Operations
    # TODO: add global, store, elem, get 
    # TODO: complete with modifiers
    def build_alloc(self, ty, target):
        ty = self.types[ty]
        loc = self.builder.alloca(ty, size=1, name=target)
        self.loc[target] = loc
    
    # TODO: complete with modifiers    
    def build_load(self, _, src, target):
        src = self.loc[src]
        loc = self.builder.load(src)
        self.loc[target] = loc
    
    # TODO: correct?
    def build_literal(self, ty, value, target):
        ty = self.types[ty]
        val = ir.Constant(ty, value)
        self.loc[target] = val
    
    # Function Operations
    # TODO: complete with define.
    def build_param(self, _, src):
        src = self.loc[src]
        self.args.append(src)
    
    # TODO: probably incorrect/incomplete atm.
    # TODO: add void return
    def build_call(self, _, fn, target):
        fn = self.module.get_global(fn)
        loc = self.builder.call(fn, self.args)
        self.loc[target] = loc
        self.args = []
    
    # TODO: probably incorrect/incomplete atm.
    # TODO: add block operations and save return value somewhere.
    def build_return(self, ty, value):
        if ty == 'void':
            self.builder.ret_void()
        else:
            value = self.loc[value]
            self.builder.ret(value)
            
    # Builtins
    # TODO: read/print - scanf/printf?
