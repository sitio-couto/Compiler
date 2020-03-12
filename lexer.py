 # ------------------------------------------------------------
 # calclex.py
 #
 # tokenizer for a simple expression evaluator for
 # numbers and +,-,*,/
 # ------------------------------------------------------------
import ply.lex as lex

class Lexer:
    '''A Lexer for the uC language.
    ''' 

    def __init__(self, filename):
        self.filename = filename
        self.last_token = None
    
        # List of token names.   This is always required
    tokens = [
        'ID',
        'NUMBER',
        'FLOAT',
        'PLUS',
        'MINUS',
        'TIMES',
        'EQUAL',
        'DIVIDE',
        'LPAREN',
        'RPAREN'
    ]
    
    # Regular expression rules for simple tokens
    t_ID      = r'[a-zA-Z_][0-9a-zA-Z_]*'
    t_PLUS    = r'\+'
    t_MINUS   = r'-'
    t_TIMES   = r'\*'
    t_EQUAL   = r'='
    t_DIVIDE  = r'/'
    t_LPAREN  = r'\('
    t_RPAREN  = r'\)'

    # Build the lexer
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    def reset_line_num(self):
        self.line_num = 1

    def input(self, text):
        self.lexer.input(text)

    def token(self):
        self.last_token = self.lexer.token()
        return self.last_token

    # Test it output
    def test(self,data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok: 
                break
            print(tok)
    
    # A regular expression rule with some action code
    def t_FLOAT(t):
        r'\d+\.\d*|\d*\.\d+'
        t.value = float(t.value)    
        return t

    def t_NUMBER(t):
        r'\d+'
        t.value = int(t.value)    
        return t

    # Define a rule so we can track line numbers
    def t_newline(t):
        r'\n+'
        t.lexer.lineno += len(t.value)
    
    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'
    
    # Error handling rule
    def t_error(t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)
    
# # Build the lexer
# lexer = lex.lex()

# # Test it out
# data = input("Write Function: ")
# data = '''
#     a + b = c
#     123.323 
# '''

# # Give the lexer some input
# lexer.input(data)
# return [t for t in lexer]