Using the D3 graphic library, write a single web page to be included within an exisitng python/jinja2 application that display USDM (Unified Study Definitions Model) v4 compliant JSON files allowing a user to explore the data:

- USDM v4 schema
    - Defines a serialization of a model
    - File is here "/Users/daveih/Documents/github/DDF-RA/Deliverables/API/USDM_API.json"
    - Note the convention of Id and Ids suffixes on the attributes
        - Used to prevent the duplication of content in the serialization
        - Id is used for singleton instance references
        - Ids is ised for multiple instance references
- Example files
    - /Users/daveih/Documents/github/usdm_data/source_data/protocols/EliLilly_NCT03421379_Diabetes/EliLilly_NCT03421379_Diabetes.json
    - /Users/daveih/Documents/github/usdm_data/source_data/protocols/EliLilly_NCT03421379_Diabetes/EliLilly_NCT03421379_Diabetes.json
- The web page will be provided with a python dict 
    - keyed by class containing each instance of the class and its child classes
    - The child classes will not contain the Id and Ids instances
- The web page should 
    - Allow for a user to select an instance of a class
    - Display that instance (and only that instance)
        - Don't display sub classes
        - Don't display Id and Ids instances
        - Display the simple type attributes and links for the other (child clases and id and ids attributes)
        - Display in a style similar to the attached image
    - Allow the user to expand by clicking on attributes that have linked instances
        - In response expand the display to include the instances selected

----- + -----

Take the utility program to_visit.py and update the HTML presentation aspects to:
- Use the bootstrap theme from here "https://bootswatch.com/zephyr/" 
- Make the presentation more modern and compact

----- + -----

In the text there can be two forms of embedded XML:
- <usdm:tag name="StudyPopulation"/>
- <usdm:ref attribute="text" id="StudyTitle_2" klass="StudyTitle"></usdm:ref>

----- + -----

Write a python program to generate an html page that can be viewed in a browser that contains a data vizualization.

- The vizualiation should be a serpentine timeline of the data in a json file
- Use the D3 graphic library, write a single web page to be included within an exisitng python/jinja2 application
- There is a simplified schema in the file pj/data_v2.json
- There are example files called pj_p<n>.json
- The web page will be provided with a python dict as per the json files

----- + -----

Now write an equivalent program to display each visit as a separate diagram withn an html page that can be viewed in a browser that contains a data vizualization.

- Use the D3 graphic library
- Style with bootstrap 5
- The vizualiation should be a serpentine timeline of each visit and the activities as per the data data in a json file
- Display every visit down the html page as a bootstrap card
- There is a simplified schema in the file pj/data_v2.json
- There are example files called pj_p<n>.json
- The web page will be provided with a python dict as per the json files
- Put the code into a file called to_pj.py

----- + -----

Update the readme.md file with details for the to_text.py program. Add the readme to the exisitng readme.md file. There is a level 1 section listing the utility programs and then add a new level 1 section at the end containing the details fro the program

----- + -----

Write a python program to generate an html page that can be viewed in a browser that contains a data vizualization.

- The vizualiation should be a vertical timeline of the data in a json file
- Use the D3 graphic library, write a single web page to be included within an exisitng python/jinja2 application
- The source data in a JSON file here /Users/daveih/Documents/github/usdm4/tests/usdm4/test_files/expander/expander.json
- In the data there is a single key "nodes" which is an array of entries
- The web page will be provided with a python dict as per the json files
- Display the nodes in the order they appear in the array
- Display the "time" and "label" attributes
- Make the "encounter" and "activities" attributes a hover over feature
- There is a similar program in to_pj.py
- Call the new program to_expanded.py

----- + -----

Write a python program to generate an html page that can be viewed in a browser that contains a data vizualization.

- The vizualiation should be a vertical timeline of the data in a json file
- Use the D3 graphic library, write a single web page to be included within an exisitng python/jinja2 application
- The source data in a JSON file here /Users/daveih/Documents/github/usdm4/tests/usdm4/test_files/expander/expander.json
- In the data there is a single key "nodes" which is an array of entries
- The web page will be provided with a python dict as per the json files
- Display the nodes in the order they appear in the array
- Display the "time" and "label" attributes
- Make the "encounter" and "activities" attributes a hover over feature
- There is a similar program in to_pj.py
- Call the new program to_expanded.py

----- + -----

Write a python program to generate an html page that can be viewed in a browser that contains a data vizualization.

- The visulization should play a JSOn file
- The file represents the main events of a clincial trial
- the file is ordered chronologically
- I want to be able the play through the trial in high speed, go forward and back like a video player
- The source data in a JSON file here /Users/daveih/Documents/python/usdm4/tests/usdm4/test_files/expander/expander.json
- There is an exisitng program that displays the data as a vertical timeline here "to_expanded.py"
- Call the new program player.py

----- + -----

Write a python program that will take an exisitng Excel workbook and update it according to the contents of a yaml file. The utility should be called update_excel.py. The program should be able:

- For an exisitng sheet in the existing workbook
  - Define which sheet
  - Add rows
  - Update cells
- Insert an entirely new sheet into the existing workbook
  - Specifiy the sheet name
  - Add rows

When a cell is updated the cell background colour should be set to a light orange color
When a sheet is updated the sheet tab should be set to the same light orange color
When a cell in added the cell background should be set to a light green color
WHen a sheet in added the sheet tab should be set to the same light green color

The update workbook should be written to a new file with the filename based on the filename of the input file (suffix with "amended")

----- + -----

Write a python program to generate an html page that can be viewed in a browser that contains the difference between two excel workbooks

The program should only compare content and not formatting. The workbooks are expected to be similar. So the utility should 

- Compare sheets of the same name. 
- Display each sheet comparison as a single tab on the web page
- The tab should contain a grid reflecting the content of the source excel sheet
- Cells containing different values should be highlighted in a github diff style for changes.
- Deleted row or columns should be highlighed in red is a github style similar to a deleted line
- Use bootstrap 5 and this theme to style the web page https://bootswatch.com/cosmo/
- The program should be called excel_diff.py
