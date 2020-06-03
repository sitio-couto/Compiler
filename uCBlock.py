'''
Third Project: Basic Block organization of uCIR code.
uCIR: check SecondProject.ipynb in 'Notebooks' submodule.

REFERENCES:
    https://en.wikipedia.org/wiki/Basic_block
    https://stackoverflow.com/questions/31305423/how-do-you-include-subroutine-calls-in-a-control-flow-graph

Subject:
    MC921 - Construction of Compilers
Authors:
    Victor Ferreira Ferrari  - RA 187890
    Vinicius Couto Espindola - RA 188115

University of Campinas - UNICAMP - 2020

Last Modified: 02/06/2020.
'''

import os
os.environ["PATH"] += os.pathsep + 'C:\Program Files (x86)/Graphviz2.38/bin'
from collections import OrderedDict
from graphviz import Digraph
from os.path import exists
import re

class Block(object):
    meta = None # Reference to UCCFG metaclass

    def __init__(self, meta):
        # Update Metainformation
        Block.meta = meta
        Block.meta.blockID += 1
        Block.meta.index[Block.meta.blockID] = self

        self.ID = Block.meta.blockID         # Integer to identify block
        self.instructions = OrderedDict()    # Instructions in the block
        self.inst_gen = OrderedDict()        # Gen set for each instruction
        self.inst_kill = OrderedDict()       # Kill set for each instruction
        self.pred = []                       # Link to parent blocks
        self.succ = []                       # Link to the next block   
        self.gen  = set()                    # Block accumulated gen set
        self.kill = set()                    # Block accumulated kill set
        self.in_set  = set()
        self.out_set = set()

    ### Instruction List Control ###
    
    def append(self, instr):
        Block.meta.lineID += 1
        key = Block.meta.lineID
        self.instructions[key] = instr
        self.inst_gen[key] = set()
        self.inst_kill[key] = set()

    def concat(self, inst_list):
        base = Block.meta.lineID + 1
        top = base + len(inst_list)
        section = range(base, top)
        Block.meta.lineID += len(inst_list)
        new_insts = zip(range(base, top), inst_list)
        self.instructions.update(new_insts)
        self.inst_gen.update([(i,set()) for i in section])
        self.inst_kill.update([(i,set()) for i in section])

    def get_inst(self, idx):
        insts = list(self.instructions.values())
        return insts[idx]

    def remove_inst(self, line):
        try:
            del(self.instructions[line])
            del(self.inst_gen[line])
            del(self.inst_kill[line])
        except KeyError:
            print(f"Line {line} not found in block {self.ID}")

    def __iter__(self):
        return iter(self.instructions.values())

    ### Node Control ###

    def add_pred(self, block):
        self.pred.append(block)

    def add_succ(self, block):
        self.succ.append(block)

    def delete(self):
        for s in self.succ:
            s.pred.remove(self)
        for p in self.pred:
            p.succ.remove(self)
        self.pred = []
        self.succ = []
        del Block.meta.index[self.ID]

    ### Exhibition Control ###

    def show_sets(self):
        show = lambda x : ', '.join(x) if x else ''

        txt = f"BLOCK {self.ID}:\n"
        txt += f"   IN: {show(self.in_set)}\n"
        txt += f"   GEN: {show(self.gen)}\n"
        txt += f"   KILL: {show(self.kill)}\n"
        txt += f"   OUT: {show(self.out_set)}\n"
        txt += '\n'

        return txt

    def __str__(self):
        txt = f"BLOCK {self.ID}:\n"
        
        txt += f"   Preds:"
        for b in self.pred:
            txt += f" {b.ID}"
        txt += '\n\n'
        
        for lin,inst in self.instructions.items():
            gen = self.inst_gen[lin] if self.inst_gen[lin] else ''
            kill = self.inst_kill[lin] if self.inst_kill[lin] else ''
            txt += f"   {lin} : {inst} \t<{gen} | {kill}>\n"
        txt += '\n'

        txt += f"   Succs:"
        for b in self.succ:
            txt += f" {b.ID}"
        txt += "\n"

        return txt

class uCCFG(object):
    def __init__(self, generator):
        # Metavariables (retains CFG info)
        self.blockID = 0 # Count blocks ids
        self.lineID  = 0 # Count lines/statements ids
        self.index = dict() # Maps blockID to block objects

        self.generator = generator
        self.first_block = None
        
        self.targets = [r'define',r'\d+']              # Possible branch targets
        self.branches = [r'return',r'jump',r'cbranch'] # Possible branching statements

    def delete_cfg(self):
        '''Erases metadata and CFG blocks for garbage collection'''
        # Wipe all block references
        for b in self.dfs_sort(): 
            b.delete()
        # Wipe CFG metadata
        self.first_block = None
        self.blockID = 0
        self.lineID  = 0
        self.index = dict()

    def dfs_sort(self, node=None, visits=None):
        ''''Topology sort blocks starting from global node.'''
        # If in root, prepare variables
        if not node: 
            node = self.first_block
            visits=[]

        # Run DFS search
        if node not in visits:
            visits.append(node)
            # print(f"{node.ID} succs: {node.succ}|visits: {visits}")
            for b in node.succ:
                visits = self.dfs_sort(node=b, visits=visits)
        return visits

    def test(self, data, quiet=False):
        self.generator.front_end.parser.lexer.reset_line_num()
        
        # Scan and parse
        if exists(data):
            with open(data, 'r') as content_file :
                data = content_file.read()
        
        # Generate IR.
        self.generator.code = []
        self.generator.generate(data)
        
        if not quiet:
            self.generator.print_code()
        
        # Build CFG.
        if self.first_block:
            self.delete_cfg()
        self.build_cfg(self.generator.code)
        
        self.print_blocks()

    ##### Building the CFG ####
    
    # Lambda functions
    is_target = lambda self, x : bool([True for t in self.targets if re.match(t, x)])
    is_branch = lambda self, x : bool([True for b in self.branches if re.match(b, x)])

    def build_cfg(self, code):
        ''' Given the IR code as a list of tuples, build a CFG.
            The CFG considers subroutines as independent subtrees.
            If there are no global variables, the global block is empty.
            Params:
                code - List of tuples where each tuple is a IR statement
            Return:
                Block - Return the global basic block (links to every subroutine) 
        '''
        # Get leaders
        leads = self.get_leaders(code)
        blocks = []

        # Create blocks
        for s,t in zip(leads, leads[1:]+[len(code)]):
            new_block = Block(self)
            new_block.concat(code[s:t])
            blocks.append(new_block)

        # Split blocks by function
        glob,funcs = self.isolate_functions(blocks) 
        
        # Link Blocks
        for blocks in funcs: 
            self.link_blocks(glob, blocks)
        self.first_block = glob
                
        # Remove unreachable blocks
        self.clean_cfg()
    
    def get_leaders(self, code):
        ''' Given a list with IR code instructions, find all leaders indexes.
            Params:
                code - List of tupes where each element is a IR instruction
            Return:
                List - indexes of the leades in the code
        '''
        leaders = set([0])
        for i in range(len(code)):
            prev = code[i-1][0]
            curr = code[i][0]
            if self.is_target(curr) or self.is_branch(prev):
                leaders = leaders.union([i])
        
        return sorted(list(leaders))

    def isolate_functions(self, blocks):
        ''' Given a list of basic blocks, group blocks by enclosing function.
            Functions are sequential instructions in the IR, so we take the 
            blocks and group then until a new 'define' statement is found, or
            until we reach the end of the code.
            Params:
                Blocks - List of unconnected Blocks 
        '''
        # Create the program entry block
        entry = blocks[0].get_inst(0)[0]
        if 'global' in entry:
            globs = blocks.pop(0)    # Separe globals block
        else:
            globs = Block(self) # Create dummy block

        aux = []
        funcs = [] # List of lists (each element is the blocks of a function)
        
        # Group blocks by functions
        for b in blocks:
            inst = b.get_inst(0)[0]
            if inst=='define': # Reset every time a define is found
                if aux: funcs.append(aux)
                aux = [b]
            else:
                aux.append(b)
        if aux: funcs.append(aux) # Append rest if eof

        return globs,funcs

    def link_blocks(self, globs, blocks):
        ''' Given the globals block and a list of basic blocks, link them 
            creating a CFG. Subroutines are handled separatedly.
            Every subroutine is connected to the globals block.
            Params:
                globs - Basic block containing global vars (program entrypoint)
                Blocks - List of unconnected Blocks of a subroutine 
        '''
        jumps  = dict() # Block : Label
        labels = dict() # Label : Block

        # Define blocks edges (jumps and labels)
        for i,b in enumerate(blocks):
            jumps[b] = [] # Make some ops easier
            first = b.get_inst(0)
            last = b.get_inst(-1)

            # Save blocks that can be jumped to
            if self.is_target(first[0]):
                # Either a define or a label
                if first[0]=='define':
                    globs.add_succ(b) # Link header to function
                    b.add_pred(globs)
                else:
                    labels[first[0]] = b
            
            # Save where the block jumps to
            if self.is_branch(last[0]):
                if last[0]=="jump":
                    jumps[b] += [last[1][1:]]
                if last[0]=="cbranch":
                    jumps[b] += [last[2][1:], last[3][1:]]

            # Link Consecutive Blocks
            else:
                b.add_succ(blocks[i+1])
                blocks[i+1].add_pred(b)

        # Link successors and predecessors
        for pred in jumps:
            for label in jumps[pred]:
                succ = labels[label]
                pred.add_succ(succ)
                succ.add_pred(pred)

        return 

    def clean_cfg(self):
        ''' Uses a DFS search stargin from the global block to check
            which blocks are unreacheable, and removes then from the instance.
        '''
        # Removing unreachable blocks
        all_ids = list(range(1, 1 + self.blockID))
        reachable = [b.ID for b in self.dfs_sort()]
        dead = set(all_ids)-set(reachable)
        if dead: print(f"\nRemoving deadblocks: {dead}\n")
        for idx in dead:
            block = self.index[idx]
            block.delete()

    ### Exhibition Control ###

    def print_blocks(self):
        '''Prints the CGF aspect of the block and the instruction wise 
           genkill sets: Predecessors, instructions and successors
        '''
        dfs = self.dfs_sort()
        ids = []
        for block in dfs:
            print(block)
            ids.append(block.ID)
        
        print('DFS Sequence: ', ids)

    def print_sets(self):
        '''Prints block wise genkill accumulated sets and in-out sets'''
        txt = ''
        for b in self.dfs_sort():
            txt += b.show_sets()
        print(txt)

    def view(self):
        '''Uses graphviz to print the prgram's CFG'''
        blocks = self.index.items()
        graph = Digraph(comment='Control Flow Graph')
        graph.attr('node', shape='box',fontname="helvetica")

        # Create blocks
        for i,b in blocks: 
            txt = ''
            for lin,inst in b.instructions.items():
                txt += f"{lin:3}  {'  '.join(map(str,inst))}\l"
            graph.node(str(i),txt)

        # Connect blocks
        for i,b in blocks:
            for p in b.pred: graph.edge(str(p.ID),str(b.ID))

        # Show CFG
        graph.view()
