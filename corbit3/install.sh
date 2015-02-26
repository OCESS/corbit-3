#!/bin/sh

cd ..
virtualenv corbit3
cd corbit3
source bin/activate
pip3 install unum
/source/bin/cp unumpatch/__init__.py lib/python3.4/site-packages/unum/units/__init__.py # because I don't think the creator has pushed the "__cmp__ doesn't work in python3" patch yet
pip3 install hg+http://bitbucket.org/pygame/pygame
pip3 install numpy
pip3 install scipy
pip3 install mysqlclient
echo "All done setting up. I've created a virtualenv for development, so if you close this terminal you will have to run 'cd corbit-3/corbit3; source bin/activate'"
