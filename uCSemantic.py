'''
Second Project: Semantic Analysis of AST for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 09/04/2020.
'''

import uCType
import uCAST as ast

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

class CheckProgramVisitor(ast.NodeVisitor):
    '''
    Program checking class. This class uses the visitor pattern. You need to define methods
    of the form visit_NodeName() for each kind of AST node that you want to process.
    Note: You will need to adjust the names of the AST nodes if you picked different names.
    '''
    def __init__(self):
        # Initialize the symbol table
        self.symtab = SymbolTable()

        # Add built-in type names (int, float, char) to the symbol table
        self.symtab.add("int",uCType.int_type)
        self.symtab.add("float",uCType.float_type)
        self.symtab.add("char",uCType.char_type)
        self.symtab.add("string",uCType.string_type)
        self.symtab.add("bool",uCType.boolean_type)

    def visit_Program(self, node):
        # 1. Visit all of the statements
        # 2. Record the associated symbol table
        self.visit(node.program)                # TODO: what should be done here?

    def visit_ArrayDecl(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit dims expression.
        self.visit(node.dims)
        
        # 3. Check if array size is nonnegative (how? If "-1" or similar, just check UnaryOp. And if not? TODO).

    def visit_ArrayRef(self, node):
        # 1. Visit identifier.
        self.visit(node.name)
        
        # 2. ???

    def visit_Assignment(self, node):
        ## 1. Make sure the location of the assignment is defined
        sym = self.symtab.lookup(node.lvalue)   # TODO: not getting name?
        assert sym, "Assigning to unknown sym"
        
        ## 2. Check that the types match
        self.visit(node.rvalue)
        assert sym.type == node.rvalue.type, "Type mismatch in assignment"
        
    def visit_Assert(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)

    def visit_BinaryOp(self, node):
        # 1. Make sure left and right operands have the same type
        self.visit(node.lvalue)
        self.visit(node.rvalue)
        assert node.lvalue.type == node.rvalue.type, "Type mismatch in binary operation"
        
        # 2. Make sure the operation is supported
        ty = node.lvalue.type.name
        assert node.op in ty.bin_ops, "Unsupported operator %s in binary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type
        node.type = node.lvalue.type

    def visit_Break(self, node):
        # TODO: check if is inside a for/while? For parser, break can be outside a loop.

    def visit_Cast(self, node):
        # 1. Visit type.
        self.visit(node.type)
        
        # 2. Visit Expression
        self.visit(node.expr)
        
        # 3. Check if the expression type is castable to "type".
        ty = node.expr.type
        while not isinstance(ty, uCType.uCType):
            ty = ty.type
            
        assert node.type.name in ty.cast_types, "Type %s can't be casted to type %s." % (ty.name, node.type.name)
        
    def visit_Compound(self, node):
        # 1. Visit all declarations
        for decl in node.decls:
            self.visit(decl)
            
        # 2. Visit all statements
        for stat in node.stats:
            self.visit(stat)

    def visit_Constant(self, node):
        # 1. Check constant type.
        visit(node.type)
        
        # 2. Convert to respective type. String by default.
        ty = node.type.name
        if ty.name == 'int':
            node.value = int(node.value)
        elif ty.name == 'float':
            node.value = float(node.value)
        # TODO: char? Anything else?
        
    def visit_Decl(self, node):
        # 1. Visit type
        self.visit(node.type)
        
        # 2. Check if variable is defined.
        assert self.symtab.lookup(node.name.name), "Symbol %s not defined" % node.name.name
        
        # 3. Visit initial value, if defined.
        if node.init:
            self.visit(node.init)
            
            # Check instance of initializer.
            # Constant
            if isinstance(node.init, ast.Constant):
                assert node.type.type.name[0] == node.init.type, "Initialization type mismatch in declaration."
            
            # InitList
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
        
        # 4. ???
    
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
        self.visit(node.init)
        
        # 2. Visit condition.
        self.visit(node.cond)
        
        # 3. Visit next.
        self.visit(node.next)
        
        # 4. Visit body.
        self.visit(node.body)
        
        # 5. ???
    
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
        self.visit(node.params)
        
        # 3. ???
    
    def visit_FuncDef(self, node):
        # 1. Visit declaration.
        self.visit(node.decl)
        
        # 2. Visit parameter list
        self.visit(node.params)
        
        # 2. Visit function. (TODO)
    
    def visit_GlobalDecl(self, node):
        # 1. Visit every global declaration.
        for decl in node.decls:
            self.visit(decl)
    
    def visit_ID(self, node):
        # TODO: What to do? Insert in symbol table (VarDecl does that)?
    
    def visit_If(self, node):
        # 1. Visit the condition
        self.visit(node.cond)
        # 2. TODO: ???
    
    def visit_InitList(self, node):
        # 1. Visit expressions
        for expr in node.exprs:
            self.visit(expr)
        
        # 2. ???
            
    def visit_ParamList(self, node):
        # 1. Visit parameters.
        for param in node.params:
            self.visit(param)
        
        # 2. ???
    
    def visit_Print(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        # TODO: check if expression is a string?

    def visit_Read(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        # TODO: check if expression is a string?

    def visit_Return(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        # TODO: check if expression is of the function type? Or is this done in FuncDef?

    def visit_Type(self, node):
        # 1. Change the string to uCType.
        # TODO: simplify for one name? Just delete the for and do if for node.name[0].
        for i, name in enumerate(node.name or []):
            if not isinstance(name, uCType):
                ty = self.symtab.lookup(name)
                assert ty, "Unsupported type %s." % name
                node.name[i] = ty
        
    def visit_UnaryOp(self, node):
        # 1. Visit the expression.
        self.visit(node.expr)
        
        # 2. Make sure the operation is supported.
        ty = node.expr.type.name
        assert node.op in ty.un_ops, "Unsupported operator %s in unary operation for type %s." % (node.op, ty.name)
        
        # 3. Assign the result type.
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
            self.symtab.add(node.declname, node)
            node.declname.type = node.type

    def visit_While(self, node):
        # 1. Visit condition.
        self.visit(node.cond)

        # 2. Visit body.
        self.visit(node.body)
        
        # 3. TODO
