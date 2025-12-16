import os
import dlc_analyzer as DlcAnalyzer

TEST_PATH = "/Users/moeab/Desktop/CAN_bus_research-main/Src/Modules/DataLength/Test_Cases2/"
analyzer = DlcAnalyzer.DataLengthAnalyzer()

for item in sorted(os.listdir(TEST_PATH)):
    if not item.startswith("test"):
        continue

    path1 = os.path.join(TEST_PATH, item)
    if not os.path.isdir(path1):
        continue

    print("_" * 100)
    print(f"Testing {item}\n")

    found = False
    for dirpath, _, filenames in os.walk(path1):
        for file in sorted(filenames):
            if file.endswith((".ino", ".cpp")):
                found = True
                path2 = os.path.join(dirpath, file)
                print(f"Test: {os.path.relpath(path2, path1)}")
                analyzer.checkDlc(path2)
                print()

    if not found:
        print(f"[WARN] No .ino/.cpp files found anywhere under: {path1}\n")