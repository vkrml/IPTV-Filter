import os
import requests
import time
from urllib.parse import urlparse

# --- Configuration ---
INPUT_FILE = "links.txt"
OUTPUT_FILE = "gofile_logs.txt"

class GofileUploader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    def get_server(self):
        """Finds the best available Gofile server"""
        try:
            response = self.session.get('https://api.gofile.io/servers')
            data = response.json()
            if data['status'] == 'ok':
                # Prefer Asia/Zone servers if available, else take first
                servers = data['data']['servers']
                return servers[0]['name']
            return 'store1'
        except Exception:
            return 'store1'

    def upload(self, file_path):
        """Uploads file to Gofile"""
        server = self.get_server()
        print(f"   -> Uploading to {server}...")
        
        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        
        try:
            with open(file_path, 'rb') as f:
                response = self.session.post(
                    f'https://{server}.gofile.io/uploadFile',
                    files={'file': (file_name, f)},
                    stream=True
                )
                data = response.json()
                if data['status'] == 'ok':
                    return data['data']['downloadPage']
                else:
                    return None
        except Exception as e:
            print(f"   -> Upload Error: {e}")
            return None

def download_from_ddl(url):
    """Downloads the file from the DDL link to a temp path"""
    try:
        # Extract filename from URL
        a = urlparse(url)
        filename = os.path.basename(a.path)
        if not filename:
            filename = f"temp_file_{int(time.time())}"
        
        print(f"1. Downloading: {filename}")
        
        # Stream download to avoid memory issues
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        return filename
    except Exception as e:
        print(f"   -> Download Error: {e}")
        return None

def main():
    # Ensure output file exists
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w') as f:
            f.write(f"--- Upload Log {time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")

    # Read Links
    try:
        with open(INPUT_FILE, 'r') as f:
            links = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found.")
        return

    uploader = GofileUploader()

    for i, link in enumerate(links):
        print(f"\n[{i+1}/{len(links)}] Processing: {link}")
        
        # Step 1: Download from DDL
        local_filename = download_from_ddl(link)
        
        if local_filename and os.path.exists(local_filename):
            # Step 2: Upload to Gofile
            gofile_link = uploader.upload(local_filename)
            
            if gofile_link:
                print(f"   -> Success: {gofile_link}")
                # Step 3: Save to file
                with open(OUTPUT_FILE, 'a') as f:
                    f.write(f"Source: {link}\nGofile: {gofile_link}\n-------------------\n")
            else:
                print("   -> Failed to upload to Gofile")
            
            # Step 4: Cleanup (Delete local file to free up runner space)
            os.remove(local_filename)
        else:
            print("   -> Failed to download source file.")

if __name__ == "__main__":
    main()
