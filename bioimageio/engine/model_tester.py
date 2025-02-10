import os

import ray
from hypha_rpc import connect_to_server
from ray import serve


@serve.deployment(
    ray_actor_options={"num_gpus": 1, "num_cpus": 1},
    max_ongoing_requests=1,
    num_replicas=1,
    max_replicas_per_node=1,
    max_queued_requests=10,
)
class ModelTester:
    def __init__(self):
        pass

    async def _download_model(self, model_url: str, package_path: str) -> str:
        import os
        import zipfile
        from pathlib import Path

        import aiohttp

        archive_path = package_path + ".zip"

        async with aiohttp.ClientSession() as session:
            async with session.get(model_url) as response:
                if response.status != 200:
                    raise RuntimeError(f"Failed to download model from {model_url}")
                content = await response.read()
                with open(archive_path, "wb") as f:
                    f.write(content)

        # Unzip package_path
        with zipfile.ZipFile(archive_path, "r") as zip_ref:
            zip_ref.extractall(package_path)

        # Cleanup the archive file
        os.remove(archive_path)

        return Path(package_path)

    async def validate(self, rdf_dict):
        from bioimageio.spec import ValidationContext, validate_format

        ctx = ValidationContext(perform_io_checks=False)
        summary = validate_format(rdf_dict, context=ctx)
        return {"success": summary.status == "passed", "details": summary.format()}

    async def __call__(self, model_id, model_url=None):
        import shutil
        from bioimageio.core import test_model
        from bioimageio.spec import save_bioimageio_package_as_folder

        package_path = f"/tmp/bioengine/{model_id}"

        if model_url is not None:
            package_path = await self._download_model(model_url, package_path)
        else:
            package_path = save_bioimageio_package_as_folder(
                model_id, output_path=package_path
            )

        assert package_path.exists()

        result = test_model(package_path / "rdf.yaml").model_dump(mode="json")
    
        # Cleanup after test run
        shutil.rmtree(str(package_path))
        
        return result


async def ping(context):
    return "pong"


async def test_model(model_id, model_url=None, context=None):
    print(f"Running model '{model_id}'")

    app_handle = ray.serve.get_app_handle("bioengine")

    return await app_handle.remote(model_id, model_url)


async def validate(rdf_dict, context=None):
    print("Validating RDF dict")
    app_handle = ray.serve.get_app_handle("bioengine")

    return await app_handle.validate.remote(rdf_dict)


async def register_resvice():
    RAY_ADDRESS = os.getenv("RAY_ADDRESS", "ray://raycluster-kuberay-head-svc.ray-cluster.svc.cluster.local:10001")
    HYPHA_SERVER_URL = os.getenv("HYPHA_SERVER_URL", "https://hypha.aicell.io")
    HYPHA_WORKSPACE = os.getenv("HYPHA_WORKSPACE", "bioimage-io")
    HYPHA_SERVICE_ID = os.getenv("HYPHA_SERVICE_ID", "bioimageio-model-runner")
    HYPHA_TOKEN = os.getenv("HYPHA_TOKEN")
    assert HYPHA_TOKEN, "Please set the HYPHA_TOKEN environment variable"
                                                
    # Connect to Ray head node
    print(f"Initializing Ray with address: {RAY_ADDRESS}")
    ray.init(
        address=RAY_ADDRESS,
        runtime_env={
            "pip": [
                "torch==2.5.1",
                "torchvision==0.20.1",
                "tensorflow==2.16.1",
                "onnxruntime==1.20.1",
                "bioimageio.core==0.7.0",
                "hypha-rpc",
            ],
        },
    )

    # Bind the arguments to the deployment and return an Application.
    app = ModelTester.bind()

    # Deploy the application
    ray.serve.run(app, name="bioengine", route_prefix=None)

    client = await connect_to_server(
        {"server_url": HYPHA_SERVER_URL, "workspace": HYPHA_WORKSPACE, "token": HYPHA_TOKEN}
    )

    # Register the service
    service_info = await client.register_service(
        {
            "id": HYPHA_SERVICE_ID,
            "config": {
                "visibility": "public",
                "require_context": True,
            },
            # Exposed functions:
            "ping": ping,
            "test_model": test_model,
            "validate": validate,
        }
    )
    sid = service_info["id"]

    print(f"Service registered with ID: {sid}")
    
    await client.serve()


if __name__ == "__main__":
    import asyncio

    asyncio.run(register_resvice())
