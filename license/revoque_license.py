import requests

url = ""
data = {"key": "TEST-ABC-123"}

response = requests.post(url, json=data)
print(response.json())
