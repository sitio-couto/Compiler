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

#### NODE CLASS - The All Father ####
# It's but a reference to other classes, allowing us to create default
# methods such as children() which can be recursively accessed by it's children.
class Node(object):
    __slots__ = ()
    
    def children(self):
        """ A sequence of all children that are Nodes. """
        pass

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

    attr_names = ('op', )

# TODO ----------------------------
# Break ( ), Cast ( ), Compound ( )

class Constant(Node):
    __slots__ = ('type', 'value', 'coord')
    
    def __init__(self, type, value, coord=None):
        self.type = type
        self.value = value
        self.coord = coord

    def children(self):
        nodelist = []
        return tuple(nodelist)

    attr_names = ('type', 'value', )

# , Constant (type, value), Decl (name), DeclList ( ), EmptyStatement ( ), ExprList ( ), For ( ), FuncCall ( ), FuncDecl ( ), FuncDef ( ), GlobalDecl ( ), ID (name), If ( ), InitList ( ), ParamList ( ), Print ( ), Program ( ), PtrDecl ( ), Read ( ), Return ( ), Type (names), VarDecl (declname), UnaryOp (op), While ( ).


# def _build_declarations(self, spec, decls):
#     """ Builds a list of declarations all sharing the given specifiers.
#     """
#     declarations = []

#     for decl in decls:
#         assert decl['decl'] is not None
#         declaration = uc_ast.Decl(
#                 name=None,
#                 type=decl['decl'],
#                 init=decl.get('init'),
#                 coord=decl['decl'].coord)

#         fixed_decl = self._fix_decl_name_type(declaration, spec)
#         declarations.append(fixed_decl)

#     return declarations

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