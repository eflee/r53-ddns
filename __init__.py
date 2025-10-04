"""
r53-ddns: Simple Dynamic DNS Script for AWS Route53

A lightweight tool to automatically update AWS Route53 DNS records
with your current public IP address. Supports both IPv4 and IPv6.
"""

__version__ = '2.0.0'
__author__ = 'Elijah Flesher'
__license__ = 'MIT'

from ddns import main

__all__ = ['main']
