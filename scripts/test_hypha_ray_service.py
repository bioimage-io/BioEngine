import asyncio
from hypha_rpc import connect_to_server

async def main():
    # Replace with the actual server URL and workspace/service ID as needed
    server_url = "https://hypha.aicell.io"
    workspace_id = "bioengine-apps"
    service_id = "ray-function-registry"

    # Connect to the Hypha server
    server = await connect_to_server({"server_url": server_url})

    # Retrieve the Ray Function Registry service
    svc = await server.get_service(f"{workspace_id}/{service_id}")

    # List registered functions
    registered_functions = await svc.list_functions()
    print("Registered Functions:", registered_functions)

    # Run a registered function if available
    if registered_functions:
        function = registered_functions[0]  # Assuming there's at least one registered function

        # Example arguments for the function
        args = ["https://ichef.bbci.co.uk/images/ic/720x405/p0517py6.jpg"]
        kwargs = {}

        # Invoke the function
        result = await svc.run_function(function_id=function["id"], args=args, kwargs=kwargs)
        print("Function Result:", result)
    else:
        print("No functions registered.")

if __name__ == "__main__":
    asyncio.run(main())
