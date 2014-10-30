"""
A script to calculate revision information for a wikipedia article.  It queries 
the API and then creates two csv files.

There's no GUI or command line interface, so if you want to search for a different
article, you need to change the article variable below.  You can alter the API
parameters by modifying the payload paramters.

Revisions.csv contains the following information for each edit:
- revision id
- username
- article size after edit (bytes)
- change in article size from edit (bytes)
- time of edit (seconds from first edit)
- time since last edit (seconds)
- URL to view diff on wikipedia.org
- comments associated with the edit

EditorFrequency.csv contains:
- username
- number of edits by user
- percentage of total edits made by user

External Dependencies:
- requests
"""

from collections import defaultdict
import datetime
import json
import time
import os

import requests




# Parameters for the wiki API request
locale = "en"
article = "Monsanto"
payload = {"prop":"revisions", "titles":article, "continue":"",
			"rvprop":"ids|timestamp|user|comment|size", 
			"rvdir":"newer", "rvlimit":"max"}





def createDatetimeFromTimestamp(timestamp):
	# Timestamp is ISO 8601: 
	#	YYYY-MM-DDTHH:MM:SSZ where T separates date from time and Z stands for UTC
	# Ex: 2001-11-03T13:19:06Z
	if timestamp[-1] == "Z": timestamp = timestamp[:-1]
	date, time = timestamp.split("T")
	year, month, day = [int(x) for x in date.split("-")]
	hours, minutes, seconds = [int(x) for x in time.split(":")]
	dt = datetime.datetime(year, month, day, hours, minutes, seconds)
	return dt

def calculateElapsedSeconds(datetime1, datetime2):
	# Uses datetime objects
	return (datetime2-datetime1).total_seconds()

def query(locale, request):
	# This function is an iterator for the API request
	request['action'] = 'query'
	request['format'] = 'json'
	lastContinue = {'continue': ''}
	baseURL = "http://" + locale + ".wikipedia.org/w/api.php?"
	while True:
		# Clone original request
		req = request.copy()
		# Modify it with the values returned in the 'continue' section of the last result.
		req.update(lastContinue)
		# Call API
		result = requests.get(baseURL, params=req).json()
		if 'error' in result: raise Error(result['error'])
		if 'warnings' in result: print(result['warnings'])
		if 'query' in result: yield result['query']
		if 'continue' not in result: break
		lastContinue = result['continue']

# Check and create data paths
pathToRevisionFolder = os.path.join(".", "RevisionData")
if not(os.path.isdir(pathToRevisionFolder)):
	os.mkdir(pathToRevisionFolder)
articleFolderName = article.replace(" ", "_")
pathToRevisionData = os.path.join(".", pathToRevisionFolder, articleFolderName)
if not(os.path.isdir(pathToRevisionData)):
	os.mkdir(pathToRevisionData)

# Prep the data file with a header
csv = open(os.path.join(pathToRevisionData, "Revisions.csv"), "w")
csv.write("Data pulled on {0}\n".format(time.strftime("%m/%d/%Y at %H:%M:%S")))
header = "revision id, username, article size after edit (bytes),"\
		 +"change in article size from edit (bytes), "\
		 +"time of edit (seconds from first edit),"\
		 +"time since last edit (seconds), URL to view diff, "\
		 +"comments associated with edit\n"
csv.write(header)

# Initialize a frequency distribution to count editor contributions
editorFreq = defaultdict(lambda:0)

# Loop variables
totalEdits = 0
lastSize = 0
firstTime = None
lastTime = None

# Process the request
for result in query(locale, payload):
	for page in result["pages"]: 
		pageRevisions = result["pages"][page]["revisions"]
		for revision in pageRevisions:

			# Get the user
			user = revision["user"].encode("utf-8")	
			editorFreq[user] += 1

			# Get the comment for the edit
			# Leaving a comment is optional when editing wiki
			comment = ""
			if "comment" in revision: 
				comment = revision["comment"].encode("utf-8")
			
			# Process the timing of the edit
			timestamp = revision["timestamp"]
			dt = createDatetimeFromTimestamp(timestamp)
			if firstTime == None: firstTime = dt
			if lastTime == None: lastTime = dt
			elapsedSeconds = calculateElapsedSeconds(firstTime, dt)
			deltaSeconds = calculateElapsedSeconds(lastTime, dt)
			
			# Get some useful ids for the edit
			# Use it to build a url that can be used to view the diff for the edit
			revid = revision["revid"]
			parentid = revision["parentid"]
			url = "https://{0}.wikipedia.org/w/index.php?title={1}".format(locale, article.replace(" ", "_"))
			url += "&diff={0}".format(revid)
			url += "&oldid={0}".format(parentid)

			# Process the size information about the edit
			size = revision["size"]
			sizeChange = size - lastSize

			# Write the info to the csv file
			line = "{0},{1},{2},{3},{4},{5},{6},{7}\n".format(revid, user, 
														  	  size, sizeChange,
														  	  elapsedSeconds,
														  	  deltaSeconds,
														  	  url, comment)
			csv.write(line)

			# Update loop variables
			lastSize = size
			lastTime = dt
			totalEdits += 1
csv.close()

# Save out a frequency distribution for editors
sortedKeys = sorted(editorFreq, key=lambda key: editorFreq[key], reverse=True)
with open(os.path.join(pathToRevisionData, "EditorFrequency.csv"), "w") as fh:
	fh.write("Data pulled on {0}\n".format(time.strftime("%m/%d/%Y at %H:%M:%S")))
	fh.write("username, number of edits, percent of total edits\n")
	for key in sortedKeys: 
		freq = editorFreq[key]
		line = "{0},{1},{2}\n".format(key, freq, freq/float(totalEdits))
		fh.write(line)