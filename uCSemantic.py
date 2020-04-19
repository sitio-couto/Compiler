'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 19/04/2020.
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
    # TODO: Insert in nodes | Handle double definition | Handle type checking

    def __init__(self):
        self.sign = dict()  # Check which functions were declared (signatures: int main(float f);)
    
    # Register function signature (when Decl is declaring a FuncDecl)
    # NOTE: function calls will be validate using self.sign table
    # Params: 
    #   node - a Decl (of a FuncDef) class form the uCAST
    def sign_func(self, node):
        name      = node.name               # Get function's name
        ty        = node.type.type.type     # get func type (Decl.FuncDecl.VarDecl.Type)
        params    = [] # Use to keep function params types

        if node.type.params:
            paramlist = node.type.params.params # From Decl get FuncDecl Params attribute
        else:
            paramlist = []

        # Getting functions parameters types and names
        for p in paramlist:
            if isinstance(p.type, ast.VarDecl):
                params.append(p.type.type)
            # TODO: array declarations (might work this way actually)
        new = dict(type=ty, params=params)

        # If function was already signed, validate signature
        if name in self.sign.keys() :
            passed = new['params']
            needed = self.sign[name]['params']

            # Check return type and amount of paramters
            ret_type    = (ty == self.sign[name]['type'])
            qnt_params  = (len(passed)==len(needed))
            assert ret_type, "Function %s has multiple declarations: diffrent return types" % name
            assert qnt_params, "Function %s missing arguments" % name
            
            # Check paramter types
            param_types = True
            for (new, sign) in zip(new['params'], sign[name]['params']):
                param_types *= (sign.type == new.type) # Check param type
            assert param_types, "Function %s has incorrect paramter types" % name

        else : # Not signed yet? 
            self.sign[name] = new

    # Fetches the function's return type
    def check_return(self, name):
        return self.sign[name]['type']

    # Fetches signature
    def get_function(self, name):
        return self.sign.get(name, None)
    
    def __str__(self):
        text = '\n'
        funcs = self.sign
        for f in funcs.keys():
            ret = funcs[f]['type'].type.name[0].name
            params = [x.name[0].name for x in funcs[f]['params']]
            text += f"{ret} {f.name} ("
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
    def add_scope(self):
        # Every function definition is considered a new scope (new symboltable)
        self.stack.append(SymbolTable()) 

    # Add a new variable to the current function's scope (in node VarDecl)
    def add_to_scope(self, node):
        # node should be Class ast.VarDecl
        var_name = node.declname.name       # Get declared variable name
        scope = self.stack[-1]              # Get current scope (top of the stack)
        assert not scope.lookup(var_name), "Variable '%s' defined twice in the same scope" % var_name 
        scope.add(node.declname.name, node) # Add to current scope      
    
    def add_func(self, node):
        # node should be Class ast.VarDecl
        f_name = node.declname.name  # Get declared variable name
        glob = self.stack[0]         # Get current scope (top of the stack)
        if not glob.lookup(f_name):  # Add global ref if func not defined
            glob.add(f_name, node)   # Add to current scope 

    # Remove current scope from stack (when a FuncDef node ends)
    def pop_scope(self):
        print(self)
        self.stack.pop() 
    
    # Check if ID name is within the current scope, return it's type
    def in_scope(self, node):
        # node arg mus be a str (var name) or one of these classes: Decl, ID
        if isinstance(node, ast.ID) : name = node.name
        else : raise Exception(f"Cannot lookup {type(node)} in scope.")
        local = self.stack[-1].lookup(name) # Check current scope
        glob  = self.stack[0].lookup(name)  # Check global scope
        return local or glob # Check if in any (local is prioritized)

    def __str__(self):
        text = '\n'
        for (i,sym) in enumerate(self.stack): 
            text += f"Level {i} => {list(sym.symtab.keys())}\n"
        return text

# MAJOR TODO: SCOPE, ENVIRONMENT (func_type, for instance), NEW ATTRIBUTES IN NODES, COORDS IN ASSERTION ERRORS, THE ID PROBLEM, CHECK ARRAY AND PTR TYPES, OTHER SEMANTIC RULES.
# MINOR TODO: code organization (variable names and accessing attributes), improving assertion error message organization and description, reduce lookups.
# MICRO TODO: more details about minor and major todos and other small issues can be found in their respective spots in code.

class CheckProgramVisitor(ast.NodeVisitor):
    '''
    Program checking class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self, parser):
        
        # Define flags
        self.flags = dict(inFDef=False)

        # Include parser
        self.parser = parser
        
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Initialize scope stack
        self.scopes = ScopeStack()

        # Initialize signatures table
        self.signatures = SignaturesTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.symtab.add("int",uCType.int_type)
        self.symtab.add("float",uCType.float_type)
        self.symtab.add("char",uCType.char_type)
        self.symtab.add("string",uCType.string_type)
        self.symtab.add("bool",uCType.boolean_type)
        self.symtab.add("void",uCType.void_type)
        self.symtab.add("array",uCType.array_type)
        self.symtab.add("ptr",uCType.ptr_type)
    
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

    def visit_ArrayDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Add array type to array.
        var = node.type
        while not isinstance(var, ast.VarDecl):
            var = var.type
        
        # TODO: correct?
        arr_type = self.symtab.lookup('array')
        var.type.name.insert(0, arr_type)
        
        # 3. Check dimensions.
        if node.dims:
            # 3.1. Visit dims.
            self.visit(node.dims)
        
            # 3.2. Check if array size is nonnegative.
            if isinstance(node.dims, ast.UnaryOp):
                assert node.dims.op != '-', "%s declared as an array with a negative size." % var.declname

    def visit_ArrayRef(self, node):
        # 1. Visit name
        self.visit(node.name)
        
        # 2. Check if ID is valid
        name = self.scopes.in_scope(node.name)
        assert name, "ID %s is not defined." % node.name.name

        # 3. Visit subscript.
        self.visit(node.subsc)
                
        # 3. Check if subscript is a valid ID, if ID.
        # TODO: scope and ID type (must be variable)
        if isinstance(node.subsc, ast.ID):
            sub = self.scopes.in_scope(node.subsc)
            assert sub, "ID %s is not defined." % node.subsc.name
            ty = name.type.name[-1]
        else:
            ty = node.subsc.type.name[-1]
        
        # 4. Check subscript type.
        type_int = self.symtab.lookup('int')
        assert ty == type_int, "Subscript must be an integer." # TODO: constant value or id name.
        
        # 5. Assign node type
        node.type = ast.Type([name.type.name[-1]])
        
    def visit_Assignment(self, node):
        # 1. Visit left value
        self.visit(node.lvalue)
        
        # 2. Is the variable defined in the scope (global/local).
        # TODO: check if ID is not function.
        if isinstance(node.lvalue, ast.ID):
            lvalue = self.scopes.in_scope(node.lvalue)   # TODO: not getting ID?
            assert lvalue, "Assigning to undefined symbol '%s'" % node.lvalue.name
        elif isinstance(node.lvalue, ast.ArrayRef):
            assert self.scopes.in_scope(node.lvalue.name), "Assigning to undefined symbol '%s'" % node.lvalue.name.name
            lvalue = node.lvalue
        else:
            assert False, "Expression is not assignable."
        
        # 3. Check if assignment is valid.
        if node.op != '=':
            ty = lvalue.type.name[0]      # TODO: name[-1]? Not necessary?
            assert node.op in ty.assign_ops, "Assignment not valid for type %s." % ty.name
        
        # 4. Visit right value.
        self.visit(node.rvalue)
        
        # 5. If ID, check if declared.
        if isinstance(node.rvalue, ast.ID):
            rvalue = self.scopes.in_scope(node.rvalue)
            assert rvalue, "ID %s is not defined." % node.rvalue.name
        elif isinstance(node.lvalue, ast.ArrayRef):
            assert self.scopes.in_scope(node.rvalue.name), "ID %s is not defined." % node.rvalue.name.name
            rvalue = node.rvalue
        else:
            rvalue = node.rvalue

        # 6. Check types
        # TODO: array can be assigned to ptr and vice-versa. Problem in simple5.uc
        assert lvalue.type.name == rvalue.type.name, "Type mismatch in assignment"
        
    def visit_Assert(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        
        # 2. Expression must be boolean
        self.boolean_check(node.expr)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        self.visit(node.lvalue)
        self.visit(node.rvalue)
        
        # TODO: Maybe change this, or add more things to ID inside visit.
        if isinstance(node.lvalue, ast.ID):
            lvalue = self.scopes.in_scope(node.lvalue)
            assert lvalue, "ID %s not defined in binary operation." % node.lvalue.name
        else:
            lvalue = node.lvalue
        
        if isinstance(node.rvalue, ast.ID):
            rvalue = self.scopes.in_scope(node.rvalue)
            assert rvalue, "ID %s not defined in binary operation." % node.rvalue.name
        else:
            rvalue = node.rvalue

        assert lvalue.type.name == rvalue.type.name, "Type mismatch in binary operation"
        
        # 2. Make sure the operation is supported
        ty = lvalue.type.name[0]                     # TODO: name[-1]? Not necessary?
        assert node.op in ty.bin_ops.union(ty.rel_ops), "Unsupported operator %s in binary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type
        if node.op in ty.bin_ops:
            if isinstance(node.lvalue, ast.ID):
                node.type = self.scopes.in_scope(node.lvalue).type
            else:
                node.type = node.lvalue.type
        else:
            node.type = self.symtab.lookup('bool')

    def visit_Break(self, node):
        # TODO: check if is inside a for/while.
        return

    def visit_Cast(self, node):
        # 1. Visit type.
        node.type.name = [node.type.name]
        self.visit(node.type)
        
        # 2. Visit Expression
        self.visit(node.expr)
        
        # 3. Check if the expression type is castable to "type".
        ty = node.expr.type
        while not isinstance(ty, ast.Type):
            ty = ty.type
        ty = ty.name[0]
        
        assert node.type.name[0].name in ty.cast_types, "Type %s can't be casted to type %s." % (ty.name, node.type.name[0].name)
        
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
            ty = self.symtab.lookup(node.type)
            assert ty, "Unsupported type %s." % node.type
            node.type = ast.Type([ty], node.coord)

        # 2. Convert to respective type. String by default.
        ty = node.type
        if ty.name == 'int':
            node.value = int(node.value)
        elif ty.name == 'float':
            node.value = float(node.value)
        # TODO: char? Anything else?
        
    def visit_Decl(self, node):
        # 1. If function, sign it.
        if isinstance(node.type, ast.FuncDecl): 
            self.signatures.sign_func(node)

        # 2. Visit type
        self.visit(node.type)
        
        # 3. Check if variable is defined in scope.
        self.scopes.in_scope(node.name)
        
        # 4. Visit initializers, if defined.
        if node.init:
            self.visit(node.init)
            
            # Check instance of initializer.
            # Constant
            if isinstance(node.init, ast.Constant):
                const = node.init
                ty = node.type.type
                strng = self.symtab.lookup('string')

                # If constant is string
                if const.type.name[0] == strng:
                    char = self.symtab.lookup('char')
                    
                    # Check if char array.
                    assert isinstance(node.type, ast.ArrayDecl) and ty.type.name[-1] == char, "A string initializer can only be assigned to a char array."
                    
                    # Check length.
                    if node.type.dims:
                        # TODO: dims can be BinOp or other expression...
                        assert len(const.value) <= node.type.dims.value, "Initializer-string for char array is too long."
                    else:
                        node.type.dims = ast.Constant('int', len(const.value))
                        self.visit_Constant(node.type.dims)
                
                # Any other constant
                else:
                    assert not isinstance(node.type, ast.ArrayDecl), "Array declaration without explicit size needs an initializer list."
                    assert ty.name[0] == const.type.name[0], "Initialization type mismatch in declaration."
            
            # InitList
            # TODO: if node.type is ArrayDecl and there is no InitList or dims, wrong
            elif isinstance(node.init, ast.InitList):
                exprs = node.init.exprs
                
                # Variable
                if isinstance(node.type, ast.VarDecl):
                    assert len(exprs) == 1, "Too many elements for variable initialization"
                    assert node.type.type == exprs[0].type, "Initialization type mismatch in declaration."
                
                # Array
                elif isinstance(node.type, ast.ArrayDecl):
                    
                    # If not explicit size of array, use initialization as size.
                    if node.type.dims is None:
                        node.type.dims = ast.Constant('int', len(exprs))
                        self.visit_Constant(node.type.dims)
                    else:
                        # TODO: dims can be binOp or other expression...
                        assert node.type.dims.value == len(exprs), "Size mismatch in variable initialization"
                
                # Pointer (TODO)
                elif isinstance(node.type, ast.PtrDecl):
                    assert True
    
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
        # TODO: A scope should be created here, but a nested one (must check top and second on top)
        # 1. Visit initializer.
        if node.init:
            self.visit(node.init)
        
        # 2. Check condition.
        if node.cond:
            
            # 2.1. Visit condition.
            self.visit(node.cond)
            
            # 2.2 Condition must be boolean
            self.boolean_check(node.cond)
        
        # 3. Visit next.
        if node.next:
            self.visit(node.next)
        
        # 4. Visit body.
        self.visit(node.body)

    def visit_FuncCall(self, node):
        # 1. Check if identifier was declared.
        self.visit(node.name)
        sym = self.scopes.in_scope(node.name)
        assert sym, "Unknown identifier in function call."
        
        # 2. Check if identifier is a function.
        assert self.signatures.get_function(sym.declname), "Identifier in function call is not a function."
        
        # 3. Visit arguments.
        self.visit(node.args)
        
        # 4. Add type
        node.type = self.signatures.check_return(sym.declname)
    
    def visit_FuncDecl(self, node):
        # 1. Add to global scope.
        self.scopes.add_func(node.type)
        
        # 2. Visit params.
        if self.flags['inFDef'] and node.params:
            self.visit(node.params)
    
    def visit_FuncDef(self, node):
        # Set flags
        self.flags['inFDef'] = True

        # 3. Add scope
        # TODO: adding scope here makes so the parameters are added to global scope, and that causes problems in ptr_function.uc
        self.scopes.add_scope()

        # 1. Visit type.
        self.visit(node.type)
                        
        # 2. Visit declaration.
        self.visit(node.decl)

        # 4. Visit parameter list
        if node.params:
            self.visit(node.params)
                
        # 5. Visit function.
        self.visit(node.body)
    
        # 6. Remove scope
        self.scopes.pop_scope()

        # Set flags
        self.flags['inFDef'] = False
    
    def visit_GlobalDecl(self, node):
        # 1. Visit every global declaration.
        for decl in node.decls:
            self.visit(decl)
    
    def visit_ID(self, node):
        # TODO: What to do? Insert in symbol table (VarDecl does that)?
        # Check if ID is in table? But vardecl creates the variable name afterwards.
        # Missing errors in int a=c; with no c declared, and a=3; with no a declared.
        return
    
    def visit_If(self, node):
        # 1. Visit the condition
        self.visit(node.cond)
        
        # 2. Condition must be boolean
        self.boolean_check(node.cond)
        
        # 3. Visit statements
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
        ty = node.type
        self.visit(ty)
        
        # 2. Add ptr type to Type
        while not isinstance(ty, ast.VarDecl):
            ty = ty.type
        
        # TODO: correct?
        ptr_type = self.symtab.lookup('ptr')
        ty.type.name.insert(0, ptr_type)
        
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
            
            # 1.3. Check if ID is declared, if ID.
            if isinstance(node.expr, ast.ID):
                expr = self.scopes.in_scope(node.expr)
            else:
                expr = node.expr
                
            ty = expr.type.name
        else:
            ty = [self.symtab.lookup('void')]
            
        # 2. Check return type.
        # TODO: check if ty is the function type. Add return type to scope?

    def visit_Type(self, node):
        # 1. Change the strings to uCType.
        # NOTE: because of the array and ptr types, node.name can have more than one item.
        for i, name in enumerate(node.name or []):
            if not isinstance(name, uCType.uCType):
                ty = self.symtab.lookup(name)
                assert ty, "Unsupported type %s." % name
                node.name[i] = ty
        
    def visit_UnaryOp(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        
        # 2. Make sure the operation is supported.
        if isinstance(node.expr, ast.ID):
            ty = self.scopes.in_scope(node.expr).type.name[0]
        else:
            ty = node.expr.type.name[0]
        assert node.op in ty.un_ops, "Unsupported operator %s in unary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type.
        # & => integer (returns address)
        # ! => Bool (logical negation)
        # *,++,--,-,+ => same type of the nearby variable 
        if isinstance(node.expr, ast.ID):
            ty = [self.scopes.in_scope(node.expr).type.name[0].name]
        else:
            ty = [node.expr.type.name[0].name]
        ty = {'&':['int'], '!':['bool']}.get(node.op, ty)
        node.type = ast.Type(ty)
        
    def visit_VarDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit name.
        self.visit(node.declname)
        
        # 3. Check scope and insert in symbol table.
        if isinstance(node.declname, ast.ID):
            # sym = self.symtab.lookup(node.declname.name)
            self.scopes.add_to_scope(node)
            # TODO (not working because ID has no type): node.declname.type = node.type

    def visit_While(self, node):
        # 1. Visit condition.
        self.visit(node.cond)

        # 2. Condition must be boolean
        self.boolean_check(node.cond)

        # 3. Visit body.
        self.visit(node.body)

    ## AUXILIARY FUNCTIONS ##
    def boolean_check(self, cond):
        ''' Check if a condition is boolean.'''
        boolean = self.symtab.lookup('bool')
        
        if isinstance(cond.type, uCType.uCType) :
            ty = cond.type
        else:
            ty = cond.type.name[0]
        
        if hasattr(cond, 'type'):
            assert ty == boolean, "Expression must be boolean, and is %s instead." % ty.name
        else:
            assert False, "Expression must be boolean."
