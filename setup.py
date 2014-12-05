from setuptools import setup

setup(name='corbit',
      version='3.0',
      package_dir={'': 'corbit3'},
      packages=['corbit',
                'corbit.objects',
                'corbit.physics',
                'corbit.network'],
      install_requires=['scipy', 'unum', 'pygame']
      )