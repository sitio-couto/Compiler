'''
Second Project: IR generation for the uC language (uCIR) based on checked AST.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 23/04/2020.
'''

import uCAST as ast
from os.path import exists

# TODO: types - -1, 0 or all?
class uCIRGenerate(ast.NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self, front_end):
        super(uCIRGenerate, self).__init__()
        
        # Adding front_end for testing.
        self.front_end = front_end
        
        # Version dictionary for temporaries
        self.fname = 'global'
        self.versions = {}
        
        # Dictionaries for operations
        self.bin_ops = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod'}
        self.un_ops = {'+':'uadd', '-':'uneg'} #TODO: ++, --, p++, p--, *, &
        self.rel_ops = {'<':'lt', '>':'gt', '<=':'le', '>=':'ge', '==':'eq', '!=':'ne', '&&':'and', '||':'or'}

        # The generated code (list of tuples)
        self.code = []

    def new_temp(self):
        ''' Create a new temporary variable of a given scope (function name). '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = f"%{self.versions[self.fname]}" 
        self.versions[self.fname] += 1
        return name

    def test(self, data, show_ast):
        self.code = []
        self.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
            ast = self.front_end.parser.parse(data, False)
        else:
            ast = self.front_end.parser.parse(data, False)
        
        # Check semantics
        self.front_end.visit(ast)
        
        # Show AST
        if show_ast:
            ast.show()
            
        # Generate IR
        self.visit(ast)
        print(self.code)

    def visit_Program(self, node):
        # Define global scope.
        self.fname = 'global'
        self.versions = {}
        
        # Visit all of the statements
        for gdecl in node.gdecls:
            self.visit(gdecl)

    def visit_Assert(self, node):
        # Visit the assert condition
        self.visit(node.expr)
        
        # Create three new temporary variable names for True/False and rest of code
        target_true = self.new_temp()
        target_fake = self.new_temp()
        target_rest = self.new_temp()

        # Create the opcode.
        branch = ('cbranch', node.expr.gen_location, target_true, target_fake)
        
        # Create TRUE
        true_label = (target_true,)
        true_jump = ('jump', target_rest)
        
        # Create FALSE
        fake_label = (target_fake,)
        coord = node.expr.coord
        msg_coord = f'{coord.line}:{coord.column}'
        error = ('print_string', 'assertion_fail on ' + msg_coord)
        
        # TODO: jump to where? hardcoded atm, probably wrong.
        fake_jump = ('jump', '%1')
        
        # Rest of code label
        rest_label = (target_rest,)
        
        # Append all instructions
        self.code += [branch, true_label, true_jump, fake_label, error, fake_jump, rest_label]
    
    def visit_Assignment(self, node):
        # Visit the expression to be assigned.
        self.visit(node.rvalue)
        
        # Create the opcode and append to list
        ty = node.rvalue.type.name[-1].name
        inst = ('store_' + ty, node.rvalue.gen_location, node.lvalue.gen_location) # TODO: lvalue has gen_location?
        self.code.append(inst)
        
        # Store location of the result on the node        
        node.gen_location = node.lvalue.gen_location
        
    def visit_BinaryOp(self, node):
        # Visit the left and right expressions
        self.visit(node.lvalue)
        self.visit(node.rvalue)

        # Make a new temporary for storing the result
        target = self.new_temp()

        # Create the opcode and append to list
        opcode = self.get_operation(node.op, node.lvalue.type)
        inst = (opcode, node.lvalue.gen_location, node.rvalue.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target

    def visit_Cast(self, node):
        # Visit the expression
        self.visit(node.expr)
        
        # Check type.
        ty = node.type.name[0].name
        if ty == 'int':
            opcode = 'fptosi'
        else:
            opcode = 'sitofp'
        
        # Create the opcode and append to list
        inst = (opcode, node.expr.gen_location)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = node.expr.gen_location

    def visit_Compound(self, node):
        if node.decls:
            for decl in node.decls:
                self.visit(decl)
        
        if node.stats:
            for stmt in node.stats:
                self.visit(stmt)

    def visit_Constant(self, node):
        # Create a new temporary variable name 
        target = self.new_temp()

        # Make the SSA opcode and append to list of generated instructions
        ty = node.type.name[0].name
        inst = ('literal_' + ty, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target
    
    def visit_DeclList(self, node):
        for decl in node.decls:
            self.visit(decl)
    
    def visit_EmptyStatement(self, node):
        return
    
    def visit_ExprList(self, node):
        # Visit expressions
        for expr in node.exprs:
            self.visit(expr)
    
    def visit_For(self, node):
        # TODO: scope?
        # Visit declarations
        if node.init:
            self.visit(node.init)
        
        # Create loop label
        label = self.new_temp()
        self.code.append((label,))
        
        if node.cond:
            # Visit the condition
            self.visit(node.cond)

            # Create two new temporary variable names for true/false labels
            target_true = self.new_temp()
            target_fake = self.new_temp()
            
            # Create the opcode and append to list
            inst = ('cbranch', node.cond.gen_location, target_true, target_fake)
            self.code.append(inst)

            self.code.append((target_true,))
        else:
            target_fake = self.new_temp()
            
        # Visit loop
        if node.body:
            self.visit(node.body)
        
        # Visit next
        if node.next:
            self.visit(node.next)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Rest of the code
        self.code.append((target_fake,))
    
    def visit_FuncCall(self, node):
        # Visit arguments.
        if node.args:
            self.visit(node.args)
            
            # 1 vs multiple arguments
            if isinstance(node.args, ast.ExprList):
                args = node.args.expr
            else:
                args = [node.args]
            
            # Create parameter opcodes and append to list
            for arg in args:
                ty = arg.type.name[-1].name
                inst = ('param_' + ty, arg.gen_location)
                self.code.append(inst)
        
        # Create opcode and append to list
        # TODO: check return type of function, and create temporary variable for it if non-void. Also, gen_location if so.
        inst = ('call', node.name.name)
        self.code.append(inst)
    
    def visit_GlobalDecl(self, node):
        for decl in node.decls:
            self.visit(decl)
    
    def visit_ID(self, node):
        # Create a new temporary variable name 
        target = self.new_temp()
        
        # Create the opcode and append to list
        inst = ('load_' + node.type.name[-1].name, node.name, target)
        self.code.append(inst)
        
        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target
    
    def visit_If(self, node):
        # Visit condition
        self.visit(node.cond)

        # Create two new temporary variable names for then/else labels
        target_then = self.new_temp()
        target_else = self.new_temp()

        # Create the opcode and append to list
        inst = ('cbranch', node.cond.gen_location, target_then, target_else)
        self.code.append(inst)
        
        # Create THEN
        self.code.append((target_then,))
        if node.if_stat:
            self.visit(node.if_stat)
        
        # Create ELSE
        self.code.append((target_else,))
        if node.else_stat:
            self.visit(node.else_stat)
    
    def visit_Print(self, node):
        # Visit the expression
        if node.expr:
            self.visit(node.expr)
            ty = node.expr.type.name[-1].name
        else:
            ty = 'void' #TODO: correct?

        # Create the opcode and append to list
        inst = ('print_' + ty, node.expr.gen_location)
        self.code.append(inst)
    
    def visit_Read(self, node):
        # Visit the expression
        self.visit(node.expr)

        # Create the opcode and append to list
        ty =  node.expr.type.name[-1].name
        inst = ('read_' + ty, node.expr.gen_location)
        self.code.append(inst)

    def visit_UnaryOp(self, node):
        # Visit the expression
        self.visit(node.expr)
        
        # Create a new temporary variable name 
        target = self.new_temp()
        
        # Create the opcode and append to list
        opcode = self.un_ops[node.op] + "_" + node.expr.type.name[-1].name
        inst = (opcode, node.expr.gen_location, target)
        self.code.append(inst)
        
        # Store location of the result on the node        
        node.gen_location = target

    def visit_VarDecl(self, node):
        # Allocate on stack memory.
        # TODO: global
        inst = ('alloc_' + node.type.name[-1].name, node.declname.name)
        self.code.append(inst)
        
        # Store optional init value.
        # TODO: return operation to Decl, where initializer can be stored.
        #if node.value:
         #   self.visit(node.value)
         #   inst = ('store_' + node.type.name, node.value.gen_location, node.id)
         #   self.code.append(inst)
    
    def visit_While(self, node):
        # Create loop label
        label = self.new_temp()
        self.code.append((label,))
        
        # Visit the condition
        self.visit(node.cond)

        # Create two new temporary variable names for true/false labels
        target_true = self.new_temp()
        target_fake = self.new_temp()

        # Create the opcode and append to list
        inst = ('cbranch', node.cond.gen_location, target_true, target_fake)
        self.code.append(inst)
        
        # Visit loop
        self.code.append((target_true,))
        if node.body:
            self.visit(node.body)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Rest of the code
        self.code.append((target_fake,))
    
    ## AUXILIARY FUNCTIONS ##
    def get_operation(self, op, ty):
        if op in self.bin_ops.keys():
            return self.bin_ops[op] + "_" + ty.name[-1].name
        else:
            return self.rel_ops[op]
