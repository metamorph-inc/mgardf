from setuptools import setup, find_packages

with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='mgardf',
    version='0.2.0',
    description='Utilities for converting GME MGA structures to RDF',
    long_description=readme,
    author='Adam Nagel',
    author_email='adam.nagel+git@gmail.com',
    url='https://github.com/metamorph-inc/mgardf',
    license=license,
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=[
        'rdflib',
        'udm'
    ]
)
