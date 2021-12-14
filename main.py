import os
import sys
import json
import socket
import time

import requests

CREDENTIALS_FILE = 'credentials.json'
credentials = None

if not os.path.exists(CREDENTIALS_FILE):
    print('Could not locate credentials.json!')
    sys.exit(1)

with open(CREDENTIALS_FILE, 'r') as file:
    credentials = json.load(file)


def ping_mydnshost():
    """Tests if connection to mydnshost is successful"""
    response = requests.get(f'https://api.mydnshost.co.uk/1.0/ping/{time.time()}')
    if response.status_code in [200, 201, 202]:
        print(f'> Status: OK')
        print(f'> Time: {response.json()["response"]["time"]}')
    else:
        print('Error communicating with MyDnsHost! Please check your internet connection!')
        sys.exit(1)


def get_hostname() -> str:
    """Retrieves hostname for system"""
    return socket.gethostname().strip()


def get_ip():
    """Retrieves public IP address for system"""
    return requests.get('https://checkip.amazonaws.com/').text.strip()


def get_records(domain: str):
    """"Retrieves existing, registered subdomains"""
    headers = {
        'X-API-USER': credentials['registrar']['user'],
        'X-API-KEY': credentials['registrar']['apikey']
    }

    response = requests.get(f'https://api.mydnshost.co.uk/1.0/domains/{domain}/records', headers=headers)

    if response.status_code in [200, 201, 202]:
        return response.json()['response']['records']
    else:
        print('Error fetching domain information! Make sure domain API access is enabled!')
        print(response.json())
        sys.exit(1)


def update_record(recordid, domain, subdomain, response):
    """Updates an existing record"""
    headers = {
        'X-API-USER': credentials['registrar']['user'],
        'X-API-KEY': credentials['registrar']['apikey']
    }
    body = {
        'data': {
            'content': response
        }
    }
    response = requests.post(f'/domains/{domain}/records/{recordid}', headers=headers, json=body)
    if response.status_code in [200, 201, 202] and response.json()['status'] == 'SUCCESS':
        print(f'> Updated: {subdomain}.{domain}')
    else:
        print(f'> Error updating: {subdomain}.{domain}')
        sys.exit(1)


def create_record(domain, subdomain, response):
    """Creates a new record"""
    headers = {
        'X-API-USER': credentials['registrar']['user'],
        'X-API-KEY': credentials['registrar']['apikey']
    }

    body = {
        'data': {
            'records': [
                {
                    'type': 'A',
                    'name': subdomain,
                    'content': response,
                    'ttl': 600
                }
            ]

        }
    }

    response = requests.post(f'https://api.mydnshost.co.uk/1.0/domains/{domain}/records', headers=headers, json=body)
    if response.status_code in [200, 201, 202]:
        print(f'> Created: {subdomain}.{domain}')
    else:
        print(f'> Error creating: {subdomain}.{domain}')
        print(f'> Status: {response.json()["status"]}')
        sys.exit(1)


def main():
    print(('=' * 5) + ' AstralJaeger\'s domain update tool for MyDNSHost.co.uk')
    ping_mydnshost()
    hostname = get_hostname()
    print(f'> Hostname: {hostname}')
    ip = get_ip()

    if len(sys.argv) != 2:
        print('Application requires exactly one argument!')
        sys.exit(1)

    domain = sys.argv[1]

    print(f'Found the following records for {domain}:')
    current_record = None
    records = get_records(domain)

    header = f' {"Index":>5s} | {"Id":>9s} | {"Name":>32s} | {"Type":>5s} | {"TTL":>5s} | {"Content":>16s}'
    print(header)
    print('-'*len(header))
    for index, record in enumerate(records, 1):
        print(f' {index:>5d} | {record["id"]:>9d} | {record["name"]:>32s} | {record["type"]:>5s} | {record["ttl"]:>5d} | {record["content"]:>16s}')
        if record['type'] == 'A' and hostname in record['name'].split('.'):
            current_record = record
    print('-' * len(header))

    if current_record is not None:
        if ip == current_record['content']:
            print('IP on record already up to date!')
            print('Done.')
            sys.exit(0)

        print('Record already exists, updating existing record')
        update_record(current_record['id'], domain, hostname, ip)

    else:
        print('Record does not exist, creating new record')
        create_record(domain, hostname, ip)

    print('Done.')
    sys.exit(0)


if __name__ == '__main__':
    main()
