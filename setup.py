from setuptools import setup, find_packages


setup(
    name="quoridor",
    version="0.1.0",
    author="Michal Hola",
    author_email="hola2@uniba.sk",
    url="https://github.com/mrkvost/quoridor",
    description=(
        "Board game Quoridor for two players with Neural Network as opponent."
    ),

    packages=find_packages(),
    setup_requires=['nose'],
    entry_points={
        'console_scripts': [
            'console = quoridor.quoridor:main',
        ],
    },
)
