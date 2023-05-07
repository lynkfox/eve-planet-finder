# Requirements

* Python3.10

# Contributing
# `python buildMapData.py`

Reads the data yaml files in `./data` and converts them to objects and lists of said objects. Automatically Pickles the objects as well, to lower load time of other scripts.

Should not need to be run as the pickles are already in the git, but if any values in any of the `yaml` files changes, or if the models themselves change, then will need to be run.

# `python plotMapData.py`

plots the map. Integrated with calculateCloseness. Loads the relevant data directly from the pickled data classes.


TODO: script arguments.
TODO: Dashly? for plotly?

# License

Copyright (C) 2023  Anthony Goh, aka [Lynkfox](https://github.com/lynkfox)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>
