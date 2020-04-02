'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 02/04/2020.
'''

from ply.yacc import yacc
from os.path import exists
import uCAST as ast

class uCParser():
    
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('nonassoc', 'EQ', 'UNEQ'),
        ('nonassoc', '<', '>', 'LE', 'GE'),
        ('left', '+', '-'),
        ('left', '*', '/', '%')
    )

    # Initializes the class with the lexer object and tokens list.
    def __init__(self, lexer):
        self.lexer = lexer
        self.tokens = lexer.tokens
    
    # Builds the parser.
    def build(self, **kwargs):
        self.parser = yacc(
            module=self,
            start='program',
            write_tables=False,
            **kwargs)
    
    # Parses an expression.
    def parse(self, data, debug):
        return self.parser.parse(data, debug=debug)
    
    # Tests an expression and prints the result
    def test(self, data):
        self.lexer.reset_line_num()
        if exists(data): 
            with open(data, 'r') as content_file :
                data = content_file.read()
        # print(self.parse(data))
        self.parse(data).show()

    #### ROOT ####
    
    def p_program(self, p) :
        ''' program : global_declaration_list '''
        p[0] = ast.Program(p[1])

    #### FIRST SPLIT ####

    def p_global_declaration_1(self, p) :
        ''' global_declaration : function_definition '''
        p[0] = p[1]
    def p_global_declaration_2(self, p) :
        ''' global_declaration : declaration '''
        p[0] = ast.GlobalDecl(p[1])

    def p_function_definition_1(self, p):
        ''' function_definition : type_specifier declarator declaration_list_opt compound_statement '''
        # p[0] = ('func', p[1], p[2], p[3], p[4])
        # p[0] = [ast.FuncDef(p[1], p[2], p[3], p[4])]
        p[0] = self._build_function_definition(p[1], p[2], p[3], p[4])
    def p_function_definition_2(self, p): # If return type not defined, defaults to INT
        ''' function_definition : declarator declaration_list_opt compound_statement '''
        #p[0] = ('func', 'void', p[1], p[2], p[3])
        # p[0] = [ast.FuncDef(None, p[1], p[2], p[3])]
        # type = ast.Type(['int'], self.get_coord(p, 1)) # If no reutur type specified, defaults to INT
        p[0] = self._build_function_definition(type, p[1], p[2], p[3])

    def p_declaration(self, p):
        ''' declaration : type_specifier init_declarator_list_opt ';' '''
        # p[0] = (p[1], p[2])
        p[0] = self._build_declarations(p[1], p[2]) # Build multiple declarations based on single specifier

    def p_init_declarator_1(self, p):
        ''' init_declarator : declarator '''
        # p[0] = (p[1], None) # returns tuple without initializer
        p[0] = dict(decl=p[1], init=None)
    def p_init_declarator_2(self, p):
        ''' init_declarator : declarator '=' initializer '''
        # p[0] = (p[1], p[3]) # Has initializer in tuple
        p[0] = dict(decl=p[1], init=p[3])


    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        #p[0] = p[1]
        p[0] = ast.Type(p[1], self.get_coord(p,1))

    def p_initializer_1(self, p):
        ''' initializer : assign_expr '''
        p[0] = p[1]
    # NOTE: Initilizer_list will never be None by the grammar (and maybe it should)
    def p_initializer_2(self, p):
        ''' initializer : '{' initializer_list '}'
                        | '{' initializer_list ',' '}'
        '''
        # p[0] = ('{', p[2], '}')
        p[0] = p[2]

    def p_declarator(self, p):
        ''' declarator : direct_declarator '''
        p[0] = p[1]
        
    def p_direct_declarator_1(self, p):
        ''' direct_declarator : identifier '''
        # p[0] = p[1]
        p[0] = ast.VarDecl(p[1], None, None) # Initialy, it has None type
    def p_direct_declarator_2(self, p):
        ''' direct_declarator : '(' declarator ')' '''
        p[0] = p[2] 
    def p_direct_declarator_3(self, p):
        ''' direct_declarator : direct_declarator '[' const_expr_opt ']' '''
        aux = ast.ArrayDecl(None, p[3] if len(p) == 5 else 1, p[1].coord)
        p[0] = self._type_modify_decl(p[1], aux)
    def p_direct_declarator_4(self, p):
        ''' direct_declarator : direct_declarator '(' parameter_list ')' 
                              | direct_declarator '(' id_list_opt ')' 
        '''
        # p[0] = (p[1], p[3]) 
        # NOTE: Not defining coodinates do it seems more like the professors output
        aux = ast.FuncDecl(None, p[3], None) # None type will be overwritten later
        p[0] = self._type_modify_decl(p[1], aux)

    #### EXPRESSIONS ####

    def p_expr_1(self, p):
        ''' expr : assign_expr '''
        p[0] = p[1]
    def p_expr_2(self, p):
        ''' expr : expr ',' assign_expr '''
        if not isinstance(p[1], ast.ExprList):
            p[1] = ast.ExprList([p[1]], p[1].coord)
            
        p[1].exprs.append(p[3])
        p[0] = p[1]

    def p_assign_expr_1(self, p):
        ''' assign_expr : bin_expr '''
        p[0] = p[1]
    def p_assign_expr_2(self, p):
        ''' assign_expr : un_expr assign_op assign_expr '''
        #  __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
        p[0] = ast.Assignment(p[2], p[1], p[3], p[1].coord)
        # p[0] = (p[1], p[2], p[3])

    def p_assign_op(self, p):
        ''' assign_op : '='
                      | TIMESEQ
                      | DIVEQ
                      | MODEQ
                      | PLUSEQ
                      | MINUSEQ
        '''
        p[0] = p[1]

    # Binary Expressions #
    # (123*4) '+' 800

    def p_bin_expr_1(self, p):
        ''' bin_expr : cast_expr '''
        p[0] = p[1]
    def p_bin_expr_2(self, p):
        ''' bin_expr : bin_expr '-' bin_expr
                     | bin_expr '*' bin_expr
                     | bin_expr '+' bin_expr
                     | bin_expr '/' bin_expr
                     | bin_expr '%' bin_expr
                     | bin_expr '<' bin_expr
                     | bin_expr LE bin_expr
                     | bin_expr '>' bin_expr
                     | bin_expr GE bin_expr
                     | bin_expr EQ bin_expr
                     | bin_expr UNEQ bin_expr
                     | bin_expr AND bin_expr
                     | bin_expr OR bin_expr
        '''
        # __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
        p[0] = ast.BinaryOp(p[2], p[1], p[3], p[1].coord)
        # p[0] = (p[1], p[2], p[3])

    # Cast Expressions # 
    # (float) 123;

    def p_cast_expr_1(self, p):
        ''' cast_expr : un_expr '''
        p[0] = p[1]
        # p[0] = p[1]
    def p_cast_expr_2(self, p):
        ''' cast_expr : '(' type_specifier ')' cast_expr '''
        p[0] = ast.Cast(p[2], p[4], self.get_coord(p,1))
        #p[0] = ('cast', p[2], p[4])

    # Unary Expressions #
    # ++i; 
    # -10;

    def p_un_expr_1(self, p):
        ''' un_expr : postfix_expr '''
        p[0] = p[1]
    def p_un_expr_2(self, p):
        ''' un_expr : PLUSPLUS un_expr
                    | MINUSMINUS un_expr
                    | un_op cast_expr
        '''
        #p[0] = (p[1], p[2])
        p[0] = ast.UnaryOp(p[1], p[2], p[2].coord)

    # Unary Operators #
    # '-' NUM | '*' PTR | '&' ADDR 

    # NOTE: the '*' is only used if pointer are considered
    def p_un_op(self, p):
        ''' un_op : '&'
                  | '+'
                  | '*' 
                  | '-'
                  | '!'
        '''
        p[0] = p[1]    

    # Postfix Expressions #

    def p_postfix_expr_1(self, p):
        '''postfix_expr : primary_expr '''
        p[0] = p[1]
    def p_postfix_expr_2(self, p):
        '''postfix_expr : postfix_expr '[' expr ']' '''
        p[0] = ast.ArrayRef(p[1], p[3], p[1].coord)
    def p_postfix_expr_3(self, p):
        '''postfix_expr : postfix_expr '(' expr_opt ')' '''
        p[0] = ast.FuncCall(p[1], p[3], p[1].coord) 
    def p_postfix_expr_4(self, p):
        '''postfix_expr : postfix_expr PLUSPLUS
                        | postfix_expr MINUSMINUS
        '''
        #p[0] = (p[1], p[2]) 
        # NOTE: 'p' as in 'postfix' (t1.ast)
        p[0] = ast.UnaryOp('p' + p[2], p[1], p[1].coord) 

    # Primary Expressios #
    # ( ... ) | var | 12.5 | "hello"

    def p_primary_expr_1(self, p):
        ''' primary_expr : '(' expr ')' '''
        p[0] = p[2]
    def p_primary_expr_2(self, p):
        ''' primary_expr : identifier
                         | constant
        '''
        p[0] = p[1] 
        
    # Terminal Expressions #

    def p_identifier(self, p):
        ''' identifier : ID '''
        p[0] = ast.ID(p[1], self.get_coord(p,1))

    # TODO: There might be a better way to do this   
    def p_constant_1(self, p):
        ''' constant : CCONST '''
        p[0] = ast.Constant('char', p[1], self.get_coord(p,1))
    def p_constant_2(self, p):
        ''' constant : ICONST '''
        p[0] = ast.Constant('int', p[1], self.get_coord(p,1))
    def p_constant_3(self, p):
        ''' constant : FCONST '''
        p[0] = ast.Constant('float', p[1], self.get_coord(p,1))
    def p_constant_4(self, p): # TODO: Check if this production is right (it seemed more organized)
        ''' constant : STRING'''
        p[0] = ast.Constant('string', p[1], self.get_coord(p,1))

    #### STATEMENTS ####

    def p_statement(self, p):
        ''' statement : expr_statement
                      | compound_statement
                      | selection_statement
                      | iteration_statement
                      | jump_statement
                      | assert_statement
                      | print_statement
                      | read_statement
        '''
        p[0] = p[1]

    def p_expr_statement(self, p):
        ''' expr_statement : expr_opt ';' '''
        p[0] = ast.EmptyStatement(self.get_coord(p,1)) if p[1] is None else p[1]

    def p_compound_statement(self, p):
        ''' compound_statement : '{' declaration_list_opt statement_list_opt '}' '''
        # p[0] = ('{', p[2], p[3], '}')
        # TODO: Same as DeclList: not printing if is None
        p[0] = ast.Compound(p[2], p[3], self.get_coord(p,1)) if p[2] or p[3] else None

    # Selection Staments #    
    # if () {} | if () {} else {}

    def p_selection_statement_1(self, p): # If block only
        ''' selection_statement : IF '(' expr ')' statement '''
        #p[0] = ('if', p[3], p[5], None)
        p[0] = ast.If(p[3], p[5], None, self.get_coord(p,1))
    def p_selection_statement_2(self, p): # If-Else block
        ''' selection_statement : IF '(' expr ')' statement ELSE statement '''
        #p[0] = ('if', p[3], p[5], p[7])
        p[0] = ast.If(p[3], p[5], p[7], self.get_coord(p,1))


    # Iteration Statements #
    # for () {} | while () {}

    def p_iteration_statement_1(self, p):
        ''' iteration_statement : WHILE '(' expr ')' statement '''
        #p[0] = (p[1], p[3], p[5])
        p[0] = ast.While(p[3], p[5], self.get_coord(p,1))
    def p_iteration_statement_2(self, p):
        ''' iteration_statement : FOR '(' expr_opt ';' expr_opt ';' expr_opt ')' statement '''
        #p[0] = (p[1], p[3], p[5], p[7], p[9])
        p[0] = ast.For(p[3], p[5], p[7], p[9], self.get_coord(p,1))
    def p_iteration_statement_3(self, p): # TODO: This might need to be revised (declaration can be a list: int a, b=0, c;)
        ''' iteration_statement : FOR '(' declaration expr_opt ';' expr_opt ')' statement '''
        #p[0] = (p[1], p[3], p[4], p[6], p[8])
        aux = ast.DeclList(p[3], self.get_coord(p,1))
        p[0] = ast.For(aux, p[4], p[6], p[8], self.get_coord(p,1))                

    # Jump Statements #
    # break; return; 

    def p_jump_statement_1(self, p):
        ''' jump_statement : BREAK ';' '''
        p[0] = ast.Break(self.get_coord(p,1))
        # p[0] = ('break')
    def p_jump_statement_2(self, p):
        ''' jump_statement : RETURN expr_opt ';' '''
        p[0] = ast.Return(p[2], self.get_coord(p,1))
        #p[0] = ('return', p[2])

    # Functions Statements #

    def p_assert_statement(self, p):
        ''' assert_statement : ASSERT expr ';' '''
        p[0] = ast.Assert(p[2], self.get_coord(p,1))
        # p[0] = ('assert', p[2])

    def p_print_statement(self, p):
        ''' print_statement : PRINT '(' expr_opt ')' ';'  '''
        p[0] = ast.Print(p[3], self.get_coord(p,1))
        #p[0] = ('print', p[3])

    def p_read_statement(self, p):
        ''' read_statement : READ '(' expr ')' ';' '''
        p[0] = ast.Read(p[3], self.get_coord(p,1))
        #p[0] = ('read', p[3])

    #### MISCELANEOUS ####

    def p_parameter_declaration(self, p):
        ''' parameter_declaration : type_specifier declarator '''
        p[0] = self._build_declarations(p[1], [dict(decl=p[2])])[0]

    # Listable Productions #
    # NOTE: SOME LISTING ALREADY HAVE A LIST AS A RETURN TYPE
    # If this is the case, there's no need to put the values in brackets ([val])

    def p_global_declaration_list_1(self, p) :
        ''' global_declaration_list : global_declaration_list global_declaration '''
        p[0] = p[1] + [p[2]]
    def p_global_declaration_list_2(self, p) :
        ''' global_declaration_list : global_declaration '''
        p[0] = [p[1]]

    def p_declaration_list_1(self, p) :
        ''' declaration_list : declaration_list declaration '''
        p[0] = p[1] + p[2]
    def p_declaration_list_2(self, p) :
        ''' declaration_list : declaration '''
        p[0] = p[1]

    def p_statement_list_1(self, p) :
        ''' statement_list : statement_list statement '''
        p[0] = p[1] + [p[2]]
    def p_statement_list_2(self, p) :
        ''' statement_list : statement '''
        p[0] = [p[1]]

    # Listable Productions Separated By Tokens #

    def p_init_declarator_list_1(self, p):
        ''' init_declarator_list : init_declarator_list ',' init_declarator '''
        p[0] = p[1] + [p[3]] 
    def p_init_declarator_list_2(self, p):
        ''' init_declarator_list : init_declarator '''
        p[0] = [p[1]] 

    def p_initializer_list_1(self, p):
        ''' initializer_list : initializer_list ',' initializer '''
        # p[0] = p[1] + [p[3]] 
        p[1].exprs.append(p[3]) # Appends elements while retuning from leftside recursion
        p[0] = p[1]             # Return appended list
    def p_initializer_list_2(self, p):
        ''' initializer_list : initializer '''
        # p[0] = [p[1]] 
        # Base Case: Ends left recursion and returns single element InitList
        p[0] = ast.InitList([p[1]], p[1].coord)

    def p_id_list_1(self, p):
        ''' id_list : id_list ',' identifier '''
        p[0] = p[1] + [p[3]] 
    def p_id_list_2(self, p):
        ''' id_list : identifier '''
        p[0] = [p[1]]

    def p_parameter_list_1(self, p):
        ''' parameter_list : parameter_list ',' parameter_declaration '''
        p[1].params.append(p[3])
        p[0] = p[1] 
    def p_parameter_list_2(self, p):
        ''' parameter_list : parameter_declaration '''
        p[0] = ast.ParamList([p[1]], p[1].coord) 
        # NOTE: Instead of creating by hand, we can use the builder to create a single Decl

    # Optional Productions #

    def p_declaration_list_opt(self, p):
        ''' declaration_list_opt : declaration_list
                                 | empty
        '''
        p[0] = p[1] 
        # TODO: His output does not use DeclList (maybe because is an Empty return)
        #p[0] = ast.DeclList(p[1]) if p[1] else None 

    def p_init_declarator_list_opt(self,p):
        ''' init_declarator_list_opt : init_declarator_list 
            	                     | empty
        '''
        p[0] = p[1]

    def p_expr_opt(self, p):
        ''' expr_opt : expr
                     | empty
        '''    
        p[0] = p[1]

    def p_statement_list_opt(self, p):
        ''' statement_list_opt : statement_list
                               | empty
        '''
        p[0] = p[1]

    def p_id_list_opt(self, p):
        ''' id_list_opt : id_list
                        | empty
        '''
        p[0] = p[1]

    def p_const_expr_opt(self, p):
        ''' const_expr_opt : bin_expr
                           | empty
        '''
        p[0] = p[1]

    #### EMPTY PRODUCTION ####
    def p_empty(self, p):
        '''empty : '''
        pass

    #### ERROR HANDLING ####
    def p_error(self, p):
        if p:
            print("Error near the symbol %s at (%s, %s)." % (p.value, p.lineno, p.lexpos))
        else:
            print("Error at the end of input")


    #### AUXILIARY FUNCTIONS ####
    
    def _build_declarations(self, spec, decls):
        """ Builds a list of declarations all sharing the given specifiers.
        
            When a list of declarations is defined (such as int a, b, c=0, d[];),
            the type specifier (spec) apears only once with an undetermined number
            of declarations, which can cause issues instanciating nodes.
            This function handles this issue.
        """
        declarations = []

        if decls is None : return None

        for decl in decls:
            assert decl['decl'] is not None
            declaration = ast.Decl(
                    name=None,
                    type=decl['decl'],
                    init=decl.get('init'),
                    coord=decl['decl'].coord)
                       
            fixed_decl = self._fix_decl_name_type(declaration, spec)
            declarations.append(fixed_decl)

        return declarations

    def _build_function_definition(self, spec, decl, param_decls, body):
        """ Builds a function definition.
        """
        declaration = self._build_declarations(spec, [dict(decl=decl, init=None)])[0]

        # Adding "list" to type.
        spec.name = [spec.name]
        return ast.FuncDef(spec, declaration, param_decls, body)

    def _fix_decl_name_type(self, decl, typename):
        """ Fixes a declaration. Modifies decl.
        """
        # Reach the underlying basic type
        type = decl
        while not isinstance(type, ast.VarDecl):
            type = type.type

        decl.name = type.declname

        # UNNECESSARY ????
        #  So from what i uderstand this is not necessary for us because
        #  typename can only be a list if we consider all the possible
        #  declaration specifiers: storage-class, type-specifier and
        #  type-qualifier. Since we only evaluate the second one, this 
        #  section is of no use to us.
        #
        #     # The typename is a list of types. If any type in this
        #     # list isn't an Type, it must be the only
        #     # type in the list.
        #     # If all the types are basic, they're collected in the
        #     # Type holder.
        #     for tn in typename:
        #         if not isinstance(tn, ast.Type):
        #             if len(typename) > 1:
        #                 self.p_error(tn.coord)
        #             else:
        #                 type.type = tn
        #                 return decl

        # This is for functions with no return value Type.
        # So yeah... Apparently C can do this
        if not typename:
            # Functions default to returning int
            if not isinstance(decl.type, ast.FuncDecl):
                self.p_error(decl.coord)
            type.type = ast.Type(['int'], coord=decl.coord)
        else:
            # Simplifying since there will never be more than one type
            type.type = ast.Type([typename.name], coord=typename.coord)
            # # At this point, we know that typename is a list of Type
            # # nodes. Concatenate all the names into a single list.
            # type.type = ast.Type(
            #     [typename.names[0]],
            #     coord=typename.coord)

        return decl
        
    def _type_modify_decl(self, decl, modifier):
        """ Tacks a type modifier on a declarator, and returns
            the modified declarator.
            Note: the declarator and modifier may be modified
        """
        modifier_head = modifier
        modifier_tail = modifier

        # The modifier may be a nested list. Reach its tail.
        # Necessary if int cube[][][]; 
        while modifier_tail.type:
            modifier_tail = modifier_tail.type

        # If the decl is a basic type, just tack the modifier onto it
        # 'decl' has the type int, now propagate to ArrayDecl
        # int x[] => int ID(x) ArrDecl(None) => int ID(x) ArrDecl(int)
        if isinstance(decl, ast.VarDecl):
            modifier_tail.type = decl
            return modifier
        else: # int x[][][]
            # Otherwise, the decl is a list of modifiers. Reach
            # its tail and splice the modifier onto the tail,
            # pointing to the underlying basic type.
            decl_tail = decl

            while not isinstance(decl_tail.type, ast.VarDecl):
                decl_tail = decl_tail.type

            modifier_tail.type = decl_tail.type
            decl_tail.type = modifier_head
            return decl

    # Get coordinates for token.
    def get_coord(self, p, token_idx):
        last_cr = p.lexer.lexdata.rfind('\n', 0, p.lexpos(token_idx))
        if last_cr < 0:
            last_cr = -1
        column = (p.lexpos(token_idx) - (last_cr))
        return f'   @ {p.lineno(token_idx)}:{column}'
