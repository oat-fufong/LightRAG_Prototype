import requests
import sys
import os

# CONFIGURATION
BASE_URL = f"http://localhost:{sys.argv[1]}" 

client = requests.Session()

def check_health():
    try:
        response = client.get(f"{BASE_URL}/health")
        response.raise_for_status()
        status = response.json()
        print(f"""
        status          : {status['status']}
        llm_model       : {status['configuration']['llm_model']}
        embedding_model : {status['configuration']['embedding_model']}
        """)
    except requests.exceptions.RequestException as err:
        print(f"Error: {err}")

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
    check_health()
