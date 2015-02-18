Corbit
======

This is a spaceflight simulator, programmed in Python. This specific repo is the
third major version of Corbit

System Requirements
-------------------

You’re going to need a MySQL server running. Also Python 3. Please and thank you.

How do I fly this thing?
------------------------

Python distribution is hard, so everything is included. Just `cd` to corbit3/ and do one of `python server.py` or `python client.py`. I know,
but I wouldn’t have done it if there were an easier way that will for sure work for everyone.

Table of Contents
-----------------

`corbit3/saves/`			this directory contains all data files that Corbit can load  
`- OCESS.json`	the default data file that is loaded  

`corbit3/corbit/`			this directory contains all the libraries that are written for this  
`- physics`         for physics calculations, like “find distance between two objects”  
`- objects`         definitions of all physical objects (eg `entity`), plus useful functions for operating on them (eg `find_entity`)  
`- network`         network functions are in here. Use these to send and receive data between processes. E.g., `network.recv_all(socket)`  
`server.py`     running this starts the server  
`client.py`     running this starts the corbit pilot  
