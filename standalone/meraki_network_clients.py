"""
A standalone script to get Meraki network clients."""

from asyncio import Semaphore
import asyncio
import os
import sys
from dotenv import load_dotenv
sys.path.append('..')
import netmanage.run_collectors as rc  # noqa
from netmanage.collectors import meraki_collectors as mc  # noqa
from netmanage.helpers import helpers as hp  # noqa


def main():
    load_dotenv(override=True)
    meraki_api_key = os.environ['meraki_api_key']
    networks = os.environ['meraki_networks'].split(',')
    orgs = os.environ['meraki_organizations'].split(',')
    database_name = os.environ['database_name']
    database_path = os.path.expanduser(os.environ['database_path'])
    database_full_path = f'{database_path}/{database_name}'

    networks = list(filter(None, [_.strip() for _ in networks]))
    orgs = list(filter(None, [_.strip() for _ in orgs]))

    timestamp = hp.set_db_timestamp()

    df = asyncio.run(
        mc.meraki_get_network_clients(meraki_api_key,
                                      networks=networks,
                                      orgs=orgs,
                                      total_pages='all',
                                      sem=Semaphore(2)))

    rc.add_to_db('MERAKI_NETWORK_CLIENTS',
                 df,
                 timestamp,
                 database_full_path)


if __name__ == '__main__':
    main()
