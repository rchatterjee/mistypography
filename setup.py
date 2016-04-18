#!/usr/bin/python

from distutils.core import setup

setup(
    name='typofix',
    version='1.0',
    description='A simple password typo correction procedure.',
    long_description="""This module tries to find possible methods to correct mistyped
    passwords. Look at https://www.cs.cornell.edu/~rahul/papers/pwtypos.pdf for more details.  """,

    url="https://github.com/rchatterjee/mistypography.git",
    author="Rahul Chatterjee",
    author_email="rahul@cs.cornell.edu",
    license="Apache",

    classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',
        
        # Indicate who your project is intended for
        'Intended Audience :: Password Researchers',
        'Topic :: Password Modeling',
        
        # Pick your license as you wish (should match "license" above)
        'License :: Apache',
        
        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
    ],

    keywords="password typo correction",
    packages=['typofix'], #find_packages(exclude(['contrib', 'docs', 'tests*'])),
                           
    install_requires=['pwmodel'],
    # data_files=[('pwmodel/data/', ['ngram-0-phpbb.dawg', 'ngram-3-phpbb.dawg', 'ngram-4-phpbb.dawg'])]
)
