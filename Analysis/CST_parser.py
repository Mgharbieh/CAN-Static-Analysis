import os
import pandas as pd
import pydriller
import tree_sitter as TreeSitter
from sys import argv

import tree_sitter_c as _C
import tree_sitter_cpp as _CPP

FILE_PATH = argv[1]
EXEL_FILE = argv[2]
FILE_TYPES = [".c", ".cpp", ".h", ".hpp"]

C_LANGUAGE = TreeSitter.Language(_C.language())
CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

dfs = pd.ExcelFile(EXEL_FILE).parse("verified-fixes-fixed")

strList = []
def visit_node(node, level=0):
   
    indent = "—" * level
    if node.type != "translation_unit" and node.type != "comment":
        strList.append(f"|{indent}Node:{node.type} Text: {node.text.decode()}\n")
    else:
       strList.append(f"|{indent}Node:{node.type}\n")
    for child in node.children:
        visit_node(child, level + 1)


completed = []
row_idx = 68
nameCount = 105
while(row_idx < 95): #95
    commitLink = dfs.iloc[row_idx]["Commit Link"]
    baseLink = commitLink[:18]
    modifiers = commitLink[19:].split('/')

    if modifiers[1] != "BlueGenieBMW":

        gitLink = baseLink + "/" + modifiers[0] + "/" + modifiers[1] + ".git"

        for commit in pydriller.Repository(gitLink, single=modifiers[-1].strip(), only_modifications_with_file_types=FILE_TYPES).traverse_commits():
            if(os.path.exists(FILE_PATH + modifiers[1] + "/") == False):
                os.mkdir(FILE_PATH + modifiers[1] + "/")
            
            for file in commit.modified_files:
                
                try:
                    nameStr = modifiers[1] + '-' + file.new_path
                except TypeError:
                    continue

                if(nameStr not in completed):

                    inFile_Name = f"{FILE_PATH}{modifiers[1]}/{(nameCount):03}-cst.txt"
                    nameCount += 1
                    
                    completed.append(nameStr)
                    sourceCode = file.source_code
                    
                    if(file.new_path.endswith(".h")): # pyright: ignore[reportOptionalMemberAccess]
                        print(file.new_path, " is a C-style header")
                        parser = TreeSitter.Parser(C_LANGUAGE)
                    elif(file.new_path.endswith(".hpp")): # pyright: ignore[reportOptionalMemberAccess]
                        print(file.new_path, " is a C++-style header")
                        parser = TreeSitter.Parser(CPP_LANGUAGE)
                    elif(file.new_path.endswith(".c")): # pyright: ignore[reportOptionalMemberAccess]
                        print(file.new_path, " is a C source file")
                        parser = TreeSitter.Parser(C_LANGUAGE)
                    elif(file.new_path.endswith(".cpp")): # pyright: ignore[reportOptionalMemberAccess]
                        print(file.new_path, " is a C++ source file")
                        parser = TreeSitter.Parser(CPP_LANGUAGE)
                    else:
                        #.ino Files not supported, most should be easy to do by hand though
                        print(f"Skipping {file.new_path}... (unsupported file type)")
                        continue
                    
                    print()
                    tree = parser.parse(bytes(sourceCode, "utf8"))
                    RootCursor = tree.root_node
                    visit_node(RootCursor)
                    with(open(inFile_Name, 'w', encoding='utf-8') as inFile):
                        inFile.write(nameStr)
                        inFile.write('\n\n')
                        for line in strList:
                            inFile.write(line)
                    
                    print(f"done with file: {nameStr}")
                    strList = []   
                else:
                    print(f"{file.new_path} already exists, skipping duplicate...")
                
                print("—" * 100)

    row_idx += 1