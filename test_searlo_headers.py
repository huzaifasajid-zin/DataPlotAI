import requests

api_key = "your api_key"
query = "site:linkedin.com/in/ Database Lahore"

headers_to_try = [
    {"Authorization": f"Bearer {api_key}"},
    {"x-api-key": api_key},
    {"api_key": api_key},
    {"X-API-KEY": api_key}
]

url = "https://api.searlo.tech/api/v1/search"

for headers in headers_to_try:
    print(f"\nTesting headers: {headers}")
    try:
        res = requests.get(f"{url}?q={query}", headers=headers, timeout=10)
        print(f"GET Status: {res.status_code}")
        if res.status_code == 200:
            print(res.json())
            break
            
        res = requests.post(url, headers=headers, json={"query": query}, timeout=10)
        print(f"POST Status: {res.status_code}")
        if res.status_code == 200:
            print(res.json())
            break
    except Exception as e:
        print(f"Error: {e}")
