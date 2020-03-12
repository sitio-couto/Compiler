 # ------------------------------------------------------------
 # calclex.py
 #
 # tokenizer for a simple expression evaluator for
 # numbers and +,-,*,/
 # ------------------------------------------------------------
import ply.lex as lex

class Lexer():
    '''A Lexer for the uC language.
    ''' 
    def __init__(self, filename=""):
        self.filename = filename
        self.last_token = None
        self.lexer = lex.lex(module=self)
    
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
        if not data : data = input("Expression: ")
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
        'COMMENT', 'LINECOMMENT', 'ID', 'MINUS', 'PLUS', 'TIMES', 'DIVIDE', 'LPAREN', 'RPAREN',
        'NUMBER', 'ASSIGN', 'SEMI',


        # constants
        'INT_CONST', 'FLOAT_CONST',

    )

    # Regular expression rules for simple tokens
    # t_UTERMINATED = r'/\\*(.|\\n)*$'
    # t_STRING      = r'\\\".*?\\\"'
    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_ASSIGN = r'='
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_SEMI = r';'

    # A string containing ignored characters (spaces and tabs)
    t_ignore  = ' \t'
    
    # Ignoring Comments
    t_ignore_COMMENT = r'/\*(.|\n)*?\*/'
    t_ignore_LINECOMMENT = r'//.*(\n|$)'

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
    
    # Error handling rule
    def t_error(self, t):
        print("Illegal character '%s'" % t.value[0])
        t.lexer.skip(1)
    
# # Build the lexer
m = Lexer()
m.build()  # Build the lexer

# # Test it out
#data = input("Write Function: ")
data = '''
     a + b + d = c;
     123.323 ;
     // lol
     lol;
'''

m.test(data)  # print tokens

# # Give the lexer some input
# lexer.input(data)
# return [t for t in lexer]
