Table of Contents
=================
In this directory, the only two important files are `server.py` and `client.py`. I’m sorry I had to
include all the libraries, but it was the most surefire way that anyone would be able to develop this.
If there were a more elegant way that most importantly worked 100% no matter what, I would do that,
but some of these packages just aren’t easily findable, and `python setup.py build` won’t cut it.

`server.py`
-----------
Usage: `python server.py`

This is a console program that reads in the default savefile `./saves/OCESS.json` and serializes the
data into all them entities. Then, it starts up a connection with a mysql database and begins updating
it with the latest state of the entities. Simultaneously, it simulates what happens to each entity
tick-by-tick.

`client.py`
-----------
Usage: `python client.py`

This is the GUI client. Very snazzy. It reads from a mysql database every now and then to find out
where all the entities are. Also gets keyboard commands and sends them to the server.

`saves/`
--------
This is where you keep your saves. Check out `saves/tableofcontents.md` for more deets.
