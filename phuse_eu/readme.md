# SDW Overview

## Login

- u: phuse2025_hamburg@outlook.com
- p: CDISC_TcB_2025

## Data Pre Loaded

Three "study definitions" of the same study, the CDISC Pilot Study, LZZT

- M11 Word document (SoA is an image)
- M11 Word document with an SoA in a table
- Excel version. Hand built to reflect the protocol but as a result it has USDM structure

## Look at sources

- Add to chat
- Word
- Excel

## JSON Viewer

- Look at JSON viewer for M11 doc
- Search for "EligibilityCriterion_1"

## ToDiagram.com

- Load Excel JSON file
- You have to pay due to size of USDM files

## JSON Explorer

- Look at explorer for Excel
- Select EligibilityCriteria number 1
- Reference to a tag
- Go to the SyntaxTemplateDictionary
- Expand
- Find min_age
- Jump to the quantity
- Quantity 9 value is 50
- Expand to the unit ... Year

# M11 Export

- Export USDM v4 for the Word version
- Export the Excel version
- In the usdm_utility project:
    - python to_m11.py phuse_eu/M11_USDM.json
    - python to_m11.py phuse_eu/Excel_USDM.json
- From finder click on:
    - phuse_eu/Excel_USDM_criterion.html
    - phuse_eu/M11_USDM_criterion.html
- Note the underline italics on the excel version
    - Why is it there?
    - It is the structured data 

## Other Export / Reuse

- In the usdm_utility project:
    - python to_visit.py phuse_eu/Excel_USDM.json "Encounter_1"
    - The "Encounter_1" is a short cut, would not normally do this
- From finder slick on:
    - phuse_eu/Excel_USDM_visit.html
- Again, note the underline italics

## FHIR Export

- In SDW, export the FHIR Madrid version
- Explain the versions
- Examine the FHIR message in an editor
- Search for "resourceType": "Group"
- Note, no fields, been expanded before transmission
- FHIR does have a mechanism for structure, current UDP work is "aligning" these

## To Another Application

- Edit the word document:
    - phuse_eu/M11SoAn.docx
    - amend the identifer (+1)
- Load into SDW
- Export as USDM v3 Excel
- Load into Tech demonstrator
- Look at the SoA
- Look at TV
- IE not included

## Timeline

- If time
- Show the example phuse_eu/Excel_USDM_timeline.html
- Further example (not IE related) of using USDM strucured content

# Commands

## Timeline Export

- python to_timeline_d3.py phuse_eu/Excel_USDM.json

## Visit Export

- python to_visit.py phuse_eu/Excel_USDM.json "Encounter_1"

## M11 IE Export

- python to_m11.py phuse_eu/Excel_USDM.json
- python to_m11.py phuse_eu/M11_USDM.json
