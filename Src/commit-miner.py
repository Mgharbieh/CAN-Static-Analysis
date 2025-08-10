import json
import pydriller
import pydriller.git 
from sys import argv

FILE_PATH = argv[1]

CAN_RELATED_WORDS = [
                        "can", "canbus", "can-bus",
                        "baud", "baudrate",
                        "mcp",
                        "mask", "masks",
                        "filter", "filters",
                        "frame", "frames", "buffer", "framebuffer",
                        "dlc",
                        "id", "ids", #IDs, lowered to avoid case sensitivity
                        "RTR", "rtr",
                        "kbps",
                        "packet", "packets",
                        "byte", "bytes"
                    ]

def search_for_fix(searchFile, outputFile):

    jsonList = []
    problematicRepos = []

    with open((FILE_PATH + searchFile), "r") as file:
        filteredData = json.load(file)

    reposToProcess = filteredData["repos"]

    for repo in reposToProcess:
        
        searched_projects = []
        
        commitList = []
        name = repo["name"]

        if(name not in searched_projects):
            print(f"checking commits for repository: {name}\n")
            totalCommits = 0
            try: 
                for commit in pydriller.Repository(repo["URL"]).traverse_commits():
                    totalCommits += 1
                    print(f"checking commit {commit.hash}...\n")
                    message =   str(commit.msg).lower()
                    message = message.split()
                    if "fix" in message or "fixed" in message:
                        commitDict = {"hash":commit.hash, "author":commit.author.name, "message":commit.msg}
                        commitList.append(commitDict.copy())
            except pydriller.git.GitCommandError:
                print(f"Problematic Repo: {name}, check mannually!")
                problematicRepos.append(name)
                continue

            if(len(commitList) > 0):
                dataDict = {"repo":repo["name"], "URL":repo["URL"], "num-total-commits":totalCommits, "num-fix-commits":len(commitList), "fix-commits":commitList.copy()}
            else:
                dataDict = {"repo":repo["name"], "URL":repo["URL"], "num-total-commits":totalCommits, "num-fix-commits":0, "fix-commits":"None Found"}
            
            jsonList.append(dataDict.copy())
            print("total commits: ", totalCommits)
            print("\n\n")
            searched_projects.append(name)

    jsonDict = {"results":jsonList, "require-review":problematicRepos}
    with open((FILE_PATH + outputFile), "w") as file:
        json.dump(jsonDict, file, indent=4)

def contains_fix_and_CAN(searchFile, outputFile):

    jsonList = []
    total = 0
    totalRepos = 0

    with open((FILE_PATH + searchFile), "r") as file:
        data = json.load(file)

    repoList = data["results"]

    for repo in repoList:

        count = 0
        CANcommitList = []

        name = repo["repo"]
        print(f"checking repository: {name}...\n")

        if(repo["num-fix-commits"] > 0):
            
            commitList = repo["fix-commits"]
            for commit in commitList:
                
                if(CANrelatedCheck(commit) == True):
                    count += 1
                    CANcommitList.append(commit)

            if(len(CANcommitList) > 0):
                total += len(CANcommitList)
                totalRepos += 1
                dataDict = {"name":repo["repo"], "URL":repo["URL"], "num-total-commits":repo["num-total-commits"], "num-CAN-commits":len(CANcommitList), "CAN-commits":CANcommitList.copy()}
                jsonList.append(dataDict.copy())

    jsonDict = {"total-commit-messages":total, "total-repos":totalRepos, "results":jsonList}
    with open((FILE_PATH + outputFile), "w") as file:
        json.dump(jsonDict, file, indent=4)

def CANrelatedCheck(commit):
    text = commit["message"]
    text = text.lower().split()

    for word in text:
        if(word in CAN_RELATED_WORDS):
            return True
    
    return False

###########################################################################################################################
search_for_fix("repo-search-list.json", "week5_commit_messages.json")
contains_fix_and_CAN("week5_commit_messages.json", "large_scrape-CAN-Fixes.json")