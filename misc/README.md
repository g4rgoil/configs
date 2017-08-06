# Misc

The files in this directory are mostly user specific configuration files. 
If you want to automatically create links to these files, run `./setup.py -M` or `./setup.py --misc` as the desired user, from the root directory of this repository.

### latexmkrc
Basic configuration file for latexmk. Will be linked to as *~/.latexmkrc* by setup.py.
No further configuration required.

### yaourtrc
Basic configuration file for yaourt. Will be linked to as *~/.yaourtrc* by setup.py.
No further configuration required.

### neofetch_config
Basic configuration file for neofetch. Will be linked to as *~/.neofetch_config* by setup.py.
For the config to be recognized, you must specify its location when using neofetch, i.e., `neofetch --config ~/.neofetch_config` (you might want to define an alias for that).

Alternatively you can replace */etc/neofetch/config* with a link to this config. In that case you don't have to explicitly specify the config, i.e., `neofetch --config`.



