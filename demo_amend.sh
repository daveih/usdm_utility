python ./update_excel.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example.xlsx /Users/daveih/Documents/$1/sdw_test/Other/xl_example.yaml
python ./excel_diff.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example.xlsx /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.xlsx
python ./from_excel.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.xlsx
python ./to_timeline.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.json
