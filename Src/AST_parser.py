import pandas as pd
import pydriller
from git import Repo
from clang import cindex

import os
import stat

# READ EXEL, START WITH INDEXED LIST
#   (Make sure to verify names so as to not read duplicates of entire project)
#
# FIND A WAY TO HAVE PYDRILLER PARSE OVER EVERY FILE IN COMMIT AND READ C++ SOURCE CODE
# USE CLANG TO BUILD THE AST AND FIGURE OUT HOW TO STORE IT

EXEL_FILE = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Data/verified-fixes-final.xlsx"
FILE_PATH = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/AST_parsing/"
GIT_PATH = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/AST_parsing/git"
FILE_TYPES = [".c", ".cpp", ".h", ".hpp"]

dfs = pd.ExcelFile(EXEL_FILE).parse("verified-fixes-fixed")

#parse data like this to get commit per row in sheet
#print(dfs.iloc[2]["Commit Link"])

indexParser = cindex.Index.create()

def rmtree(top): # Windows sucks 
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWRITE)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)      

def visit_node(node, level=0):
    # Process the current cursor (e.g., print its kind and display name)
    print("  " * level + f"Kind: {node.kind}, Display Name: {node.displayname},  Location: {node.location}")

    # Recursively visit children
    for child in node.get_children():
        visit_node(child, level + 1)

row_idx = 0 
while(row_idx < 1): #95
    
    commitLink = dfs.iloc[row_idx]["Commit Link"]
    baseLink = commitLink[:18]
    modifiers = commitLink[19:].split('/')

    gitLink = baseLink + "/" + modifiers[0] + "/" + modifiers[1] + ".git"
    Repo.clone_from(gitLink, GIT_PATH)
    includeFlag = '-I' + GIT_PATH

    for commit in pydriller.Repository(gitLink, single=modifiers[-1], only_modifications_with_file_types=FILE_TYPES).traverse_commits():
        for file in commit.modified_files:
            sourceCode = file.source_code
            
            if(file.new_path.endswith(".h")):
                tu = indexParser.parse(file.new_path, unsaved_files=[(file.new_path, sourceCode)])
                print(file.new_path, " is a C-style header")
            elif(file.new_path.endswith(".hpp")):
                tu = indexParser.parse(file.new_path, unsaved_files=[(file.new_path, sourceCode)])
                print(file.new_path, " is a C++-style header")
            elif(file.new_path.endswith(".c")):
                tu = indexParser.parse(file.new_path, unsaved_files=[(file.new_path, sourceCode)])
                print(file.new_path, " is a C source file")
            elif(file.new_path.endswith(".cpp")):
                tu = indexParser.parse(None, args=[includeFlag, file.new_path], unsaved_files=[(file.new_path, sourceCode)])
                print(file.new_path, " is a C++ source file")
            
            print()
            visit_node(tu.cursor)
            print("-" * 100)
    
    for object in os.listdir(GIT_PATH):
        filePath = os.path.join(GIT_PATH, object)
        if(os.path.isfile(filePath)):
            os.remove(filePath)
        else:
           rmtree(filePath)

    row_idx += 1
