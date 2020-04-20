'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 20/04/2020.
'''
 
import uCType
import uCAST as ast
from os.path import exists

class SymbolTable(object):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self):
        self.symtab = {}
    def lookup(self, a):
        return self.symtab.get(a, None)
    def add(self, a, v):
        self.symtab[a] = v
    def pop(self, a):
        self.symtab.pop(a)
    
    def __str__(self, offset=''):
        text = ''
        for name in self.symtab.keys():
            text += f"{offset}    {name}\n"
        return text

class SignaturesTable():
    '''
    Class responsible for keeping funcions signatures (type, name and parameters).
    Is also used to keep consistency between functions declaration, definition and calls.S
    Atributes:
        - sign: dictionary with func names as keys, and dictionary as values.
                Each value containes the following 
                    ret:ast.Type - Type class for function return type 
                    name:string - function name 
                    params:List - List of parameters
                Each item in params contains: 
                    type:ast.Type - Type class for the variable
                    name:string - variable name
    '''

    def __init__(self):
        self.sign = dict()  # Check which functions were declared (signatures: int main(float f);)
    
    # Register function signature (when Decl is declaring a FuncDecl)
    # NOTE: function calls will be validate using self.sign table
    # Params: 
    #   node - a FuncDecl class from the uCAST
    def sign_func(self, node, defining):
        name      = node.type.declname.name # Get function's name
        ty        = node.type.type          # get func type (FuncDecl.VarDecl.Type)
        params    = []                      # Use to keep function params types

        if node.params: 
            paramlist = node.params.params 
        else:
            paramlist = []

        # Getting functions parameters types and names
        for p in paramlist:
            if isinstance(p.type, ast.VarDecl):
                params.append(p.type.type) # Append ast.Type instances
        new = dict(type=ty, params=params, defined=defining)

        # If function was already signed, validate signature
        if name in self.sign.keys() :
            signature = self.sign[name]
            
            # Check if this function was defined twice
            defined = signature['defined']
            condition = not defining or (defining and not defined)
            assert condition, f"Function {name} was defined twice"
            signature['defined'] = defining # Update flag if defining and not defined

            # Check return type and amount of paramters
            ret_type   = (ty.name[0] == signature['type'].name[0])
            qnt_params = (len(new['params']) == len(signature['params']))
            assert ret_type, "Function %s has multiple declarations: diffrent return types" % name
            assert qnt_params, "Function %s has exceding/missing arguments" % name
            
            # Check paramter types
            param_types = True # Assume their types match
            for (new, sign) in zip(new['params'], self.sign[name]['params']):
                param_types *= (sign.name[0] == new.name[0]) # Check if all params match
            assert param_types, "Function %s has incorrect parameter types" % name

        else : # Not signed yet? 
            self.sign[name] = new

    # Fetches the function's return type (node must be ast.ID)
    def get_return(self, node):
        return self.sign[node.name]['type']

    # Fetches the functions params types (node must be ast.ID)
    def check_params(self, fcall, fid):
        # NOTE: We must compare names (Type attr has coord which will differ)
        f_name = fcall.name.name

        # Fetch list of passed params
        if fcall.args:
            allowed = [ast.ID, ast.Constant, ast.FuncCall, ast.BinaryOp, ast.UnaryOp]
            params = []
            if not isinstance(fcall.args, ast.ExprList):
                p = fcall.args
                assert type(p) in allowed, f"Function call '{f_name}' has invalid argument {p}" 
                params = [p]
            else:
                for p in fcall.args.exprs:
                    assert type(p) in allowed, f"Function call '{f_name}' has invalid argument {p}" 
                    params.append(p)

            # Iterate through params checking their classes ans taking measures:
            # ID, Constant, FuncCall, BinOp, UnOp
            args = []
            for p in params:
                args.append(p.type.name[0])
        else: # It's possible to have no arguments
            args = []

        # Fetch expected params from signatures
        expects = [ty.name[0] for ty in self.sign[fid.name]['params']]

        return (args == expects)

    # Fetches signature (node must be ast.ID)
    def get_sign(self, node):
        return self.sign.get(node.name, None)
    
    def __str__(self):
        text = '\n'
        funcs = self.sign
        for f in funcs.keys():
            ret = funcs[f]['type'].name[0].name
            params = [x.name[0].name for x in funcs[f]['params']]
            text += f"{ret} {f} ("
            for arg in params: text +=f"{arg}, "
            text = text[:-2]+')\n'
        return str(text)

class ScopeStack():
    '''
    Class responsible for keeping variables scopes.
    Used for type checking variables as well as checking if they're are defined.
    Atributes:
        - stack: stack of SymbolTables. Each item is a different scope ([0] is global [-1] is local)
    '''
    def __init__(self):
        # Index 0 is the global scope, -1 is the current scope
        self.stack = [] # last element is the top of the stack
    
    # Add new scope (if a function definition started)
    # Every function definition is considered a new scope (new symboltable)
    def add_scope(self, node=None):
        sym_tab = SymbolTable()
        if node : node = node.decl.name # Get funcs name (None if loop)
        sym_tab.add(0, node)            # Add scope name to table with key 0 (only numeric)
        self.stack.append(sym_tab) 

    # Add a new variable to the current function's scope (in node VarDecl)
    def add_to_scope(self, node):
        # node should be Class ast.VarDecl
        scope = self.stack[-1]              # Get current scope (top of the stack)
        var_name = node.declname.name       # Get declared variable name
        assert not scope.lookup(var_name), "Variable '%s' defined twice in the same scope" % var_name 
        scope.add(node.declname.name, node) # Add to current scope      
    
    def add_func(self, node):
        # node should be Class ast.VarDecl
        f_name = node.declname.name  # Get declared variable name
        glob = self.stack[0]         # Get global scope
        loc = self.stack[-1]         # Get current scope (top of the stack)
        if not glob.lookup(f_name):  # Add global ref if func not defined
            glob.add(f_name, node)   # Add to global scope 
        if loc.lookup(f_name):       # if in current scope
            loc.pop(f_name)          # Remove from current scope.

    # Remove current scope from stack (when a FuncDef node ends)
    def pop_scope(self):
        self.stack.pop() 
    
    # Check the current enclosure
    def enclosure(self):
        scope = self.stack[-1]
        return scope.lookup(0)
    
    # Get current function scope.
    def nearest_func_scope(self):
        for scope in self.stack[::-1]:
            if scope.lookup(0): return scope
        return None

    # Check the current function
    def nearest_function(self):
        func = self.nearest_func_scope()
        return func.lookup(0) if func else None
    
    # TODO: Needs more testing, but seems to work.
    def set_returned(self):
        func = self.nearest_func_scope()
        if func: func.add('returned', True)

    # Get if function is returned.
    def check_returned(self):
        func = self.nearest_func_scope()
        return func.lookup('returned')

    # Check if ID name is within the current scope, return it's type
    # Must be of type ast.ID
    def in_scope(self, node):
        name = node.name
        
        # Check all scopes from last to global.
        for scope in self.stack[::-1]:
            var = scope.lookup(name)
            if var: break                       # Prioritize local
        return var

    def __str__(self):
        text = '\n'
        for (i,sym) in enumerate(self.stack):
            ids = list(sym.symtab.keys())
            ids.remove(0) # Remove enclosure
            text += f"Level {i} => {ids}\n"
        return text

# MAJOR TODO: COORDS IN ASSERTION ERRORS.
# MINOR TODO: code organization (variable names and accessing attributes), improving assertion error message organization and description.
# MICRO TODO: more details about minor and major todos and other small issues can be found in their respective spots in code.

class uCSemanticCheck(ast.NodeVisitor):
    '''
    Program checking class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self, parser):

        # Set flags
        self.flags = dict(inFDef=False)

        # Include parser
        self.parser = parser
        
        # Initialize the types table
        self.types = SymbolTable()

        # Initialize scope stack
        self.scopes = ScopeStack()

        # Initialize signatures table
        self.signatures = SignaturesTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.types.add("int",uCType.int_type)
        self.types.add("float",uCType.float_type)
        self.types.add("char",uCType.char_type)
        self.types.add("string",uCType.string_type)
        self.types.add("bool",uCType.boolean_type)
        self.types.add("void",uCType.void_type)
        self.types.add("ptr",uCType.ptr_type)
        self.types.add("array", uCType.arr_type)
    
    def test(self, data, show_ast):
        self.parser.lexer.reset_line_num()
        
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
            ast = self.parser.parse(data, False)
        else:
            ast = self.parser.parse(data, False)
        
        # Show AST
        if show_ast:
            ast.show()
            
        # Semantic test
        self.visit_Program(ast)
        # print(self.signatures)
    
    def visit_Program(self, node):
        # 1. Add global scope.
        self.scopes.add_scope()
        
        # 2. Visit all of the statements
        for gdecl in node.gdecls:
            self.visit(gdecl)
        
        # 3. Remove global scope.
        self.scopes.pop_scope()
        
        # 4. Clear signatures table for next semantic check.
        self.signatures = SignaturesTable()

    def visit_ArrayDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Add array type to array.
        var = self.get_inner_type(node.type)
        
        arr_type = self.types.lookup('array')
        var.name.insert(0, arr_type)
        
        # 3. Check dimensions.
        if node.dims:
            # 3.1. Visit dims.
            self.visit(node.dims)
        
            # 3.2. Check if array size is nonnegative.
            if isinstance(node.dims, ast.UnaryOp):
                assert node.dims.op != '-', "%s declared as an array with a negative size." % var.declname

    def visit_ArrayRef(self, node):
        # 1. Visit name (ID)
        self.visit(node.name)
        name = node.name
        
        # 2. Check if ID is array or ptr.
        ptr = self.types.lookup('ptr')
        arr = self.types.lookup('array')
        assert name.type.name[0] == ptr or name.type.name[0] == arr, "ID %s is not an array or pointer." % name.name

        # 3. Visit subscript.
        self.visit(node.subsc)
                
        # 4. Check if subscript is a valid ID, if ID.
        if isinstance(node.subsc, ast.ID):
            assert not self.signatures.get_sign(node.subsc), "ID %s is a function, can't be used as subscript." %  node.subsc.name

        # 5. Check subscript type.
        type_int = self.types.lookup('int')
        ty = node.subsc.type.name[-1]
        assert ty == type_int, "Array index must be of type int." 
        
        # 6. Assign node type
        node.type = ast.Type(name.type.name[1:])
        
    def visit_Assignment(self, node):
        ptr = self.types.lookup('ptr')

        # 1. Visit left value
        self.visit(node.lvalue)
        lvalue = node.lvalue
        
        # 2. Check if ID or ArrayRef.
        if isinstance(lvalue, ast.ID):
            func = self.signatures.get_sign(lvalue)
            if func: assert func['type'].name[0] == ptr, "Assigning to function %s." % lvalue.name
        elif not isinstance(lvalue, ast.ArrayRef):
            assert False, "Expression is not assignable."
        
        # 3. Check if assignment is valid.
        if node.op != '=':
            ty = lvalue.type.name[0]
            assert node.op in ty.assign_ops, "Assignment not valid for type %s." % ty.name
        
        # 4. Visit right value.
        self.visit(node.rvalue)
        rvalue = node.rvalue

        # 5. If ID, check if function.
        if isinstance(rvalue, ast.ID):
            assert not self.signatures.get_sign(rvalue), "Assigning function %s." % rvalue.name

        # 6. Check types
        string = self.types.lookup('string')
        array = self.types.lookup('array')
        ltype = lvalue.type.name
        rtype = rvalue.type.name
        
        # 6.1. Special cases.
        if ltype[0] == array:
            assert False, "Array is not assignable."
        elif rtype[0] == string:
            char = self.types.lookup('char')
            assert ltype == [ptr,char], "Type mismatch in assignment"
        elif ltype[0] == ptr:
            assert rtype[0] == ptr or rtype[0] == array, "Pointer can only be assigned array or other pointer."
            assert ltype[1:] == rtype[1:], "Type mismatch in assignment"
        
        # 6.2. Regular case
        else:
            assert ltype == rtype, "Type mismatch in assignment"
        
    def visit_Assert(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        
        # 2. Expression must be boolean
        self.boolean_check(node.expr)

    def visit_BinaryOp(self, node):
        # 1. Visit left value
        self.visit(node.lvalue)
        lvalue = node.lvalue

        # 2. If ID, check if function
        if isinstance(lvalue, ast.ID):
            assert not self.signatures.get_sign(lvalue), "Function %s in binary operation." % lvalue.name
        
        # 3. Visit right value
        self.visit(node.rvalue)
        rvalue = node.rvalue
        
        # 4. If ID, check if function        
        if isinstance(rvalue, ast.ID):
            assert not self.signatures.get_sign(rvalue), "Function %s in binary operation." % rvalue.name

        # 5. Check types.
        assert lvalue.type.name == rvalue.type.name, "Type mismatch in binary operation"
        
        # 6. Make sure the operation is supported
        ty = lvalue.type.name[0]
        assert node.op in ty.bin_ops.union(ty.rel_ops), "Unsupported operator %s in binary operation for type %s." % (node.op, ty.name)
        
        # 7. Assign the result type
        if node.op in ty.bin_ops:
            node.type = lvalue.type
        else:
            node.type = ast.Type([self.types.lookup('bool')])

    def visit_Break(self, node):
        # 1. Check if enclosure is a loop, error if not
        assert not self.scopes.enclosure(), "'break' can only be used inside a loop"

    def visit_Cast(self, node):
        # 1. Visit type.
        node.type.name = [node.type.name]
        self.visit(node.type)
        
        # 2. Visit Expression
        self.visit(node.expr)
        
        # 3. Check if the expression type is castable to "type".
        ty = self.get_inner_type(node.expr).name[0]
        cast = node.type.name[0].name
        
        assert cast in ty.cast_types, "Type %s can't be casted to type %s." % (ty.name, cast)
        
    def visit_Compound(self, node):
        # 1. Visit all declarations
        if node.decls:
            for decl in node.decls:
                self.visit(decl)
            
        # 2. Visit all statements
        if node.stats:
            for stat in node.stats:
                self.visit(stat)

    def visit_Constant(self, node):
        # 1. Constant type to Type, with an uCType.
        if isinstance(node.type, str):
            ty = self.types.lookup(node.type)
            assert ty, "Unsupported type %s." % node.type
            node.type = ast.Type([ty], node.coord)

        # 2. Convert to respective type. Char by default.
        ty = node.type.name[0]
        if ty.name == 'int':
            node.value = int(node.value)
        elif ty.name == 'float':
            node.value = float(node.value)
        
    def visit_Decl(self, node):
        # 1. Visit type
        self.visit(node.type)
        ty = node.type

        # 2. Visit name ID.
        self.visit(node.name)
        
        # 3. Visit initializers, if defined.
        if node.init:
            self.visit(node.init)
            
            # Check instance of initializer.
            # 3.1. Constant
            if isinstance(node.init, ast.Constant):
                const = node.init
                ty = ty.type
                strng = self.types.lookup('string')

                # 3.1.1. If constant is string
                if const.type.name[0] == strng:
                    char = self.types.lookup('char')
                    
                    # 3.1.1.1. Check if char array.
                    assert isinstance(node.type, ast.ArrayDecl) and ty.type.name[-1] == char, "A string initializer can only be assigned to a char array."
                    
                    # 3.1.1.2. Check length.
                    if node.type.dims:
                        # TODO: dims can be UnOp or other expression... Not worth it?
                        assert len(const.value) <= node.type.dims.value, "Initializer-string for char array is too long."
                    else:
                        node.type.dims = ast.Constant('int', len(const.value))
                        self.visit_Constant(node.type.dims)
                
                # 3.1.2. Any other constant
                else:
                    assert not isinstance(node.type, ast.ArrayDecl), "Array declaration without explicit size needs an initializer list."
                    assert ty.name[0] == const.type.name[0], "Initialization type mismatch in declaration."
            
            # 3.2. InitList
            elif isinstance(node.init, ast.InitList):
                exprs = node.init.exprs
                
                # 3.2.1. Variable
                if isinstance(ty, ast.VarDecl):
                    assert len(exprs) == 1, "Too many elements for variable initialization"
                    assert ty.type.name == exprs[0].type.name, "Initialization type mismatch in declaration."
                
                # 3.2.2. Array
                elif isinstance(ty, ast.ArrayDecl):
                    
                    # 3.2.2.1. If not explicit size of array, use initialization as size.
                    if ty.dims is None:
                        ty.dims = ast.Constant('int', len(exprs))
                        self.visit_Constant(ty.dims)
                    else:
                        # TODO: dims can be unOp or other expression... Not worth it?
                        assert ty.dims.value == len(exprs), "Size mismatch in variable initialization"
                    
                    # 3.2.2.2. Get basic type.
                    ty = self.get_inner_type(ty)
                    assert ty, "No basic type in array declaration."
                    
                    # 3.2.2.3. Check type.
                    for expr in exprs:
                        assert ty.name[-1] == expr.type.name[-1], "Initialization type mismatch in declaration."
                
                # 3.2.3. Pointer
                elif isinstance(ty, ast.PtrDecl):
                    
                    # 3.2.3.1. Check length.
                    assert len(exprs) == 1, "Too many elements for variable initialization"

                    # 3.2.3.2. Get basic type.
                    ty = self.get_inner_type(ty)
                    assert ty, "No basic type in ptr declaration."
                    
                    # 3.2.3.3. Initializer has to be of same type
                    assert ty.name == exprs[0].type.name, "Initialization type mismatch in declaration."

            # 3.3. Any other expression.
            else:
                assert ty.type.name == node.init.type.name, "Initialization type mismatch in declaration."
        
        # 4. If array declaration has no init.    
        elif isinstance(ty, ast.ArrayDecl):
            assert ty.dims, "An array has to have a size or initializer."
    
    def visit_DeclList(self, node):
        # 1. Visit all decls.
        for decl in node.decls:
            self.visit(decl)
    
    def visit_EmptyStatement(self, node):
        return
    
    def visit_ExprList(self, node):
        # 1. Visit all expressions
        for expr in node.exprs:
            self.visit(expr)
            
    def visit_For(self, node):
        # 1. Create scope 
        self.scopes.add_scope()
        
        # 2. Visit initializer.
        if node.init:
            self.visit(node.init)
        
        # 3. Check condition.
        if node.cond:
            
            # 3.1. Visit condition.
            self.visit(node.cond)
            
            # 3.2 Condition must be boolean
            self.boolean_check(node.cond)
        
        # 4. Visit next.
        if node.next:
            self.visit(node.next)
        
        # 5. Visit body.
        if node.body:
            self.visit(node.body)

        # 6. Remove scope
        self.scopes.pop_scope()

    def visit_FuncCall(self, node):
        # 1. Visit name ID.
        self.visit(node.name)
        name = node.name
        
        # 2. Check if identifier is a function.
        assert self.signatures.get_sign(name), "Identifier in function call is not a function."
        
        # 3. Visit arguments.
        if node.args:
            self.visit(node.args)
        
        # 4. Check args types
        test = self.signatures.check_params(node, name)
        assert test, f"Incorrect arguments passed to '{name.name}' function"

        # 5. Add type
        node.type = self.signatures.get_return(name)
    
    def visit_FuncDecl(self, node):
        # 1. Visit type
        self.visit(node.type)
        
        # 2. Add to global scope.
        self.scopes.add_func(node.type)
        
        # 3. Visit params.
        if node.params:
            self.visit(node.params)
        
        # 4. Sign function.
        define = (True if self.flags['inFDef'] else False)
        self.signatures.sign_func(node, define)
    
    def visit_FuncDef(self, node):
        # 1. Setup flags
        self.flags['inFDef'] = True

        # 2. Add scope
        self.scopes.add_scope(node=node)

        # 3. Visit type.
        self.visit(node.type)
                        
        # 4. Visit declaration.
        self.visit(node.decl)

        # 5. Visit parameter list
        if node.params:
            self.visit(node.params)
                
        # 6. Visit function.
        if node.body:
            self.visit(node.body)
    
        # 7. Check if returned.
        void = self.types.lookup('void')
        if node.type.name[-1] != void:
            assert self.scopes.check_returned(), "No return from a non-void function."
        
        # 8. Remove scope
        self.scopes.pop_scope()

        # 9. Setdown flags
        self.flags['inFDef'] = False
    
    def visit_GlobalDecl(self, node):
        # 1. Visit every global declaration.
        for decl in node.decls:
            
            # 1.1. Check declaration type.
            ty = decl.type
            while not isinstance(ty, ast.FuncDecl) and not isinstance(ty, ast.VarDecl):
                ty = ty.type
            
            # 1.2. If function declaration, create temporary scope.
            if isinstance(ty, ast.FuncDecl):
                self.scopes.add_scope()
                self.visit(decl)
                self.scopes.pop_scope()
            else:
                self.visit(decl)
    
    def visit_ID(self, node):
        # 1. Check if ID was defined.
        decl = self.scopes.in_scope(node)
        assert decl, "ID %s is not defined." % node.name
        
        # 2. Assign type
        node.type = decl.type
    
    def visit_If(self, node):
        # 1. Visit the condition
        self.visit(node.cond)
        
        # 2. Condition must be boolean
        self.boolean_check(node.cond)
        
        # 3. Visit statements
        if node.if_stat:
            self.visit(node.if_stat)
        
        if node.else_stat:
            self.visit(node.else_stat)
    
    def visit_InitList(self, node):
        # 1. Visit expressions
        for expr in node.exprs:
            self.visit(expr)
                    
    def visit_ParamList(self, node):
        # 1. Visit parameters.
        for param in node.params:
            self.visit(param)
    
    def visit_Print(self, node):
        # 1. Visit the expressions.
        if node.expr:
            self.visit(node.expr)

    def visit_PtrDecl(self, node):
        # 1. Visit pointer
        self.visit(node.type)
        
        # 2. Add ptr type to Type
        ty = self.get_inner_type(node.type)
        ptr_type = self.types.lookup('ptr')
        ty.name.insert(0, ptr_type)
        
    def visit_Read(self, node):
        # 1. Visit the expressions.
        self.visit(node.expr)

    def visit_Return(self, node):
        # 1. Check expression.
        if node.expr:
            
            # 1.1. Only 1 expression is allowed to return.
            assert not isinstance(node.expr, ast.ExprList), "Only one return expression is allowed."
            
            # 1.2. Visit expression.
            self.visit(node.expr)
            ty = node.expr.type.name
        else:
            ty = [self.types.lookup('void')]
            
        # 2. Check return type.
        # TODO: in most tests, int functions have return with no expression. Mistake?
        ret = self.signatures.get_return(self.scopes.nearest_function())
        assert ty == ret.name, "Incorrect return type."
        
        # 3. Set function as returned
        # TODO: doesn't recognize if return is inside if... Not worth it?
        self.scopes.set_returned()

    def visit_Type(self, node):
        # 1. Change the strings to uCType.
        # NOTE: because of the array and ptr types, node.name can have more than one item.
        for i, name in enumerate(node.name or []):
            if not isinstance(name, uCType.uCType):
                ty = self.types.lookup(name)
                assert ty, "Unsupported type %s." % name
                node.name[i] = ty
        
    def visit_UnaryOp(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        
        # 2. Make sure the operation is supported.
        ty = node.expr.type
        assert node.op in ty.name[0].un_ops, "Unsupported operator %s in unary operation for type %s." % (node.op, ty.name[0].name)
        
        # 3. Assign the result type.
        # & => integer (returns address)
        # ! => Bool (logical negation)
        # *,++,--,-,+ => same type of the nearby variable 
        if node.op == '*':
            ty = ast.Type(ty.name[1:])
            self.visit(ty)
        elif node.op == '&':
            ptr = self.types.lookup('ptr')
            ty.name.insert(0, ptr)
        elif node.op == '!':
            ty = ast.Type(['bool'])
            self.visit(ty)

        node.type = ty
        
    def visit_VarDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Check scope and insert in symbol table.
        if isinstance(node.declname, ast.ID):
            self.scopes.add_to_scope(node)
        
        # 3. Visit name.
        self.visit(node.declname)

    def visit_While(self, node):
        # 1. Create Scope
        self.scopes.add_scope()

        # 2. Visit condition.
        self.visit(node.cond)

        # 3. Condition must be boolean
        self.boolean_check(node.cond)

        # 4. Visit body.
        if node.body:
            self.visit(node.body)

        # 5. Create Scope
        self.scopes.pop_scope()

    ## AUXILIARY FUNCTIONS ##
    def boolean_check(self, cond):
        ''' Check if a condition is boolean.'''
        boolean = self.types.lookup('bool')
        
        if isinstance(cond.type, uCType.uCType) :
            ty = cond.type
        else:
            ty = cond.type.name[0]
        
        if hasattr(cond, 'type'):
            assert ty == boolean, "Expression must be boolean, and is %s instead." % ty.name
        else:
            assert False, "Expression must be boolean."
        
    def get_inner_type(self, node):
        ''' Get innermost type node. Useful in declarations. '''
        ty = node
        while ty and not isinstance(ty, ast.Type):
            ty = ty.type
        return ty
