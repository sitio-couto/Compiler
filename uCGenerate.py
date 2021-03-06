'''
Second Project: IR generation for the uC language (uCIR) based on checked AST.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 09/07/2020.
'''

import re
import uCAST as ast
from uCSemantic import SymbolTable
from os.path import exists

class ScopeStack():
    '''
    Class responsible for keeping variables scopes.
    Used for type checking variables as well as checking if they're are defined.
    Atributes:
        - stack: stack of SymbolTables. Each item is a different scope ([0] is global [-1] is local)
    '''
    def __init__(self):
        self.stack = []
        self.dims = dict()
    
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

    def add_dims(self, node, data):
        name = node.declname.name
        dims = list(map(int, re.findall(r'_(\d+)', data)))
        self.dims[name] = dims

    def fetch_dims(self, node):
        return list(reversed(self.dims[node.name]))

    # Get type of function, stored as a global var.
    def get_func_type(self, name):
        return self.stack[0].lookup(name).type

    # Return a variable's address
    def fetch_temp(self, node):
        name = node.name
        for scope in self.stack[::-1]:
            var = scope.lookup(name)
            if var: break
        
        # If function
        if isinstance(var, ast.VarDecl):
            var = var.gen_location
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

class uCIRGenerator(ast.NodeVisitor):
    '''
    Node visitor class that creates 3-address encoded instruction sequences.
    '''
    def __init__(self, front_end=None):
        super(uCIRGenerator, self).__init__()

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
        self.cnst_counter = 0

        # Dictionaries for operations
        self.bin_ops = {'+':'add', '-':'sub', '*':'mul', '/':'div', '%':'mod'}
        self.rel_ops = {'<':'lt', '>':'gt', '<=':'le', '>=':'ge', '==':'eq', '!=':'ne', '&&':'and', '||':'or'}

        # The generated code (list of tuples)
        self.code = []
        
        # Useful attributes
        self.arr = {'offset':0, 'depth':-1, 'stack':[]} 
        self.ret = {}
        self.loop_end = []
        self.alloc_phase = None

    def new_str(self):
        ''' Create a new string constant on the global scope. '''
        name = f"@.str.{self.cnst_counter}" 
        self.cnst_counter += 1
        return name
    
    def new_const(self, name):
        ''' Create a new array constant on the global scope. '''
        const = f"@.const_" + name + f".{self.cnst_counter}" 
        self.cnst_counter += 1
        return const

    def new_temp(self):
        ''' Create a new temporary variable of a given scope (function name). '''
        if self.fname not in self.versions:
            self.versions[self.fname] = 1
        name = f"%{self.versions[self.fname]}" 
        self.versions[self.fname] += 1
        return name

    def generate(self, data):
        ast = self.front_end.parser.parse(data, False)
        self.front_end.visit(ast)
        self.visit(ast)

    def test(self, data, show_ast, out_file=None, quiet=False):
        self.code = []
        self.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()

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
    
    def format_instruction(self, t):
        # Auxiliary method to pretty print the instructions 
        # t is the tuple that contains one instruction
        op = t[0]
        if len(t) > 1:
            if op.startswith("define"):
                return f"\n{op} {t[1]} " + ', '.join(list(' '.join(el) for el in t[2]))+'\nentry:'
            else:
                _str = "" if op.startswith('global') else "  "
                if op == 'jump':
                    _str += f"{op} label {t[1]}"
                elif op == 'cbranch':
                    _str += f"{op} {t[1]} label {t[2]} label {t[3]}"
                elif op == 'global_string':
                    _str += f"{op} {t[1]} \'{t[2]}\'"
                elif op.startswith('return'):
                    _str += f"{op} {t[1]}"
                else:
                    for _el in t:
                        _str += f"{_el} "
                return _str
        elif op == 'print_void' or op == 'return_void':
            return f"  {op}"
        elif op.isdigit():
             return f"{op}:"
        else:
            return f"{op}"
        
    def print_code(self):
        formatted = map(self.format_instruction, self.code)
        print(*list(formatted), sep='\n')
    
    def show(self, buf=None):
        if not buf:
            self.print_code()
        else:
            _str = ''
            for _code in self.code:
                _str += self.format_instruction(code)+'\n'
            buf.write(_str)

    def write_file(self, code, out_file):
        out = ''
        for inst in code: out += self.format_instruction(inst)+'\n'
        f = open(out_file, 'w')
        f.write(out)
        f.close()

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
        # Getting type
        ty = self.build_decl_types(node)
        
        # Adding to scope
        var = node.type
        while not isinstance(var, ast.VarDecl):
            var = var.type
        self.scopes.add_dims(var, ty)
        
        # Allocate
        if self.fname == 'global':
            node.gen_location = '@'+var.declname.name
        else:
            alloc_target = '%'+var.declname.name
            inst = ('alloc_' + ty, alloc_target)
            self.code.append(inst)
            node.gen_location = alloc_target

        self.scopes.add_to_scope(var, node.gen_location)
    
    def visit_ArrayRef(self, node):
        self.arr['depth'] += 1
        
        # Fetch the array's dimensions (if on root)
        self.build_offset(node)
        
        # If not root, skip elem instruction
        if self.arr['depth'] == 0: 
            # get address and type
            addr = self.arr['temp']
            ty = self.arr['type']

            # Get new temp variables
            target = self.new_temp()
                    
            # Create instructions
            elem = ("elem_" + ty, addr, self.arr['offset'], target)
            self.code.append(elem)

            # If ArrayRef in ArrayRef must manually load
            if self.arr['stack']:
                addr = target
                target = self.new_temp()
                load = (f'load_{ty}_*', addr, target)
                self.code.append(load)
                
            # Update class gen_location
            node.gen_location = target

        self.arr['depth'] -= 1

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
        
        # Create types
        ty = self.build_reg_types(node.rvalue.type)
        
        # Load if ArrayRef
        if isinstance(node.rvalue, ast.ArrayRef):
            target = self.new_temp()
            inst = ('load_'+ty+'_*', node.rvalue.gen_location, target)
            self.code.append(inst)
            node.rvalue.gen_location = target
        
        # Assignable expressions are ID, ArrayRef and UnaryOp
        visited = False
        if isinstance(node.lvalue, ast.ID):
            laddr = self.scopes.fetch_temp(node.lvalue)
        elif isinstance(node.lvalue, ast.UnaryOp) and node.lvalue.op == '*':
            laddr = self.scopes.fetch_temp(node.lvalue.expr)
            ty += '_*'
        else:
            visited = True
            self.visit(node.lvalue)
            laddr = node.lvalue.gen_location
            
            # Get content if ArrayRef.
            if isinstance(node.lvalue, ast.ArrayRef):
                ty += '_*'
        
        # Other assignment ops
        if node.op != '=':
            if not visited:   self.visit(node.lvalue)
            loc = self.new_temp()
            opcode = self.bin_ops[node.op[0]] + "_" + ty
            inst = (opcode, node.lvalue.gen_location, node.rvalue.gen_location, loc)
            self.code.append(inst)
        else:
            loc = node.rvalue.gen_location
        
        if isinstance(node.rvalue, ast.UnaryOp) and node.rvalue.op == '&':
            inst = ('get_' + ty + '_*', loc, laddr)
        else:
            inst = ('store_' + ty, loc, laddr)
        self.code.append(inst)
                
        # Store location of the result on the node        
        node.gen_location = laddr
        
    def visit_BinaryOp(self, node):
        # Visit the left and right expressions        
        self.visit(node.lvalue)
        # Load if ArrayRef
        if isinstance(node.lvalue, ast.ArrayRef):
            ty = self.build_reg_types(node.lvalue.type)
            target = self.new_temp()
            inst = ('load_'+ty+'_*', node.lvalue.gen_location, target)
            self.code.append(inst)
            node.lvalue.gen_location = target
        
        self.visit(node.rvalue)
        # Load if ArrayRef
        if isinstance(node.rvalue, ast.ArrayRef):
            ty = self.build_reg_types(node.rvalue.type)
            target = self.new_temp()
            inst = ('load_'+ty+'_*', node.rvalue.gen_location, target)
            self.code.append(inst)
            node.rvalue.gen_location = target

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
        
        # Load if ArrayRef
        if isinstance(node.expr, ast.ArrayRef):
            ty = self.build_reg_types(node.expr.type)
            target = self.new_temp()
            inst = ('load_'+ty+'_*', node.expr.gen_location, target)
            self.code.append(inst)
            node.expr.gen_location = target
        
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
        # Get type and check if is a string
        ty = node.type.name[0].name

        # Strings are a special case
        if ty == 'string': 
            # Constant must be in array (no opcode)
            name = self.new_str()
            inst = ('global_string', name, node.value)
            self.constants[name] = inst
            node.gen_location = name
            return

        # Create a new temporary variable name 
        target = self.new_temp()

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
            
            # Check function ptr
            dec = node.type
            while not (isinstance(dec, ast.Type) or isinstance(dec, ast.FuncDecl)):
                dec = dec.type
            
            # Get decl type and name.
            ty = self.build_decl_types(node.type)
            ty = 'global_' + ty 
            name = node.type.gen_location
            
            # Function Pointer.
            if isinstance(dec, ast.FuncDecl):
                params_list = []
                for i, p in enumerate(dec.params.params or []):
                    par = self.build_decl_types(p)
                    params_list.append(par)
                inst = (ty, name, params_list)
            
            # Regular variables.
            elif node.init:
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
                
                name = self.new_const(node.name.name)
                inst = ('global_' + ty, name, init)
                self.constants[name] = inst
                            
                # Create opcode and append to instruction list
                inst = ('store_' + ty, name, node.gen_location)
                self.code.append(inst)
            else:
                # Visit initializers
                self.visit(node.init)
                name = node.init.gen_location

                # Create opcode and append to instruction list
                if isinstance(node.init, ast.UnaryOp) and node.init.op == '&':
                    inst = ('get_' + ty, name, node.gen_location)
                    self.code.append(inst)
                elif isinstance(node.init, ast.ArrayRef):
                    target = self.new_temp()
                    inst1 = ('load_' + ty + '_*', name, target)
                    inst2 = ('store_' + ty, target, node.gen_location)
                    self.code += [inst1, inst2]
                else:
                    inst = ('store_' + ty, name, node.gen_location)
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
        
        # Create loop label
        label = self.new_temp()
        inst = ('jump', label)
        
        # Create true/false labels
        if node.cond:
            target_true = self.new_temp()
            target_fake = self.new_temp()
        else:
            target_fake = self.new_temp()
        
        # Visit declarations
        if node.init:
            self.visit(node.init)
        
        self.code += [inst, (label[1:],)]
        
        if node.cond:
            # Visit the condition
            self.visit(node.cond)
            
            # Create the opcode and append to list
            inst = ('cbranch', node.cond.gen_location, target_true, target_fake)
            self.code.append(inst)

            self.code.append((target_true[1:],))
        
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
        
        # Get ptr if function ptr.
        if ty.name[0].name == 'ptr':
            self.visit(node.name)
            name = node.name.gen_location
        else:
            name = '@' + node.name.name
        
        # Create opcode and append to list.
        ty = self.build_reg_types(ty)
        if ty != 'void':
            node.gen_location = self.new_temp()
            inst = ('call_' + ty, name, node.gen_location)
        else:
            node.gen_location = None
            inst = ('call_void', name)
    
        self.code.append(inst)

    def visit_FuncDecl(self, node):
        var = node.type
        while not isinstance(var, ast.VarDecl):
            var = var.type
        
        var.gen_location = '@'+var.declname.name
        
        if self.fname != 'global':
            if node.params:
                self.visit(node.params)
        
        # Add function node to global scope.
        self.scopes.add_global(var, var)
        
        node.gen_location = var.gen_location
    
    def visit_FuncDef(self, node):
        # Add function's scope
        self.scopes.add_scope(node=node)

        # Find out function name.
        var = node.decl
        while not isinstance(var, ast.VarDecl):
            var = var.type
        name = var.declname.name
        
        # Start function
        self.fname = name
        
        # Skip temp variables for params, and create list.
        par = node.decl.type
        params_list = []
        if par.params:
            for i, p in enumerate(par.params.params or []):
                ty = self.build_decl_types(p)
                new = self.new_temp()
                params_list.append((ty, new))
        
        # Create definition and append to list
        ty = self.build_reg_types(var.type)
        inst = ('define_'+ty, '@'+name, params_list)
        self.code.append(inst)
        
        # Get return temporary variable
        if ty != 'void':
            self.ret['value'] = self.new_temp()
            inst = ('alloc_'+ty, self.ret['value'])
            self.code.append(inst)

        # Get return label, if needed.
        self.ret['label'] = self.new_temp()
        label = (self.ret['label'][1:],)
        
        # Visit function declaration (FuncDecl)
        self.alloc_phase = True
        self.visit(node.decl.type)
        
        # Visit body
        if node.body:
            
            # Allocate first, without init
            if node.body.decls:
                for decl in node.body.decls:
                    self.visit(decl)
                    
            # Visiting for declaration.
            # TODO: only works if the For is directly in function compound statement.
            if node.body.stats:
                for stmt in node.body.stats:
                    if isinstance(stmt, ast.For) and isinstance(stmt.init, ast.DeclList):
                        self.visit(stmt.init)
            
            # Initiate params, decls and visit body.
            self.alloc_phase = False
            if par.params:
                self.visit(par.params)
                
            self.visit(node.body)
        
        # Return label and return        
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
            self.visit(decl)
    
    def visit_ID(self, node):
        # Get temporary with ID name.
        var = self.scopes.fetch_temp(node)

        # Create a new temporary variable name 
        target = self.new_temp()
        
        # Check pointer
        ty = self.build_reg_types(node.type)
        if node.type.name[0].name == 'ptr':
            ty += '_*'
        
        # Create the opcode and append to list
        inst = ('load_' + ty, var, target)
        self.code.append(inst)
        
        # Save the name of the temporary variable where the value was placed 
        node.gen_location = target
        
    def visit_If(self, node):
        # Create two new temporary variable names for then/else labels
        target_then = self.new_temp()
        target_else = self.new_temp()
        
        # Visit condition
        self.visit(node.cond)

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
        if self.alloc_phase:
            for par in node.params:
                # Visit parameter (allocate vars)
                self.visit(par)
        
        else:
            for i, par in enumerate(node.params or []):
                # Store value in temp var "i" in newly allocated var.
                ty = self.build_decl_types(par)
                inst = ('store_'+ty, f'%{i+1}', par.gen_location)
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
                
                # Load if ArrayRef
                if isinstance(expr, ast.ArrayRef):
                    target = self.new_temp()
                    inst = ('load_'+ty+'_*', expr.gen_location, target)
                    self.code.append(inst)
                    expr.gen_location = target
                    
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
            ty = self.build_reg_types(expr.type)
            
            if isinstance(expr, ast.ID):
                target = self.scopes.fetch_temp(expr)
            elif isinstance(expr, ast.ArrayRef):
                self.visit(expr)
                ty += '_*'
                target = expr.gen_location
            else:
                self.visit(expr)
                target = expr.gen_location
            inst = ('read_' + ty, target)
            self.code.append(inst)

    def visit_Return(self, node):
        # If there is a return expression.
        if node.expr:
            self.visit(node.expr)
            expr_loc = node.expr.gen_location
            
            # Store return value in allocated variable
            ty = self.build_reg_types(node.expr.type)
            
            # Load if ArrayRef
            if isinstance(node.expr, ast.ArrayRef):
                target = self.new_temp()
                inst = ('load_'+ty+'_*', expr_loc, target)
                self.code.append(inst)
                expr_loc = target
            
            inst = ('store_'+ty, expr_loc, self.ret['value'])
            self.code.append(inst)
                    
        # Jump to return label.
        inst = ('jump', self.ret['label'])
        self.code.append(inst)

    def visit_Type(self, node):
        assert False, "'Type' nodes are not visited in code generation!"
    
    def visit_UnaryOp(self, node):
        # With address, don't load ID.
        if node.op == '&' and isinstance(node.expr, ast.ID):
            node.gen_location = self.scopes.fetch_temp(node.expr)
            return
        
        # Visit the expression
        self.visit(node.expr)
        expr_loc = node.expr.gen_location
        ty = self.build_reg_types(node.expr.type)
        
        # With address, we ignore pointers or ArrayRef.
        if node.op == '&':
            node.gen_location = expr_loc
            return
        
        # Load if ArrayRef
        if isinstance(node.expr, ast.ArrayRef):
            target = self.new_temp()
            inst = ('load_'+ty+'_*', expr_loc, target)
            self.code.append(inst)
            expr_loc = target
        
        # Operation '+' is useless.
        # Pointer operation is purely semantic.
        if node.op == '+' or node.op == '*':
            node.gen_location = expr_loc
            return
        
        # NOT is a specific case.
        if node.op == '!':
            target = self.new_temp()
            inst1 = ('not_bool', expr_loc, target)
            self.code.append(inst1)
            node.gen_location = target
            return
                
        # Create new temporary variables
        literal = self.new_temp()
        target = self.new_temp()
        
        # Create the opcode and append to list
        if node.op == '-':
            inst1 = ('literal_' + ty, 0, literal)
            inst2 = ('sub_' + ty, literal, expr_loc, target)
        elif '++' in node.op:
            inst1 = ('literal_int', 1, literal)
            inst2 = ('add_int', expr_loc, literal, target)
        elif '--' in node.op:
            inst1 = ('literal_int', 1, literal)
            inst2 = ('sub_int', expr_loc, literal, target)
        else:
            assert False, "Unsupported unary operation."

        self.code += [inst1, inst2]
        
        if isinstance(node.expr, ast.ID) and node.op != '-':
            var = self.scopes.fetch_temp(node.expr)
            inst = ('store_int', target, var)
            self.code.append(inst)
        
        # Store location of the result (or expr) on the node
        if node.op[0] == 'p':
            node.gen_location = expr_loc
        else:
            node.gen_location = target

    def visit_VarDecl(self, node):
        ty = self.build_var_types(node.type)
        
        # Try global
        if self.fname == 'global':
            node.gen_location = '@'+node.declname.name
        else:
            # Allocate on stack memory.
            alloc_target = '%'+node.declname.name
            inst = ('alloc_' + ty, alloc_target)
            self.code.append(inst)
        
            node.gen_location = alloc_target
        
        # Adding to scope
        self.scopes.add_to_scope(node, node.gen_location)
    
    def visit_While(self, node):
        # Create loop label
        label = self.new_temp()
        inst = ('jump', label)
        self.code += [inst, (label[1:],)]
        
        # Create two new temporary variable names for true/false labels
        target_true = self.new_temp()
        target_fake = self.new_temp()
        
        # Visit the condition
        self.visit(node.cond)

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

    def build_index(self, node):
        # Fetch array access index
        if isinstance(node.subsc, ast.ArrayRef):
            # Stack recursion if ArraryRef of ArrayRef (x[y[i]])
            self.arr['stack'] += [self.arr['depth']]
            self.arr['depth'] = -1 
            self.visit(node.subsc)
            self.arr['depth'] = self.arr['stack'].pop()
        else:
            self.visit(node.subsc)

    def build_offset(self, node):
        ''' This function receives the root of a ArrayRef chain and creates
            the necessary instuctions to build the offset of the referenced 
            position. It is also responsible for collecting necessary info 
            to build the elem_(type) instuction in the ArrayRef node.
        '''

        if isinstance(node.name, ast.ArrayRef):
            self.visit(node.name)
        else: # Recursion's Base
            self.arr['temp'] = self.scopes.fetch_temp(node.name)
            self.arr['type'] = self.build_reg_types(node.type)
            self.arr['ref'] = self.scopes.fetch_dims(node.name)
            self.arr['offset'] = 0

        # Multiply index by dimension's elements size
        if self.arr['depth'] == 0:
            self.build_index(node)
            result = node.subsc.gen_location
        else:
            # Load dimension's element size value
            # We want the size of the dimension's elements, therefore we fetch the inner dimension's size (hence the -1 in self.arr['depth']-1)
            element_size = self.arr['ref'][self.arr['depth']-1] 
            size = self.new_temp()
            literal = ('literal_int', element_size, size)
            self.code.append(literal)

            # Fetch array access index
            self.build_index(node)

            # Multiply index and the dimension's element size
            result = self.new_temp()
            mult = ('mul_int', size, node.subsc.gen_location, result)
            self.code.append(mult)

        # Update the current offset
        # if not 0, then create a add instruction to acumulate
        if self.arr['offset']: 
            new_offset = self.new_temp()
            add = ('add_int', self.arr['offset'], result, new_offset)
            self.code.append(add)
        # If 0, define the offset as the multiplication's result
        else: 
            new_offset = result
            
        # Update offset
        self.arr['offset'] = new_offset

    # Get Expression for constant initilization
    # This should handle the possible assignment expressions
    def get_expr(self, expr, ty=None, name=None):
        if isinstance(expr, ast.BinaryOp):
            left = self.get_expr(expr.lvalue)
            right = self.get_expr(expr.rvalue)
            ret = eval(f"({left}{expr.op}{right})")
        elif isinstance(expr, ast.UnaryOp):
            right = self.get_expr(expr.expr)
            ret = eval(f"({expr.op}{right})")
        elif isinstance(expr, ast.ID):
            ret = self.scopes.fetch_temp(expr)
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

    ## TYPE-RELATED FUNCTIONS ##

    def build_decl_types(self, node):
        ptr = 0
        name = ''
        ty = node
        
        # Identify modifiers.
        while not isinstance(ty, ast.VarDecl):
            if isinstance(ty, ast.ArrayDecl):
                name += f'_{ty.dims.value}'  
            elif isinstance(ty, ast.PtrDecl):
                ptr += 1
            ty = ty.type
        
        # Ptrs
        if ptr > 0:
            name += ('_*'*ptr)
        
        name = ty.type.name[-1].name + name
        return name
    
    def build_reg_types(self, ty):
        return ty.name[-1].name
    
    def build_var_types(self, ty):
        name = ''
        for item in ty.name[::-1]:
            if item.name == 'array':
                pass
            elif item.name == 'ptr':
                name += '_*'
            else:
                name += item.name
        return name
