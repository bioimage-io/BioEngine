import asyncio
from hypha_rpc import connect_to_server
from pydantic import Field

async def main():
    # Connect to the Hypha server
    server_url = "https://hypha.aicell.io"
    workspace_id = "bioengine-apps"
    service_id = "ray-function-registry"

    server = await connect_to_server({"server_url": server_url})

    # Retrieve the Ray Function Registry service
    svc = await server.get_service(f"{workspace_id}/{service_id}")

    # Example script to classify an image using ResNet
    example_script = """
import torch
import torchvision.transforms as transforms
from PIL import Image
import requests
from io import BytesIO

def execute(image_url: str):
    # Load the image from the URL
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    # Define the transform to match what the model expects
    preprocess = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    # Apply the preprocessing
    img_tensor = preprocess(img)
    img_tensor = img_tensor.unsqueeze(0)  # Add a batch dimension

    # Load the ResNet model
    model = torch.hub.load('pytorch/vision:v0.10.0', 'resnet18', pretrained=True)
    model.eval()

    # Perform the inference
    with torch.no_grad():
        output = model(img_tensor)
    
    # Load the labels for ImageNet
    labels = requests.get("https://raw.githubusercontent.com/anishathalye/imagenet-simple-labels/master/imagenet-simple-labels.json").json()
    
    # Find the top predicted class
    _, predicted_idx = torch.max(output, 1)
    predicted_label = labels[predicted_idx.item()]

    return predicted_label
"""

    # Register the ResNet function
    pip_requirements = ['torch', 'torchvision', 'requests', 'pillow']
    function_id = await svc.register_function(name="ResNet image classifier", script=example_script, pip_requirements=pip_requirements)
    print(f"Registered ResNet function with id: {function_id}")

    # Example image URL
    image_url = "https://cdn2.thecatapi.com/images/9vs.jpg"

    # Run the ResNet function
    result = await svc.run_function(function_id=function_id, args=[image_url])
    print("Classification Result:", result)

if __name__ == "__main__":
    asyncio.run(main())
