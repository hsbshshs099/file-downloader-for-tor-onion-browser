#!/usr/bin/env python3
import requests
import threading
import os
import sys
import random
import string
import time
from tqdm import tqdm

# --- Configuration ---
TOR_PORT = 9050  # Default port for Linux Tor daemon (systemctl start tor)
TOR_HOST = '127.0.0.1'
THREADS = 16     # 16 threads for high speed

# Timeout for connection attempts
TIMEOUT = 45

def get_tor_session():
    """Create a fresh Tor circuit using random credentials."""
    session = requests.session()
    # Random credentials force Tor to create a NEW circuit
    rnd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    proxy_url = f'socks5h://{rnd}:{rnd}@{TOR_HOST}:{TOR_PORT}'
    session.proxies = {'http': proxy_url, 'https': proxy_url}
    return session

def get_file_info(url):
    """Fetch file size and resume capability."""
    print(f"[*] Metadata fetch kar raha hoon...")
    try:
        session = get_tor_session()
        # Try HEAD request first
        try:
            resp = session.head(url, timeout=30, allow_redirects=True)
            if resp.status_code >= 400: raise Exception("Head failed")
        except:
            # Fallback to GET request (first byte only)
            resp = session.get(url, stream=True, timeout=30, headers={'Range': 'bytes=0-1'})
            resp.close()

        size = int(resp.headers.get('content-length', 0))
        # Check if server supports 'Range' (Resume feature requires this)
        accept_ranges = resp.headers.get('accept-ranges', 'none')
        can_split = 'bytes' in accept_ranges or (size > 0 and resp.status_code == 206)
        
        final_url = resp.url
        return size, can_split, final_url
    except Exception as e:
        print(f"[!] Error: Server se connect nahi ho pa raha. ({e})")
        sys.exit(1)

def download_chunk(url, start, end, chunk_id, progress_bar, part_filename):
    """
    Worker with TRUE RESUME capability.
    Checks existing file size and resumes exactly from there.
    """
    total_bytes_for_chunk = end - start + 1
    
    # --- RESUME LOGIC ---
    downloaded_bytes = 0
    mode = 'wb' # Default write mode
    
    if os.path.exists(part_filename):
        existing_size = os.path.getsize(part_filename)
        
        if existing_size == total_bytes_for_chunk:
            # Part pura complete hai
            progress_bar.update(existing_size)
            return
        elif existing_size < total_bytes_for_chunk:
            # Part aadha hai, resume karein
            downloaded_bytes = existing_size
            start += existing_size # Shift start position
            mode = 'ab' # Append mode (aage jodo)
            progress_bar.update(existing_size)
        else:
            # File size zyada hai (Corrupt), delete and restart
            os.remove(part_filename)

    # Calculate remaining bytes
    headers = {'Range': f'bytes={start}-{end}'}

    while True: # Infinite Retry Loop
        try:
            if start > end: break # Already done

            session = get_tor_session()
            with session.get(url, headers=headers, stream=True, timeout=TIMEOUT) as r:
                r.raise_for_status()
                with open(part_filename, mode) as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress_bar.update(len(chunk))
                            downloaded_bytes += len(chunk)
            break # Success, break loop
            
        except Exception as e:
            # Agar fail hua, toh sirf loop repeat hoga.
            # Range header automatically next attempt mein wahi rahega.
            time.sleep(random.randint(2, 5)) 

def merge_files(filename, num_chunks):
    """Sare parts ko jodkar final file banata hai."""
    print(f"\n[*] Parts ko merge kar raha hoon...")
    with open(filename, 'wb') as outfile:
        for i in range(num_chunks):
            part_name = f"{filename}.part{i}"
            if os.path.exists(part_name):
                with open(part_name, 'rb') as infile:
                    outfile.write(infile.read())
                os.remove(part_name) # Part delete kar do
            else:
                print(f"[!] Error: Part {i} gayab hai!")

def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <onion_url>")
        return

    url = sys.argv[1]
    
    # 1. Tor Connection Check
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if s.connect_ex((TOR_HOST, TOR_PORT)) != 0:
        print(f"\n[!] Error: Tor daemon port {TOR_PORT} par run nahi kar raha!")
        print("    Agar Tor install nahi hai, toh terminal me run karein:")
        print("      sudo apt update && sudo apt install tor")
        print("    Agar installed hai, toh service start karein:")
        print("      sudo systemctl start tor")
        print("    (Agar aap Tor Browser use kar rahe hain, toh code me TOR_PORT = 9150 karein)")
        return
    s.close()

    # 2. Get File Info
    file_size, can_split, final_url = get_file_info(url)
    filename = final_url.split('/')[-1].split("?")[0] or "download.dat"
    
    print(f"[*] File: {filename}")
    print(f"[*] Size: {file_size / (1024*1024):.2f} MB")
    
    if not can_split:
        print("[!] Server resume/split support nahi karta. Normal download start...")
        # Fallback to single thread
        session = get_tor_session()
        with session.get(url, stream=True) as r, open(filename, 'wb') as f:
             for chunk in tqdm(r.iter_content(chunk_size=8192), total=file_size//8192, unit='KB'):
                 f.write(chunk)
        return

    # 3. Setup Threads
    chunk_size = file_size // THREADS
    ranges = []
    for i in range(THREADS):
        start = i * chunk_size
        end = start + chunk_size - 1 if i < THREADS - 1 else file_size
        ranges.append((start, end))

    print(f"[*] {THREADS} Threads start ho rahe hain (Resume Supported)...")
    
    # Tqdm config for proper resume display
    progress = tqdm(total=file_size, unit='B', unit_scale=True, desc="Status", smoothing=0.1)
    
    threads = []
    for i, (start, end) in enumerate(ranges):
        part_name = f"{filename}.part{i}"
        t = threading.Thread(target=download_chunk, args=(url, start, end, i, progress, part_name))
        t.daemon = True
        threads.append(t)
        t.start()

    # Wait loop
    try:
        for t in threads:
            while t.is_alive():
                t.join(1)
    except KeyboardInterrupt:
        print("\n[!] Download paused. Agli baar wahi se shuru hoga.")
        sys.exit(0)

    progress.close()
    merge_files(filename, THREADS)
    print("\n[✓] Download Complete!")

if __name__ == "__main__":
    main()