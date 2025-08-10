import pandas as pd
import pydriller
import subprocess
from sys import argv
from clang import cindex

import os
import stat

# READ EXEL, START WITH INDEXED LIST
#   (Make sure to verify names so as to not read duplicates of entire project)
#
# FIND A WAY TO HAVE PYDRILLER PARSE OVER EVERY FILE IN COMMIT AND READ C++ SOURCE CODE
# USE CLANG TO BUILD THE AST AND FIGURE OUT HOW TO STORE IT

FILE_PATH = argv[1] 
EXEL_FILE = argv[2]
GIT_PATH = argv[3] 
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

strList = []
def visit_node(node, level=0):
   
    indent = "—" * level
    strList.append(f"|{indent}{node.kind}: {node.displayname} (Line: {node.location.line}, Col: {node.location.column})\n")
    for child in node.get_children():
        visit_node(child, level + 1)
    
    '''
        # Process the current cursor (e.g., print its kind and display name)
        print("  " * level + f"Kind: {node.kind}, Display Name: {node.displayname},  Location: {node.location}")

        # Recursively visit children
        for child in node.get_children():
        visit_node(child, level + 1)
    '''
old_cloned_repo = ""
completed = []
ino_files = []
row_idx = 0
nameCount = 1
while(row_idx < 95): #95
    
    commitLink = dfs.iloc[row_idx]["Commit Link"]
    baseLink = commitLink[:18]
    modifiers = commitLink[19:].split('/')

    gitLink = baseLink + "/" + modifiers[0] + "/" + modifiers[1] + ".git"
    
    if(old_cloned_repo != GIT_PATH):

        while(os.listdir(GIT_PATH)):
            for object in os.listdir(GIT_PATH):
                filePath = os.path.join(GIT_PATH, object)
                if(os.path.isfile(filePath)):
                    os.remove(filePath)
                else:
                    rmtree(filePath)

        try:
            # Construct the git clone command
            # Using a list of arguments is generally safer than shell=True
            command = ["git", "clone", gitLink]
            if GIT_PATH:
                command.append(GIT_PATH)

            # Execute the command
            # check_call raises an exception if the command returns a non-zero exit code
            subprocess.check_call(command)

            print(f"Repository cloned successfully to: {GIT_PATH or 'current directory'}")
            old_cloned_repo = GIT_PATH
        except subprocess.CalledProcessError as e:
            print(f"Error cloning repository: {e}")
            print(f"Command: {' '.join(e.cmd)}")
            print(f"Return Code: {e.returncode}")
            print(f"Output: {e.output.decode('utf-8') if e.output else 'No output'}")
            print(f"Error Output: {e.stderr.decode('utf-8') if e.stderr else 'No error output'}")
        
    includeFlag = '-I' + GIT_PATH + "/" + modifiers[1]

    for commit in pydriller.Repository(gitLink, single=modifiers[-1].strip(), only_modifications_with_file_types=FILE_TYPES).traverse_commits():
        if(os.path.exists(FILE_PATH + modifiers[1] + "/") == False):
            os.mkdir(FILE_PATH + modifiers[1] + "/")
        
        for file in commit.modified_files:

            nameStr = modifiers[1] + '-' + file.new_path
            if(nameStr not in completed):

                inFile_Name = f"{FILE_PATH}{modifiers[1]}/{(nameCount):03}-ast.txt"
                nameCount += 1
                
                completed.append(nameStr)
                sourceCode = file.source_code
                
                if(file.new_path.endswith(".h")):
                    #tu = indexParser.parse(None, args=[includeFlag, '-ast-dump', file.new_path], unsaved_files=[(file.new_path, sourceCode)])
                    print(file.new_path, " is a C-style header")
                elif(file.new_path.endswith(".hpp")):
                    #tu = indexParser.parse(None, args=[includeFlag, '-ast-dump', file.new_path], unsaved_files=[(file.new_path, sourceCode)])
                    print(file.new_path, " is a C++-style header")
                elif(file.new_path.endswith(".c")):
                    #tu = indexParser.parse(None, args=[includeFlag, '-ast-dump', file.new_path], unsaved_files=[(file.new_path, sourceCode)])
                    print(file.new_path, " is a C source file")
                elif(file.new_path.endswith(".cpp")):
                    #tu = indexParser.parse(None, args=[includeFlag, '-ast-dump', file.new_path], unsaved_files=[(file.new_path, sourceCode)])
                    print(file.new_path, " is a C++ source file")
                elif(file.new_path.endswith(".ino")):
                    ino_files.append(nameStr)
                    print(f"Skipping {file.new_path}... (.ino files are not supported)")
                    continue
                else:
                    print(f"Skipping {file.new_path}... (unsupported file type)")
                    continue
                
                print()
                visit_node(indexParser.parse(None, args=[includeFlag, '-ast-dump', file.new_path], unsaved_files=[(file.new_path, sourceCode)]).cursor)
                with(open(inFile_Name, 'w') as inFile):
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


print(ino_files)
with(open((FILE_PATH + "_inoFiles"), 'w') as inFile):
    inFile.write(ino_files)
