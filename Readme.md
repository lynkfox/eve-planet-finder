# Requirements

* Python3.10

# `python buildMapData.py`

Reads the data yaml files in `./data` and converts them to objects and lists of said objects. Automatically Pickles the objects as well, to lower load time of other scripts.

Should not need to be run as the pickles are already in the git, but if any values in any of the `yaml` files changes, then will need to be run.

# `python plotMapData.py`

plots the map. Integrated with calculateCloseness. Loads the relevant data directly from the pickled data classes.