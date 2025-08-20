# Medical_Device_System_Designer
This website is my personal attempt to automate as much of the tasks that Medical Device System Designers are typically responsible for doing to release a product onto the market. My hope is that it will help System Designers everywhere to increase the amount of time they spend on the more engaging and challenging aspects of their roles. 

Tools that exist:
- None

Tools that are in the works:
- Product Characterization Literature Review Assistant
- Product Characterization MAUDE Analysis Assistant


## Product Characterization Pubmed Literature Review:
**One tab to import all free pdfs based on a Pubmed Search**

One Form that: 
- takes in 
    - Pubmed search csv file listing all pdfs
    - Focus Theme/Subject/Technology of the literature review
    - Inclusion/Exclusion criteria for papers
    - Future Dev: (Optional) Student access logins to journals 
- outputs:
    - List of papers that remain after applying the inclusion/exclusion criteria to the abstracts
    - zip file of all papers that could be downloaded for free
    - excel list of papers that are protected by a paywal that are relevant to the search

**Another tab to analyze the pdfs**
- Form that 
    - takes in:
        - List of papers that remain after applying the inclusion/exclusion criteria to the abstracts
        - zip file of all pdfs 
        - focus of the literature review (type of tech being compared to conventional surgery)
    - outputs:
        - Excel spreadsheet with lit review summary along with extra columns containing LLM details that should be reviewed by a human
        - aip file of all pdfs, (marked up by LLM?)


## Technical Stack
We are using Django and Deploying on Render. 
TailwindCSS version 4.1.12

## Reminders when deploying locally:
1. make sure that your PostgreSQL server is running:
> pgrep -l postgres

if it is not running, then run:
> brew services start postgresql

once running, access the PostgreSQL command line:
> psql -U postgres

To start the server locally with live TailwindCSS updates, in one terminal, run the following to start the tailwind watcher:
> python meddevmate/tailwind_watcher.py

Simultaneously in a separate terminal, run the following to launch the website:
> python manage.py runserver