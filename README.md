Corbit
======

This is a spaceflight simulator, programmed in Python. This specific repo is the
third major version of Corbit


Requirements
------------

By running `sudo python setup.py install` everything should be installed for you wow isn’t that cool

Installation
------------

`sudo python setup.py install` installs the required libraries. Then, run `server.py` from `corbit3` and `client.py` from `corbit3`.

Project Structure
-----------------

`corbit3/saves/`			this directory contains all data files that Corbit can load  
`- OCESS.json`	the default data file that is loaded  

`corbit3/corbit/`			this directory contains all the libraries that are written for this  
`- physics`         for physics calculations, like “find distance between two objects”  
`- objects`         definitions of all physical objects (eg `entity`), plus useful functions for operating on them (eg `find_entity`)  
`- network`         network functions are in here. Use these to send and receive data between processes. E.g., `network.recv_all(socket)`  
`server.py`     running this starts the server  
`client.py`     running this starts the corbit pilot  
