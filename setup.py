import sys
import pip

from setuptools import setup, find_packages


REQUIREMENTS = {
    'nose': '1.3.7',
    'numpy': '1.10.4',
    'SQLAlchemy': '1.0.12',
}


def get_setup_requirements():
    matching_installed_packages = dict([
        (package.project_name.lower(), package)
        for package in pip.get_installed_distributions()
        if str(package.project_name) in REQUIREMENTS
    ])
    # ...TODO...

    setup_requirements = []
    for package_name, required_version in REQUIREMENTS.items():
        if package_name.lower() in matching_installed_packages:
            installed = matching_installed_packages[package_name.lower()]
            if installed.version < required_version:
                warning = (
                    'Warning, package {name} is already installed but version '
                    'is lower than required one {current} < {required}. If'
                    'any program functionality fails, try to upgrade this '
                    'package.'
                ).format(
                    name=package_name,
                    current=installed.version,
                    required=required_version,
                )
                print warning
        else:
            setup_requirements.append(
                '=='.join([package_name, required_version])
            )
    return setup_requirements


def create_setup_info():
    setup_requirements = get_setup_requirements()
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
        setup_requires=setup_requirements,
        entry_points={
            'console_scripts': [
                'qc = quoridor.quoridor:main',
                'train = quoridor.training:run',
            ],
        },
    )

    if 'install_requires' not in setup_info:
        setup_info['install_requires'] = []

    if 'develop' in sys.argv or 'install' in sys.argv:
        setup_info['install_requires'] = list(set(
            setup_info['install_requires'] + setup_requirements
        ))

    if 'develop' in sys.argv:
        setup_info['install_requires'].append('latex==0.6.1')

        if 'scripts' not in setup_info:
            setup_info['scripts'] = []
        setup_info['scripts'].append('bin/docmake')
    return setup_info

setup(**create_setup_info())
