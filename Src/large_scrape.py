##
#   Search for github repositories using keyword
#   "can bus"
##

import os
import requests
import json
import time
from sys import argv


print(os.getcwd())

FILE_PATH = argv[1]
jsonDict = {}

def search_github_gitlab_repos():

    total = 0

    #GitHub
    url = 'https://api.github.com/search/repositories'
    headers = {
        'Accept': 'application/vnd.github.v3+json',
    }
        
    jsonList = []
    
    print(f"\nSearching for: 'can bus'\n{'-'*50}")
    page = 1 

    counter = 0
    while page <= 74:
        jsonString = ""
        print(f"searching page {page}/167")
        params = {
            'q': 'can bus',
            'sort': 'stars',
            'order': 'desc',
            'per_page': 10,
            'page': page,
            'language':'C'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            jsonString += response.text
            jsonList.append(json.loads(jsonString))
        else:
            print(f"Error {response.status_code}: {response.text}")
        
        page += 1
        counter += 1
        if(counter == 9):
            print("delay - 90 seconds...")
            time.sleep(90)
            counter = 0

    page = 1 

    counter = 0
    while page <= 93:
        jsonString = ""
        print(f"searching page {page + 74}/167")
        params = {
            'q': 'can bus',
            'sort': 'stars',
            'order': 'desc',
            'per_page': 10,
            'page': page,
            'language':'C++'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            jsonString += response.text
            jsonList.append(json.loads(jsonString))
        else:
            print(f"Error {response.status_code}: {response.text}")
        
        page += 1
        counter += 1
        if(counter == 9):
            print("delay - 90 seconds...")
            time.sleep(90)
            counter = 0

    total += len(jsonList)
    jsonDict["github"] = jsonList.copy()
    print("Github search finished, searching GitLab...")

    #GitLab
    url = 'https://gitlab.com/api/v4/projects'
    headers = {
        'Accept': 'application/json'
        # 'PRIVATE-TOKEN': 'your_access_token_here'  # Optional: use your token to increase rate limits
    }
  
    jsonList = []
    page = 1
    print(f"\n Searching GitLab for: 'can bus'\n{'-'*50}")

    counter = 0
    while page <= 12:
        jsonString = ""
        print(f"searching page {page}/12\n")
        params = {
            'search': 'can bus',
            'per_page': 20,
            'page': page,
            'simple': True,  # Returns only basic project info
            'visibility': 'public'
        }

        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            if not data:
                print("No results found.")
            else:
                jsonString += response.text
                jsonList.append(json.loads(jsonString))
        else:
            print(f"Error {response.status_code}: {response.text}")
        
        page += 1
        counter += 1
        if(counter == 9):
            print("delay - 90 seconds...")
            time.sleep(90)
            counter = 0

    total += len(jsonList)
    jsonDict["gitlab"] = jsonList.copy()
    jsonDict["total"] = total
    print("Done! Saving...")

    with open((FILE_PATH + "canbus_repositories.json"), 'w') as file:
        json.dump(jsonDict, file, indent=4)
        
    return


#NEEDS TO BE REDONE
def extract_repo_links(input_file, output_file):
    
    jsonList = []
    dataDict = {}
    
    urlList = []
    counter = 0

    with open((FILE_PATH + input_file), 'r') as file:
        dataDump = json.load(file)

    with open((FILE_PATH + "already-checked.json"), 'r') as oldFile:
        oldDat = json.load(oldFile)
    
    for item in oldDat["repos"]:
        urlList.append(item["URL"])

    github = dataDump['github']
    for repoList in github:
        searchList = repoList["items"]
        for project in searchList:
            dataDict["site"] = "GitHub"
            dataDict["name"] = project["name"]
            dataDict["URL"] = project["clone_url"]

            #if(dataDict["URL"] not in urlList):
            jsonList.append(dataDict.copy())
            counter += 1


    gitlab = dataDump['gitlab']
    for repoList in gitlab:
        searchList = repoList
        for project in searchList:
            dataDict["site"] = "GitLab"
            dataDict["name"] = project["name"]
            dataDict["URL"] = project["http_url_to_repo"]

            #if(dataDict["URL"] not in urlList):
            jsonList.append(dataDict.copy())
            counter += 1
        
    with open((FILE_PATH + output_file), 'w') as file:
        jsonDict = {"total":len(jsonList), "repos":jsonList} 
        json.dump(jsonDict, file, indent=4)

    print(counter)    
    return
        
            
########################################################################################################
#search_github_gitlab_repos()
extract_repo_links("canbus_repositories.json", "repo-search-list.json")         