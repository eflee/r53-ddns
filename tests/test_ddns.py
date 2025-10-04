#!/usr/bin/env python3
"""
Comprehensive test suite for r53-ddns

Run with: python -m pytest test_ddns.py -v
Or: python test_ddns.py
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import sys
import os
from io import StringIO

# Import the module under test
import ddns


class TestEnvDefault(unittest.TestCase):
    """Test the env_default helper function."""
    
    def test_env_var_used_as_default(self):
        """Test that environment variable is used when set."""
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            result = ddns.env_default('TEST_VAR')
            self.assertEqual(result, 'test_value')
    
    def test_explicit_default_when_no_env(self):
        """Test that explicit default is used when env var not set."""
        with patch.dict(os.environ, {}, clear=True):
            result = ddns.env_default('MISSING_VAR', 'fallback')
            self.assertEqual(result, 'fallback')
    
    def test_none_when_no_env_no_default(self):
        """Test that None is returned when env var not set and no default."""
        with patch.dict(os.environ, {}, clear=True):
            result = ddns.env_default('MISSING_VAR')
            self.assertIsNone(result)


class TestFetchIP(unittest.TestCase):
    """Test IP fetching functionality."""
    
    @patch('ddns.urlopen')
    def test_fetch_ipv4_success(self, mock_urlopen):
        """Test successful IPv4 fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'192.0.2.1\n'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        ip = ddns.fetch_ip('https://api.ipify.org')
        self.assertEqual(ip, '192.0.2.1')
    
    @patch('ddns.urlopen')
    def test_fetch_ipv6_success(self, mock_urlopen):
        """Test successful IPv6 fetch."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'2001:db8::1\n'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        ip = ddns.fetch_ip('https://api64.ipify.org')
        self.assertEqual(ip, '2001:db8::1')
    
    @patch('ddns.urlopen')
    def test_fetch_ip_url_error(self, mock_urlopen):
        """Test handling of URL errors."""
        from urllib.error import URLError
        mock_urlopen.side_effect = URLError('Connection failed')
        
        ip = ddns.fetch_ip('https://invalid.example.com')
        self.assertIsNone(ip)
    
    @patch('ddns.urlopen')
    def test_fetch_ip_http_error(self, mock_urlopen):
        """Test handling of HTTP errors."""
        from urllib.error import HTTPError
        mock_urlopen.side_effect = HTTPError(
            'https://api.ipify.org', 500, 'Server Error', {}, None
        )
        
        ip = ddns.fetch_ip('https://api.ipify.org')
        self.assertIsNone(ip)
    
    @patch('ddns.urlopen')
    def test_fetch_ip_timeout(self, mock_urlopen):
        """Test timeout parameter is used."""
        mock_response = MagicMock()
        mock_response.read.return_value = b'192.0.2.1'
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response
        
        ddns.fetch_ip('https://api.ipify.org', timeout=5)
        
        # Verify timeout was passed to urlopen
        call_args = mock_urlopen.call_args
        self.assertEqual(call_args[1]['timeout'], 5)


class TestValidateIP(unittest.TestCase):
    """Test IP address validation."""
    
    def test_valid_ipv4(self):
        """Test valid IPv4 addresses."""
        self.assertTrue(ddns.validate_ip('192.0.2.1', 4))
        self.assertTrue(ddns.validate_ip('10.0.0.1', 4))
        self.assertTrue(ddns.validate_ip('172.16.0.1', 4))
    
    def test_valid_ipv6(self):
        """Test valid IPv6 addresses."""
        self.assertTrue(ddns.validate_ip('2001:db8::1', 6))
        self.assertTrue(ddns.validate_ip('fe80::1', 6))
        self.assertTrue(ddns.validate_ip('::1', 6))
    
    def test_invalid_ipv4_format(self):
        """Test invalid IPv4 format."""
        self.assertFalse(ddns.validate_ip('256.0.0.1', 4))
        self.assertFalse(ddns.validate_ip('not.an.ip', 4))
        self.assertFalse(ddns.validate_ip('192.0.2', 4))
    
    def test_invalid_ipv6_format(self):
        """Test invalid IPv6 format."""
        self.assertFalse(ddns.validate_ip('gggg::1', 6))
        self.assertFalse(ddns.validate_ip('not:valid:ipv6', 6))
    
    def test_wrong_version(self):
        """Test IPv4 when expecting IPv6 and vice versa."""
        self.assertFalse(ddns.validate_ip('192.0.2.1', 6))
        self.assertFalse(ddns.validate_ip('2001:db8::1', 4))


class TestValidateFQDN(unittest.TestCase):
    """Test FQDN validation."""
    
    def test_valid_fqdn(self):
        """Test valid FQDNs."""
        self.assertTrue(ddns.validate_fqdn('example.com.'))
        self.assertTrue(ddns.validate_fqdn('sub.example.com.'))
        self.assertTrue(ddns.validate_fqdn('deep.sub.example.com.'))
    
    def test_missing_trailing_dot(self):
        """Test FQDN without trailing dot."""
        self.assertFalse(ddns.validate_fqdn('example.com'))
        self.assertFalse(ddns.validate_fqdn('sub.example.com'))
    
    def test_too_short(self):
        """Test FQDN that's too short."""
        self.assertFalse(ddns.validate_fqdn('a.'))
        self.assertFalse(ddns.validate_fqdn('.'))


class TestParseRecordTypes(unittest.TestCase):
    """Test record type parsing."""
    
    def test_single_a_record(self):
        """Test parsing single A record."""
        result = ddns.parse_record_types('A')
        self.assertEqual(result, ['A'])
    
    def test_single_aaaa_record(self):
        """Test parsing single AAAA record."""
        result = ddns.parse_record_types('AAAA')
        self.assertEqual(result, ['AAAA'])
    
    def test_both_records(self):
        """Test parsing both A and AAAA."""
        result = ddns.parse_record_types('A,AAAA')
        self.assertEqual(result, ['A', 'AAAA'])
    
    def test_lowercase_normalized(self):
        """Test that lowercase is normalized to uppercase."""
        result = ddns.parse_record_types('a,aaaa')
        self.assertEqual(result, ['A', 'AAAA'])
    
    def test_whitespace_stripped(self):
        """Test that whitespace is stripped."""
        result = ddns.parse_record_types(' A , AAAA ')
        self.assertEqual(result, ['A', 'AAAA'])
    
    def test_invalid_record_type(self):
        """Test invalid record type raises error."""
        with self.assertRaises(ValueError):
            ddns.parse_record_types('CNAME')
        with self.assertRaises(ValueError):
            ddns.parse_record_types('A,MX')


class TestGetCurrentRecord(unittest.TestCase):
    """Test getting current Route53 record."""
    
    def test_existing_record(self):
        """Test getting existing record."""
        mock_client = MagicMock()
        mock_client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': [{
                'Name': 'example.com.',
                'Type': 'A',
                'ResourceRecords': [{'Value': '192.0.2.1'}]
            }]
        }
        
        ip = ddns.get_current_record(mock_client, 'Z123', 'example.com.', 'A')
        self.assertEqual(ip, '192.0.2.1')
    
    def test_no_existing_record(self):
        """Test when record doesn't exist."""
        mock_client = MagicMock()
        mock_client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': []
        }
        
        ip = ddns.get_current_record(mock_client, 'Z123', 'example.com.', 'A')
        self.assertIsNone(ip)
    
    def test_wrong_record_type(self):
        """Test when record exists but wrong type."""
        mock_client = MagicMock()
        mock_client.list_resource_record_sets.return_value = {
            'ResourceRecordSets': [{
                'Name': 'example.com.',
                'Type': 'AAAA',
                'ResourceRecords': [{'Value': '2001:db8::1'}]
            }]
        }
        
        ip = ddns.get_current_record(mock_client, 'Z123', 'example.com.', 'A')
        self.assertIsNone(ip)
    
    def test_client_error(self):
        """Test handling of AWS client errors."""
        from botocore.exceptions import ClientError
        mock_client = MagicMock()
        mock_client.list_resource_record_sets.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchHostedZone', 'Message': 'Zone not found'}},
            'ListResourceRecordSets'
        )
        
        ip = ddns.get_current_record(mock_client, 'Z123', 'example.com.', 'A')
        self.assertIsNone(ip)


class TestUpdateRecord(unittest.TestCase):
    """Test Route53 record updates."""
    
    def test_successful_update(self):
        """Test successful record update."""
        mock_client = MagicMock()
        mock_client.change_resource_record_sets.return_value = {
            'ChangeInfo': {'Id': '/change/C123'}
        }
        
        result = ddns.update_record(
            mock_client, 'Z123', 'example.com.', 'A', '192.0.2.1', 300
        )
        self.assertTrue(result)
        
        # Verify the call was made correctly
        mock_client.change_resource_record_sets.assert_called_once()
        call_args = mock_client.change_resource_record_sets.call_args[1]
        self.assertEqual(call_args['HostedZoneId'], 'Z123')
        self.assertEqual(
            call_args['ChangeBatch']['Changes'][0]['ResourceRecordSet']['Name'],
            'example.com.'
        )
    
    def test_dry_run_mode(self):
        """Test dry run doesn't make actual changes."""
        mock_client = MagicMock()
        
        result = ddns.update_record(
            mock_client, 'Z123', 'example.com.', 'A', '192.0.2.1', 300, dry_run=True
        )
        self.assertTrue(result)
        
        # Verify no API call was made
        mock_client.change_resource_record_sets.assert_not_called()
    
    def test_update_with_custom_ttl(self):
        """Test update with custom TTL."""
        mock_client = MagicMock()
        mock_client.change_resource_record_sets.return_value = {
            'ChangeInfo': {'Id': '/change/C123'}
        }
        
        ddns.update_record(
            mock_client, 'Z123', 'example.com.', 'A', '192.0.2.1', 60
        )
        
        call_args = mock_client.change_resource_record_sets.call_args[1]
        self.assertEqual(
            call_args['ChangeBatch']['Changes'][0]['ResourceRecordSet']['TTL'],
            60
        )
    
    def test_client_error_handling(self):
        """Test handling of AWS client errors."""
        from botocore.exceptions import ClientError
        mock_client = MagicMock()
        mock_client.change_resource_record_sets.side_effect = ClientError(
            {'Error': {'Code': 'InvalidChangeBatch', 'Message': 'Invalid'}},
            'ChangeResourceRecordSets'
        )
        
        result = ddns.update_record(
            mock_client, 'Z123', 'example.com.', 'A', '192.0.2.1', 300
        )
        self.assertFalse(result)


class TestProcessRecordType(unittest.TestCase):
    """Test the main record processing logic."""
    
    @patch('ddns.fetch_ip')
    @patch('ddns.validate_ip')
    @patch('ddns.get_current_record')
    @patch('ddns.update_record')
    def test_update_needed(self, mock_update, mock_get, mock_validate, mock_fetch):
        """Test when update is needed."""
        mock_fetch.return_value = '192.0.2.2'
        mock_validate.return_value = True
        mock_get.return_value = '192.0.2.1'
        mock_update.return_value = True
        
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.zone_id = 'Z123'
        mock_args.fqdn = 'example.com.'
        mock_args.ttl = 300
        mock_args.timeout = 10
        mock_args.dry_run = False
        
        result = ddns.process_record_type(
            mock_client, mock_args, 'A', 'https://api.ipify.org'
        )
        
        self.assertTrue(result)
        mock_update.assert_called_once()
    
    @patch('ddns.fetch_ip')
    @patch('ddns.validate_ip')
    @patch('ddns.get_current_record')
    @patch('ddns.update_record')
    def test_no_update_needed(self, mock_update, mock_get, mock_validate, mock_fetch):
        """Test when no update is needed."""
        mock_fetch.return_value = '192.0.2.1'
        mock_validate.return_value = True
        mock_get.return_value = '192.0.2.1'
        
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.zone_id = 'Z123'
        mock_args.fqdn = 'example.com.'
        mock_args.timeout = 10
        
        result = ddns.process_record_type(
            mock_client, mock_args, 'A', 'https://api.ipify.org'
        )
        
        self.assertTrue(result)
        mock_update.assert_not_called()
    
    @patch('ddns.fetch_ip')
    def test_fetch_failure(self, mock_fetch):
        """Test handling of IP fetch failure."""
        mock_fetch.return_value = None
        
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.fqdn = 'example.com.'
        mock_args.timeout = 10
        
        result = ddns.process_record_type(
            mock_client, mock_args, 'A', 'https://api.ipify.org'
        )
        
        self.assertFalse(result)
    
    @patch('ddns.fetch_ip')
    @patch('ddns.validate_ip')
    def test_invalid_ip(self, mock_validate, mock_fetch):
        """Test handling of invalid IP."""
        mock_fetch.return_value = 'invalid'
        mock_validate.return_value = False
        
        mock_client = MagicMock()
        mock_args = MagicMock()
        mock_args.fqdn = 'example.com.'
        mock_args.timeout = 10
        
        result = ddns.process_record_type(
            mock_client, mock_args, 'A', 'https://api.ipify.org'
        )
        
        self.assertFalse(result)


class TestIntegration(unittest.TestCase):
    """Integration tests for the full workflow."""
    
    @patch('ddns.boto3.Session')
    @patch('ddns.fetch_ip')
    @patch('ddns.validate_ip')
    @patch('ddns.get_current_record')
    @patch('ddns.update_record')
    def test_full_update_workflow(self, mock_update, mock_get, mock_validate, 
                                   mock_fetch, mock_session):
        """Test complete update workflow."""
        # Setup mocks
        mock_fetch.return_value = '192.0.2.2'
        mock_validate.return_value = True
        mock_get.return_value = '192.0.2.1'
        mock_update.return_value = True
        
        mock_client = MagicMock()
        mock_session.return_value.client.return_value = mock_client
        
        # Run with test args
        test_args = [
            'ddns.py',
            '-z', 'Z123',
            '-d', 'example.com.',
            '-a', 'AKIATEST',
            '-s', 'secretkey'
        ]
        
        with patch.object(sys, 'argv', test_args):
            with self.assertRaises(SystemExit) as cm:
                ddns.main()
            self.assertEqual(cm.exception.code, 0)


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
