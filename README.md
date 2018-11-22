# Obtaining German Physicians
* Read the specification PPT [part1](https://www.dropbox.com/s/npic7dqlknpvlqa/1german%20physician%20scraping%20crowdworker%20instructions.pptx?dl=0) or [part2](https://www.dropbox.com/s/mprf6rfxqm9quoh/2german%20physician%20scraping%20crowdworker%20instructions.pptx?dl=0) carefully. 
* You are responsible for either the first half (stored under the `half1` folder) or the second half (stored under the `half2` folder). Please only edit files that are in YOUR folder (except for this readme)
* In your folder you will find an INPUT folder and an OUTPUT folder. both are `.gitignore`-d. Please do NOT store large files on git. Instead, you can send us a link to your results (and temporary results) when uploaded to GDrive/Dropbox. 
* You might get gitlab notifications for commit comments. Please ensure that you regularly check the email these are delivered to, as we will mainly use gitlab for interaction with you (NOT the upwork chat)

## How to handle Questions / Issues
* If you have a question, do NOT use UpWork chat to ask it. Instead, please create [an issue on gitlab](https://gitlab.com/PeakData/external_datascience/german_physicians/issues/new). Assign `Michael Feldman` to the task, such that he gets a notification once you save. Describe the issue in-depth. 
* If you are blocked by an issue (you cannot proceed), and it is truly important, assign it the _Blocker_ label. 
* All discussion within an issue is handled through the [GitLab Board](https://gitlab.com/PeakData/external_datascience/german_physicians/boards). Once you are satisfied with an answer, please drag the issue to the _Waiting for integration into Readme_ Swimlane. 
* From most issues there is something to learn for the project. Every important detail of the project should be captured within THIS readme that you're looking at right now. (You can easily edit it directly in your browser using [this link](https://gitlab.com/PeakData/external_datascience/german_physicians/edit/master/README.md)


# Handled Questions / Issues
## Sample issue 23: Language
As discussed in task [put link to task here], Python should be used as the programming language of this job

## solved bayren without using selenium
I made some tests and I found that I didn't have to put a specialty, only a postal code, and I got for a postal code 500 results. 
Then I removed the lat long and I got a 1000 results and the message that was saying that there are 63000 entries.
Then I found that there is a parameter named resultCount and I placed it in the url and increased value of it.
So I found the solution is to crawl [this link](https://arztsuche.kvb.de/cargo/app/suchergebnisse.htm?hashwert=97f24e6c79d5c3c7ebedfb3e1f7de67&page=101&resultCount=65000). 


## solved bayren without using selenium
Here is the [result](https://www.dropbox.com/s/jh2s70nbnzuzm2r/result.zip?dl=0) for half1.


# Physician Scraper Installation Guide


## Installation


### Retrieve code
* `$ git clone https://gitlab.com/PeakData/external_datascience/german_physicians.git`

### Create virtual Environment
* `$ apt-get install python-pip`
* `$ pip install virtualenv`
* `$ virtualenv venv`

### Activate virtual Environment
* `$ source venv/bin/activate`

### Installation Packages
* `$ cd half1/physicians`
* `$ pip install -r requirements.txt`


## Run Spiders with command line
* `$ cd half1/physicians/physicians/spiders`
* `$ python runspider.py`