from glob import glob
from os.path import basename, splitext
from setuptools import find_packages, setup

setup(
    name='sharpytools',
    version='0.1',
    packages=find_packages(include=['sharpytools']),
    py_modules=[splitext(basename(path))[0] for path in glob('sharpytools/*.py')],
)
