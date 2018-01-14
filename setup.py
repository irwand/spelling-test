from __future__ import print_function
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand
import io
import codecs
import os
import sys

here = os.path.abspath(os.path.dirname(__file__))

def read(*filenames, **kwargs):
    encoding = kwargs.get('encoding', 'utf-8')
    sep = kwargs.get('sep', '\n')
    buf = []
    for filename in filenames:
        with io.open(filename, encoding=encoding) as f:
            buf.append(f.read())
    return sep.join(buf)

long_description = read('README.md')

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errcode = pytest.main(self.test_args)
        sys.exit(errcode)

setup(
    name='spellingtest',
    version='0.1',
    url='https://github.com/irwand/spelling-test',
    license='GPL v3',
    author='Irwan Djajadi',
    tests_require=['pytest'],
    install_requires=[
        'PyDictionary',
        'pypiwin32',
        'six',
    ],
    cmdclass={'test': PyTest},
    description='Program to do spelling test',
    long_description=long_description,
    packages=['spellingtest'],
    include_package_data=True,
    platforms='any',
    classifiers = [
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Natural Language :: English',
        'Environment :: Python',
        'Intended Audience :: Users',
        'License :: OSI Approved :: GPL v3',
        'Operating System :: Windows 10',
        'Topic :: Software Development :: Program :: Python Modules',
        ],
    extras_require={
        'testing': ['pytest'],
    },
    entry_points={
        'console_scripts': ['spellingtest = spellingtest.__main__:main']
    },
)
