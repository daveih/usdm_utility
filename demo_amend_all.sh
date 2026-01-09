python ./update_excel.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example.xlsx /Users/daveih/Documents/$1/sdw_test/Other/xl_example.yaml
python ./excel_diff.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example.xlsx /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.xlsx
python ./from_excel.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.xlsx
python ./to_timeline.py /Users/daveih/Documents/$1/sdw_test/Other/xl_example_amended.json
python ./study_journey_visualizer.py /Users/daveih/Documents/python/sdw_test/Other/xl_example_amended_expansion.json
python ./player.py /Users/daveih/Documents/python/sdw_test/Other/xl_example_amended_expansion.json /Users/daveih/Documents/python/sdw_test/Other/xl_example_amended_expansion_player.html