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

`res/`			this directory contains all data files that Corbit can load  
`- OCESS.json`	the default data file that is loaded  

`.project`		I develop this using PyDev, these are my project files  
`.pydevproject`	see above  

`src/`			this directory contains all the source files  
`- server.py`		running this will start a headless server that is running Corbit, which loads OCESS.json by default  
`- client.py`		running this will connect to a running instance of server.py, on the local machine. Then, it will tell the server to reload the default OCESS.json file  
`- entity.py`		contains the class definitions for any physical objects. Entity is the base object, Habitat is derived from Entity  
`- camera.py`		contains the calss definitions for the camera object, used by client.py to move the camera around
