import json
import random

FILE_PATH = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Data/"

def randomSelect(inputFile, outputFile):
    
    searchList = []

    with open((FILE_PATH + inputFile), 'r') as inFile:
        data = json.load(inFile)

    selectionPool = data['results']
    lowerBound = 9
    upperBound = len(selectionPool) - 1
    count = 0

    while(count <= 300):
        repoIDX = random.randint(lowerBound, upperBound)
        commitPool = selectionPool[repoIDX]["CAN-commits"]

        commitBound = len(commitPool) - 1
        commitIDX = random.randint(0, commitBound)

        searchPair = (repoIDX, commitIDX)
        if(searchPair not in searchList):
            searchList.append(searchPair)
            count += 1
    
    print(len(searchList))
    parseString = ""
    for entry in searchList:
        parseString += (str(entry) + ',')
    
    with open((FILE_PATH + outputFile), 'w') as outFile:
        outFile.write(parseString)
    
####################################################################
randomSelect("large_scrape-CAN-Fixes.json", "search-pool.txt")