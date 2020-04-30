'''
Second Project: IR generation for the uC language (uCIR) based on checked AST.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 29/04/2020.
'''

import re
import uCAST as ast
from uCSemantic import SymbolTable
from os.path import exists

# TODO:
# - Pass multiple times through functions (first decl, then inits, then the rest)
# - Add local arrays allocations based on global initializations
# - With constants, and globals stacks, scopes can now be removed (or can be used with a new add_global function)

class ScopeStack():
    '''
    Class responsible for keeping variables scopes.
    Used for type checking variables as well as checking if they're are defined.
    Atributes:
        - stack: stack of SymbolTables. Each item is a different scope ([0] is global [-1] is local)
    '''
    def __init__(self):
        self.stack = []
        self.constants = []
    
    # Add new scope (if a function definition started)
    # Every function definition is considered a new scope (new symboltable)
    def add_scope(self, node=None):
        sym_tab = SymbolTable()
        if node : node = node.decl.name 
        sym_tab.add(0, node)
        self.stack.append(sym_tab) 

    # Add a new variable's address to the current function's scope
    def add_to_scope(self, node, addr):
        scope = self.stack[-1]
        name = node.declname.name
        scope.add(name, addr)

    # Return a variable's address
    # TODO: global is different than local
    def fetch_temp(self, node):
        name = node.name
        for scope in self.stack[::-1]:
            var = scope.lookup(name)
            if var: break
        return var

    # Remove current scope from stack (when a FuncDef node ends)
    def pop_scope(self):
        self.stack.pop() 
    
    # Print for debugging
    def __str__(self):
        text = '\n'
        for (i,sym) in enumerate(self.stack):
            st = sym.symtab
            labels = list(st.keys())
            labels.remove(0) # Remove enclosure
            labels = [(x,st[x]) for x in labels]
            if i: enclosure = f"At '{st[0].name}'" if st[0] else 'In a loop'
            else : enclosure = 'Globals'
            text += f"{enclosure} => |"
            for k,v in labels: text+=f" {k} {v} |"
            text += '\n'
        return text

# TODO: remove returns from visit, replace with deep dive from upper nodes.
class uCIRGenerate(ast.NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self, front_end):
        super(uCIRGenerate, self).__init__()

        # Adding variables tables
        self.scopes = ScopeStack()

        # Adding front_end for testing.
        self.front_end = front_end
        
        # Exclusive stacks
        self.constants = dict()
        self.globals = dict() 

        # Version dictionary for temporaries
        self.fname = 'global'
        self.versions = {}
        
        # Dictionaries for operations
        self.bin_ops = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod'}
        self.un_ops = {'+':'uadd', '-':'uneg', '++':'uinc', '--':'udec', 'p++':'upinc', 'p--':'updec', '&':'addr', '*':'ptr'} #TODO: wrong. See new examples
        self.rel_ops = {'<':'lt', '>':'gt', '<=':'le', '>=':'ge', '==':'eq', '!=':'ne', '&&':'and', '||':'or'}

        # The generated code (list of tuples)
        self.code = []
        
        # Useful attributes
        self.ret = {'label':None, 'value':None}
        self.loop_end = None
        self.alloc_phase = None

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
        self.print_code()
    
    def print_code(self):
        for inst in self.code:
            print(inst)

    def visit_Program(self, node):
        # Define volatile vars scope.
        self.fname = 'global'
        self.versions = {}

        # Add global scope.
        self.scopes.add_scope()
        
        # Visit all of the statements
        for gdecl in node.gdecls:
            self.visit(gdecl)

        # Remove global scope.
        self.scopes.pop_scope()

        # Append to special stacks
        globs = list(self.globals.values())
        consts = list(self.constants.values())
        self.code = globs + consts + self.code

    def visit_ArrayDecl(self, node):
        # TODO: local and init
        ret = self.visit(node.type)
        
        if ret:
            ret = (f'{ret[0]}_{node.dims.value}', ret[1])
        
        node.gen_location = node.type.gen_location
        return ret

    def visit_ArrayRef(self, node):
        # Visit subscript
        self.visit(node.subsc)
        
        # TODO: ArrayRef of ArrayRef not working
        arr = self.scopes.fetch_temp(node.name)
        ty = self.build_reg_types(node.type)
        
        # Get new temp variable
        target = self.new_temp()
        
        # Create instruction
        inst = ("elem_" + ty, arr, node.subsc.gen_location, target)
        self.code.append(inst)

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
        true_label = (target_true[1:],)
        true_jump = ('jump', target_rest)
        
        # Create FALSE
        fake_label = (target_fake[1:],)
        coord = node.expr.coord
        msg_coord = f'{coord.line}:{coord.column}'
        # TODO: add string to global, and then print the global
        error = ('print_string', 'assertion_fail on ' + msg_coord)
        
        # Jump to return
        fake_jump = ('jump', self.ret['label'])
        
        # Rest of code label
        rest_label = (target_rest[1:],)
        
        # Append all instructions
        self.code += [branch, true_label, true_jump, fake_label, error, fake_jump, rest_label]
    
    def visit_Assignment(self, node):
        # Visit the expression to be assigned.
        self.visit(node.rvalue)
        
        # Create the opcode and append to list
        ty = self.build_reg_types(node.rvalue.type)
        
        # Assignable expressions are ID, ArrayRef and UnaryOp
        # TODO: arrayRef correct?
        if isinstance(node.lvalue, ast.ID):
            laddr = self.scopes.fetch_temp(node.lvalue)
        else:
            self.visit(node.lvalue)
            laddr = node.lvalue.gen_location
        
        # Other assignment ops
        if node.op != '=':
            loc = self.new_temp()
            opcode = self.bin_ops[node.op[0]] + "_" + ty
            inst = (opcode, laddr, node.rvalue.gen_location, loc)
            self.code.append(inst)
        else:
            loc = node.rvalue.gen_location
        
        inst = ('store_' + ty, loc, laddr)
        self.code.append(inst)
        
        # Store location of the result on the node        
        node.gen_location = laddr
        
    def visit_BinaryOp(self, node):
        # Visit the left and right expressions
        self.visit(node.rvalue)
        self.visit(node.lvalue)

        # Make a new temporary for storing the result
        target = self.new_temp()

        # Create the opcode and append to list
        opcode = self.get_operation(node.op, node.lvalue.type)
        inst = (opcode, node.lvalue.gen_location, node.rvalue.gen_location, target)
        self.code.append(inst)

        # Store location of the result on the node
        node.gen_location = target
        
    def visit_Break(self, node):
        inst = ('jump', self.loop_end)
        self.code.append(inst)

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

        # Get type and check if is a string
        ty = node.type.name[0].name
        
        # TODO: wrong
        if ty == 'string': 
            # Constant must be in array (no opcode)
            node.gen_location = node.value
            return
        
        # Make the SSA opcode and append to list of generated instructions
        inst = ('literal_' + ty, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target
    
    def visit_Decl(self, node):
        # Check if allocation phase (TODO: really incomplete, confusing and maybe not appropriate)
        ty = None
        if not isinstance(node.type, ast.FuncDecl):
            # Get instruction name
            ty = self.build_decl_types(node.type)

            # Check for globals and arrays shenanigans
            # TODO: wrong
            global_scope = (self.fname == 'global')
            array_decl = isinstance(node.type, ast.ArrayDecl)
            if global_scope or array_decl:
                ty = 'global_' + ty 
                if global_scope: name = '@'+node.name.name
                else: name = '@_const_'+node.name.name
                init = self.get_expr(node.init, ty=node.type, name=ty)
                inst = (ty, name, init)
                
                # Add to global or constant if local array initialization
                if global_scope: self.globals[name] = inst
                else: self.constants[name] = inst
                return
                
            # TODO: this is far from complete or working.
            elif self.alloc_phase:
                self.visit(node.type)
                
            # Get gen_location
            node.gen_location = node.type.gen_location
        
        # Handle initialization
        if node.init:
            # Visit initializers
            self.visit(node.init)

            # Create opcode and append to instruction list
            # TODO: array?
            if ty:
                # TODO: this does not get the actual value, but the register. what to do?
                inst = ('store_' + ty, node.gen_location, node.init.gen_location)
            else:
                ty = node.init.type.name[-1].name
                inst = ('store_' + ty, node.init.gen_location, node.type.gen_location)

            self.code.append(inst)
            
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
        # Add loop scope
        self.scopes.add_scope()

        # Visit declarations
        if node.init:
            self.visit(node.init)
        
        # Create loop label
        label = self.new_temp()
        self.code.append((label[1:],))
        
        if node.cond:
            # Visit the condition
            self.visit(node.cond)

            # Create two new temporary variable names for true/false labels
            target_true = self.new_temp()
            target_fake = self.new_temp()
            
            # Create the opcode and append to list
            inst = ('cbranch', node.cond.gen_location, target_true, target_fake)
            self.code.append(inst)

            self.code.append((target_true[1:],))
        else:
            target_fake = self.new_temp()
        
        # Add loop ending to attribute.
        self.loop_end = target_fake
            
        # Visit loop
        if node.body:
            self.visit(node.body)
        
        # Visit next
        if node.next:
            self.visit(node.next)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Remove loop scope
        self.scopes.pop_scope()

        # Rest of the code
        self.code.append((target_fake[1:],))
    
    def visit_FuncCall(self, node):
        # Visit arguments.
        if node.args:
            self.visit(node.args)
            
            # 1 vs multiple arguments
            if isinstance(node.args, ast.ExprList):
                args = node.args.exprs
            else:
                args = [node.args]
            
            # Create parameter opcodes and append to list
            for arg in args:
                ty = self.build_reg_types(arg.type)
                inst = ('param_' + ty, arg.gen_location)
                self.code.append(inst)
        
        # Create opcode and append to list
        inst = ('call', node.name.name)
        self.code.append(inst)
        
        # TODO: check return type of function, and create temporary variable for it if non-void. Also, gen_location if so.
        node.gen_location = self.new_temp()
    
    def visit_FuncDecl(self, node):
        # TODO: what? Anything? Ask for more examples.
        # TODO: not including signatures
        if node.params:
            self.visit(node.params)
    
    def visit_FuncDef(self, node):
        # Add function's scope
        self.scopes.add_scope(node=node)

        # Find out function name.
        var = node.decl
        while not isinstance(var, ast.VarDecl):
            var = var.type
        name = var.declname.name
        
        # Create opcode and append to list.
        inst = ('define', name)
        self.code.append(inst)
        
        # Start function
        self.fname = name
        
        # Skip temp variables for params and return
        par = node.decl
        while not isinstance(par, ast.FuncDecl):
            par = par.type
        if par.params:
            self.versions[name] = len(par.params.params)
        else:
            self.versions[name] = 0

        # Get return temporary variable
        self.ret['value'] = self.new_temp()
                
        # Visit function declaration
        self.visit(node.decl)
        
        # Get return label, if needed.
        self.ret['label'] = self.new_temp()
        label = (self.ret['label'][1:],)
                
        # Visit body
        if node.body:
            self.alloc_phase = True # TODO: just so it allocates for now, use it later for other things.
            self.visit(node.body)
        
        # Return label and return
        ty = self.build_reg_types(var.type)
        
        # Void = no return, only label and return_void inst.
        if ty == 'void':
            ret_inst = ('return_void',)
            self.code += [label, ret_inst]
        # Type: get return value from ret_val and return it.
        else:
            # New temp for return value.
            ret_target = self.new_temp()
            
            # Get return value from ret_val (stored)
            val_inst = ('load_'+ty, self.ret['value'], ret_target)
            
            # Return instruction and append.
            ret_inst = ('return_'+ty, ret_target)
            self.code += [label, val_inst, ret_inst]
        
        # Remove function's scope
        print(self.scopes)
        self.scopes.pop_scope()
    
    def visit_GlobalDecl(self, node):
        for decl in node.decls:
            self.visit(decl)
    
    def visit_ID(self, node):
        # Create a new temporary variable name 
        target = self.new_temp()
        
        # Get temporary with ID name.
        var = self.scopes.fetch_temp(node)
        
        # Create the opcode and append to list
        ty = self.build_reg_types(node.type)
        inst = ('load_' + ty, var, target)
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
        self.code.append((target_then[1:],))
        if node.if_stat:
            self.visit(node.if_stat)
        
        # Create ELSE
        self.code.append((target_else[1:],))
        if node.else_stat:
            self.visit(node.else_stat)
    
    def visit_InitList(self, node):
        node.gen_location = []
        for expr in node.exprs:
            node.gen_location.append(expr.value)
            # self.visit(expr)
    
    def visit_ParamList(self, node):
        for par in node.params:
            # Visit parameter (allocate vars)
            self.visit(par)
        
        for i, par in enumerate(node.params or []):
            # Store value in temp var "i" in newly allocated var.
            ty = par.type
            while not isinstance(ty, ast.Type):
                ty = ty.type
            ty = self.build_reg_types(ty)
            inst = ('store_'+ty, f'%{i}', par.gen_location)
            self.code.append(inst)

    def visit_Print(self, node):
        # Visit the expression
        if node.expr:
            self.visit(node.expr)
            
            # Handle 1 or more exprs
            if isinstance(node.expr, ast.ExprList):
                exprs = node.expr.exprs
            else:
                exprs = [node.expr]
            
            for expr in exprs:
                ty = self.build_reg_types(expr.type)
                inst = ('print_' + ty, expr.gen_location)
                self.code.append(inst)
        else:
            inst = ('print_void',)
            self.code.append(inst)
    
    def visit_PtrDecl(self, node):
        # TODO: ptr?
        ret = self.visit(node.type)
        node.gen_location = node.type.gen_location
        return ret
    
    def visit_Read(self, node):
        # Visit the expression
        self.visit(node.expr)

        # Create the opcode and append to list
        ty = self.build_reg_types(node.expr.type)
        inst = ('read_' + ty, node.expr.gen_location)
        self.code.append(inst)

    def visit_Return(self, node):
        # If there is a return expression.
        if node.expr:
            self.visit(node.expr)
            
            # Store return value in allocated variable
            ty = self.build_reg_types(node.expr.type)
            inst = ('store_'+ty, node.expr.gen_location, self.ret['value'])
            self.code.append(inst)
        
        # Jump to return label.
        inst = ('jump', self.ret['label'])
        self.code.append(inst)

    def visit_Type(self, node):
        assert False, "'Type' nodes are not visited in code generation!"
    
    def visit_UnaryOp(self, node):
        # Visit the expression
        self.visit(node.expr)
        
        # Create a new temporary variable name 
        target = self.new_temp()
        
        # Create the opcode and append to list
        ty = self.build_reg_types(node.expr.type)
        opcode = self.un_ops[node.op] + "_" + ty
        inst = (opcode, node.expr.gen_location, target)
        self.code.append(inst)
        
        # Store location of the result on the node        
        node.gen_location = target

    def visit_VarDecl(self, node):
        ty = self.build_reg_types(node.type)
        
        # Try global
        if self.fname == 'global':
            node.gen_location = '@'+node.declname.name
            return
        
        # Allocate on stack memory.
        alloc_target = self.new_temp()
        inst = ('alloc_' + ty, alloc_target)
        self.code.append(inst)
        
        self.scopes.add_to_scope(node, alloc_target)

        node.gen_location = alloc_target
    
    def visit_While(self, node):
        # Create loop label
        label = self.new_temp()
        self.code.append((label[1:],))
        
        # Visit the condition
        self.visit(node.cond)

        # Create two new temporary variable names for true/false labels
        target_true = self.new_temp()
        target_fake = self.new_temp()

        # Create the opcode and append to list
        inst = ('cbranch', node.cond.gen_location, target_true, target_fake)
        self.code.append(inst)
        
        # Add loop ending to attribute.
        self.loop_end = target_fake
        
        # Visit loop
        self.code.append((target_true[1:],))
        if node.body:
            self.visit(node.body)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Rest of the code
        self.code.append((target_fake[1:],))
    
    ## AUXILIARY FUNCTIONS ##

    # Get Expression for constant initilization
    # This should handle the possible assignment expressions
    def get_expr(self, expr, ty=None, name=None):
        if isinstance(expr, ast.BinaryOp):
            left = self.get_expr(expr.lvalue)
            right = self.get_expr(expr.rvalue)
            ret = f"({left}{expr.op}{right})"
        elif isinstance(expr, ast.UnaryOp):
            right = self.get_expr(expr.expr)
            ret = f"({expr.op}{right})"
        elif isinstance(expr, ast.ID):
            ret = expr.name # TODO: should replace ID.name by the ID's value
        elif isinstance(expr, ast.Constant):
            ret = expr.value
        elif isinstance(expr, ast.InitList):
            ret = [self.get_expr(val) for val in expr.exprs]
        elif expr==None:
            ret = 0
            if isinstance(ty,ast.ArrayDecl):
                dims = [int(x) for x in re.findall(r"_(\d+)", name)]
                for d in reversed(dims): ret = [ret]*d
        else:
            raise Exception(f"get_expr: Unable to process {type(expr)} class")
        return ret

    def get_operation(self, op, ty):
        if op in self.bin_ops.keys():
            return self.bin_ops[op] + "_" + self.build_reg_types(ty)
        else:
            return self.rel_ops[op] + "_" + self.build_reg_types(ty)

    def build_decl_types(self, node):
        name = ''
        ty = node
        while not isinstance(ty, ast.VarDecl):
            if isinstance(ty, ast.ArrayDecl):
                name += f'_{ty.dims.value}'
            elif isinstance(ty, ast.PtrDecl):
                name += '_*'
            ty = ty.type
        name = ty.type.name[-1].name + name
        return name
    
    def build_reg_types(self, ty):
        name = ''
        for item in ty.name[::-1]:
            if item.name == 'array':
                name += f'_{ty.dims.value}' # TODO: get dims (save in scope?)
            elif item.name == 'ptr':
                name += '_*'
            else:
                name += item.name
        return name