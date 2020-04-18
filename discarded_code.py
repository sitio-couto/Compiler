#### DECLARATIONS TABLES ####
# NOTE: Variables declarations only seems to be acceptable if right after a function declaration.
# NOTE: We are considering only global function declarations (no nested funcs allowed)
# NOTE: func def with only types (int main(int,char,float);) doesnt work
# When declaring a new function a new table will be added. it will consist an item which keeps
# the functions name, return type, params types and variables within the scope.
# We'll use a stack to build and maintain such structure, since the AST will pass through functions 
# as they are declared. This allows us to know which scope we are currently at (top of the stack is 
# the current scope) and check which IDs are defined within the scope, as well as cross referencing 
# types assignments. The scopes will also be sequentially saved in the symbols table to be accessed 
# after the semantic check.
class DeclarationsTable():
    def __init__(self):
        self.param_list = False # Set if we are checking vars in a parameter list
        self.globals = dict()   # Special list for global variables
        self.scopes = dict()    # Dictionary of scopes: keys are funcion names
        self.stack = []         # last element is the top of the stack
    
    # Add new scope (if a function declaration started)
    def add_scope(self, name, return_type, params, defined=False): 
        # {func_name:('ret':return_type, 'params':[int,char,...], 'vars':{'name':('type',val)})}
        #  - Every function declaration is considered a new scope
        #  - The scope element is indexed by the function's name
        #  - The return type and a ORDERED param list are kept for type checking
        #  - 'vars' are the variables available within the scope (include func parameters)
        #  - 'vars' will keep both the initial values as well as it's type
        #  - NOTE: functions only declared have 'vars':None, if defined 'vars':{} (will be used to check if defined)        
        if defined : new_scope = dict(ret=return_type, params=[], vars=dict())
        else : new_scope = dict(ret=return_type, params=[], vars=dict())
        # Here we will save two pointers to the same dictionary. 
        # This way, when altering the stack, self.scopes will also be updated
        self.scopes[name] = new_scope 
        self.stack.append(new_scope) # The function's name is not relevant on the stack (we only access the top item)
   
    # If a function is declared but defined only later, use this.
    def define_scope(self, name):
        self.scopes[name]['vars'] = dict()

    # Add a new variable to the current function's scope (when variables are declared)
    def add_to_scope(self, name, value):
        if self.stack : # Stack not emtpy? then not on the global scope
            current = self.stack[-1]      # Get current function
            current['vars'][name] = value # Add declaration to function
        else : # if global
            self.globals[name] = value    # Add var to global scope
    
    # remove current scope from stack (if a function def has ended)
    def pop_scope(self):
        self.stack.pop()
    
    # Check if name is a declared variable in the stack (when variable is used)
    # NOTE: Should work to check if function was declared: name will can be kept in global scope
    def is_defined(self, name):
        local = name in self.stack[-1].keys() # Check if in current scope
        glob = name in self.globals.keys()    # Check if in global scope
        return glob or local

    # Fetches the current function's return type
    def check_return(self):
        return self.stack[-1]['ret']

    def show_scopes(self):
        pass