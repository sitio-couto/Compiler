 # ------------------------------------------------------------
 # calclex.py
 #
 # tokenizer for a simple expression evaluator for
 # numbers and +,-,*,/
 # ------------------------------------------------------------
import ply.lex as lex
import os.path
from os import path

#### CONFLICTING TYPES ####
# ID & KEYWORDS => Longest Match & Rule Order Using Dictionary
# COMMENT & UNTCOMMENT => Rule Order (comment func comes first)
# STRING & UNTSTRING => Rule Order (string func comes first)
class Lexer():
    '''A Lexer for the uC language.
    ''' 
    def __init__(self, filename=""):
        self.filename = filename
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
        
        if not path.exists(data) : 
            data = input("Expression: ")
        else : 
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
        'ID', 'NUMBER', 'ASSIGN', 'SEMI', 'COMMA', 'ADRESS',
        # Enclosings
        'LPAREN', 'RPAREN', 'LBRACKET', 'RBRACKET', 'LBRACE', 'RBRACE',
        # Comparators
        'LT', 'GT', 'EQ', 'NG',
        # Operators
        'MINUS', 'PLUS', 'TIMES', 'DIVIDE', 'PLUSPLUS',
        # Comments
        'LINECOMMENT', 'COMMENT', 'UNTCOMMENT',
    )

    # Regular expression rules for simple tokens
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_ASSIGN = r'='
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_SEMI = r';'
    t_LBRACKET = r'\['
    t_RBRACKET = r'\]'
    t_LBRACE = r'{'
    t_RBRACE = r'}'
    t_COMMA = r','
    t_LT = r'<'
    t_GT = r'>'
    t_EQ = r'=='
    t_NG = r'!'
    t_PLUSPLUS = r'\+\+'
    t_ADRESS = r'&'

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'

    # Define a rule so we can track line numbers
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    def t_ID(self, t):
        r'[a-zA-Z_][0-9a-zA-Z_]*'
        t.type = self.keyword_map.get(t.value, "ID")
        return t        

    def t_FLOAT(self, t):
        r'\d+\.\d*|\d*\.\d+'
        t.value = float(t.value)    
        return t

    def t_NUMBER(self, t):
        r'\d+'
        t.value = int(t.value)    
        return t

    def t_LINECOMMENT (self, t) :
        r'//.*(\n|$)'
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_COMMENT (self, t) :
        r'/\*(.|\n)*?\*/'
        t.lexer.lineno += t.value.count("\n")
        return t

    def t_STRING (self, t) :
        r'\".*?\"'
        return t

    #### ERROR HANDLING RULES ####
    def t_UNTCOMMENT (self, t) :
        r'/\*(.|\n)*$'
        print(f"Unterminated comment at l:{t.lineno}")
    
    def t_UNTSTRING (self, t) :
        r'\".*?$'
        print(f"Unterminated quotes at l:{t.lineno}")

    # If an unmatched character is found
    def t_error(self, t):
        print(f"Illegal character '{t.value[0]}' at l:{t.lineno}")
        t.lexer.skip(1)
    
# # # Build the lexer
# m = Lexer()
# m.build()  # Build the lexer

# # Test it out
#data = input("Write Function: ")
# data = '''
#      a + b + d = c;
#      123.323 ;
#      // lol
#      lol;
# '''

# m.test(data)  # print tokens

# # Give the lexer some input
# lexer.input(data)
# return [t for t in lexer]
