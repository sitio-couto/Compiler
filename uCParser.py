'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 28/03/2020.
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
    def parse(self, data):
        return self.parser.parse(data)
    
    # Tests an expression and prints the result
    def test(self, data):
        self.lexer.reset_line_num()
        if exists(data): 
            with open(data, 'r') as content_file :
                data = content_file.read()
        print(self.parse(data))
    
    #### ROOT ####
    
    def p_program(self, p) :
        ''' program : global_declaration_list
        '''
        p[0] = p[1]

    #### FIRST SPLIT ####

    def p_global_declaration(self, p) :
        ''' global_declaration : function_definition
                               | declaration
        '''
        p[0] = p[1]

    def p_function_definition_1(self, p):
        ''' function_definition : type_specifier declarator declaration_list_opt compound_statement '''
        p[0] = ('func', p[1], p[2], p[3], p[4])
    def p_function_definition_2(self, p):
        ''' function_definition : declarator declaration_list_opt compound_statement '''
        p[0] = ('func', 'void', p[1], p[2], p[3]) # TODO: This 'void' might be wrong

    def p_declaration(self, p):
        ''' declaration : type_specifier init_declarator_list_opt ';' '''
        p[0] = ('declaration', p[1], p[2])

    def p_init_declarator_1(self, p):
        ''' init_declarator : declarator '''
        p[0] = p[1]
    def p_init_declarator_2(self, p):
        ''' init_declarator : declarator '=' initializer '''
        p[0] = (p[1], p[2], p[3])


    def p_type_specifier(self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        p[0] = p[1]

    def p_initializer_1(self, p):
        ''' initializer : assign_expr '''
        p[0] = p[1]
    def p_initializer_2(self, p):
        ''' initializer : '{' initializer_list '}'
                        | '{' initializer_list ',' '}'
        '''
        p[0] = ('{', p[2], '}')

    def p_declarator(self, p):
        ''' declarator : direct_declarator
        '''
        p[0] = p[1]
        
    def p_direct_declarator_1(self, p):
        ''' direct_declarator : identifier '''
        p[0] = p[1]
    def p_direct_declarator_2(self, p):
        ''' direct_declarator : '(' declarator ')' '''
        p[0] = p[2] 
    def p_direct_declarator_3(self, p):
        ''' direct_declarator : direct_declarator '[' const_expr_opt ']'
                              | direct_declarator '(' parameter_list ')'
                              | direct_declarator '(' id_list_opt ')'
        '''
        p[0] = (p[1], p[3]) 

    #### EXPRESSIONS ####

    def p_expr_1(self, p):
        ''' expr : assign_expr '''
        p[0] = p[1]
    def p_expr_2(self, p):
        ''' expr : expr ',' assign_expr '''
        p[0] = (p[1], p[3])

    def p_assign_expr_1(self, p):
        ''' assign_expr : bin_expr '''
        p[0] = p[1]
    def p_assign_expr_2(self, p):
        ''' assign_expr : un_expr assign_op assign_expr '''
        #  __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
        p[0] = ast.Assignment(p[2], p[1], p[3])
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
        p[0] = ast.BinaryOp(p[2], p[1], p[3])
        # p[0] = (p[1], p[2], p[3])

    # Cast Expressions # 
    # (float) 123;

    def p_cast_expr_1(self, p):
        ''' cast_expr : un_expr '''
        p[0] = p[1]
    def p_cast_expr_2(self, p):
        ''' cast_expr : '(' type_specifier ')' cast_expr '''
        p[0] = ('cast', p[2], p[4])

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
        p[0] = (p[1], p[2])

    # Unary Operators #
    # '-' NUM | '*' PTR | '&' ADDR 

    # TODO: the '*' is only used if pointer are considered
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
        '''postfix_expr : postfix_expr '[' expr ']'
                        | postfix_expr '(' expr_opt ')'
        '''
        p[0] = ( p[1], (p[2], p[3], p[4]) )
    def p_postfix_expr_3(self, p):
        '''postfix_expr : postfix_expr PLUSPLUS
                        | postfix_expr MINUSMINUS
        '''
        p[0] = (p[1], p[2]) 

    # Primary Expressios #
    # ( ... ) | var | 12.5 | "hello"

    def p_primary_expr_1(self, p):
        ''' primary_expr : '(' expr ')' '''
        p[0] = p[2]
    def p_primary_expr_2(self, p):
        ''' primary_expr : identifier
                         | constant
                         | STRING
        '''
        p[0] = p[1] # TODO: Not sure if there should be a tuple here (pe (ID,val))

    # Terminal Expressions #

    def p_identifier(self, p):
        ''' identifier : ID '''
        p[0] = ('id', p[1])
        
    def p_constant(self, p):
        ''' constant : CCONST
                     | ICONST
                     | FCONST
        '''
        p[0] = ('const', p[1]) # TODO: check if num is realy the best tag for this

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
        p[0] = p[1]

    def p_compound_statement(self, p):
        ''' compound_statement : '{' declaration_list_opt statement_list_opt '}' '''
        p[0] = ('{', p[2], p[3], '}')

    # Selection Staments #    
    # if () {} | if () {} else {}

    def p_selection_statement_1(self, p): # If block only
        ''' selection_statement : IF '(' expr ')' statement '''
        p[0] = ('if', p[3], p[5], None)
    def p_selection_statement_2(self, p): # If-Else block
        ''' selection_statement : IF '(' expr ')' statement ELSE statement '''
        p[0] = ('if', p[3], p[5], p[7]) # TODO: Might not be the best nesting option for ELSE 


    # Iteration Statements #
    # for () {} | while () {}

    def p_iteration_statement_1(self, p):
        ''' iteration_statement : WHILE '(' expr ')' statement '''
        p[0] = (p[1], p[3], p[5])
    def p_iteration_statement_2(self, p):
        ''' iteration_statement : FOR '(' expr_opt ';' expr_opt ';' expr_opt ')' statement '''
        p[0] = (p[1], p[3], p[5], p[7], p[9])
    def p_iteration_statement_3(self, p): # TODO: This might need to be revised (declaration can be a list: int a, b=0, c;)
        ''' iteration_statement : FOR '(' declaration expr_opt ';' expr_opt ')' statement '''
        p[0] = (p[1], p[3], p[4], p[6], p[8])                

    # Jump Statements #
    # break; return; 

    def p_jump_statement_1(self, p):
        ''' jump_statement : BREAK '''
        p[0] = ('break')
    def p_jump_statement_2(self, p):
        ''' jump_statement : RETURN expr_opt ';' '''
        p[0] = ('return', p[2])

    # Functions Statements #

    def p_assert_statement(self, p):
        ''' assert_statement : ASSERT expr ';' '''
        p[0] = ('assert', p[2])

    def p_print_statement(self, p):
        ''' print_statement : PRINT '(' expr_opt ')' ';'  '''
        p[0] = ('print', p[3])

    def p_read_statement(self, p):
        ''' read_statement : READ '(' expr ')' ';' '''
        p[0] = ('read', p[3])

    #### MISCELANEOUS ####

    def p_parameter_declaration(self, p):
        ''' parameter_declaration : type_specifier declarator '''
        p[0] = (p[1], p[2])
    

    # Listable Productions #

    def p_global_declaration_list_1(self, p) :
        ''' global_declaration_list : global_declaration_list global_declaration '''
        p[0] = p[1] + (p[2])
    def p_global_declaration_list_2(self, p) :
        ''' global_declaration_list : global_declaration '''
        p[0] = p[1]

    def p_declaration_list_1(self, p) :
        ''' declaration_list : declaration_list declaration '''
        p[0] = p[1] + (p[2])
    def p_declaration_list_2(self, p) :
        ''' declaration_list : declaration '''
        p[0] = p[1]

    def p_statement_list_1(self, p) :
        ''' statement_list : statement_list statement '''
        p[0] = (p[1], p[2]) # TODO: Double check if this is the proper tree association
    def p_statement_list_2(self, p) :
        ''' statement_list : statement '''
        p[0] = p[1]

    # Listable Productions Separated By Tokens #
    # TODO: Not sure if the comma token should be in the tree

    def p_init_declarator_list_1(self, p):
        ''' init_declarator_list : init_declarator_list ',' init_declarator '''
        p[0] = p[1] + (p[3]) 
    def p_init_declarator_list_2(self, p):
        ''' init_declarator_list : init_declarator '''
        p[0] = p[1]

    def p_initializer_list_1(self, p):
        ''' initializer_list : initializer_list ',' initializer '''
        p[0] = p[1] + (',', p[3]) 
    def p_initializer_list_2(self, p):
        ''' initializer_list : initializer '''
        p[0] = p[1]

    def p_id_list_1(self, p):
        ''' id_list : id_list ',' identifier '''
        p[0] = p[1] + (',', p[3]) 
    def p_id_list_2(self, p):
        ''' id_list : identifier '''
        p[0] = p[1]

    def p_parameter_list_1(self, p):
        ''' parameter_list : parameter_list ',' parameter_declaration '''
        p[0] = p[1] + (',', p[3]) 
    def p_parameter_list_2(self, p):
        ''' parameter_list : parameter_declaration '''
        p[0] = p[1]

    # Optional Productions #

    def p_declaration_list_opt(self, p):
        ''' declaration_list_opt : declaration_list
                                 | empty
        '''
        p[0] = p[1]

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
        '''empty :
        '''
        pass

    #### ERROR HANDLING ####
    def p_error(self, p):
        if p:
            print("Error near the symbol %s at (%s, %s)." % (p.value, p.lineno, p.lexpos))
        else:
            print("Error at the end of input")
