phl-budget
=========

An explorable budget visualization for the City of Philadelphia.

This is hastily copied / forked from the [ny-budget](https://github.com/datamade/ny-budget) by the amazing folks at [Datamade](https://datamade.us/).

## Building the data for Philly

The data build has been moved from within this app to the `/data` folder in the root directory. Run `ub run datamade.py` to build the `budget_finished.csv` file and copy it from `data/output/datamade` to `website/src/datamade/data/phl`. All other years must be run first.

## Running the site locally

As a temporary and ugly measure, the `datamade` directory has been hardcoded into the `js/settings.js` and `js/helpers/budget_helpers.js` files to facilitate viewing the site from a subdirectory.

To run / test locally, run a webserver (`python -m http.server`) in the `website/src` directory.