import sys

from setuptools import setup, find_packages


setup_info = dict(
    name="quoridor",
    version="0.1.0",
    author="Michal Hola",
    author_email="hola2@uniba.sk",
    url="https://github.com/mrkvost/quoridor",
    description=(
        "Board game Quoridor for two players with Neural Network as opponent."
    ),

    packages=find_packages(),
    setup_requires=['nose==1.3.7'],
    entry_points={
        'console_scripts': [
            'qc = quoridor.quoridor:main',
        ],
    },
)

if 'develop' in sys.argv:
    if 'install_requires' not in setup_info:
        setup_info['install_requires'] = []
    setup_info['install_requires'].append('latex==0.6.1')

    if 'scripts' not in setup_info:
        setup_info['scripts'] = []
    setup_info['scripts'].append('bin/docmake')

setup(**setup_info)
