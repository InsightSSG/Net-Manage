"""
A standalone script to get Meraki CDP and LLDP neighbors for all organizations
that a user's API key has access to."""

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
    database_name = os.environ['database_name']
    database_path = os.path.expanduser(os.environ['database_path'])
    database_full_path = f'{database_path}/{database_name}'

    timestamp = hp.set_db_timestamp()

    df = asyncio.run(
        mc.meraki_get_device_cdp_lldp_neighbors(
            meraki_api_key, database_full_path))

    rc.add_to_db('MERAKI_CDP_LLDP_NEIGHBORS',
                 df,
                 timestamp,
                 database_full_path)


if __name__ == '__main__':
    main()
