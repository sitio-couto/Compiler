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

class uCIRTranslator(object):
    def __init__(self, builder):
        self.builder = builder
        self.module  = None
        self.regs    = dict()
        self.types   = dict()
        self.init_types()
    
    def init_types(self):
        int_t   = ir.IntType(32)
        float_t = ir.FloatType()
        char_t  = ir.IntType(8)
        void_t  = ir.VoidType()
        str_t   = ir.PointerType(char_t)
        
        self.types.add('int', int_t)
        self.types.add('float', float_t)
        self.types.add('char', char_t)
        self.types.add('void', void_t)
        
        self.types.add('int_*', int_t.as_pointer())
        self.types.add('float_*', float_t.as_pointer())
        self.types.add('char_*', char_t.as_pointer())
        self.types.add('void_*', void_t.as_pointer())
        self.types.add('string', str_t.as_pointer())
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
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fadd(left, right)
        else:
            loc = self.builder.add(left, right)
        self.regs[target] = loc

    def build_sub(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fsub(left, right)
        else:
            loc = self.builder.sub(left, right)
        self.regs[target] = loc

    def build_mul(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fmul(left, right)
        else:
            loc = self.builder.mul(left, right)
        self.regs[target] = loc

    def build_div(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fdiv(left, right)
        else:
            loc = self.builder.sdiv(left, right)
        self.regs[target] = loc

    def build_mod(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.frem(left, right)
        else:
            loc = self.builder.srem(left, right)
        self.regs[target] = loc
    
    # Relational Operations
    def build_gt(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('>', left, right)
        else:
            loc = self.builder.icmp('>', left, right)
        self.regs[target] = loc
    
    def build_ge(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('>=', left, right)
        else:
            loc = self.builder.icmp('>=', left, right)
        self.regs[target] = loc
    
    def build_eq(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('==', left, right)
        else:
            loc = self.builder.icmp('==', left, right)
        self.regs[target] = loc
    
    def build_le(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('<=', left, right)
        else:
            loc = self.builder.icmp('<=', left, right)
        self.regs[target] = loc
    
    def build_le(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('<', left, right)
        else:
            loc = self.builder.icmp('<', left, right)
        self.regs[target] = loc
    
    def build_ne(self, ty, left, right, target):
        left,right = self.regs[left],self.regs[right]
        if ty == 'float':
            loc = self.builder.fcmp('!=', left, right)
        else:
            loc = self.builder.icmp('!=', left, right)
        self.regs[target] = loc
    
    # TODO: correct?
    def build_and(self, _, left, right, target):
        left,right = self.regs[left],self.regs[right]
        loc = self.builder.and_(left, right)
        self.regs[target] = loc
    
    def build_or(self, _, left, right, target):
        left,right = self.regs[left],self.regs[right]
        loc = self.builder.or_(left, right)
        self.regs[target] = loc
    
    def build_not(self, _, left, right, target):
        left,right = self.regs[left],self.regs[right]
        loc = self.builder.neg(left, right)
        self.regs[target] = loc

    # Cast operations
    def build_fptosi(self, _, value, target):
        value = self.regs[value]
        loc = self.builder.fptosi(value, self.types['int'])
        self.regs[target] = loc

    def build_sitofp(self, _, value, target):
        value = self.regs[value]
        loc = self.builder.sitofp(value, self.types['float'])
        self.regs[target] = loc
    
    # Branch Operations
    #TODO: terminators (block operations). Probably incorrect atm.
    def build_jump(self, _, target):
        target = self.regs[target]
        self.builder.branch(target)
    
    def build_cbranch(self, _, test, true, false):
        test = self.regs[test]
        true, false = self.regs[true], self.regs[false]
        self.builder.cbranch(test, true, false)
    
    # Memory Operations
    # Function Operations
    # Builtins
