import requests

# CONFIGURATION
BASE_URL = "http://localhost:9621" 

headers = {
    "Content-Type": "application/json",
}

client = requests.Session()
client.headers.update(headers)

def check_health():
    try:
        response = client.get(f"{BASE_URL}/health") # OR /status or /ping
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        return f"Error: {err}"

if __name__ == "__main__":
    status = check_health()
    print(f"""
        status : {status['status']}
        llm_model : {status['configuration']['llm_model']}
        embedding_model : {status['configuration']['embedding_model']}
    """)