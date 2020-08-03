MC921 - Construction of Compilers
=================================
Compiler for the uC (a.k.a. micro C) language.

The full specification of the language and each project is available in the `Notebooks` submodule.

Projects
--------

**Project 1** - Lexer (`uCLexer.py`) and parser (`uCParser.py`) with AST (`uCAST.py`) for uC language, using the [PLY](https://www.dabeaz.com/ply/) library. 

**Project 2** - Semantic checks (`uCSemantic.py`), uCIR generation (`uCGenerate.py`) and interpreter (`uCInterpreter`) for uC language.

**Project 3** - Basic block separation (`uCBlock.py`), dataflow analysis (`uCDFA.py`) and optimizations (`uCOptimize.py`) for uCIR.

**Project 4** - uCIR translation to LLVM IR (`uCTranslate.py`) and LLVM JIT compilation (`uCBuild.py`) using the [llvmlite](https://llvmlite.readthedocs.io/en/latest/) library.

Grade (for all projects): 8/8.

Lexer and parser based on [Eli Bendersky](https://github.com/eliben)'s [pycparser](https://github.com/eliben/pycparser).

Files
-----

- `uCCompiler.py` - Main script for the uC Compiler, very configurable, a little modular.
- `test.py`       - Test script for the uC Compiler, a little configurable, very modular.
- `uCType.py`     - Auxiliary script for semantic checks (Project 2).
- `tests`         - Test files for different parts of the compiler. Includes tests for lexer (`lex_in`), parser (`parse_in`, `ast_in`), semantic check (`sem_in`), **IR generation** (`IR_in`), interpreter (`int_in`), dataflow analysis (`dfa_in`), **optimizer** (`opt_in`) and code translation (`llvm`). Also contains some common errors (`errors`), **actual programs with purpose** (`complete_codes`) and scripts for **unit testing** (`unittest`). Most important test folders are in bold.

Course given by professor [Guido Araujo](https://guidoaraujo.wordpress.com/).

[Institute of Computing](http://ic.unicamp.br/en) - [UNICAMP](http://www.unicamp.br/unicamp/) (State University of Campinas) - 2020


