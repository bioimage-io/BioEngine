

import os
import asyncio
from hypha_rpc import login, connect_to_server

async def start_server(server_url):
    print(f"Connecting to server at {server_url}")
    token = await login({"server_url": server_url})
    server = await connect_to_server({'server_url': server_url, "token": token})

    ws = await server.create_workspace({
        "name": "bioengine-apps",
        "description": "Workspace for bioengine",
        "persistent": True,
    })
    
    print(f"Workspace created: {ws['name']}")
    
    
if __name__ == '__main__':
    server_url = 'https://hypha.aicell.io'
    print(f"Starting server with URL: {server_url}")
    asyncio.run(start_server(server_url))
