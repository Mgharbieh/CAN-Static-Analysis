import pydriller

gitLink = "https://github.com/Seeed-Studio/Seeed_Arduino_CAN.git"
hash = "43d936ddf3132b91e2970fc63a98ed493cce5ee9"
FILE_TYPES = [".c", ".cpp", ".h", ".hpp"]

for commit in pydriller.Repository(gitLink, hash, only_modifications_with_file_types=FILE_TYPES).traverse_commits():
     for file in commit.modified_files:
        sourceCode = file.source_code
        print(sourceCode)
         