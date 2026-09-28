Tor Multi-Threaded Accelerator 🧅🚀

A Python-based, highly resilient, multi-threaded download manager designed specifically for the Tor network (.onion links).

Downloading large files over Tor can often be slow and unreliable due to dropped connections and circuit changes. This tool circumvents those issues by splitting the download into multiple chunks, downloading them concurrently through separate Tor circuits, and offering true resume capabilities.

✨ Features

Multi-Threaded Downloading: Splits the file into multiple parts (default 16 threads) and downloads them simultaneously, significantly accelerating download speeds over the Tor network.

Isolated Tor Circuits: Generates random credentials for each thread's session, forcing Tor to create a unique, fresh circuit for every chunk. This distributes the load and bypasses speed restrictions on single nodes.

True Resume Capability: If your connection drops or you stop the script (Ctrl+C), you won't lose your progress. The script remembers exactly where each thread left off and will resume downloading only the remaining bytes upon restart.

Infinite Retry Mechanism: Automatically handles failed connections, timeouts, or Tor circuit collapses by silently retrying the chunk without crashing.

Dynamic Progress Tracking: Utilizes tqdm for a clean, unified progress bar that scales accurately even when resuming paused downloads.

📋 Requirements

Before running the script, ensure you have Tor installed and running on your system.

1. Install Tor

For Linux (Debian/Ubuntu):

sudo apt update
sudo apt install tor
sudo systemctl start tor
sudo systemctl enable tor # (Optional) Start Tor on boot


Note: This starts the Tor background service on the default port 9050.

For Windows / MacOS / Tor Browser Users:
If you prefer not to install the background service, simply open the Tor Browser and leave it running in the background. The Tor Browser listens on port 9150.

Important: If you use the Tor Browser method, you must change line 12 in the script to TOR_PORT = 9150.

2. Install Python Dependencies

This script requires Python 3. Install the required Python packages using pip:

pip3 install requests pysocks tqdm


🚀 Usage

Run the script from your terminal, passing the .onion (or clearnet) URL as an argument.

# Make the script executable (Linux/macOS only)
chmod +x tor_accelerator.py

# Run the downloader
./tor_accelerator.py 


Example:

python3 tor_accelerator.py http://exampleonionlink.onion/large_file.zip


Pausing and Resuming

Pause: Press Ctrl+C while the download is running. The script will safely exit.

Resume: Run the exact same command again. The script will detect the .part files in the current directory, calculate the missing bytes, and resume seamlessly.

⚙️ Configuration

You can easily adjust the script's behavior by editing the variables at the top of the file:

TOR_PORT = 9050  # Use 9150 if using Tor Browser instead of the daemon
TOR_HOST = '127.0.0.1'
THREADS = 16     # Increase/decrease based on your CPU and bandwidth
TIMEOUT = 45     # Connection timeout limit


⚠️ Disclaimer

This tool is provided for educational and research purposes only. Users are solely responsible for ensuring that their use of this software complies with all applicable laws and regulations. The author assumes no liability for any misuse or damage caused by this program.
