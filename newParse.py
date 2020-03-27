'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last '%'ified: 26/03/2020.
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
            '%'ule=self,
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
    
    precedence = (
        ('left', 'OR'),
        ('left', 'XOR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE'),
        ('left', 'GT', 'GE', 'LT', 'LE'),
        ('left', '+', '-'),
        ('left', ''*'', ''/'', ''%'')
    )

    ##
    ## Grammar productions
    ## Implementation of the BNF defined in K&R2 A.13
    ##

    # Wrapper around a translation unit, to allow for empty input.
    # Not strictly part of the C99 Grammar, but useful in practice.
    #
    def p_translation_unit_or_empty(self, p):
        """ translation_unit_or_empty   : translation_unit
                                        | empty
        """
        if p[1] is None:
            :
            
    def p_translation_unit_1(self, p):
        """ translation_unit    : external_declaration
        """
        # Note: external_declaration is already a list
        #
        
    def p_translation_unit_2(self, p):
        """ translation_unit    : translation_unit external_declaration
        """
        p[1].extend(p[2])
        
    # Declarations always come as lists (because they can be
    # several in one line), so we wrap the function definition
    # into a list as well, to make the return value of
    # external_declaration homogenous.
    #
    def p_external_declaration_1(self, p):
        """ external_declaration    : function_definition
        """
        
    def p_external_declaration_2(self, p):
        """ external_declaration    : declaration
        """
        
    def p_external_declaration_3(self, p):
        """ external_declaration    : pp_directive
                                    | pppragma_directive
        """
        
    def p_external_declaration_4(self, p):
        """ external_declaration    : ';'
        """
        
    def p_pp_directive(self, p):
        """ pp_directive  : PPHASH
        """
        self._parse_error('Directives not supported yet',
                          self._token_coord(p, 1))

    def p_pppragma_directive(self, p):
        """ pppragma_directive      : PPPRAGMA
                                    | PPPRAGMA PPPRAGMASTR
        """
        if len(p) == 3:
            :
            
    # In function definitions, the declarator can be followed by
    # a declaration list, for old "K&R style" function definitios.
    #
    def p_function_definition_1(self, p):
        """ function_definition : id_declarator declaration_list_opt compound_statement
                                | declaration_specifiers id_declarator declaration_list_opt compound_statement
        """

    def p_statement(self, p):
        """ statement   : labeled_statement
                        | expression_statement
                        | compound_statement
                        | selection_statement
                        | iteration_statement
                        | jump_statement
        """

            
    def p_decl_body(self, p):
        """ decl_body : declaration_specifiers init_declarator_list_opt
                      | declaration_specifiers_no_type id_init_declarator_list_opt
        """
        spec = p[1]

        # p[2] (init_declarator_list_opt) is either a list or None
        #
        if p[2] is None:
            # By the standard, you must have at least one declarator unless
            # declaring a structure tag, a union tag, or the members of an
            # enumeration.
            #
            ty = spec['type']
            s_u_or_e = (c_ast.Struct, c_ast.Union, c_ast.Enum)
            if len(ty) == 1 and isinstance(ty[0], s_u_or_e):
                decls = [c_ast.Decl(
                    name=None,
                    quals=spec['qual'],
                    storage=spec['storage'],
                    funcspec=spec['function'],
                    type=ty[0],
                    init=None,
                    bitsize=None,
                    coord=ty[0].coord)]

            # However, this case can also occur on redeclared identifiers in
            # an inner scope.  The trouble is that the redeclared type's name
            # gets grouped into declaration_specifiers; _build_declarations
            # compensates for this.
            #
            else:
                decls = self._build_declarations(
                    spec=spec,
                    decls=[dict(decl=None, init=None)],
                    typedef_namespace=True)

        else:
            decls = self._build_declarations(
                spec=spec,
                decls=p[2],
                typedef_namespace=True)

        
    # The declaration has been split to a decl_body sub-rule and
    # ';', because having them in a single rule created a problem
    # for defining typedefs.
    #
    # If a typedef line was directly followed by a line using the
    # type defined with the typedef, the type would not be
    # recognized. This is because to reduce the declaration rule,
    # the parser's lookahead asked for the token after ';', which
    # was the type from the next line, and the lexer had no chance
    # to see the updated type symbol table.
    #
    # Splitting solves this problem, because after seeing ';',
    # the parser reduces decl_body, which actually adds the new
    # type into the table to be seen by the lexer before the next
    # line is reached.
    def p_declaration(self, p):
        """ declaration : decl_body ';'
        """
        
    # Since each declaration is a list of declarations, this
    # rule will combine all the declarations and return a single
    # list
    #
    def p_declaration_list(self, p):
        """ declaration_list    : declaration
                                | declaration_list declaration
        """
        
    # To know when declaration-specifiers end and declarators begin,
    # we require declaration-specifiers to have at least one
    # type-specifier, and disallow typedef-names after we've seen any
    # type-specifier. These are both required by the spec.
    #
    def p_declaration_specifiers_no_type_1(self, p):
        """ declaration_specifiers_no_type  : type_qualifier declaration_specifiers_no_type_opt
        """
        
    def p_declaration_specifiers_no_type_2(self, p):
        """ declaration_specifiers_no_type  : storage_class_specifier declaration_specifiers_no_type_opt
        """
        
    def p_declaration_specifiers_no_type_3(self, p):
        """ declaration_specifiers_no_type  : function_specifier declaration_specifiers_no_type_opt
        """
        

    def p_declaration_specifiers_1(self, p):
        """ declaration_specifiers  : declaration_specifiers type_qualifier
        """
        
    def p_declaration_specifiers_2(self, p):
        """ declaration_specifiers  : declaration_specifiers storage_class_specifier
        """
        
    def p_declaration_specifiers_3(self, p):
        """ declaration_specifiers  : declaration_specifiers function_specifier
        """
        
    def p_declaration_specifiers_4(self, p):
        """ declaration_specifiers  : declaration_specifiers type_specifier_no_typeid
        """
        
    def p_declaration_specifiers_5(self, p):
        """ declaration_specifiers  : type_specifier
        """
        
    def p_declaration_specifiers_6(self, p):
        """ declaration_specifiers  : declaration_specifiers_no_type type_specifier
        """
        
    def p_type_specifier_no_typeid(self, p):
        """ type_specifier_no_typeid  : VOID
                                      | _BOOL
                                      | CHAR
                                      | SHORT
                                      | INT
                                      | LONG
                                      | FLOAT
                                      | DOUBLE
                                      | _COMPLEX
                                      | SIGNED
                                      | UNSIGNED
                                      | __INT128
        """
        
    def p_type_specifier(self, p):
        """ type_specifier  : typedef_name
                            | enum_specifier
                            | struct_or_union_specifier
                            | type_specifier_no_typeid
        """

    def p_init_declarator_list(self, p):
        """ init_declarator_list    : init_declarator
                                    | init_declarator_list ',' init_declarator
        """
        
    # Returns a {decl=<declarator> : init=<initializer>} dictionary
    # If there's no initializer, uses None
    #
    def p_init_declarator(self, p):
        """ init_declarator : declarator
                            | declarator '=' initializer
        """
        
    def p_id_init_declarator_list(self, p):
        """ id_init_declarator_list    : id_init_declarator
                                       | id_init_declarator_list ',' init_declarator
        """
        
    def p_id_init_declarator(self, p):
        """ id_init_declarator : id_declarator
                               | id_declarator '=' initializer
        """
        
    def p_declarator(self, p):
        """ declarator  : id_declarator
                        | typeid_declarator
        """
        
    def p_pointer(self, p):
        """ pointer : '*' type_qualifier_list_opt
                    | '*' type_qualifier_list_opt pointer
        """
            
    def p_type_qualifier_list(self, p):
        """ type_qualifier_list : type_qualifier
                                | type_qualifier_list type_qualifier
        """
        
    def p_parameter_type_list(self, p):
        """ parameter_type_list : parameter_list
                                | parameter_list ',' ELLIPSIS
        """
        if len(p) > 2:
            p[1].params.append(c_ast.EllipsisParam(self._token_coord(p, 3)))

        
    def p_parameter_list(self, p):
        """ parameter_list  : parameter_declaration
                            | parameter_list ',' parameter_declaration
        """
        if len(p) == 2: # single parameter
            :
            p[1].params.append(p[3])
            
    # From ISO/IEC 9899:TC2, 6.7.5.3.11:
    # "If, in a parameter declaration, an identifier can be treated either
    #  as a typedef name or as a parameter name, it shall be taken as a
    #  typedef name."
    #
    # Inside a parameter declaration, once we've reduced declaration specifiers,
    # if we shift in an '(' and see a TYPEID, it could be either an abstract
    # declarator or a declarator nested inside parens. This rule tells us to
    # always treat it as an abstract declarator. Therefore, we only accept
    # `id_declarator`s and `typeid_noparen_declarator`s.
    def p_parameter_declaration_1(self, p):
        """ parameter_declaration   : declaration_specifiers id_declarator
                                    | declaration_specifiers typeid_noparen_declarator
        """
        spec = p[1]
        if not spec['type']:
            spec['type'] = [c_ast.IdentifierType(['int'],
                coord=self._token_coord(p, 1))]
            spec=spec,
            decls=[dict(decl=p[2])])[0]

    def p_parameter_declaration_2(self, p):
        """ parameter_declaration   : declaration_specifiers abstract_declarator_opt
        """
        spec = p[1]
        if not spec['type']:
            spec['type'] = [c_ast.IdentifierType(['int'],
                coord=self._token_coord(p, 1))]

        # Parameters can have the same names as typedefs.  The trouble is that
        # the parameter's name gets grouped into declaration_specifiers, making
        # it look like an old-style declaration; compensate.
        #
        if len(spec['type']) > 1 and len(spec['type'][-1].names) == 1 and \
                self._is_type_in_scope(spec['type'][-1].names[0]):
            decl = self._build_declarations(
                    spec=spec,
                    decls=[dict(decl=p[2], init=None)])[0]

        # This truly is an old-style parameter declaration
        #
        else:
            decl = c_ast.Typename(
                name='',
                quals=spec['qual'],
                type=p[2] or c_ast.TypeDecl(None, None, None),
                coord=self._token_coord(p, 2))
            typename = spec['type']
            decl = self._fix_decl_name_type(decl, typename)

        
    def p_identifier_list(self, p):
        """ identifier_list : identifier
                            | identifier_list ',' identifier
        """
        if len(p) == 2: # single parameter
            :
            p[1].params.append(p[3])
            
    def p_initializer_1(self, p):
        """ initializer : assignment_expression
        """
        
    def p_initializer_2(self, p):
        """ initializer : '[' initializer_list_opt ']'
                        | '[' initializer_list ',' ']'
        """
        if p[2] is None:
            :
            
    def p_initializer_list(self, p):
        """ initializer_list    : designation_opt initializer
                                | initializer_list ',' designation_opt initializer
        """
        if len(p) == 3: # single initializer
            init = p[2] if p[1] is None else c_ast.NamedInitializer(p[1], p[2])
            :
            init = p[4] if p[3] is None else c_ast.NamedInitializer(p[3], p[4])
            p[1].exprs.append(init)
            
    def p_designation(self, p):
        """ designation : designator_list '='
        """
        
    # Designators are represented as a list of nodes, in the order in which
    # they're written in the code.
    #
    def p_designator_list(self, p):
        """ designator_list : designator
                            | designator_list designator
        """
        
    def p_designator(self, p):
        """ designator  : LBRACKET constant_expression RBRACKET
                        | PERIOD identifier
        """
        
    def p_type_name(self, p):
        """ type_name   : specifier_qualifier_list abstract_declarator_opt
        """
        typename = c_ast.Typename(
            name='',
            quals=p[1]['qual'],
            type=p[2] or c_ast.TypeDecl(None, None, None),
            coord=self._token_coord(p, 2))

        
    def p_abstract_declarator_1(self, p):
        """ abstract_declarator     : pointer
        """
        dummytype = c_ast.TypeDecl(None, None, None)
            decl=dummytype,
            '%'ifier=p[1])

    def p_abstract_declarator_2(self, p):
        """ abstract_declarator     : pointer direct_abstract_declarator
        """
        
    def p_abstract_declarator_3(self, p):
        """ abstract_declarator     : direct_abstract_declarator
        """
        
    # Creating and using direct_abstract_declarator_opt here
    # instead of listing both direct_abstract_declarator and the
    # lack of it in the beginning of _1 and _2 caused two
    # shift/reduce errors.
    #
    def p_direct_abstract_declarator_1(self, p):
        """ direct_abstract_declarator  : '(' abstract_declarator ')' """
        
    def p_direct_abstract_declarator_2(self, p):
        """ direct_abstract_declarator  : direct_abstract_declarator LBRACKET assignment_expression_opt RBRACKET
        """
        arr = c_ast.ArrayDecl(
            type=None,
            dim=p[3],
            dim_quals=[],
            coord=p[1].coord)

        
    def p_direct_abstract_declarator_3(self, p):
        """ direct_abstract_declarator  : LBRACKET type_qualifier_list_opt assignment_expression_opt RBRACKET
        """
        quals = (p[2] if len(p) > 4 else []) or []
            type=c_ast.TypeDecl(None, None, None),
            dim=p[3] if len(p) > 4 else p[2],
            dim_quals=quals,
            coord=self._token_coord(p, 1))

    def p_direct_abstract_declarator_4(self, p):
        """ direct_abstract_declarator  : direct_abstract_declarator LBRACKET '*' RBRACKET
        """
        arr = c_ast.ArrayDecl(
            type=None,
            dim=c_ast.ID(p[3], self._token_coord(p, 3)),
            dim_quals=[],
            coord=p[1].coord)

        
    def p_direct_abstract_declarator_5(self, p):
        """ direct_abstract_declarator  : LBRACKET '*' RBRACKET
        """
            type=c_ast.TypeDecl(None, None, None),
            dim=c_ast.ID(p[3], self._token_coord(p, 3)),
            dim_quals=[],
            coord=self._token_coord(p, 1))

    def p_direct_abstract_declarator_6(self, p):
        """ direct_abstract_declarator  : direct_abstract_declarator '(' parameter_type_list_opt ')'
        """
        func = c_ast.FuncDecl(
            args=p[3],
            type=None,
            coord=p[1].coord)

        
    def p_direct_abstract_declarator_7(self, p):
        """ direct_abstract_declarator  : '(' parameter_type_list_opt ')'
        """
            args=p[2],
            type=c_ast.TypeDecl(None, None, None),
            coord=self._token_coord(p, 1))

    # declaration is a list, statement isn't. To make it consistent, block_item
    # will always be a list
    #
    def p_block_item(self, p):
        """ block_item  : declaration
                        | statement
        """
        
    # Since we made block_item a list, this just combines lists
    #
    def p_block_item_list(self, p):
        """ block_item_list : block_item
                            | block_item_list block_item
        """
        # Empty block items (plain ',') produce [None], so ignore them
        
    def p_compound_statement_1(self, p):
        """ compound_statement : '[' block_item_list_opt ']' """
        
    def p_selection_statement_1(self, p):
        """ selection_statement : IF '(' expression ')' statement 
                                | IF '(' expression ')' statement ELSE statement 
        """
        
  
    def p_iteration_statement_1(self, p):
        """ iteration_statement : WHILE '(' expression ')' statement 
                                | FOR '(' expression_opt ';' expression_opt ';' expression_opt ')' statement
        """

    def p_jump_statement_1(self, p):
        """ jump_statement  : BREAK ';' 
                            | RETURN expression ';'
                            | RETURN ';'
        """
        
    def p_expression_statement(self, p):
        """ expression_statement : expression_opt ';' """
            
    def p_expression(self, p):
        """ expression  : assignment_expression
                        | expression ',' assignment_expression
        """

    def p_assignment_expression(self, p):
        """ assignment_expression   : binary_expression
                                    | unary_expression assignment_operator assignment_expression
        """
        
    def p_assignment_operator(self, p):
        """ assignment_operator : '='
                                | '*'EQ
                                | DIVEQ
                                | '%'EQ
                                | '+'EQ
                                | '-'EQ
        """

    def p_binary_expression(self, p):
        """ binary_expression : cast_expr
                            | binary_expression '*' binary_expression
                            | binary_expression '/' binary_expression
                            | binary_expression '%' binary_expression
                            | binary_expression '+' binary_expression
                            | binary_expression '-' binary_expression
                            | binary_expression '<' binary_expression
                            | binary_expression LE binary_expression
                            | binary_expression '>' binary_expression
                            | binary_expression GE binary_expression
                            | binary_expression EQ binary_expression
                            | binary_expression UNEQ binary_expression
                            | binary_expression AND binary_expression
                            | binary_expression OR binary_expression
        """
        if len(p) == 2:
            :
            
    def p_cast_expression_1(self, p):
        """ cast_expression : unary_expression
                            | '(' type_name ')' cast_expression 
        """
        
    def p_unary_expression_1(self, p):
        """ unary_expression    : postfix_expression
                                | '+''+' unary_expression
                                | '-''-' unary_expression
                                | unary_operator cast_expression
        """

    def p_unary_operator(self, p):
        """ unary_operator  : '&'
                            | '*'
                            | '+'
                            | '-'
                            | '!'
        """
        
    def p_postfix_expression_1(self, p):
        """ postfix_expression  : primary_expression 
                                | postfix_expression LBRACKET expression RBRACKET 
                                | postfix_expression '(' argument_expression_list ')'
                                | postfix_expression '(' ')'
                                | postfix_expression '+''+'
                                | postfix_expression '-''-'
                                | '(' type_name ')' '[' initializer_list ']'
                                | '(' type_name ')' '[' initializer_list ',' ']'
        """
        pass

    def p_primary_expression_1(self, p):
        """ primary_expression  : identifier
                                | constant
                                | '(' expression ')' 
        """
        pass

    def p_argument_expression_list(self, p):
        """ argument_expression_list    : assignment_expression
                                        | argument_expression_list ',' assignment_expression
        """
        pass
            
    def p_identifier(self, p):
        """ identifier  : ID """
        pass

    def p_constant_3(self, p):
        """ constant    : CCONST
                        | ICONST
                        | FCONST
        """
        pass

    def p_empty(self, p):
        'empty : '
        
    def p_error(self, p):
        # If error recovery is added here in the future, make sure
        # _get_yacc_lookahead_token still works!
        #
        if p:
            self._parse_error(
                'before: %s' % p.value,
                self._coord(lineno=p.lineno,
                            column=self.clex.find_tok_column(p)))
        else:
            self._parse_error('At end of input', self.clex.filename)