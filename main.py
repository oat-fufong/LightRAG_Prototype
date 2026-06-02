import requests
import sys
import os
import glob
import time
from datetime import timedelta
from requests.adapters import HTTPAdapter, Retry

# CONFIGURATION
BASE_URL = f"http://localhost:{sys.argv[1]}" 
HOST_INPUT_DIR = sys.argv[2]
FILE_TO_PROCESS = sys.argv[3]  # 'all' = process everything
CHECK_INTERVAL_RAW = sys.argv[4]  # Check every x seconds

REQUIRED_VARS = [HOST_INPUT_DIR, CHECK_INTERVAL_RAW]
if any(var is None for var in REQUIRED_VARS):
    print(f"Missing required environment variables. Exiting.")
    sys.exit(1)
else:
    print(f"{REQUIRED_VARS} succesfully loaded.")

CHECK_INTERVAL = int(CHECK_INTERVAL_RAW)

client = requests.Session()

retries = Retry(total=10,
                backoff_factor=0.1,
                status_forcelist=[ 500, 502, 503, 504 ])

client.mount('http://', HTTPAdapter(max_retries=retries))

# Start Timer
start_time = time.time()
start_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')

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
            print(response.json())

            return True
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return False
    except Exception as e:
        print(f"Upload Error: {str(e)}")
        return False    

def reprocess_doc():
    try:

        response = client.post(f"{BASE_URL}/documents/reprocess_failed")

        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Upload Error: {str(e)}"
    
def get_file_list():
    if FILE_TO_PROCESS == 'all':
        # Scan directory for files
        pattern = os.path.join(HOST_INPUT_DIR, '*')
        files = glob.glob(pattern)
        # Only add files (not directories)
        return [f.split('/')[-1] for f in files if os.path.isfile(f)]
    
    else:
        # Split by comma
        return [HOST_INPUT_DIR + '/' + f.strip() + ".txt" for f in FILE_TO_PROCESS.split(',') if f.strip()]

def get_status_counts():
    try:
        response = client.get(f"{BASE_URL}/documents/status_counts")
        response.raise_for_status()
        result = response.json()

        counts = result.get('status_counts', {})
        if 'all' not in counts:
            counts['all'] = sum(counts.values())

        return counts
    except requests.exceptions.HTTPError as e:
        return f"HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return f"Upload Error: {str(e)}"

def wait_until_processing_complete(total_files=0, check_interval=CHECK_INTERVAL):
    """
    Poll status_counts endpoint until processing is complete
    or a document failed
    """
    print("\nWaiting for document processing to complete...")

    attempt = 0
    max_attempts = 50
    checked_count = 0
    failed_count = 0

    while attempt < max_attempts:
        checked_count += 1
        
        counts = get_status_counts()
        
        if not counts:
            print(f"[{checked_count}] Status unavailable, retrying...")
            time.sleep(check_interval)
            continue
        
        # Extract count values
        pending = counts.get('pending', 0)
        processing = counts.get('processing', 0)
        preprocessed = counts.get('preprocessed', 0)
        processed = counts.get('processed', 0)
        failed = counts.get('failed', 0)
        all_count = counts.get('all', pending + processing + preprocessed + processed + failed)
        
        # Build status indicator
        current_time = time.strftime('%H:%M:%S')
        all_status = f"P:{pending} | W:{processing} | PP:{preprocessed} | ✓:{processed} | ✗:{failed}"
        total = all_count
        
        if total > 0:
            percent_done = (processed / total) * 100 if total else 0
        else:
            percent_done = 0
        
        print(f"  [{current_time}] [{checked_count}] [{all_status}] ({percent_done:.1f}%)")
        
        # Check if any documents failed
        if failed > 10:
            print(f"\n{failed} document(s) FAILED during processing!")
            failed_count += 1
            reprocess_doc()
        
        # Wait until processed + failed == total_files
        if (processed + failed) >= total_files:
            print(f"\n✅ All processing complete!")
            print(f"Processed: {processed}/{total_files}")
            print(f"Failed: {failed}/{total_files}")
            return processed
        
        # Safety: Exit early if processing stopped
        if processing == 0 and pending == 0 and processed + failed < total_files:
            print(f"\nWARNING: No processing activity, but {total_files - (processed + failed)} files not complete")
            # Don't exit, keep waiting to be sure
            time.sleep(check_interval)
            continue
        
        time.sleep(check_interval)
    
    # Timeout
    print(f"\n⚠️  Timeout: Processing not complete after {failed_count} fails")
    sys.exit(0)

def formatted_time(seconds):
    """Format seconds into human-readable time"""
    return str(timedelta(seconds=int(seconds)))

if __name__ == "__main__":
    print("=" * 70)
    print(f"🕐 Start Time: {start_timestamp}")
    print(f"📁 HOST_INPUT_DIR: {HOST_INPUT_DIR}")
    print(f"📋 FILE_TO_PROCESS: {FILE_TO_PROCESS}")
    print("=" * 70)

    check_health()

    # Upload & Process Files 
    files = get_file_list()
    total_files = len(files)

    if not files:
        print("⚠️  No files found to process!")
        sys.exit(0)

    print(f"Found {total_files} file(s) to process")

    for filename in files:
        if upload_doc(filename):
            print(f"{filename} has been uploaded")
        else:
            print(f"{filename} failed to load")
            sys.exit(0)

    # Status Check
    success_count = wait_until_processing_complete(total_files=total_files)

    # ✅ FINAL SUMMARY
    end_time = time.time()
    end_timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    total_elapsed = end_time - start_time
    
    print("\n" + "=" * 70)
    print(f"📊 FINAL SUMMARY")
    print("=" * 70)
    print(f"🕐 Start: {start_timestamp}")
    print(f"🕐 End:   {end_timestamp}")
    print(f"⏱️  Total Time: {formatted_time(total_elapsed)} ({int(total_elapsed)} seconds)")
    print(f"✅ Success: {success_count}/{len(files)} files")
    print("=" * 70)
    



    