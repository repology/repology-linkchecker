#!/usr/bin/env python3

from setuptools import setup


setup(
    name='repology-linkchecker',
    version='0.0.0',
    description='Link validity checker utility for Repology project',
    author='Dmitry Marakasov',
    author_email='amdmi3@amdmi3.ru',
    url='https://repology.org/',
    license='GNU General Public License v3 or later (GPLv3+)',
    packages=[
        'linkchecker',
    ],
    scripts=[
        'repology-linkchecker.py',
    ],
    data_files={
        'hostlists': ['hosts.yaml'],
    },
    classifiers=[
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: System :: Networking :: Monitoring',
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    python_requires=">=3.7",
    install_requires=[
        'PyYAML>=5.1',
        'aiodns>=1.1.1',
        'aiohttp>=3.5.4',
        'aiopg>=0.16.0',
    ]
)
