from setuptools import setup, find_packages


def create_setup_info():
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
        entry_points={
            'console_scripts': [
                'qc = quoridor.quoridor:main',
                'build_db = quoridor.db.utils:run',
                'peto = quoridor.peto:run',
            ],
        },
        scripts=['bin/docmake', 'bin/plot'],
    )
    return setup_info


setup(**create_setup_info())
