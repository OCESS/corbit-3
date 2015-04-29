Corbit
======

This is a spaceflight simulator, programmed in Python. This specific repo is the
third major version of Corbit


How do I fly this thing?
------------

Python distribution is hard. so for development do this in the same directory as this README.md:

    virtualenv corbit3
    cd corbit3
    source bin/activate
    pip3 install unum
    cp unumpatch/__init__.py lib/python3.4/site-packages/unum/units/__init__.py # because I don’t think the creator has pushed the “__cmp__ doesn’t work in python3” patch yet
    pip3 install hg+http://bitbucket.org/pygame/pygame
    pip3 install numpy
    pip3 install scipy
    pip3 install mysqlclient

then from here you have to run `source corbit3/bin/activate` do get your virtualenv for development back again.
If you don’t want a virtualenv (useful to have exactly the right versions of libraries you need and not conflict with other projects on your system)
then you can leave out the first three lines.

To run:

    cd corbit3
    python3 server.py
    python3 client.py

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
