'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 24/03/2020.
'''

from ply.yacc import yacc

class uCParser():
    
    precedence = (
        ('left', '+', '-'),
        ('left', '*', '/')
        )

    # Initializes the class with the lexer object and tokens list.
    def __init__(self, lexer):
        self.lexer = lexer
        self.tokens = lexer.tokens
    
    # Builds the parser.
    def build(self, **kwargs):
        self.parser = yacc(
            module=self,
            start='declaration',
            write_tables=False,
            **kwargs)
    
    # Parses an expression.
    def parse(self, data):
        print(self.parser.parse(data))
    
    def p_statement_list(self, p):
        ''' statement_list : statement_list statement
                           | statement
        '''
        if len(p) == 3:
            p[0] = p[1] + (p[2])
        else:
            p[0] = p[1]

    ### RENAMED TO p_assignment_statement
    # def p_assign_statement (self, p):
    #     ''' statement : ID '=' expr
    #                   | ID TIMESEQ expr
    #                   | ID DIVEQ expr 
    #                   | ID MODEQ expr 
    #                   | ID PLUSEQ expr 
    #                   | ID MINUSEQ expr
    #     '''
    #     p[0] = ('assign', p[1], p[2], p[3])
    def p_assign_statement (self, p):
        ''' statement : assignment_statement
        '''
        p[0] = p[1]
    #####################################

    def p_print_statement (self, p):
        ''' statement : PRINT '(' expr ')'
        '''
        p[0] = ('print', p[3])
        
    def p_binop_expr (self, p):
        ''' expr : expr '+' expr
                 | expr '-' expr
                 | expr '*' expr
                 | expr '/' expr
        '''
        p[0] = (p[2], p[1], p[3])
        
    def p_num_expr (self, p):
        ''' expr : ICONST
                 | FCONST
        '''
        p[0] = ('num', p[1])
        
    def p_name_expr (self, p):
        ''' expr : ID
        '''
        p[0] = ('id', p[1])
        
    def p_compound_expr (self, p):
        ''' expr : '(' expr ')'
        '''
        p[0] = p[2]

    #### IMPLEMENTING VARIABLE DECLARATIONS ####

    def p_declaration (self, p):
        ''' declaration : type_specifier init_declarator_list ';'
        '''
        p[0] = ('declaration', p[1], p[2])

    def p_init_declarator_list (self, p) :
        ''' init_declarator_list : init_declarator_list declarator
                                 | init_declarator_list declarator '=' initializer
                                 | empty
        '''
        if len(p) == 3 :
            p[0] = p[1] + (p[2])
        elif len(p) == 5 :
            p[0] = p

    def p_type_specifier (self, p):
        ''' type_specifier : VOID
                           | CHAR
                           | INT
                           | FLOAT
        '''
        p[0] = p[1]

    # INCOMPLETE
    def p_initializer (self, p):
        ''' initializer : assignment_statement
        '''
        p[0] = p[1]

    # INCOMPLETE
    def p_declarator (self, p):
        ''' declarator : ID
        '''
        if len(p) == 2 :
            p[0] = ('id',p[1])

    def p_assignment_statement (self, p):
        ''' assignment_statement : ID '=' expr
                                 | ID TIMESEQ expr
                                 | ID DIVEQ expr 
                                 | ID MODEQ expr 
                                 | ID PLUSEQ expr 
                                 | ID MINUSEQ expr
        '''
        p[0] = ('assign', p[1], p[2], p[3])


    #### EMPTY PRODUCTION ####
    def p_empty (self, p):
        pass

    #### ERROR HANDLING ####
    def p_error (self, p):
        if p:
            print("Error near the symbol %s" % p.value)
        else:
            print("Error at the end of input")
