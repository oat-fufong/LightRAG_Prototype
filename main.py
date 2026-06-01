import requests
import os

# CONFIGURATION
BASE_URL = "http://localhost:9621" 

client = requests.Session()

def check_health():
    try:
        response = client.get(f"{BASE_URL}/health") # OR /status or /ping
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        return f"Error: {err}"

def upload_doc(path_to_doc):
    try:
        with open(path_to_doc, 'rb') as f:
            payload = {
                'file': (os.path.basename(path_to_doc), f)
            }
            response = client.post(f"{BASE_URL}/documents/upload", 
                                   files=payload)
            
            response.raise_for_status()
            return response.json()
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Upload Error: {str(e)}"

def reprocess_doc():
    try:

        response = client.post(f"{BASE_URL}/documents/reprocess_failed")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Upload Error: {str(e)}"

if __name__ == "__main__":
    status = check_health()
    print(f"""
        status : {status['status']}
        llm_model : {status['configuration']['llm_model']}
        embedding_model : {status['configuration']['embedding_model']}
    """)