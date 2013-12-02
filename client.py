# Test Client for Bitcasa Python SDK
from bitcasa import Bitcasa

# Start Client
client = Bitcasa('config.json')
print("Bitcasa has been authorized with your account.")
print("### Folder List (/) ###")
print(client.list_folder('/'))
print("### Adding Folder ###")
print(client.add_folder("Test", "/VeKqFJiJSbqdoV5XFwbxxg"))


