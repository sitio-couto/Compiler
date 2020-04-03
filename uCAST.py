'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 03/04/2020.
'''

import sys

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
    __slots__ = ('coord')

    def __repr__(self):
        """ Generates a python representation of the current node
        """
        result = self.__class__.__name__ + '('
        indent = ''
        separator = ''
        for name in self.__slots__[:-1]:
            result += separator
            result += indent
            result += name + '=' + (_repr(getattr(self, name)).replace('\n', '\n  ' + (' ' * (len(name) + len(self.__class__.__name__)))))
            separator = ','
            indent = ' ' * len(self.__class__.__name__)
        result += indent + ')'
        return result

    def children(self):
        """ A sequence of all children that are Nodes. """
        children = []
        return tuple(children)

    def show(self, buf=sys.stdout, offset=0, attrnames=False, nodenames=False, showcoord=True, _my_node_name=None):
        """ Pretty print the Node and all its attributes and children (recursively) to a buffer.
            buf:
                Open IO buffer into which the Node is printed.
            offset:
                Initial offset (amount of leading spaces)
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
            if self.coord : buf.write('%s' % self.coord)
        buf.write('\n')

        for (child_name, child) in self.children():
            child.show(buf, offset + 4, attrnames, nodenames, showcoord, child_name)
            
    attr_names = () 

class NodeVisitor(object):
    """ A base NodeVisitor class for visiting uc_ast nodes.
        Subclass it and define your own visit_XXX methods, where
        XXX is the class name you want to visit with these
        methods.

        For example:

        class ConstantVisitor(NodeVisitor):
            def __init__(self):
                self.values = []

            def visit_Constant(self, node):
                self.values.append(node.value)

        Creates a list of values of all the constant nodes
        encountered below the given node. To use it:

        cv = ConstantVisitor()
        cv.visit(node)

        Notes:

        *   generic_visit() will be called for AST nodes for which
            no visit_XXX method was defined.
        *   The children of nodes for which a visit_XXX was
            defined will not be visited - if you need this, call
            generic_visit() on the node.
            You can use:
                NodeVisitor.generic_visit(self, node)
        *   Modeled after Python's own AST visiting facilities
            (the ast module of Python 3.0)
    """

    _method_cache = None

    def visit(self, node):
        """ Visit a node.  """

        if self._method_cache is None:
            self._method_cache = {}

        visitor = self._method_cache.get(node.__class__.__name__, None)
        if visitor is None:
            method = 'visit_' + node.__class__.__name__
            visitor = getattr(self, method, self.generic_visit)
            self._method_cache[node.__class__.__name__] = visitor

        return visitor(node)

    def generic_visit(self, node):
        """ Called if no explicit visitor function exists for a
            node. Implements preorder visiting of the node.
        """
        for c in node:
            self.visit(c)

# Tree's root - Represents the program
class Program(Node):
    __slots__ = ('gdecls', 'coord')
    
    def __init__(self, gdecls, coord=None):
        self.gdecls = gdecls
        self.coord = coord

    def children(self):
        children = []
        for i, child in enumerate(self.gdecls or []):
            children += [("gdecls[%d]" % i, child)]
        return tuple(children)

#### AST NODES CLASSES ####

class ArrayDecl(Node):
    __slots__ = ('type', 'dims', 'coord')
    
    def __init__(self, type, dims, coord=None):
        self.type = type
        self.dims = dims
        self.coord = coord

    def children(self):
        children = []
        if self.type: children += [("type", self.type)]
        if self.dims: children += [("dims", self.dims)]
        return tuple(children)


class ArrayRef(Node):
    __slots__ = ('name', 'subsc', 'coord')
    
    def __init__(self, name, subsc, coord):
        self.name = name
        self.subsc = subsc
        self.coord = coord
        
    def children(self):
        children = []
        if self.name: children += [('name', self.name)]
        if self.subsc: children += [('subscript', self.subsc)]
        return tuple(children)

class Assert(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        children = []
        if self.expr: children += [('expr', self.expr)]
        return tuple(children)

class Assignment(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')

    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.lvalue = left
        self.rvalue = right
        self.coord = coord

    def children(self):
        children = []
        if self.lvalue: children += [("lvalue", self.lvalue)]
        if self.rvalue: children += [("rvalue", self.rvalue)]
        return tuple(children)

    attr_names = ('op', ) 

class BinaryOp(Node):
    __slots__ = ('op', 'lvalue', 'rvalue', 'coord')
    
    def __init__(self, op, left, right, coord=None):
        self.op = op
        self.lvalue = left
        self.rvalue = right
        self.coord = coord

    def children(self):
        children = []
        if self.lvalue: children += [("lvalue", self.lvalue)]
        if self.rvalue: children += [("rvalue", self.rvalue)]
        return tuple(children)

    attr_names = ('op', )

class Break(Node):
    __slots__ = ('coord')
    
    def __init__(self, coord=None):
        self.coord = coord

class Cast(Node):
    __slots__ = ('type', 'expr', 'coord')
    
    def __init__(self, type, expr, coord=None):
        self.type = type
        self.expr = expr
        self.coord = coord
        
    def children(self):
        children = []
        if self.type: children += [('type', self.type)]
        if self.expr: children += [('expr', self.expr)]
        return tuple(children)

class Compound(Node):
    __slots__ = ('decls', 'stats', 'coord')
    
    def __init__(self, decls, stats, coord=None):
        self.decls = decls
        self.stats = stats
        self.coord = coord
        
    def children(self):
        children = []
        for i, child in enumerate(self.decls or []):
            if child: children += [("decls[%d]" % i, child)]
        for i, child in enumerate(self.stats or []):
            if child: children += [("stats[%d]" % i, child)]
        return tuple(children)

class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    attr_names = ('type', 'value', )

class Coord(Node):
    """ Coordinates of a syntactic element. Consists of:
            - Line number
            - (optional) column number, for the Lexer
    """
    __slots__ = ('line', 'column')

    def __init__(self, line, column=None):
        self.line = line
        self.column = column

    def __str__(self):
        if self.line:
            coord_str = "   @ %s:%s" % (self.line, self.column)
        else:
            coord_str = ""
        return coord_str 
        
class Decl(Node):
    __slots__ = ('name', 'type', 'init', 'coord')

    def __init__(self, name, type, init, coord=None):
        self.name = name 
        self.type = type 
        self.init = init 
        self.coord = coord

    def children(self):
        children = []
        if self.type: children += [("type", self.type)]
        if self.init: children += [("init", self.init)]
        return tuple(children)

    attr_names = ('name', )

class DeclList(Node):
    __slots__ = ('decls', 'coord')
    
    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord

    def children(self):
        children = []
        for i, child in enumerate(self.decls or []):
            children += [("decls[%d]" % i, child)]
        return tuple(children)

class EmptyStatement(Node):
    __slots__ = ('coord')
    
    def __init__(self, coord=None):
        self.coord = coord

class ExprList(Node):
    __slots__ = ('exprs', 'coord')
    
    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord
        
    def children(self):
        children = []
        for i, child in enumerate(self.exprs or []):
            children += [("exprs[%d]" % i, child)]
        return tuple(children)

class For(Node):
    __slots__ = ('init', 'cond', 'next', 'body', 'coord')
    
    def __init__(self, init, cond, next, body, coord=None):
        self.init = init
        self.cond = cond
        self.next = next
        self.body = body
        self.coord = coord
    
    def children(self):
        children = []
        if self.init: children += [('init', self.init)]
        if self.cond: children += [('cond', self.cond)]
        if self.next: children += [('next', self.next)]
        if self.body: children += [('body', self.body)]
        return tuple(children)

class FuncCall(Node):
    __slots__ = ('name', 'args', 'coord')
    
    def __init__ (self, name, args, coord=None):
        self.name = name
        self.args = args
        self.coord = coord
        
    def children(self):
        children = []
        if self.name: children += [('name', self.name)]
        if self.args: children += [('args', self.args)]
        return tuple(children)

class FuncDecl(Node):
    __slots__ = ('type', 'params', 'coord')
    
    def __init__(self, type, params, coord=None):
        self.type = type
        self.params = params
        self.coord = coord

    def children(self):
        children = []
        if self.params: children += [("params", self.params)]
        if self.type: children += [("type", self.type)]
        return tuple(children)

class FuncDef(Node):
    __slots__ = ('type', 'decl', 'params', 'body', 'coord')
    
    def __init__(self, type, decl, params, body, coord=None):
        self.type = type
        self.decl = decl
        self.params = params
        self.body = body
        self.coord = coord
        
    def children(self):
        children = []
        if self.type: children += [('type', self.type)]
        if self.decl: children += [('decl', self.decl)]
        if self.params: children += [('params', self.params)]
        if self.body: children += [('body', self.body)]
        return tuple(children)

class GlobalDecl(Node):
    __slots__ = ('decls', 'coord')
    
    def __init__(self, decls, coord=None):
        self.decls = decls
        self.coord = coord
        
    def children(self):
        children = []
        for child in self.decls or []:
            if child: children += [("Decl", child)]
        return tuple(children)

class ID(Node):
    __slots__ = ('name', 'coord')

    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord 

    attr_names = ('name', )

class If(Node):
    __slots__ = ('cond', 'if_stat', 'else_stat', 'coord')
    
    def __init__(self, cond, if_stat, else_stat, coord=None):
        self.cond = cond
        self.if_stat = if_stat 
        self.else_stat = else_stat
        self.coord = coord
        
    def children(self):
        children = []
        if self.cond: children += [('cond', self.cond)]
        if self.if_stat: children += [('if_stat', self.if_stat)]
        if self.else_stat: children += [('else_stat', self.else_stat)]
        return tuple(children)

class InitList(Node):
    __slots__ = ('exprs', 'coord')

    def __init__(self, exprs, coord=None):
        self.exprs = exprs
        self.coord = coord

    def children(self):
        children = []
        for i, child in enumerate(self.exprs or []):
            children += [("exprs[%d]" % i, child)]
        return tuple(children)

class ParamList(Node):
    __slots__ = ('params', 'coord')
    def __init__(self, params, coord=None):
        self.params = params
        self.coord = coord

    def children(self):
        children = []
        for i, child in enumerate(self.params or []):
            children += [("params[%d]" % i, child)]
        return tuple(children)

class Print(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        children = []
        if self.expr: children += [('expr', self.expr)]
        return tuple(children)

class PtrDecl(Node):
    __slots__ = ('type', 'coord')
    
    def __init__(self, type, coord=None):
        self.type = type
        self.coord = coord

    def children(self):
        children = []
        if self.type: children += [("type", self.type)]
        return tuple(children)

class Read(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        children = []
        if self.expr: children += [('expr', self.expr)]
        return tuple(children)

class Return(Node):
    __slots__ = ('expr', 'coord')
    
    def __init__(self, expr, coord=None):
        self.expr = expr
        self.coord = coord
        
    def children(self):
        children = []
        if self.expr: children += [('expr', self.expr)]
        return tuple(children)

class Type(Node):
    __slots__ = ('name', 'coord')
    
    def __init__(self, name, coord=None):
        self.name = name
        self.coord = coord
        
    attr_names = ('name',)

class VarDecl(Node):
    __slots__ = ('declname', 'type', 'coord')

    def __init__(self, declname, type, coord=None):
        self.declname = declname
        self.type = type
        self.coord = coord 

    def children(self):
        children = []
        if self.type: children += [('type', self.type)]
        return tuple(children)

class UnaryOp(Node):
    __slots__ = ('op', 'expr', 'coord')
    
    def __init__(self, op, expr, coord=None):
        self.op = op
        self.expr = expr
        self.coord = coord
    
    def children(self):
        children = []
        if self.expr: children += [("expr", self.expr)]
        return tuple(children)
    
    attr_names = ('op', )

class While(Node):
    __slots__ = ('cond', 'body', 'coord')
    
    def __init__(self, cond, body, coord=None):
        self.cond = cond 
        self.body = body
        self.coord = coord
        
    def children(self):
        children = []
        if self.cond: children += [('cond', self.cond)]
        if self.body: children += [('body', self.body)]
        return tuple(children)

