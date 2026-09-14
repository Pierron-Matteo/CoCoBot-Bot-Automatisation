import requests

SERVER_URL = ""

license_key = "TEST-1234-5678"
duration_days = 9999

response = requests.post(f"{SERVER_URL}/create_license", json={
    "key": license_key,
    "duration_days": duration_days
})

print("Status code:", response.status_code)
print("Réponse du serveur:", response.text)
