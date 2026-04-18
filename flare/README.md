# flare

This Generates d3 flare.json used by [open-budget](https://github.com/cityofphiladelphia/open-budget)

 ## NOTE
This is copied from https://github.com/CityOfPhiladelphia/open-budget-data-transformer/tree/master/flare which focused on 2017 - 2019 data. This is focused on data after 2025. The old repo is archived, and the data is similar but easier to start fresh.


## Usage
Configure `INPUT_FILES` at the top of `flare.py` and run:
```sh
python flare.py > data.json
```
Copy the generated `data.json` file into the `open-budget` application directory at `src/data/phl/`

Configure the application to use the `data.json` file instead of
the existing `cache.json` file by modifying `src/data/phl/meta.js`
and commenting out the `cache_url` property.

After verifying the data in the application, run the optimization
process below to create `cache.json` and then uncomment that
property to use the cached file.

## Production optimization
From [tpreusse/open-budget wiki](https://github.com/tpreusse/open-budget/wiki/Data-Format#cache-cachejson):
> For production you can create a cache with pre-processed values and without arbitrary data.
> Call `OpenBudget.nodes.createCache()` via your browser console and save the output to your
> data directory as `cache.json`. Cache is used whenever `cache_url` is specified in `meta.json`.
(Ideally this would be implemented in python inside this repo as well, but it is not currently.)
