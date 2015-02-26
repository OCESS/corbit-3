#!/bin/sh

cd ..
virtualenv corbit3
cd corbit3
source bin/activate
pip3 install https://bitbucket.org/kiv/unum/get/tip.tar.gz
pip3 install hg+http://bitbucket.org/pygame/pygame
pip3 install numpy
pip3 install scipy
pip3 install mysqlclient
echo "All done setting up. I've created a virtualenv for development, so if you close this terminal you will have to run 'cd corbit-3/corbit3; source bin/activate' again."
