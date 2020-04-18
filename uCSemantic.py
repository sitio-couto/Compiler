'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 16/04/2020.
'''

import uCType
import uCAST as ast
from os.path import exists, splitext

class SymbolTable(object):
    '''
    Class representing a symbol table.  It should provide functionality
    for adding and looking up nodes associated with identifiers.
    '''
    def __init__(self):
        self.symtab = {}
    def lookup(self, a):
        return self.symtab.get(a)
    def add(self, a, v):
        self.symtab[a] = v


class SignaturesTable():
    '''
    Class responsible for keeping funcions signatures (type, name and parameters).
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
        self.sign    = dict()  # Check which functions were declared (signatures: int main(float f);)
    
    # Register function signature (when Decl is declaring a FuncDecl)
    # NOTE: function calls will be validate using self.sign table
    # Params: 
    #   node - a Decl (of a FuncDef) class form the uCAST
    def sign_func(self, node):
        name   = node.name      # get func name
        ty     = node.type.type # get func type (Decl.VarDecl.Type)
        params = [] # Get functions parameters types and names
        
        for p in node.param:
            if isinstance(p.type, ast.VarDecl):
                # Append to params: {type:ast.Type, name:'f'}
                params.append(dict(type=p.type.type, name=p.type.name))
            # TODO: array declarations
        new = dict(type=ty, params=params)

        # If function was already signed, validate signature
        if name in self.sign.keys() :
            check = (ty == self.sign[name]['type']) # Check return type
            for (sign, new) in zip(new['params'], sign[name]['params']):
                check *= (sign.type == new.type)    # Check param type
                sign.name = new.name # this overrides paramenters names (Decl: int main(float a); | Def: int main(float f) => overrides to f)        
            assert check, "Function %s has multiple declarations" % name
        else : # Not signed yet? 
            self.sign[name] = new

    
    # Fetches the function's return type
    def check_return(self, name):
        return self.sign[name]['ret']



class ScopesTable():
    def __init__(self):
        self.sign    = dict()  # Check which functions were declared (signatures: int main(float f);)
        self.funcs   = dict()  # Defined functions and their scopes
        self.globals = []      # Special list for global variables
        self.stack   = []      # last element is the top of the stack
    
    # Add new scope (if a function definition started)
    def add_scope(self, name, params): 
        assert not name in self.funcs.keys(), "Fuction %s is being declared twice!!" % name
        # {func_name:[vars in scope])}
        #  - Every function definition is considered a new scope
        #  - The element consists of list of names (Strings)
        #  - 'vars' keeps the variables names declared within the function's scope 
        # Here we will save two pointers to the same 'new_scope' list. 
        # This way, when altering the stack, self.scopes will also be updated
        new_scope = [x['name'] for x in params[:]] # Copy parameters to scope
        self.funcs[name] = new_scope # Add function's scope to list
        self.stack.append(new_scope) # The function's name is not relevant on the stack (we only access the top item)

    # Add a new variable to the current function's scope (when variables are declared)
    def add_to_scope(self, name):
        if self.stack : # Stack not emtpy? then not on the global scope
            self.stack[-1].append(name) # Add declaration to current scope (top of the stack)
        else : # if global
            self.globals.append(name)   # Add var to global scope
    
    # remove current scope from stack (if a function def has ended)
    def pop_scope(self):
        self.stack.pop() # scopes remain in self.funcs
    
    # Check if ID name is within the current scope
    def in_scope(self, name):
        local = name in self.stack[-1] # Check if in current scope
        glob  = name in self.globals   # Check if in global scope
        return glob or local

    # # Print current scopes
    # def __str__(self):
    #     text = "globals:\n" 
    #     for v in self.globals:
    #         text += f"  {v}"
            
    #     text = "\nFunctions:\n" 
    #     for f in self.funcs.keys():
    #         ty = self.funcs[f]['ret']
    #         params = self.funcs[f]['params']
    #         text += f"\n  {ty} {f} {params}:\n"
    #         for v in self.funcs[f]['vars']:
    #             text += f"      {v}\n"    

    #     return text

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
        
        # Include parser
        self.parser = parser
        
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Initialize scopes table
        self.scopes = ScopesTable()

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
    
    def visit_Program(self, node):
        # 1. Visit all of the statements
        for gdecl in node.gdecls:
            self.visit(gdecl)
        
        # 2. Record the associated symbol table
        # TODO: what should be done here?

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
        # 1. Visit subscript.
        self.visit(node.subsc)
        
        # 2. Check if subscript is a valid ID, if ID.
        # TODO: scope and ID type (must be variable)
        if isinstance(node.subsc, ast.ID):
            name = self.symtab.lookup(node.subsc.name)
            assert name, "ID %s is not defined." % node.subsc.name
            ty = name.type.name[-1]
        else:
            ty = node.subsc.type.name[-1]
        
        # 3. Check subscript type.
        type_int = self.symtab.lookup('int')
        assert ty == type_int, "Subscript must be an integer." # TODO: constant value or id name.
        
        # 4. Visit name
        self.visit(node.name)
        
        # 5. Assign node type
        # TODO: how? how does the type.name list work at this point?
        
    def visit_Assignment(self, node):
        # 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.lvalue)   # TODO: not getting ID?
        assert sym, "Assigning to unknown sym"
        
        # 2. Check if assignment is valid.
        if node.op != '=':
            ty = node.lvalue.type.name[0]      # TODO: name[-1]? Not necessary?
            assert node.op in ty.assign_ops, "Assignment not valid for type %s." % ty.name
        
        # 3. Check that the types match
        self.visit(node.rvalue)
        assert sym.type.name[0] == node.rvalue.type.name[0], "Type mismatch in assignment"
        
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
            lvalue = self.symtab.lookup(node.lvalue.name)
        else:
            lvalue = node.lvalue
        
        if isinstance(node.rvalue, ast.ID):
            rvalue = self.symtab.lookup(node.rvalue.name)
        else:
            rvalue = node.rvalue
        assert lvalue.type.name[0] == rvalue.type.name[0], "Type mismatch in binary operation"
        
        # 2. Make sure the operation is supported
        ty = lvalue.type.name[0]                     # TODO: name[-1]? Not necessary?
        assert node.op in ty.bin_ops.union(ty.rel_ops), "Unsupported operator %s in binary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type
        # TODO: BinaryOp has no type.
        if node.op in ty.bin_ops:
            node.type = node.lvalue.type
        else:
            node.type = self.symtab.lookup('bool')

    def visit_Break(self, node):
        # TODO: check if is inside a for/while.
        return

    def visit_Cast(self, node):
        # 1. Visit type.
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
        # 0. If function, sign it
        if isinstance(node.type, ast.FuncDecl): 
            self.scopes.sign_func(node)

        # 1. Visit type
        self.visit(node.type)
        
        # 2. Check if variable is defined.
        assert self.symtab.lookup(node.name.name), "Symbol %s not defined" % node.name.name
        
        # 3. Check if ArrayDecl has InitList if no dimensions.
        if isinstance(node.type, ast.ArrayDecl) and node.type.dims is None:
            assert isinstance(node.init, ast.InitList), "Array declaration without explicit size needs an initializer list."
        
        # 4. Visit initializers, if defined.
        if node.init:
            self.visit(node.init)
            
            # Check instance of initializer.
            # Constant
            if isinstance(node.init, ast.Constant):
                assert node.type.type.name[0] == node.init.type.name[0], "Initialization type mismatch in declaration."
            
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
                        assert node.type.dims.value == len(exprs), "Size mismatch in variable initialization"
                
                # Pointer (TODO)
                elif isinstance(node.type, ast.PtrDecl):
                    assert True
            
        # 5. ???
    
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
        sym = self.symtab.lookup(node.name.name)
        assert sym, "Unknown identifier in function call."
        
        # 2. Check if identifier is a function.
        assert isinstance(sym, ast.FuncDecl), "Identifier in function call is not a function."
        
        # 3. Visit arguments.
        self.visit(node.args)
    
    def visit_FuncDecl(self, node):
    
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit params.
        if node.params:
            self.visit(node.params)
    
    def visit_FuncDef(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit declaration.
        self.visit(node.decl)

        # 3. Visit parameter list
        if node.params:
            self.visit(node.params)
                
        # 4. Visit function.
        if node.body:
            self.visit(node.body)
    
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
        for expr in node.expr:
            self.visit(expr)

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
        for expr in node.expr:
            self.visit(node.expr)

    def visit_Return(self, node):
        # 1. Visit the expression.
        if node.expr:
            self.visit(node.expr)
            ty = node.expr.type.name
        else:
            ty = [self.symtab.lookup('void')]
        # TODO: check if ty is the function type.

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
        ty = node.expr.type.name[0]
        assert node.op in ty.un_ops, "Unsupported operator %s in unary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type.
        # TODO: UnaryOp has no type.
        node.type = node.expr.type      # TODO: check if type is the same as operand.

    def visit_VarDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit name.
        self.visit(node.declname)
        
        # 3. Check scope and insert in symbol table.
        if isinstance(node.declname, ast.ID):
            sym = self.symtab.lookup(node.declname.name)
            # TODO: check scope
            # If not in scope, add IN SCOPE (how? TODO):
            self.symtab.add(node.declname.name, node)
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
