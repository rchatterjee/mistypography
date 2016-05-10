#!/usr/bin/python

from distutils.core import setup

setup(
    name='typofixer',
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
        'Programming Language :: Python :: 2.7',
    ],

    keywords="password typo correction",
    packages=['typofixer'], #find_packages(exclude(['contrib', 'docs', 'tests*'])),
    package_data = {'typofixer': ['data/*']},
    install_requires=[
        "python-levenshtein"
        # "pwmodel==1.0",
    ],
    dependency_links=[
#        "https://github.com/rchatterjee/pwmodels/master#egg=pwmodel-1.0"
        "git+https://github.com/rchatterjee/pwmodels.git"
    ],
    # data_files=[('pwmodel/data/', ['ngram-0-phpbb.dawg', 'ngram-3-phpbb.dawg', 'ngram-4-phpbb.dawg'])]
)
