import requests
import uuid

url = ""

# Génère une clé hwid
hwid = str(uuid.getnode())

data = {
    "key": "TEST-ABC-123",
    "hwid": hwid
}

response = requests.post(url, json=data)

print("Status code:", response.status_code)
print("Réponse du serveur:", response.json())
