# Phila Budget Data Parsing

This folder contains scripts to parse PDF data stored in the `input` folder to create CSV versions of the Philadelphia budget in the `output` folder.

The output csv files are used in the `openbudget` visualization in the website folder.

The `datamade.py` creates a longitudal budget view from the `output` csv files and the `input/descriptions.csv` file to create the `output/datamade/budget_finished.csv` file for the datamade visualization.

The `tagging.yml` file is used to add categories to the budget expenditures to see where budget data is spent by category instead of just by fund.

To process all of the data run `uv run run-budget-data.py`.
