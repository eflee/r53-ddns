# r53-ddns

[![Tests](https://github.com/eflee/r53-ddns/actions/workflows/test.yml/badge.svg)](https://github.com/eflee/r53-ddns/actions/workflows/test.yml)
[![Version Check](https://github.com/eflee/r53-ddns/actions/workflows/version-check.yml/badge.svg)](https://github.com/eflee/r53-ddns/actions/workflows/version-check.yml)
[![PyPI](https://img.shields.io/pypi/v/r53-ddns)](https://pypi.org/project/r53-ddns/)
[![Python Version](https://img.shields.io/pypi/pyversions/r53-ddns)](https://pypi.org/project/r53-ddns/)

Simple Dynamic DNS Script for AWS Route53

Automatically updates your Route53 DNS records with your current public IP address. Supports both IPv4 (A records) and IPv6 (AAAA records).

## Features

- IPv4 and IPv6 support (A and AAAA records)
- Updates only when IP changes
- IAM role support (no credentials needed on EC2/ECS)
- Dry run mode for testing
- Configurable TTL
- Only one dependency (boto3)

## Installation

### From PyPI

```bash
pip install r53-ddns
```

### From Source

```bash
git clone https://github.com/eflee/r53-ddns.git
cd r53-ddns
pip install .
```

### Development

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
```

## Quick Start

```bash
# Basic usage
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com.

# With IPv6
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com. -t A,AAAA

# Using environment variables
export ZONE_ID=YOUR_HOSTED_ZONE_ID
export FQDN=home.example.com.
r53-ddns
```

## Usage

### Command Line Options

```
-z, --zone-id ZONE_ID          Route53 Hosted Zone ID (required, env: ZONE_ID)
-d, --fqdn FQDN                Fully qualified domain name with trailing dot (required, env: FQDN)
-t, --record-types TYPES       Record types: A, AAAA, or A,AAAA (default: A, env: RECORD_TYPES)
-4, --ipv4-query-url URL       URL to query for IPv4 address (default: https://api.ipify.org, env: IPV4_QUERY_URL)
-6, --ipv6-query-url URL       URL to query for IPv6 address (default: https://api64.ipify.org, env: IPV6_QUERY_URL)
-a, --aws-access-key-id ID     AWS Access Key ID (optional, env: AWS_ACCESS_KEY_ID)
-s, --aws-secret-access-key    AWS Secret Access Key (optional, env: AWS_SECRET_ACCESS_KEY)
-r, --aws-region REGION        AWS Region (default: us-east-1, env: AWS_REGION)
--ttl TTL                      DNS TTL in seconds (default: 300, env: TTL)
--timeout SECONDS              HTTP request timeout in seconds (default: 10, env: TIMEOUT)
--dry-run                      Show changes without updating
-v, --verbose                  Enable debug logging
```

All options can be set via environment variables as shown above.

### Examples

**Basic IPv4 update:**
```bash
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com.
```

**Dual-stack (IPv4 + IPv6):**
```bash
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com. -t A,AAAA
```

**With explicit credentials:**
```bash
r53-ddns \
  -z YOUR_HOSTED_ZONE_ID \
  -d home.example.com. \
  -a YOUR_ACCESS_KEY_ID \
  -s YOUR_SECRET_ACCESS_KEY
```

**Using IAM role (recommended for EC2/ECS):**
```bash
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com.
```

**Test without making changes:**
```bash
r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com. --dry-run -v
```

## Periodic Updates

### Cron

Run every 5 minutes:

```bash
crontab -e
# Add:
*/5 * * * * /usr/local/bin/r53-ddns -z YOUR_HOSTED_ZONE_ID -d home.example.com. >> /var/log/ddns.log 2>&1
```

### Docker

Build and run:

```bash
docker build -t r53-ddns .
docker run --rm \
  -e ZONE_ID=YOUR_HOSTED_ZONE_ID \
  -e FQDN=home.example.com. \
  -e AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY \
  r53-ddns
```

Or use docker-compose:

```yaml
version: '3.8'
services:
  ddns:
    build: .
    environment:
      - ZONE_ID=YOUR_HOSTED_ZONE_ID
      - FQDN=home.example.com.
      - RECORD_TYPES=A,AAAA
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: r53-ddns
  namespace: default
spec:
  schedule: "*/5 * * * *"
  successfulJobsHistoryLimit: 3
  failedJobsHistoryLimit: 1
  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: r53-ddns
        spec:
          restartPolicy: OnFailure
          serviceAccountName: r53-ddns
          containers:
          - name: ddns
            image: ghcr.io/eflee/r53-ddns:latest
            imagePullPolicy: Always
            env:
            - name: ZONE_ID
              value: "YOUR_HOSTED_ZONE_ID"
            - name: FQDN
              value: "home.example.com."
            - name: RECORD_TYPES
              value: "A,AAAA"
            resources:
              requests:
                memory: "64Mi"
                cpu: "50m"
              limits:
                memory: "128Mi"
                cpu: "100m"
            securityContext:
              runAsNonRoot: true
              runAsUser: 1000
              allowPrivilegeEscalation: false
              readOnlyRootFilesystem: true
              capabilities:
                drop:
                - ALL

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: r53-ddns
  namespace: default
  # For EKS with IRSA, add IAM role annotation:
  # annotations:
  #   eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/r53-ddns-role
```

## AWS IAM Permissions

Required permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "route53:ListResourceRecordSets",
      "route53:ChangeResourceRecordSets"
    ],
    "Resource": "arn:aws:route53:::hostedzone/YOUR_ZONE_ID_HERE"
  }]
}
```

## Building and Publishing

### Build Package

```bash
pip install build twine
python -m build
```

### Publish to PyPI

```bash
twine upload dist/*
```

## Troubleshooting

**FQDN must end with a dot**
- Correct: `example.com.`
- Wrong: `example.com`

**Failed to fetch IP**
- Check internet connection
- Try different IP query URL: `--ipv4-query-url https://icanhazip.com`

**AWS API errors**
- Verify credentials and IAM permissions
- Check zone ID is correct
- Ensure FQDN exists in your hosted zone

**IPv6 not working**
- Check IPv6 connectivity: `curl -6 https://api64.ipify.org`
- Some networks don't support IPv6, use `-t A` for IPv4 only

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

Run tests: `python -m pytest tests/ -v`

## License

MIT License - see [LICENSE](LICENSE) for details.

## Security

Report security issues via GitHub issues or pull requests.