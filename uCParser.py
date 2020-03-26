'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 26/03/2020.
'''

from ply.yacc import yacc
from os.path import exists

class uCParser():
    
    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQ', 'UNEQ'),
        ('left', '<', '>', 'LE', 'GE'),
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
        if exists(data): 
            with open(data, 'r') as content_file :
                data = content_file.read()
        print(self.parse(data))
    
    #### ROOT ####
    
    def p_program (self, p) :
        ''' program : global_declaration_list
        '''
        p[0] = p[1]

    def p_global_declaration_list (self, p) :
            ''' global_declaration_list : global_declaration_list global_declaration
                                        | global_declaration
            '''
            if len(p) == 3 :
                p[0] = p[1] + (p[2])
            else :
                p[0] = p[1]

    #### FIRST SPLIT ####

    def p_global_declaration (self, p) :
        ''' global_declaration : function_definition
                               | declaration
        '''
        p[0] = p[1]

    def p_function_definition (self, p):
        ''' function_definition : type_specifier_opt declarator declaration_list compound_statement
        '''
        p[0] = ('func', p[1], p[2], p[3], p[4])

    def p_declaration_list (self, p):
        ''' declaration_list : declaration_list declaration
                             | declaration
                             | empty
        '''
        if len(p) == 3 :
            if p[1] is None : p[0] = (p[2])
            else : p[0] = p[1] + (p[2])
        elif len(p) == 2 :
            p[0] = p[1]

    def p_declaration (self, p):
        ''' declaration : type_specifier init_declarator_list ';'
        '''
        p[0] = ('declaration', p[1], p[2])

    def p_declarator_list (self, p):
        ''' declarator_list : declarator_list declarator
                            | declarator
        '''
        if len(p) == 3 :
            p[0] = p[1] + (p[2])
        else :
            p[0] = p[1]

    def p_init_declarator_list (self, p):
        ''' init_declarator_list : init_declarator_list init_declarator
                                 | init_declarator 
                                 | empty
        '''
        if len(p) == 3 :
            if p[1] is None : p[0] = (p[2])
            else : p[0] = p[1] + (p[2])
        elif len(p) == 2 :
            p[0] = p[1]

    def p_init_declarator (self, p):
        ''' init_declarator : declarator
                            | declarator '=' initializer
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else:
            p[0] = (p[1], p[2], p[3])

    def p_type_specifier_opt (self, p):
        ''' type_specifier_opt : type_specifier
                               | empty
        '''
        p[0] = p[1]

    def p_type_specifier (self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        p[0] = p[1]

    def p_initializer_list (self, p):
        ''' initializer_list : initializer
                             | initializer_list ',' initializer 
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else:
            p[0] = p[1] + (p[2], p[3])

    def p_initializer (self, p):
        ''' initializer : assign_expr
                        | '{' initializer_list '}'
                        | '{' initializer_list ',' '}'
        '''
        if len(p) == 2 :
            p[0] = ('assign', p[1])
        elif len(p) == 4 :
            p[0] = ('{', p[2], '}')
        else:
            p[0] = ('{', p[2], ',', '}')

    def p_declarator (self, p):
        ''' declarator : ID
                       | '(' declarator ')'
                       | declarator '[' const_expr_opt ']'
                       | declarator '(' parameter_list ')'
                       | declarator '(' id_list ')'
        '''
        if len(p) == 2 :
            p[0] = ('id', p[1])
        elif len(p) == 4 :
            p[0] = p[2]
        else:
            p[0] = (p[1], p[3]) 

    #### EXPRESSIONS ####

    def p_expr_list(self, p):
        ''' expr_list : expr_list expr
                      | expr_opt
        '''
        if len(p) == 2 :
            p[0] = p[1] + (p[2])
        else:
            p[0] = p[1]

    def p_expr_opt(self, p):
        ''' expr_opt : expr
                     | empty
        '''    
        p[0] = p[1]

    def p_expr(self, p):
        ''' expr : assign_expr
                 | expr ',' assign_expr
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else:
            p[0] = (p[1], p[3])

    def p_assign_expr_opt (self, p):
        ''' assign_expr_opt : assign_expr
                            | empty
        '''
        p[0] = p[1]


    def p_assign_expr(self, p):
        ''' assign_expr : bin_expr
                        | un_expr assign_op assign_expr
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else:
            p[0] = (p[1], p[2], p[3])

    def p_assign_op(self, p):
        ''' assign_op : '='
                      | TIMESEQ
                      | DIVEQ
                      | MODEQ
                      | PLUSEQ
                      | MINUSEQ
        '''
        p[0] = p[1]

    def p_bin_expr(self, p):
        ''' bin_expr : cast_expr
                     | bin_expr '*' bin_expr
                     | bin_expr '/' bin_expr
                     | bin_expr '%' bin_expr
                     | bin_expr '+' bin_expr
                     | bin_expr '-' bin_expr
                     | bin_expr '<' bin_expr
                     | bin_expr LE bin_expr
                     | bin_expr '>' bin_expr
                     | bin_expr GE bin_expr
                     | bin_expr EQ bin_expr
                     | bin_expr UNEQ bin_expr
                     | bin_expr AND bin_expr
                     | bin_expr OR bin_expr
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else:
            p[0] = (p[1], p[2], p[3])

    def p_cast_expr (self, p):
        ''' cast_expr : un_expr
                      | '(' type_specifier ')' cast_expr
        '''
        if len(p) == 2 :
            p[0] = p[1]
        else :
            p[0] = ('cast', p[2], p[4])

    def p_un_expr (self, p):
        ''' un_expr : postfix_expr
                    | PLUSPLUS un_expr
                    | MINUSMINUS un_expr
                    | un_op cast_expr
        '''
        if len(p) == 2 :
            p[0] = p[1]
        elif p[1] == '++':
            p[0] = ('++', p[2])
        elif p[1] == '--':
            p[0] = ('--', p[2])
        else:
            p[0] = (p[1], p[2])

    def p_un_op(self, p):
        ''' un_op : '&'
                  | '*'
                  | '+'
                  | '-'
                  | '!'
        '''
        p[0] = p[1]    

    def p_postfix_expr (self, p):
        '''postfix_expr : primary_expr
                        | postfix_expr '[' expr ']'
                        | postfix_expr '(' assign_expr_opt ')'
                        | postfix_expr PLUSPLUS
                        | postfix_expr MINUSMINUS
        '''
        if len(p) == 2 :
            p[0] = p[1]
        elif p[2] == '[':
            p[0] = (p[1], ('[', p[3],']'))
        elif p[2] == '(':
            p[0] = (p[1], ('(', p[3],')'))
        elif p[2] == '--': 
            p[0] = (p[1], '--')
        elif p[2] == '++':
            p[0] = (p[1], '++')

    def p_primary_expr (self, p): # TODO: Might need to rethink these symbols
        ''' primary_expr : ID
                         | constant
                         | STRING
                         | '(' expr ')'
        '''
        if len(p) == 2 :
            p[0] = p[1] # TODO: Not sure if there should be a tuple here (pe (ID,val))
        else:
            p[0] = p[2]

    def p_constant (self, p):
        ''' constant : CCONST
                     | ICONST
                     | FCONST
        '''
        p[0] = ('const', p[1]) # TODO: check if num is realy the best tag for this

    #### STATEMENTS ####

    def p_statement_list(self, p):
        ''' statement_list : statement_list statement
                           | statement
                           | empty
        '''
        if len(p) == 3 :
            if p[1] is None: p[0] = p[2]
            else: p[0] = p[1] + (p[2])
        else:
            p[0] = p[1]

    def p_statement (self, p):
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
        ''' expr_statement : expr_opt ';'
        '''
        p[0] = p[1]

    def p_compound_statement(self, p):
        ''' compound_statement : '{' declaration_list statement_list '}'
        '''
        p[0] = ('{', p[2], p[3],'}')

    def p_selection_statement(self, p):
        ''' selection_statement : IF '(' expr ')' statement
                                | IF '(' expr ')' statement ELSE statement
        '''
        if len(p) == 6 :
            p[0] = ('if', p[3], p[5], None)
        else:
            p[0] = ('if', p[3], p[5], p[7]) # TODO: Might not be the best nesting option for ELSE 

    def p_iteration_statement(self, p):
        ''' iteration_statement : WHILE '(' expr ')' statement
                                | FOR '(' expr_opt ';' expr_opt ';' expr_opt ')' statement
        '''
        if p[1] == 'WHILE':
            p[0] = ('while', p[3], p[5])
        else:
            p[0] = ('for', p[3], p[5], p[7], p[9])

    def p_jump_statement(self, p):
        ''' jump_statement : BREAK ';'
                           | RETURN expr_opt ';'
        '''
        if p[1] == 'BREAK':
            p[0] = ('break')
        else:
            p[0] = ('return', p[2])

    def p_assert_statement(self, p):
        ''' assert_statement : ASSERT expr ';'
        '''
        p[0] = ('assert', p[2])

    def p_print_statement(self, p):
        ''' print_statement : PRINT '(' expr_list ')' ';'
        '''
        p[0] = ('print', p[3])

    def p_read_statement(self, p):
        ''' read_statement : READ '(' declarator_list ')' ';'
        '''
        p[0] = ('read', p[3])

    #### MISCELANEOUS ####
    
    def p_id_list(self, p):
        ''' id_list : id_list ',' ID
                    | ID
        '''
        if len(p) == 4 :
            p[0] = p[1] + (p[3])
        else:
            p[0] = p[1]

    def p_parameter_list(self, p):
        ''' parameter_list : parameter_list ',' parameter_declaration
                           | parameter_declaration
        '''
        if len(p) == 4 :
            p[0] = p[1] + (p[3])
        else:
            p[0] = p[1]

    def p_parameter_declaration(self, p):
        ''' parameter_declaration : type_specifier declarator
        '''
        p[0] = (p[1], p[2])
    
    def p_const_expr_opt(self, p):
        ''' const_expr_opt : bin_expr
                           | empty
        '''
        p[0] = p[1]

    #### EMPTY PRODUCTION ####
    def p_empty (self, p):
        '''empty :
        '''
        pass

    #### ERROR HANDLING ####
    def p_error (self, p):
        if p:
            print("Error near the symbol %s at (%s, %s)." % (p.value, p.lineno, p.lexpos))
        else:
            print("Error at the end of input")
