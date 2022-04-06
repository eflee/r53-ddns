# r53-ddns
[![Docker](https://github.com/eflee/r53-ddns/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/eflee/r53-ddns/actions/workflows/docker-publish.yml)

Simple DynamicDNS Script (and Container) for Route53 

```
Usage: ddns.py [-h] [-q IP_QUERY_URL] -z ZONE_ID -d FQDN -a AWS_ACCESS_KEY_ID -s AWS_SECRET_ACCESS_KEY

Update a AWS Route53 record with the current internet IP. Accepts all arguments as command-line flags or environment variables.

options:
  -h, --help            show this help message and exit
  -q IP_QUERY_URL, --ip-query-url IP_QUERY_URL
                        URL to query to get IP
  -z ZONE_ID, --zone-id ZONE_ID
                        R53 Zone ID to Update
  -d FQDN, --fqdn FQDN  FQDN to Update in the Zone, i.e. "example.com." (note the trailing ".")
  -a AWS_ACCESS_KEY_ID, --aws-access-key-id AWS_ACCESS_KEY_ID
                        AWS Access Key ID
  -s AWS_SECRET_ACCESS_KEY, --aws-secret-access-key AWS_SECRET_ACCESS_KEY
                        AWS Secret Access Key
```
