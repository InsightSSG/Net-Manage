#!/usr/bin/env python3

import asyncio
from meraki.aio import AsyncDashboardAPI


async def meraki_get_network_clients(api_key, network_ids):
    """
    Get all clients for a list of network IDs.
    """
    async def get_clients_for_network(dashboard, network_id):
        """
        Get all clients for a single network ID.
        """
        # get all the clients for the network
        clients = await dashboard.networks.getNetworkClients(network_id)
        print(f'Clients for network {network_id}:')
        for client in clients:
            print(f"   {client['id']}: {client['description']}")

    async with AsyncDashboardAPI(api_key) as dashboard:
        # schedule get_clients_for_network() for all network_ids to run concurrently
        await asyncio.gather(*(get_clients_for_network(dashboard, network_id) for network_id in network_ids))


# Replace 'your_api_key' with your actual Meraki API key
# Replace ['net1', 'net2'] with your actual network IDs
asyncio.run(meraki_get_network_clients('your_api_key', ['net1', 'net2']))
