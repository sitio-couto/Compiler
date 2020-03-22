// Reference: https://theasciicode.com.ar/
//  - Must read all printable chars (exept ones which must be escaped \"')
//  - Must read all escape sequences (except \?)

char x = '1';
char a = 'a';
char v[] = {'a','b','c','d','e','f','g'};
char special1[] = {' ', '~', '`', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')'} 
char special2[] = {'-', '_', '+', '=', '{', '['};
char escaped_commom = {'\\', '\'', '\"'}
char escaped_special[] = {'\a', '\v' '\f', '\n', '\t', '\b', '\e', '\r', '\0'}
char nl = '\n'
char tb = '\t'
