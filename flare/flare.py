import json
import csv
from collections import defaultdict
import random

SORT_BY = '2026'

#NEST_KEYS = ['tag_peoples_budget', 'department', 'fund']
NEST_KEYS = ['fund', 'department', 'class']

INPUT_FILES = [
  {
    'fiscal_year': '2025',
    'path': '../data/output/FY2025-adopted.csv',
  },
  {
    'fiscal_year': '2026',
    'path': '../data/output/FY2026-adopted.csv',
  },
]

def construct_id(row, keys, max_index):
  id_parts = []
  for index in range(0, max_index+1):
    id_parts.append(row[keys[index]])
  return hash('|'.join(id_parts))

def nest(rows, keys, current_index=0, sort_by=None):
  key = keys[current_index]

  # Create the structure of what's returned
  grouped_rows = defaultdict(lambda: {
    'children': [],
    'gross_cost': {
      'accounts': defaultdict(int)
    }
  })

  # Group rows by the current key
  for row in rows:
    group_dict = grouped_rows[row[key]]
    group_dict['id'] = construct_id(row, keys, current_index)
    group_dict['name'] = row[key]
    group_dict['gross_cost']['accounts'][row['fiscal_year']] += int(row['total'])
    group_dict['children'].append(row)

  # For each grouping, recurse on its children until at last key
  for key, val in grouped_rows.items():
    if len(keys) > current_index + 1:
      val['children'] = nest(val['children'], keys, current_index=current_index + 1, sort_by=sort_by).values()
      if sort_by:
        val['children'] = sorted(val['children'], key=lambda row: -row['gross_cost']['accounts'][sort_by])
    else:
      del(val['children'])
  
  return grouped_rows

# Read files into one list of dicts
rows = []
for file in INPUT_FILES:
  with open(file['path'], 'rt') as file:
    rows = rows + list(csv.DictReader(file))

# Nest the list by list of keys recursively
nested_rows = nest(rows, NEST_KEYS, sort_by=SORT_BY).values()
nested_rows = sorted(nested_rows, key=lambda row: -row['gross_cost']['accounts'][SORT_BY])

print(json.dumps(nested_rows, indent=2, sort_keys=True))
