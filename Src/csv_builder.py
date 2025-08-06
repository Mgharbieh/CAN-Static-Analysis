import csv
import json

FILE_PATH = "//100.83.44.15/shared/Michael/UMich/Research/Static_Analysis_Research/Data/"
HEADER_ROW = ["Project", "Commit Author", "Commit Message", "Commit Link"]

def jsonToCSV(inputFile, outputFile):

    csvRows = []

    with open((FILE_PATH + inputFile), 'r') as inFile:
        data = json.load(inFile)

    projectList = data["results"]
    for project in projectList: 
        name = project["repo"]
        platform = str(project['URL'][8:14])
        print(platform)
        if(platform == "github"):
            platform = "GitHub"
        else:
            platform = "GitLab"

        for commit in project["commits"]:
            author = commit["author"]
            message = commit["message"]
            link = str(project['URL'][:-4]) + "/commit/" + commit["hash"]
            category = commit["category"]
            note = commit["note"]

            row = [platform, name, author, message, link, category, note]
            csvRows.append(row.copy())

    with open((FILE_PATH + outputFile), 'w', newline='', encoding="utf-8") as outFile:
        writer = csv.writer(outFile, delimiter=',')
        #writer.writerow(HEADER_ROW)
        writer.writerows(csvRows)

#########################################################################################################
jsonToCSV("verified-commits.json", "verified-fixes2.csv")
