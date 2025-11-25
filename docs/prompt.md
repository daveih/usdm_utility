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
