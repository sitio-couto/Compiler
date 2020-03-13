from lexer import Lexer

tokenizer = Lexer()
tokenizer.build()

while True : 
    tokenizer.test(input("Filename or expression: "))

#asdfasdfasdfasdf