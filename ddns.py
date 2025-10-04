#!/usr/bin/env python3
"""
Simple Dynamic DNS Script for AWS Route53

Updates AWS Route53 DNS records with your current public IP address.
Supports both IPv4 (A records) and IPv6 (AAAA records).
"""

import os
import sys
import argparse
import logging
from datetime import datetime
from ipaddress import ip_address, IPv4Address, IPv6Address
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from typing import Optional, List

import boto3
from botocore.exceptions import ClientError, BotoCoreError


# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def env_default(env_var: str, default: Optional[str] = None) -> Optional[str]:
    """Get value from environment variable or use default."""
    return os.getenv(env_var, default)


def fetch_ip(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch IP address from a URL.
    
    Args:
        url: URL to query for IP address
        timeout: Request timeout in seconds
        
    Returns:
        IP address as string, or None if fetch fails
    """
    try:
        req = Request(url, headers={'User-Agent': 'r53-ddns/2.0'})
        with urlopen(req, timeout=timeout) as response:
            ip = response.read().decode('utf-8').strip()
            logger.debug(f"Fetched IP from {url}: {ip}")
            return ip
    except (URLError, HTTPError) as e:
        logger.error(f"Failed to fetch IP from {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error fetching IP from {url}: {e}")
        return None


def validate_ip(ip_str: str, expected_version: int) -> bool:
    """
    Validate IP address format and version.
    
    Args:
        ip_str: IP address string to validate
        expected_version: Expected IP version (4 or 6)
        
    Returns:
        True if valid, False otherwise
    """
    try:
        ip = ip_address(ip_str)
        if expected_version == 4 and isinstance(ip, IPv4Address):
            return True
        elif expected_version == 6 and isinstance(ip, IPv6Address):
            return True
        else:
            logger.error(f"IP {ip_str} is not IPv{expected_version}")
            return False
    except ValueError as e:
        logger.error(f"Invalid IP address {ip_str}: {e}")
        return False


def get_current_record(client, zone_id: str, fqdn: str, record_type: str) -> Optional[str]:
    """
    Get current IP from Route53 record.
    
    Args:
        client: boto3 Route53 client
        zone_id: Route53 zone ID
        fqdn: Fully qualified domain name
        record_type: Record type (A or AAAA)
        
    Returns:
        Current IP address, or None if record doesn't exist
    """
    try:
        response = client.list_resource_record_sets(
            HostedZoneId=zone_id,
            StartRecordName=fqdn,
            StartRecordType=record_type,
            MaxItems='1'
        )
        
        for record_set in response.get('ResourceRecordSets', []):
            if record_set['Name'] == fqdn and record_set['Type'] == record_type:
                if record_set.get('ResourceRecords'):
                    return record_set['ResourceRecords'][0]['Value']
        
        logger.info(f"No existing {record_type} record found for {fqdn}")
        return None
        
    except ClientError as e:
        logger.error(f"AWS API error getting {record_type} record: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting {record_type} record: {e}")
        return None


def update_record(client, zone_id: str, fqdn: str, record_type: str, 
                 new_ip: str, ttl: int, dry_run: bool = False) -> bool:
    """
    Update Route53 DNS record.
    
    Args:
        client: boto3 Route53 client
        zone_id: Route53 zone ID
        fqdn: Fully qualified domain name
        record_type: Record type (A or AAAA)
        new_ip: New IP address
        ttl: Time to live in seconds
        dry_run: If True, don't actually update
        
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        logger.info(f"DRY RUN: Would update {record_type} record {fqdn} to {new_ip} (TTL: {ttl})")
        return True
    
    try:
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': fqdn,
                        'Type': record_type,
                        'TTL': ttl,
                        'ResourceRecords': [{'Value': new_ip}]
                    }
                }]
            }
        )
        
        change_id = response['ChangeInfo']['Id']
        logger.info(f"Updated {record_type} record {fqdn} to {new_ip} (Change ID: {change_id})")
        return True
        
    except ClientError as e:
        logger.error(f"AWS API error updating {record_type} record: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error updating {record_type} record: {e}")
        return False


def process_record_type(client, args, record_type: str, ip_query_url: str) -> bool:
    """
    Process a single record type (A or AAAA).
    
    Args:
        client: boto3 Route53 client
        args: Parsed command-line arguments
        record_type: Record type (A or AAAA)
        ip_query_url: URL to query for IP
        
    Returns:
        True if successful or no update needed, False on error
    """
    ip_version = 4 if record_type == 'A' else 6
    logger.info(f"Processing {record_type} record for {args.fqdn}")
    
    # Fetch current public IP
    new_ip = fetch_ip(ip_query_url, timeout=args.timeout)
    if not new_ip:
        logger.error(f"Failed to fetch IPv{ip_version} address")
        return False
    
    # Validate IP format
    if not validate_ip(new_ip, ip_version):
        logger.error(f"Invalid IPv{ip_version} address: {new_ip}")
        return False
    
    # Get current Route53 record
    current_ip = get_current_record(client, args.zone_id, args.fqdn, record_type)
    
    # Compare and update if needed
    if new_ip == current_ip:
        logger.info(f"NO UPDATE NEEDED: {record_type} record already set to {new_ip}")
        return True
    
    logger.info(f"UPDATE NEEDED: {record_type} record changing from {current_ip} to {new_ip}")
    return update_record(client, args.zone_id, args.fqdn, record_type, 
                        new_ip, args.ttl, args.dry_run)


def validate_fqdn(fqdn: str) -> bool:
    """
    Validate FQDN format.
    
    Args:
        fqdn: Fully qualified domain name
        
    Returns:
        True if valid, False otherwise
    """
    if not fqdn.endswith('.'):
        logger.error(f"FQDN must end with a dot: {fqdn}")
        return False
    if len(fqdn) < 3:
        logger.error(f"FQDN too short: {fqdn}")
        return False
    return True


def parse_record_types(record_types_str: str) -> List[str]:
    """
    Parse comma-separated record types.
    
    Args:
        record_types_str: Comma-separated record types (e.g., "A,AAAA")
        
    Returns:
        List of record types
    """
    types = [t.strip().upper() for t in record_types_str.split(',')]
    valid_types = ['A', 'AAAA']
    
    for t in types:
        if t not in valid_types:
            raise ValueError(f"Invalid record type: {t}. Must be A or AAAA")
    
    return types


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Update AWS Route53 DNS records with current public IP address. '
                   'Supports both IPv4 (A) and IPv6 (AAAA) records. '
                   'Accepts all arguments as command-line flags or environment variables.'
    )
    
    # IP query URLs
    parser.add_argument(
        "-4", "--ipv4-query-url",
        default=env_default("IPV4_QUERY_URL", "https://api.ipify.org"),
        help="URL to query for IPv4 address (default: https://api.ipify.org, env: IPV4_QUERY_URL)"
    )
    
    parser.add_argument(
        "-6", "--ipv6-query-url",
        default=env_default("IPV6_QUERY_URL", "https://api64.ipify.org"),
        help="URL to query for IPv6 address (default: https://api64.ipify.org, env: IPV6_QUERY_URL)"
    )
    
    # Route53 configuration
    parser.add_argument(
        "-z", "--zone-id",
        default=env_default("ZONE_ID"),
        required=not env_default("ZONE_ID"),
        help="Route53 Hosted Zone ID (env: ZONE_ID)"
    )
    
    parser.add_argument(
        "-d", "--fqdn",
        default=env_default("FQDN"),
        required=not env_default("FQDN"),
        help='Fully Qualified Domain Name to update (must end with ".", e.g., "example.com.") (env: FQDN)'
    )
    
    # AWS credentials (optional - can use IAM roles, env vars, or AWS config)
    parser.add_argument(
        "-a", "--aws-access-key-id",
        default=env_default("AWS_ACCESS_KEY_ID"),
        help="AWS Access Key ID (optional if using IAM role or AWS config) (env: AWS_ACCESS_KEY_ID)"
    )
    
    parser.add_argument(
        "-s", "--aws-secret-access-key",
        default=env_default("AWS_SECRET_ACCESS_KEY"),
        help="AWS Secret Access Key (optional if using IAM role or AWS config) (env: AWS_SECRET_ACCESS_KEY)"
    )
    
    parser.add_argument(
        "-r", "--aws-region",
        default=env_default("AWS_REGION", "us-east-1"),
        help="AWS Region (default: us-east-1, env: AWS_REGION)"
    )
    
    # Record configuration
    parser.add_argument(
        "-t", "--record-types",
        default=env_default("RECORD_TYPES", "A"),
        help='Record types to update: "A", "AAAA", or "A,AAAA" (default: A, env: RECORD_TYPES)'
    )
    
    parser.add_argument(
        "--ttl",
        type=int,
        default=int(env_default("TTL", "300")),
        help="DNS record TTL in seconds (default: 300, env: TTL)"
    )
    
    # Operational options
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(env_default("TIMEOUT", "10")),
        help="HTTP request timeout in seconds (default: 10, env: TIMEOUT)"
    )
    
    parser.add_argument(
        "--dry-run",
        action='store_true',
        help="Show what would be updated without making changes"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action='store_true',
        help="Enable verbose debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        logging.getLogger('boto3').setLevel(logging.DEBUG)
        logging.getLogger('botocore').setLevel(logging.DEBUG)
    
    # Validate FQDN
    if not validate_fqdn(args.fqdn):
        sys.exit(1)
    
    # Parse record types
    try:
        record_types = parse_record_types(args.record_types)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)
    
    logger.info(f"Starting DDNS update for {args.fqdn} (record types: {', '.join(record_types)})")
    
    # Create boto3 client
    try:
        session_kwargs = {'region_name': args.aws_region}
        
        # Only set explicit credentials if provided
        if args.aws_access_key_id and args.aws_secret_access_key:
            session_kwargs['aws_access_key_id'] = args.aws_access_key_id
            session_kwargs['aws_secret_access_key'] = args.aws_secret_access_key
            logger.debug("Using explicit AWS credentials")
        else:
            logger.debug("Using AWS credential chain (IAM role, env vars, or config file)")
        
        session = boto3.Session(**session_kwargs)
        client = session.client('route53')
        
    except (ClientError, BotoCoreError) as e:
        logger.error(f"Failed to create AWS client: {e}")
        sys.exit(1)
    
    # Process each record type
    success = True
    for record_type in record_types:
        ip_query_url = args.ipv4_query_url if record_type == 'A' else args.ipv6_query_url
        
        if not process_record_type(client, args, record_type, ip_query_url):
            success = False
    
    if success:
        logger.info("DDNS update completed successfully")
        sys.exit(0)
    else:
        logger.error("DDNS update completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()