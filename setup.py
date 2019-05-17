from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gaecl',
    version='0.1.0',
    description='Collerated request logger for GAE python3 flexible|standard environment',
    url='https://github.com/takashi8/gaecl',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Takashi Morioka',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    keywords='google app engine stackdriver',
    packages=find_packages(exclude=['docs', 'tests']),
    python_requires='>=3.6',
    install_requires=['google-cloud-logging', 'werkzeug'],
    project_urls={
        'Bug Reports': 'https://github.com/takashi8/gaecl/issues',
        'Say Thanks!': 'https://github.com/takashi8/gaecl#thanks-for-using',
        'Source': 'https://github.com/takashi8/gaecl',
    },
)
