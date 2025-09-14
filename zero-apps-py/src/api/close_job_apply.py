import hashlib
import json
import requests

traits = ["Craftsman", "Pragmatic", "Curious", "Methodical", "Driven", "Collaborator"]
key = "Close-f05f05e3"
hashes = [
    hashlib.blake2b(trait.encode('utf-8'), key=key.encode('utf-8'), digest_size=64).hexdigest()
    for trait in traits
]

# Replace with the actual endpoint URL
endpoint = "https://api.close.com/buildwithus/?Key=???"

response = requests.post(endpoint, json=hashes)
print("Status Code:", response.status_code)
print("Response:", response.text)