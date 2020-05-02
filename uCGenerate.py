'''
Second Project: IR generation for the uC language (uCIR) based on checked AST.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 02/05/2020.
'''

import re
import uCAST as ast
from uCSemantic import SymbolTable
from os.path import exists

# TODO:
# - Other TODOs in the code body.

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
    
    # Add a new variable's name to the global scope
    def add_global(self, node, addr):
        name = node.declname.name
        self.stack[0].add(name, addr)

    # Get type of function, stored as a global var.
    def get_func_type(self, name):
        return self.stack[0].lookup(name).type

    # Return a variable's address
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
        self.str_counter = 0

        # Dictionaries for operations
        self.bin_ops = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod'}
        self.un_ops = {'+':'uadd', '-':'uneg', '++':'uinc', '--':'udec', 'p++':'upinc', 'p--':'updec', '&':'addr', '*':'ptr'} #TODO: wrong. See new examples
        self.rel_ops = {'<':'lt', '>':'gt', '<=':'le', '>=':'ge', '==':'eq', '!=':'ne', '&&':'and', '||':'or'}

        # The generated code (list of tuples)
        self.code = []
        
        # Useful attributes
        self.ret = {'label':None, 'value':None}
        self.loop_end = []
        self.alloc_phase = None

    def new_str(self):
        ''' Create a new string constant on the global scope. '''
        name = f"@.str.{self.str_counter}" 
        self.str_counter += 1
        return name

    def new_temp(self):
        ''' Create a new temporary variable of a given scope (function name). '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 0
        name = f"%{self.versions[self.fname]}" 
        self.versions[self.fname] += 1
        return name

    def write_file(self, code, out_file):
        out = ''
        for inst in code: out += str(inst)+'\n'
        f = open(out_file, 'w')
        f.write(out)
        f.close()

    def test(self, data, show_ast, out_file=None, quiet=False):
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
        if not quiet: self.print_code()
        if out_file: self.write_file(self.code, out_file)
    
    def print_code(self):
        for inst in self.code:
            print(inst)

    def visit_Program(self, node):
        # Define volatile vars scope.
        self.fname = 'global'
        self.versions = {}

        # Add global scope.
        self.scopes.add_scope()
        
        # Visit all global declarations.
        for gdecl in node.gdecls:
            if isinstance(gdecl, ast.GlobalDecl):
                self.visit(gdecl)
                
        # Visit all function definitions.
        for fdef in node.gdecls:
            if isinstance(fdef, ast.FuncDef):
                self.visit(fdef)

        # Remove global scope.
        self.scopes.pop_scope()

        # Append to special stacks
        globs = list(self.globals.values())
        consts = list(self.constants.values())
        self.code = globs + consts + self.code

    def visit_ArrayDecl(self, node):
        # TODO: Repeated code from VarDecl, so that we have the array dims. Can we do it without repeating?
        # TODO: save dims somewhere? We need it afterward.
        ty = self.build_decl_types(node)
        
        alloc_target = self.new_temp()
        inst = ('alloc_' + ty, alloc_target)
        self.code.append(inst)
        
        # Adding to scope
        var = node.type
        while not isinstance(var, ast.VarDecl):
            var = var.type
        self.scopes.add_to_scope(var, alloc_target)
        node.gen_location = alloc_target
        
    def visit_ArrayRef(self, node):
        # Visit subscript
        self.visit(node.subsc)
        
        # TODO: ArrayRef of ArrayRef not working (check test06)
        if isinstance(node.name, ast.ArrayRef):
            self.visit(node.name)
        else:
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
        
        name = self.new_str()
        inst = ('global_string', name, 'assertion_fail on '+msg_coord)
        self.constants[name] = inst

        error = ('print_string', name)
        
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
        inst = ('jump', self.loop_end[-1])
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
        old = node.expr.gen_location
        casted = self.new_temp()
        inst = (opcode, old, casted)
        node.expr.gen_location = casted
    
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
        
        if ty == 'string': 
            # Constant must be in array (no opcode)
            name = self.new_str()
            inst = ('global_string', name, node.value)
            self.constants[name] = inst
            node.gen_location = name
            return
        
        # Make the SSA opcode and append to list of generated instructions
        inst = ('literal_' + ty, node.value, target)
        self.code.append(inst)

        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target
    
    def visit_Decl(self, node):
        
        # Check for globals
        if self.fname == 'global':
            # Visit declaration
            self.visit(node.type)
            
            # Get decl type.
            ty = self.build_decl_types(node.type)
            
            ty = 'global_' + ty 
            name = node.type.gen_location
            if node.init:
                init = self.get_expr(node.init, ty=node.type, name=ty)
                inst = (ty, name, init)
            else:
                inst = (ty, name)
            
            # Add to global or constant if local array initialization
            self.globals[name] = inst
            
            # Get gen_location
            node.gen_location = node.type.gen_location
            
        elif self.alloc_phase:
            self.visit(node.type)
            
            # Get gen_location
            node.gen_location = node.type.gen_location
        
        # Handle initialization
        elif node.init:
            
            # Get decl type.
            ty = self.build_decl_types(node.type)
                    
            # Check for array initializers
            arr_decl = isinstance(node.type, ast.ArrayDecl) 
            init_type = isinstance(node.init, ast.InitList)
            
            # If InitList
            if arr_decl and init_type:
                init = self.get_expr(node.init, ty=node.type, name=ty)
                
                name = self.new_str()
                inst = ('global_' + ty, name, init)
                self.constants[name] = inst
                            
                # Create opcode and append to instruction list
                inst = ('store_' + ty, name, node.gen_location)
                self.code.append(inst)
            else:
                # Visit initializers
                self.visit(node.init)

                # Create opcode and append to instruction list
                inst = ('store_' + ty, node.init.gen_location, node.gen_location)
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
        self.loop_end.append(target_fake)
            
        # Visit loop
        if node.body:
            self.visit(node.body)
        
        # Visit next
        if node.next:
            self.visit(node.next)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Remove loop scope and end
        self.loop_end.pop()
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
        
        # Get function return type.
        ty = self.scopes.get_func_type(node.name.name)
        
        # Create opcode and append to list.
        if ty.name[0].name != 'void':
            node.gen_location = self.new_temp()
            inst = ('call', '@'+node.name.name, node.gen_location)
        else:
            node.gen_location = None
            inst = ('call', '@'+node.name.name)
    
        self.code.append(inst)

    def visit_FuncDecl(self, node):
        var = node.type
        while not isinstance(var, ast.VarDecl):
            var = var.type
        
        # Add function node to global scope.
        self.scopes.add_global(var, var)
        
        if self.fname != 'global':
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
        inst = ('define', '@'+name)
        self.code.append(inst)
        
        # Start function
        self.fname = name
        
        # Skip temp variables for params and return
        par = node.decl.type
        self.versions[name] = len(par.params.params) if par.params else 0

        # Get return temporary variable
        self.ret['value'] = self.new_temp()
                
        # Visit function declaration (FuncDecl)
        self.alloc_phase = True
        self.visit(node.decl.type)
        
        # Get return label, if needed.
        self.ret['label'] = self.new_temp()
        label = (self.ret['label'][1:],)
                
        # Visit body
        if node.body:
            
            # Allocate first, without init
            if node.body.decls:
                for decl in node.body.decls:
                    self.visit(decl)
            
            # Initiate decls and visit body.
            self.alloc_phase = False
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
        self.scopes.pop_scope()
        
        # Return to global
        self.fname = 'global'
    
    def visit_GlobalDecl(self, node):
        for decl in node.decls:
            # TODO: Ptr FuncDecl
            if not isinstance(decl.type, ast.FuncDecl):
                self.visit(decl)
    
    def visit_ID(self, node):
        # Get temporary with ID name.
        var = self.scopes.fetch_temp(node)
        
        # NOTE: Globals are stored directly from label
        if '@' in var: 
            node.gen_location = var
            return 
        
        # Create a new temporary variable name 
        target = self.new_temp()
        
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
        self.visit(node.if_stat)
        
        # Create ELSE
        if node.else_stat:
            target_exit = self.new_temp()
            inst = ('jump', target_exit)
            self.code.append(inst)
            self.code.append((target_else[1:],))
            self.visit(node.else_stat)
            self.code.append((target_exit[1:],))
        else:
            self.code.append((target_else[1:],))
            
    def visit_InitList(self, node):
        node.gen_location = []
        for expr in node.exprs:
            if isinstance(expr, ast.InitList):
                self.visit(expr)
                node.gen_location.append(expr.gen_location)
            else:
                node.gen_location.append(expr.value)
    
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
                        
            # Handle 1 or more exprs
            if isinstance(node.expr, ast.ExprList):
                exprs = node.expr.exprs
            else:
                exprs = [node.expr]
            
            for expr in exprs:
                self.visit(expr)
                ty = self.build_reg_types(expr.type)
                inst = ('print_' + ty, expr.gen_location)
                self.code.append(inst)
        else:
            inst = ('print_void',)
            self.code.append(inst)
    
    def visit_PtrDecl(self, node):
        self.visit(node.type)
        node.gen_location = node.type.gen_location
    
    def visit_Read(self, node):
        # Create the opcode and append to list
        if isinstance(node.expr, ast.ExprList):
            exprs = node.expr.exprs
        else:
            exprs = [node.expr]
            
        for expr in exprs:
            # Read
            aux = self.new_temp()
            ty = self.build_reg_types(expr.type)
            inst = ('read_' + ty, aux)
            
            # Store
            if isinstance(expr, ast.ID):
                target = self.scopes.fetch_temp(expr)
            else:
                target = expr.gen_location
            stor = ('store_' + ty, aux, target)
            self.code += [inst, stor]

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
        else:
            # Allocate on stack memory.
            alloc_target = self.new_temp()
            inst = ('alloc_' + ty, alloc_target)
            self.code.append(inst)
        
            node.gen_location = alloc_target
        
        # Adding to scope
        self.scopes.add_to_scope(node, node.gen_location)
    
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
        self.loop_end.append(target_fake)
        
        # Visit loop
        self.code.append((target_true[1:],))
        if node.body:
            self.visit(node.body)
        
        # Go back to the beginning.
        inst = ('jump', label)
        self.code.append(inst)
        
        # Remove loop ending.
        self.loop_end.pop()
        
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
            ret = self.scopes.fetch_temp(expr) # TODO: should replace ID.name by the ID's value (done?)
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
        # TODO: maybe add array total size in semantic check?
        size,dims = 1,0
        ptr = 0
        name = ''
        ty = node
        while not isinstance(ty, ast.VarDecl):
            if isinstance(ty, ast.ArrayDecl):
                size *= ty.dims.value
                dims += 1
            elif isinstance(ty, ast.PtrDecl):
                ptr += 1
            ty = ty.type
        
        if dims > 0:    
            if dims == 1:
                name += f'_{size}'
            else:
                name += f'_{size}_{dims}'                
        
        if ptr > 0:
            name += ('_*'*ptr)
        
        name = ty.type.name[-1].name + name
        return name
    
    def build_reg_types(self, ty):
        name = ''
        for item in ty.name[::-1]:
            if item.name == 'array':
                pass
            #    name += f'_'{ty.dims.value}' # TODO: get dims (save in scope?)
            elif item.name == 'ptr':
                name += '_*'
            else:
                name += item.name
        return name
