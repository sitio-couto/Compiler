'''
First Project: Parser for the uC language.

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 30/03/2020.
'''

# TODO: CLASSESS NOT IMPLEMENTED YET
# ArrayDecl     
# ArrayRef     
# Assert  
# Break     
# Cast     
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
# Print    
# PtrDecl     # Guess we can ignore this
# Read     
# Return     
# Type     
# UnaryOp     
# While     


#### NODE CLASS - The All Father ####
# It's but a reference to other classes, allowing us to create default
# methods such as children() which can be recursively accessed by it's children.
class Node(object):
    __slots__ = ()
    
    # NOTE: Imma use this function as a inheritance for leaf classes
    # If a class has children, it will be overriden, else it will use it 
    def children(self):
        """ A sequence of all children that are Nodes. """
        nodelist = []
        return tuple(nodelist)

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
    __slots__ = []

class ArrayRef(Node):
    __slots__ = []

class Assert(Node):
    __slots__ = []

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
    __slots__ = ()

class Cast(Node):
    __slots__ = ()

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
    __slots__ = ()

class PtrDecl(Node):
    __slots__ = ()

class Read(Node):
    __slots__ = ()

class Return(Node):
    __slots__ = ()

class Type(Node):
    __slots__ = ('names')

class VarDecl(Node):
    __slots__ = ('declname', 'coord') # NOTE: Not sure it there's

    def __init__(self, declname, coord=None):
        self.declname = declname   # Var name [ID token value]
        self.coord = coord 

    attr_names = ('declname', )

class UnaryOp(Node):
    __slots__ = ()

class While(Node):
    __slots__ = ()

#### AUXILIARY FUNCTIONS ####

# def _fix_decl_name_type(self, decl, typename):
#     """ Fixes a declaration. Modifies decl.
#     """
#     # Reach the underlying basic type
#     type = decl
#     while not isinstance(type, uc_ast.VarDecl):
#         type = type.type

#     decl.name = type.declname

#     # The typename is a list of types. If any type in this
#     # list isn't an Type, it must be the only
#     # type in the list.
#     # If all the types are basic, they're collected in the
#     # Type holder.
#     for tn in typename:
#         if not isinstance(tn, uc_ast.Type):
#             if len(typename) > 1:
#                 self._parse_error(
#                     "Invalid multiple types specified", tn.coord)
#             else:
#                 type.type = tn
#                 return decl

#     if not typename:
#         # Functions default to returning int
#         if not isinstance(decl.type, uc_ast.FuncDecl):
#             self._parse_error("Missing type in declaration", decl.coord)
#         type.type = uc_ast.Type(['int'], coord=decl.coord)
#     else:
#         # At this point, we know that typename is a list of Type
#         # nodes. Concatenate all the names into a single list.
#         type.type = uc_ast.Type(
#             [typename.names[0]],
#             coord=typename.coord)
#     return decl


# def _type_modify_decl(self, decl, modifier):
#     """ Tacks a type modifier on a declarator, and returns
#         the modified declarator.
#         Note: the declarator and modifier may be modified
#     """
#     modifier_head = modifier
#     modifier_tail = modifier

#     # The modifier may be a nested list. Reach its tail.
#     while modifier_tail.type:
#         modifier_tail = modifier_tail.type

#     # If the decl is a basic type, just tack the modifier onto it
#     if isinstance(decl, uc_ast.VarDecl):
#         modifier_tail.type = decl
#         return modifier
#     else:
#         # Otherwise, the decl is a list of modifiers. Reach
#         # its tail and splice the modifier onto the tail,
#         # pointing to the underlying basic type.
#         decl_tail = decl

#         while not isinstance(decl_tail.type, uc_ast.VarDecl):
#             decl_tail = decl_tail.type

#         modifier_tail.type = decl_tail.type
#         decl_tail.type = modifier_head
#         return decl