class Node(object):
    """
    Base class example for the AST nodes.  Each node is expected to
    define the _fields attribute which lists the names of stored
    attributes.   The __init__() method below takes positional
    arguments and assigns them to the appropriate fields.  Any
    additional arguments specified as keywords are also assigned.
    """
    _fields = []
    def __init__(self, *args, **kwargs):
        assert len(args) == len(self._fields)
        for name,value in zip(self._fields,args):
            setattr(self,name,value)
        # Assign additional keyword arguments if supplied
        for name,value in kwargs.items():
            setattr(self,name,value)

# This is the top of the AST, representing a uC program (a
# translation unit in K&R jargon). It contains a list of
# global-declaration's, which is either declarations (Decl),
# or function definitions (FuncDef).
class Program(Node):
    _fields = ['decls']