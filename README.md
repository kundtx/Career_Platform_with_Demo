# Career Platform with Demo

Welcome to the Career Platform! This project is designed to analyze Chinese resumes and extract important career relationships about the working experiences of each person, providing you with segmentation results and a career social network visualization. You can also try our demo on http://8.129.175.102/CareerMiner/

## Parts of Code

The system consists of several main components, including:

- `app`: This is the Vue application that serves as demo of the system. It handles the user input, sends it to the appropriate modules for processing and presents the results in a clear and concise manner.
- `Career_API`: This module handles interface between demo and backend algorithms.
- `Career_Platform`: Main part of the system. This module processes the text data, builds OCTree and extracts Career Social Network based on Neo4j.
- `runApp.py`: A simple script which helps turn on `Career_API`.
- `sample_resumes.txt`: Some sample data, the format needed for the demo's input.

## Installation and Running Steps

To run the Career Platform Demo, follow these steps:

1. Clone the repository to your local machine using `git clone https://github.com/kundtx/Career_Platform_with_Demo.git`.
2. Install the required libraries using `pip install -r requirements.txt`. A python environment with version 3.8.x is recommended.
3. Install and run the Neo4j database. Version 3.5.x is recommended.
4. Prepare `Career_Platform` by following these steps:
   1. Download the [chinese_L-12_H-768_A-12](https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip), convert tf checkpoints to pytorch, and put the folder in `Career_Platform\career_platform\algorithm\exp_parser\segment\ner\ckpts\ ` 
   2. execute `python career_platform\algorithm\exp_parser\segment\ner\bert.py` at the command line  
   3. execute `python career_platform\algorithm\exp_parser\segment\ner\parser.py` at the command line
5. Run the `Career_API` using `python runApp.py`.
6. Run the `app` using `npm run dev` under its folder.
7. Enjoy the demo:
   1. Open your web browser and navigate to `http://localhost:8080`.
   2. Enter a list of Chinese resumes separated by the `#` symbol, with each working experience listed on a separate line and the working period indicated at the beginning of each line in the format of `yyyy.mm-yyyy.mm`.
   3.  Click the "Start Analysis" button to analyze the resumes and view the results.
   4.  Click the "Synchronize Data" buttons under OCTree and CSN parts to view the corresponding visualizations.
