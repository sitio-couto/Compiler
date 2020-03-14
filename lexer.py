'''
First Project: Lexer for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020
'''

import ply.lex as lex
from os.path import exists

#### CONFLICTING TYPES ####
# ID & KEYWORDS => Longest Match & Rule Order Using Dictionary
# COMMENT & UNTCOMMENT => Rule Order (comment func comes first)
# STRING & UNTSTRING => Rule Order (string func comes first)
class Lexer():
    '''A Lexer for the uC language.
    ''' 
    def __init__(self):
        self.last_token = None

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def reset_line_num(self):
        self.lexer.lineno = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    # Test the output
    def test(self, data):
        
        # If filename.
        if exists(data): 
            with open(data, 'r') as content_file :
                data = content_file.read()
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok: 
                break
            print(tok)
    
    # Reserved keywords
    keywords = (
        'ASSERT', 'BREAK', 'CHAR', 'ELSE', 'FLOAT', 'FOR', 'IF',
        'INT', 'PRINT', 'READ', 'RETURN', 'VOID', 'WHILE',
    )

    keyword_map = {}
    for keyword in keywords:
        keyword_map[keyword.lower()] = keyword

    #
    # All the tokens recognized by the lexer
    #
    tokens = keywords + (
        # Identifiers
        'ID', 'ICONST', 'FCONST', 'STRING',
        # Math Operators
        'PLUSPLUS', 'MINUSMINUS',
        # Logical Operators
        'EQ', 'OR', 'AND', 'UNEQ', 'GE', 'LE',
        # Assignment Operators
        'PLUSEQ', 'MINUSEQ', 'TIMESEQ', 'DIVEQ', 'MODEQ',
        # Comments
        'LINECOMMENT', 'COMMENT', 'UNTCOMMENT'
    )
    
    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'
    
    # Regular expression rules for simple tokens
    t_EQ = r'=='
    t_OR = r'\|\|'
    t_AND = r'&&'
    t_UNEQ = r'!='
    t_GE = r'>='
    t_LE = r'<='
    t_PLUSPLUS = r'\+\+'
    t_MINUSMINUS = r'--'
    t_PLUSEQ = r'\+='
    t_MINUSEQ = r'-='
    t_TIMESEQ = r'\*='
    t_DIVEQ = r'/='
    t_MODEQ = r'%='
    
    literals = ['+', '-', '/', '*', '%', '=', '&', '!', ',', ';', '(', ')', '{', '}', '[', ']', '<', '>']

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t        

    def t_FCONST(self, t):
        r'\d+\.\d*|\d*\.\d+'
        t.value = float(t.value)    
        return t

    def t_ICONST(self, t):
        r'\d+'
        t.value = int(t.value)    
        return t

    def t_LINECOMMENT (self, t) :
        r'//.*(\n|$)'
        t.lexer.lineno += t.value.count("\n")

    def t_COMMENT (self, t) :
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count("\n")

    def t_STRING (self, t) :
        r'\".*?\"'
        return t

    #### ERROR HANDLING RULES ####
    def t_UNTCOMMENT (self, t) :
        r'/\*(.|\n)*$'
        print(f"{t.lineno}: Unterminated comment")
    
    def t_UNTSTRING (self, t) :
        r'\".*?$'
        print(f"{t.lineno}: Unterminated string")

    # If an unmatched character is found
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at l:{t.lineno}")
        t.lexer.skip(1)
