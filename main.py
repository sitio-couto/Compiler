from lexer import Lexer

tokenizer = Lexer()
tokenizer.build()

tokenizer.test("tests/test01.c")

while True : 
    tokenizer.test("")

#asdfasdfasdfasdf