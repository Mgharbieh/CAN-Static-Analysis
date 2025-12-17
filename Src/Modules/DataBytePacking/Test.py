import os
import tree_sitter as TreeSitter
import tree_sitter_cpp as _CPP
import DataByte_Analyzer as DataByteAnalyzer

CPP_LANGUAGE = TreeSitter.Language(_CPP.language())

FOLDER = r"C:\Users\seren\OneDrive\Desktop\CAN_bus_research\Src\Modules\DataBytePacking\Test_Cases"
analyzer = DataByteAnalyzer.DataBytePackingAnalyzer()

for item in sorted(os.listdir(FOLDER)):
    if item.startswith("test_"):
        path1 = os.path.join(FOLDER, item)


        print("_" * 100)
        print(f"Testing {item[5:]}\n")

        for file in sorted(os.listdir(path1)):
            if file.endswith(".ino") or file.endswith(".cpp"):
                print(f"Test: {file}")
                path2 = os.path.join(path1, file)

                with open(path2, "r", encoding="utf-8", errors="ignore") as f:
                    src = f.read()

                parser = TreeSitter.Parser(CPP_LANGUAGE)
                tree = parser.parse(bytes(src, "utf8"))
                root = tree.root_node

                analyzer.checkDataPack(root)
                print()
