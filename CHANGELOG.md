# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-04

### Changed License
- **BREAKING**: Changed from GPL-3.0 to MIT License for maximum permissiveness and adoption

### Added
- **Python Package**: Now installable via pip as `r53-ddns`
- **Console Script**: Install creates `r53-ddns` command-line tool
- **Package Metadata**: Full PyPI package with setup.py and pyproject.toml
- **Development Extras**: Optional dev dependencies for testing and linting
- **IPv6 Support**: Now supports AAAA records in addition to A records
- **Dual-Stack Support**: Can update both IPv4 and IPv6 records simultaneously with `-t A,AAAA`
- **IAM Role Support**: Works with EC2/ECS IAM roles, no explicit credentials needed
- **Comprehensive Logging**: Structured logging with configurable verbosity
- **IP Validation**: Validates IP addresses before updating Route53
- **Dry Run Mode**: Test changes without actually updating DNS records with `--dry-run`
- **Configurable TTL**: Set custom TTL values (default changed to 300 seconds)
- **Custom IP Query URLs**: Separate URLs for IPv4 and IPv6 queries
- **Timeout Configuration**: Configurable HTTP request timeout
- **Better Error Handling**: Graceful handling of network and AWS API errors
- **Type Hints**: Modern Python type hints throughout
- **Comprehensive Test Suite**: Full unit and integration tests
- **Docker Security**: Non-root user, health checks, and security best practices
- **Example Configurations**: systemd, Kubernetes, cron, and docker-compose examples
- **Contributing Guide**: Documentation for contributors

### Changed
- **BREAKING**: Migrated from `boto` (v2) to `boto3` - requires `pip install boto3`
- **BREAKING**: Default TTL changed from 10 seconds to 300 seconds (more reasonable default)
- **BREAKING**: Default IPv4 query URL changed from `https://wtfismyip.com/text` to `https://api.ipify.org`
- Replaced `requests` library with built-in `urllib.request` (one less dependency!)
- Simplified environment variable handling from custom argparse Action to simple helper function
- Improved argument parsing with better help text (now shows environment variable names)
- Enhanced logging with timestamps and log levels
- Docker image now runs as non-root user
- Docker image updated to Python 3.11-slim
- Reduced code complexity by 34 lines (430 → 396 lines)

### Removed
- Dependency on `requests` library (now using stdlib `urllib`)
- Dependency on legacy `boto` library

### Fixed
- Better error handling for network failures
- Proper handling of missing Route53 records
- Validation of FQDN format (must end with dot)
- AWS credential chain support (IAM roles, env vars, config files)

### Security
- Docker container now runs as non-root user (uid 1000)
- Added health checks to Docker container
- Better credential handling (supports IAM roles)
- Input validation for IP addresses and FQDNs

## [1.0.0] - Previous Release

### Initial Release
- Basic IPv4 (A record) support
- Command-line and environment variable configuration
- Simple Docker container
- AWS Route53 integration using boto v2
