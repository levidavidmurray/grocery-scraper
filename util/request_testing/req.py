#! ../../venv/bin/python
import requests
import json

headers = {
    'Authorization': '0953ab9d-e403-436d-acec-22848305c15e',
    'Accept': 'application/vnd.mywebgrocer.grocery-list+json',
    'Accept-Language': 'en-CA',
    'Referer': 'https://shop.saveonfoods.com/store/3EA81116/',
    'Sec-Metadata': 'destination="", site=same-origin',
    'X-Requested-With': 'XMLHttpRequest'
}

params = {
    'userId': '26f3c90a-11e4-43d4-ba5a-caf9bb3a6384',
    'sort': 'Brand',
    'skip': '0',
    'take': '40'
}

url = 'https://shop.saveonfoods.com/api/product/v7/products/category/622/store/3EA81116'

request = requests.get(url, headers=headers, params=params)
response = json.dumps(request.json())

with open('response.json', 'w') as file:
    file.write(response)
