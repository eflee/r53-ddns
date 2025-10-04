#!/usr/bin/env python3
"""Setup script for r53-ddns package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='r53-ddns',
    version='2.0.0',
    description='Simple Dynamic DNS Script for AWS Route53',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Elijah Flesher',
    author_email='eli@flesher.io',
    url='https://github.com/eflee/r53-ddns',
    license='MIT',
    
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    
    py_modules=['ddns'],
    
    python_requires='>=3.8',
    
    install_requires=[
        'boto3>=1.34.0',
    ],
    
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=4.0.0',
            'pylint>=2.15.0',
            'flake8>=5.0.0',
            'mypy>=1.0.0',
            'black>=23.0.0',
        ],
    },
    
    entry_points={
        'console_scripts': [
            'r53-ddns=ddns:main',
        ],
    },
    
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Topic :: Internet :: Name Service (DNS)',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
    ],
    
    keywords='dns ddns route53 aws dynamic-dns ipv4 ipv6',
    
    project_urls={
        'Source': 'https://github.com/eflee/r53-ddns',
        'Bug Reports': 'https://github.com/eflee/r53-ddns/issues',
        'Changelog': 'https://github.com/eflee/r53-ddns/blob/main/CHANGELOG.md',
    },
)
