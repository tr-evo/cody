# Cody

This repository contains the Cody artifact as presented in the publication *Cody: An AI-Based System to Semi-Automate Coding for Qualitative Research* (https://dl.acm.org/doi/10.1145/3411764.3445591). The repository is maintained only sporadically at the moment. Please feel free to report issues, ideas, and bugs in the issues list or via email to tim.rietz(at)kit.edu. 

This repository is licenced under Creative Commons BY-NC. This means you are free to remix, adapt, and build upon this repository non-commercially, as long as you credit the original publication (see below). 

![CC BY-NC](https://licensebuttons.net/l/by-nc/3.0/88x31.png "CC BY-NC"). 

Preferred citation
> Tim Rietz and Alexander Maedche. 2021. Cody: An AI-Based System to Semi-Automate Coding for Qualitative Research. Proceedings of the 2021 CHI Conference on Human Factors in Computing Systems. Association for Computing Machinery, New York, NY, USA, Article 394, 1–14. DOI:https://doi.org/10.1145/3411764.3445591

## Project setup
Cody runs on Vue on the front end and python on the back end. Follow the following steps to set up and run the front end locally.

```
npm install
```

### Compiles and hot-reloads for development
```
npm run serve
```

### Compiles and minifies for production
```
npm run build
```

### Run backend
I'd recommend you set up a virtual env for python first. Then, install the relevant requirements: 

```
pip install -r requirements.txt
```

In the *server* folder, run:

```
python appserver.py
```


## Using the Cody artifact
Currently (July 12st, 2021), I am hosting the latest master at http://217.160.57.62/#/login. You can register with a user name / email and a password of your choosing (stored as a SHA-256 hash) and use the artifact as you like.

### Data upload
Use the *New* button to upload a new document. You can provide a name and select a document from your system. The most relevant information for you will be regarding (3) the document settings.

For type of document select *Text* to upload a .txt file. There are no special requirements for .txt files. The document will be split on a per-sentence level.

For .csv files, in particular for interviews that follow the laddering interview technique (or for documents that can be grouped into interviews and topics), use the *Laddering* document type. This type requires .csv documents in the following shape. However, your .csv should not contain a table head.

| Interview ID | Topic/Attribute | One Sentence each |
| ------------- |:-------------:| -----:|
| Peter | Motivation | Interview Sentence #1 |
| Peter | Motivation | Interview Sentence #2 |
| Peter | Learning | Interview Sentence #1 |
| Kat | Motivation | Interview Sentence #1 |

### Data export
Currently, no dedicated export functionality is implemented in Cody. If you use Cody for your work, you should host it on your system to access the database directly. If you use the online version and require an export of your data, let me know. 

There is an "advanced" analysis branch with improved front-end-based analysis functionality for your coding / your data already. However, I have yet to merge it into the master (and live) branch.
