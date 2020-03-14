'''
Compiler for the uC Language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020
'''

from lexer import Lexer

tokenizer = Lexer()
tokenizer.build()

while True: 
    try:
        tokenizer.test(input("Filename or expression: "))
        tokenizer.reset_line_num()
    except EOFError:
        break

#asdfasdfasdfasdf
