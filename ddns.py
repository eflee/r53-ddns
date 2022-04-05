import sys
import requests
import argparse
import os
from datetime import datetime
from boto.route53.connection import Route53Connection
from boto.route53.record import ResourceRecordSets

# Cribbed environment variable argparse action. Credit to Russell Heilling
class EnvDefault(argparse.Action):
    def __init__(self, envvar, required=True, default=None, **kwargs):
        if envvar:
            if envvar in os.environ:
                default = os.environ[envvar]
        if required and default:
            required = False
        super(EnvDefault, self).__init__(default=default, required=required, 
                                         **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, values)

def main():

    #Parse the args
    parser = argparse.ArgumentParser(description='Update a AWS Route53 record with the current internet IP. Accepts all arguments as command-line flags or environment variables.')
    parser.add_argument("-q", "--ip-query-url", action=EnvDefault, envvar="IP_QUERY_URL", required=False, default="https://wtfismyip.com/text", help="URL to query to get IP")
    parser.add_argument("-z", "--zone-id", action=EnvDefault, envvar='ZONE_ID', required=True, help="R53 Zone ID to Update")
    parser.add_argument("-d", "--fqdn", action=EnvDefault, envvar='FQDN', required=True, help="FQDN to Update in the Zone, i.e. \"example.com.\" (note the trailing \".\")")
    parser.add_argument("-a", "--aws-access-key-id", action=EnvDefault, envvar='AWS_ACCESS_KEY_ID', required=True, help="AWS Access Key ID")
    parser.add_argument("-s", "--aws-secret-access-key", action=EnvDefault, envvar='AWS_SECRET_ACCESS_KEY', required=True, help="AWS Secret Access Key")

    args = parser.parse_args()
    # Get my IP
    ip = requests.get(args.ip_query_url).text.strip()
    
    # Connect R53, Get IP from A Record
    conn = Route53Connection(aws_access_key_id=args.aws_access_key_id, aws_secret_access_key=args.aws_secret_access_key)
    r53_ip = conn.get_all_rrsets(args.zone_id, 'A', args.fqdn, maxitems=1)[0].resource_records[0]

    if ip == r53_ip:
        print("NO UPDATE: {} @ {}\n".format(ip,datetime.now()))
        sys.exit(0)

    # Change needed, upsert the record
    changes = ResourceRecordSets(conn, args.zone_id)
    record = changes.add_change("UPSERT", args.fqdn, "A", 10)
    record.add_value(ip)

    #commit
    response = changes.commit()

    print("UPDATED: FROM {} to {} @ {}\n".format(r53_ip,ip,datetime.now()))

if __name__ == "__main__":
    main()
