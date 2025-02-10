import asyncio
from hypha_rpc import connect_to_server

async def main():
    # Connect to the Hypha server
    server_url = "https://hypha.aicell.io"
    workspace_id = "bioengine-apps"
    service_id = "ray-function-registry"

    server = await connect_to_server({"server_url": server_url})

    # Retrieve the Ray Function Registry service
    svc = await server.get_service(f"{workspace_id}/{service_id}")
    # Example image URL
    image_url = "https://i.natgeofe.com/n/d7c8f811-670c-434e-b451-5d08793dade0/NationalGeographic_2802033.jpg"
    functions = await svc.list_functions()
    # Fine the function named "ResNet image classifier"
    resnet_function = next((f for f in functions if f["name"] == "ResNet image classifier"), None)
    # Run the ResNet function
    result = await svc.run_function(function_id=resnet_function["id"], args=[image_url])
    print("Classification Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
