import json
import ast
import pydriller
from sys import argv

FILE_PATH = argv[1]

def checkCommits(inputFile, outputFile):

    dataDict = {}
    jsonList = []
    verifiedCommits = []

    with open((FILE_PATH + inputFile), 'r') as inFile:
        data = json.load(inFile)

    with open((FILE_PATH + outputFile), 'r') as outFile:       #Used so that can stop and resume later, appending to file w/ proper formatting
        resultSet = json.load(outFile)

    search_entries = data["results"]
    jsonList = resultSet['results']

    repoTotal = resultSet["total-repositories"]
    commitTotal = resultSet["total-commits"]

    projectIDX = resultSet["proj-index"]
    commitIDX = resultSet["commit-index"]

    lastChecked = resultSet["results"]

    if(len(lastChecked) != 0):
        check = lastChecked[-1]
        next = search_entries[projectIDX]
        if(check["repo"] == next["name"]):
            verifiedCommits = check["commits"]
            lastChecked.pop()

    for i in range(projectIDX, len(search_entries)):
        
        project = search_entries[i]
        name = project["name"]
       
        #for commit in pydriller.Repository(project["URL"], ).traverse_commits():
        commits = len(project["CAN-commits"])
        for commitNum in range(commitIDX, commits):
            commitInfo = project["CAN-commits"][commitNum]
            for commit in pydriller.Repository(project["URL"], single=commitInfo["hash"]).traverse_commits():

                print(f"checking commit {commitNum + 1}/{commits} ({commit.hash}) [project-idx:{projectIDX} ({name})]")
                print(f"Github link: {project['URL'][:-4]}/commit/{commit.hash}")
                print("-"*100)

                message = str(commit.msg)
                message = ' '.join(message.split()[:3])
                if( message == "Merge pull request"):
                    print("skipping merge pull request...\n\n")
                    continue

                verified = ''
                while verified == '':
                    verified = input("Save as valid bugfix commit? (y/n): ")
                    if(verified == 'y'):
                        print("Adding commit to verified list...")
                        category = input("Bug type: ")
                        if(category == "Usage Error" or category == "Data Bug"):
                            note = input("Description of error/bug: ")
                            commitDict = {"hash":commit.hash, "author":commit.author.name, "message":commit.msg, "category":category, "note":note}
                        else:
                            commitDict = {"hash":commit.hash, "author":commit.author.name, "message":commit.msg, "category":category, "note":""}
                              
                        verifiedCommits.append(commitDict.copy())
                        commitTotal += 1
                        commitIDX += 1

                    elif(verified == 'n'):
                        print("No valid commit in file, checking next...")
                        commitIDX += 1

                    elif(verified == 'e'):
                        if(len(verifiedCommits) > 0):
                            dataDict = {"repo":project["name"], "URL":project["URL"], "commits":verifiedCommits.copy()}
                            jsonList.append(dataDict.copy()) 

                        jsonDict = {"total-repositories":repoTotal, "total-commits":commitTotal, "results":jsonList, "proj-index":projectIDX, "commit-index":commitIDX}
                        with open((FILE_PATH + outputFile), 'w') as file:
                            json.dump(jsonDict, file, indent=4) 
                        
                        exit(0)
                    
                    else:
                        verified = ''                    

                    print()

        if(len(verifiedCommits) > 0):
            dataDict = {"repo":project["name"], "URL":project["URL"], "commits":verifiedCommits.copy()}
            jsonList.append(dataDict.copy())   
            repoTotal += 1

        projectIDX += 1
        commitIDX = 0

        verifiedCommits = []

    jsonDict = {"total-repositories":repoTotal, "total-commits":commitTotal, "results":jsonList, "proj-index":projectIDX, "commit-index":commitIDX}
    with open((FILE_PATH + outputFile), 'w') as file:
        json.dump(jsonDict, file, indent=4)

    print("Done!\n\n")

def randomCheck(inputFile, outputFile, randFile):

    dataDict = {}
    jsonList = []
    verifiedCommits = []

    with open((FILE_PATH + randFile), 'r') as rFile:
        searchList = rFile.read()
    
    searchList = searchList.split('|')

    with open((FILE_PATH + inputFile), 'r') as inFile:
        data = json.load(inFile)

    with open((FILE_PATH + outputFile), 'r') as outFile:       #Used so that can stop and resume later, appending to file w/ proper formatting
        resultSet = json.load(outFile)

    search_entries = data["results"]
    jsonList = resultSet['results']

    existingRepos = []
    existingDatabase = {}
    for i in range(0, len(jsonList)):
        item = jsonList[i]
        existingRepos.append(item['repo'])
        existingDatabase[item['repo']] = i #index of repo
        

    repoTotal = resultSet["total-repositories"]
    commitTotal = resultSet["total-commits"]

    projectIDX = resultSet["proj-index"]
    commitIDX = resultSet["commit-index"]

    searchPoolIDX = resultSet["random-index"]

    for i  in range (searchPoolIDX, len(searchList)):

        newSearchIDX = i

        entry = searchList[i]
        entry = ast.literal_eval(entry)
        project = search_entries[entry[0]]
        name = project["name"]
       
        comList = project["CAN-commits"]
        selectedCommit = comList[entry[1]]
        hashCode = selectedCommit["hash"]

        print(f"checking commit {i + 1}/300 ({entry}) | ({hashCode}) (project name: {name})")
        print(f"Github link: {project['URL'][:-4]}/commit/{hashCode}")
        print("-"*100)

        message = str(selectedCommit["message"])
        message = ' '.join(message.split()[:3])
        if( message == "Merge pull request"):
            print("skipping merge pull request...\n\n")
            continue

        verified = ''
        while verified == '':
            verified = input("Save as valid bugfix commit? (y/n): ")
            if(verified == 'y'):
                print("Adding commit to verified list...")
                category = input("Bug type: ")
                if(category == "Usage Error" or category == "Data Bug"):
                    note = input("Description of error/bug: ")
                    commitDict = {"hash":selectedCommit["hash"], "author":selectedCommit["author"], "message":selectedCommit["message"], "category":category, "note":note}
                else:
                    commitDict = {"hash":selectedCommit["hash"], "author":selectedCommit["author"], "message":selectedCommit["message"], "category":category, "note":""}
                        
                verifiedCommits.append(commitDict.copy())
                commitTotal += 1
                #commitIDX += 1

            elif(verified == 'n'):
                print("No valid commit in file, checking next...")
                #commitIDX += 1

            elif(verified == 'e'):
                if(len(verifiedCommits) > 0):
                    if(project["name"] not in existingRepos):
                        dataDict = {"repo":project["name"], "URL":project["URL"], "commits":verifiedCommits.copy()}
                        jsonList.append(dataDict.copy())   
                        repoTotal += 1
                    else:
                        dataDict = jsonList.pop([existingDatabase[project["name"]]])
                        existingCommitList = dataDict["commits"]
                        existingCommitList += verifiedCommits
                        dataDict["commits"] = existingCommitList.copy()
                        jsonList.append(dataDict.copy())                

                jsonDict = {"total-repositories":repoTotal, "total-commits":commitTotal, "results":jsonList, 
                            "proj-index":projectIDX, "commit-index":commitIDX, "random-index":newSearchIDX}
                
                with open((FILE_PATH + outputFile), 'w') as file:
                    json.dump(jsonDict, file, indent=4) 
                
                exit(0)
            
            else:
                verified = ''                    

            print()

        if(len(verifiedCommits) > 0):
            if(project["name"] not in existingRepos):
                dataDict = {"repo":project["name"], "URL":project["URL"], "commits":verifiedCommits.copy()}
                jsonList.append(dataDict.copy())   
                repoTotal += 1
            else:
                existingIDX = existingDatabase[project["name"]]
                dataDict = jsonList.pop(existingIDX)
                existingCommitList = dataDict["commits"]
                existingCommitList += verifiedCommits
                dataDict["commits"] = existingCommitList.copy()
                jsonList.append(dataDict.copy())                

        verifiedCommits = []

    jsonDict = {"total-repositories":repoTotal, "total-commits":commitTotal, "results":jsonList, "proj-index":projectIDX, "commit-index":commitIDX}
    with open((FILE_PATH + outputFile), 'w') as file:
        json.dump(jsonDict, file, indent=4)

    print("Done!\n\n")
        



def recount(inputFile):
    
    with open((FILE_PATH + inputFile), 'r') as file:
        data = json.load(file)
       
    repoCount = 0
    commitCount = 0   
     
    checklist = data["results"]
    for item in checklist:
        repoCount += 1
        commitCount += len(item["CAN-commits"])
    
    data["total-commit-messages"] = commitCount
    data["total-repos"] = repoCount
    
    with open("large_scrape-CAN-Fixes-2.json", 'w') as outFile:
        json.dump(data, outFile, indent=4)
    

#########################################################################################################
#checkCommits("large_scrape-CAN-Fixes.json", "verified-commits.json")
randomCheck("large_scrape-CAN-Fixes.json", "verified-commits.json", "search-pool.txt")

