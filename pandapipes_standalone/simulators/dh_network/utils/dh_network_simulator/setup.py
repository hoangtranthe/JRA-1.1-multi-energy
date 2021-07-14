# Copyright (c) 2020-2021 by Fraunhofer Institute for Energy Economics
# and Energy System Technology (IEE), Kassel, and University of Kassel. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be found in the LICENSE file.

from setuptools import find_packages
from setuptools import setup
import re

with open('README.rst', 'rb') as f:
    install = f.read().decode('utf-8')

with open('CHANGELOG.rst', 'rb') as f:
    changelog = f.read().decode('utf-8')

classifiers = [
    'Development Status :: 1 - Initial',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'Intended Audience :: Education',
    'Intended Audience :: Science/Research',
    'License :: OSI Approved :: BSD License',
    'Natural Language :: English',
    'Operating System :: OS Independent',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3']

# with open('.github/workflows/run_tests_master.yml', 'rb') as f:
    # lines = f.read().decode('utf-8')
    # for version in re.findall('python: 3.[0-9]', lines):
        # classifiers.append('Programming Language :: Python :: 3.%s' % version[-1])

long_description = '\n\n'.join((install, changelog))

setup(
    name='dhnetwork_simulator',
    version='0.0.1',
    author='Christopher W. Wild',
    author_email='cwowi@elektro.dtu.dk',
    description='A pipeflow simulation tool that complements pandapipes and enables static and dynamic heat transfer simulation in district heating systems',
    long_description=long_description,
	long_description_content_type='text/x-rst',
    url='',
    license='BSD',
    install_requires=["pandapipes>=0.3.0, "numpy", "pandas", "dataclasses"],
    extras_require={"docs": ["numpydoc", "sphinx", "sphinxcontrib.bibtex"],
                    "plotting": ["matplotlib"],
                    "test": ["pytest"]},
    python_requires='>=3, <4',
    packages=find_packages(),
    include_package_data=True,
    classifiers=classifiers
)
