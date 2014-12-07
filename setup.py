from setuptools import setup

setup(name='corbit',
      version='3.0',
      package_dir={'': 'corbit3'},
      packages=['corbit'],
      install_requires=['scipy', 'unum', 'pygame']
      )
