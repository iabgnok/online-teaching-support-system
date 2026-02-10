import requests
url = 'http://localhost:5000/api/v1/contacts/requests'
headers = {'Authorization': 'Bearer eyJ1c2VyX2lkIjoyMDAxfQ.aYmZbQ.6B_gmTr-jz4c5LqCz3TIykHVJew', 'Content-Type':'application/json'}
resp = requests.post(url, json={'target_id': 3004, 'message': "Hi from API test"}, headers=headers)
print(resp.status_code, resp.text)
