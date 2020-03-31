'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 31/03/2020.
'''

# TODO: CLASSESS NOT IMPLEMENTED YET
# ArrayDecl     
# ArrayRef     
# Compound
# DeclList     
# EmptyStatement     
# ExprList     
# For     
# FuncCall     
# FuncDecl     
# FuncDef     # Difference between FuncDef and FuncDecl?
# GlobalDecl  
# If     
# InitList     
# ParamList     
# PtrDecl     # Guess we can ignore this
# UnaryOp     

def _repr(obj):
    """
    Get the representation of an object, with dedicated pprint-like format for lists.
    """
    if isinstance(obj, list):
        return '[' + (',\n '.join((_repr(e).replace('\n', '\n ') for e in obj))) + '\n]'
    else:
        return repr(obj) 

#### NODE CLASS - The All Father ####
# It's but a reference to other classes, allowing us to create default
# methods such as children() which can be recursively accessed by it's children.
class Node(object):
    __slots__ = ()

    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-2]:
            result += separator
            result += indent
            result += name + '=' + (_repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result
            
    # NOTE: Imma use this function as a inheritance for leaf classes
    # If a class has children, it will be overriden, else it will use it 
    def children(self):
        """ A sequence of all children that are Nodes. """
        nodelist = []
        return tuple(nodelist)

        def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=False, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
            attrnames:
                True if you want to see the attribute names in name=value pairs. False to only see the values.
            nodenames:
                True if you want to see the actual node names within their parents.
            showcoord:
                Do you want the coordinates of each Node to be displayed.
        """
        lead = ' ' * offset
        if nodenames and _my_node_name is not None:
            buf.write(lead + self.__class__.__name__+ ' <' + _my_node_name + '>: ')
        else:
            buf.write(lead + self.__class__.__name__+ ': ')

        if self.attr_names:
            if attrnames:
                nvlist = [(n, getattr(self, n)) for n in self.attr_names if getattr(self, n) is not None]
                attrstr = ', '.join('%s=%s' % nv for nv in nvlist)
            else:
                vlist = [getattr(self, n) for n in self.attr_names]
                attrstr = ', '.join('%s' % v for v in vlist)
            buf.write(attrstr)

        if showcoord:
            if self.coord:
                buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)
            
    # NOTE: it seems to be a list for variables contained in the class (excluding subtrees)
    attr_names = () 

# This is the top of the AST, representing a uC program (a
# translation unit in K&R jargon). It contains a list of
# global-declaration's, which is either declarations (Decl),
# or function definitions (FuncDef).
class Program(Node):
    __slots__ = ('gdecls', 'coord')
    
    def __init__(self, gdecls, coord=None):
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        nodelist = []
        for i, child in enumerate(self.gdecls or []):
            nodelist.append(("gdecls[%d]" % i, child))
        return tuple(nodelist)

    attr_names = ()

#### AST NODES CLASSES ####

class ArrayDecl(Node):
    __slots__ = ()

class ArrayRef(Node):
    __slots__ = ()

class Assert(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to assert.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')

    def __init__(self, op, left, right, coord=None):
        self.op = op        # assign_op (TERMINAL EXPR - represents the node)
        self.lvalue = left  # un_expr
        self.rvalue = right # assign_expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op', ) 

class BinaryOp(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
    
    def __init__(self, op, left, right, coord=None):
        self.op = op        # TOKEN (represents the node)
        self.lvalue = left  # bin_expr
        self.rvalue = right # bin_expr
        self.coord = coord

    def children(self):
        nodelist = []
        if self.lvalue is not None: nodelist.append(("lvalue", self.lvalue))
        if self.rvalue is not None: nodelist.append(("rvalue", self.rvalue))
        return tuple(nodelist)

    attr_names = ('op', ) # NOTE: lvalue and rvalue are subtrees, so they dont make the list

class Break(Node):
    __slots__ = ('coord')
    
    def __init__(self, coord=None):
        self.coord = coord
    
    attr_names = ()

class Cast(Node):
    __slots__ = ('type', 'expr', 'coord')
    
    def __init__(self, type, expr, coord=None):
        self.type = type
        self.expr = expr
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(('type', self.type))
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
        
    attr_names = ()

class Compound(Node):
    __slots__ = ()

class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    attr_names = ('type', 'value', )

class Decl(Node):
    __slots__ = ('name', 'type', 'init', 'coord')

    def __init__(self, name, type, init, coord=None):
        self.name = name # TODO: Not sure what's this name variable (I think it will derive from one of the childre or just remain as none)
        self.type = type # Func/Var Type [type_specifier] (int, float... tokens)
        self.init = init # One or more initializers [init_declarator_list_opt]
        self.coord = coord

    def children(self):
        nodelist = []
        if self.type is not None: nodelist.append(("type", self.type))
        if self.init is not None: nodelist.append(("init", self.init))
        return tuple(nodelist)

    attr_names = ('name', 'type', )

class DeclList(Node):
    __slots__ = ()

class EmptyStatement(Node):
    __slots__ = ()

class ExprList(Node):
    __slots__ = ()

class For(Node):
    __slots__ = ()

class FuncCall(Node):
    __slots__ = ()

class FuncDecl(Node):
    __slots__ = ()

class FuncDef(Node):
    __slots__ = ()

class GlobalDecl(Node):
    __slots__ = ()

class ID(Node): # NOTE: Const class is ID's sibiling, not child
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name   # Func/Var name [ID token value]
        self.coord = coord 

    attr_names = ('name', )


class If(Node):
    __slots__ = ()

class InitList(Node):
    __slots__ = ()

class ParamList(Node):
    __slots__ = ()

class Print(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to print.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class PtrDecl(Node):
    __slots__ = ()

class Read(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr      # Expression to read.
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Return(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        return tuple(nodelist)
    
    attr_names = ()

class Type(Node):
    __slots__ = ('names', 'coord')
    
    def __init__(self, names, coord=None):
        self.names = names
        self.coord = coord
    
    attr_names = ('names',)

class VarDecl(Node):
    __slots__ = ('declname', 'coord') # NOTE: Not sure it there's

    def __init__(self, declname, coord=None):
        self.declname = declname   # Var name [ID token value]
        self.coord = coord 

    attr_names = ('declname', )

class UnaryOp(Node):
    __slots__ = ()

class While(Node):
    __slots__ = ('expr', 'statement')
    
    def __init__(self, expr, statement, coord=None):
        self.expr = expr
        self.statement = statement
        self.coord = coord
        
    def children(self):
        nodelist = []
        if self.expr is not None: nodelist.append(('expr', self.expr))
        if self.statement is not None: nodelist.append(('statement', self.statement))
        return tuple(nodelist)
        
    attr_names = ()
