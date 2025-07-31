#!/usr/bin/env python3
import os
import re
import sys
import time
import json
import random
import signal
import requests
import threading
import subprocess
from datetime import datetime, timedelta
from urllib.parse import urlparse
import platform
import socket
import sqlite3
import geoip2.database
import qrcode
from pyfiglet import Figlet
from colorama import Fore, Style, init
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# Initialize colorama
init(autoreset=True)

# ===== CONFIGURATION =====
PROXY_API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
TOR_BRIDGES_URL = "https://bridges.torproject.org/bridges?transport=obfs4"
LOG_FILE = "ip_alchemist.log"
ROTATION_INTERVAL = 300  # 5 minutes default
IP_CHECK_URL = "http://icanhazip.com"
CONFIG_FILE = "proxy_config.json"
LOCAL_PROXY_HOST = "0.0.0.0"  # Listen on all interfaces
LOCAL_PROXY_PORT = 8080  # Fixed local proxy port
VERSION = "ULTIMATE v10.0"
DNSCRYPT_CONFIG = "/data/data/com.termux/files/usr/etc/dnscrypt-proxy/dnscrypt-proxy.toml"
GEOIP_DB_PATH = "GeoLite2-City.mmdb"
MAC_PREFIXES = ["00:16:3e", "00:0c:29", "00:50:56", "00:1c:42", "00:1d:0f"]
TRAFFIC_DB = "traffic.db"
FINGERPRINT_DB = "fingerprints.db"
TOR_CONTROL_PORT = 9051
TOR_PROXY_PORT = 9050

# ===== STUNNING CREATIVE BANNER =====
def display_banner():
    f = Figlet(font='epic')
    print(Fore.MAGENTA + f.renderText('IP CHANGER'))
    print(Fore.CYAN + "="*80)
    print(Fore.YELLOW + "ADVANCED PROXY MANAGEMENT SYSTEM".center(80))
    print(Fore.CYAN + "="*80)
    print(Fore.GREEN + f"Version: {VERSION} | Author: {Fore.RED}Aryan")
    print(Fore.CYAN + "="*80)
    print(Fore.MAGENTA + "Features: Auto Tor IP Changer | Proxy Chaining | Stealth Mode | Traffic Analysis")
    print(Fore.CYAN + "="*80 + Style.RESET_ALL)

# ===== THREADED HTTP PROXY SERVER =====
class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread"""
    daemon_threads = True

class FixedProxyHandler(BaseHTTPRequestHandler):
    """HTTP handler for fixed proxy endpoint"""
    def do_GET(self):
        if self.server.proxy_master.current_proxy:
            proxy = self.server.proxy_master.current_proxy
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(f"""
                <html>
                <head><title>IP Alchemist Proxy</title></head>
                <body>
                    <h1>Active Proxy Endpoint</h1>
                    <p>This device is serving as a fixed proxy endpoint</p>
                    <p><strong>Host:</strong> {self.server.server_address[0]}</p>
                    <p><strong>Port:</strong> {self.server.server_address[1]}</p>
                    <p><strong>Current Proxy:</strong> {proxy['host']}:{proxy['port']}</p>
                    <p><strong>Your IP:</strong> {proxy.get('ip', 'Unknown')}</p>
                    <p><strong>Country:</strong> {proxy.get('country', 'Unknown')}</p>
                    <p><strong>Rotation Interval:</strong> {self.server.proxy_master.rotation_interval} seconds</p>
                </body>
                </html>
            """.encode())
        else:
            self.send_error(503, "No active proxy configured")

# ===== ENHANCED IP ALCHEMIST =====
class IPAlchemist:
    def __init__(self):
        self.proxies = []
        self.tor_bridges = []
        self.current_proxy = None
        self.favorites = []
        self.rotation_active = False
        self.rotation_thread = None
        self.local_proxy_active = False
        self.local_proxy_server = None
        self.rotation_interval = 300  # Default rotation in seconds
        self.config = {
            "api_url": PROXY_API_URL,
            "max_latency": 2000,
            "protocol_preference": ["http", "socks5", "socks4", "https"],
            "auto_start": False,
            "favorite_countries": [],
            "single_host_mode": True,  # Enabled by default
            "auto_refresh": False,
            "refresh_interval": 60,  # minutes
            "max_history": 50,
            "notifications": True,
            "theme": "dark",
            "enable_tor": False,
            "proxy_chain": [],
            "dns_protection": True,
            "kill_switch": False,
            "mac_randomization": False,
            "packet_fragmentation": False,
            "browser_spoofing": True,
            "traffic_compression": False,
            "cloud_sync": False,
            "doh_enabled": True,
            "doq_enabled": False,
            "tor_integration": False,
            "stealth_mode": False,
            "auto_rotate_fail": True,
            "proxy_load_balancing": False,
            "bandwidth_throttle": 0,
            "proxy_health_alerts": True,
            "proxy_uptime_monitor": False,
            "proxy_usage_analytics": True,
            "proxy_geofencing": False,
            "proxy_auto_benchmark": False,
            "proxy_anonymity_level": "elite",
            "proxy_encrypted_storage": False
        }
        self.tor_process = None
        self.tor_rotation_active = False
        self.tor_rotation_thread = None
        self.proxy_sources = {
            "online": PROXY_API_URL,
            "tor": "tor",
            "custom": None
        }
        self.current_source = "online"
        self.load_config()
        self.setup_directories()
        self.load_favorites()
        self.load_history()
        self.traffic_stats = {"sent": 0, "received": 0}
        self.proxy_uptime = {}
        self.blacklist = []
        self.geoip_reader = self.init_geoip()
        self.setup_databases()
        signal.signal(signal.SIGINT, self.signal_handler)
        
    def init_geoip(self):
        if os.path.exists(GEOIP_DB_PATH):
            try:
                return geoip2.database.Reader(GEOIP_DB_PATH)
            except:
                print(f"{Fore.YELLOW}⚠️ Error loading GeoIP database{Style.RESET_ALL}")
                return None
        return None
        
    def setup_databases(self):
        """Initialize databases for traffic and fingerprints"""
        # Traffic database
        conn = sqlite3.connect(TRAFFIC_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS traffic
                     (timestamp DATETIME, sent INTEGER, received INTEGER, proxy TEXT)''')
        conn.commit()
        conn.close()
        
        # Fingerprint database
        conn = sqlite3.connect(FINGERPRINT_DB)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS fingerprints
                     (id INTEGER PRIMARY KEY, user_agent TEXT, platform TEXT, 
                     language TEXT, timezone TEXT, screen TEXT, fonts TEXT, 
                     canvas_hash TEXT, webgl_hash TEXT, created DATETIME)''')
        conn.commit()
        conn.close()
        
    def signal_handler(self, signum, frame):
        print(f"\n{Fore.RED}🛑 Interrupt received! Shutting down...{Style.RESET_ALL}")
        self.stop_rotation()
        self.stop_tor_rotation()
        self.stop_tor_service()
        self.stop_local_proxy()
        self.disable_kill_switch()
        self.save_state()
        sys.exit(0)
        
    def setup_directories(self):
        os.makedirs("proxy_cache", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        os.makedirs("browser_profiles", exist_ok=True)
        os.makedirs("proxy_stats", exist_ok=True)
        os.makedirs("proxy_backups", exist_ok=True)
        os.makedirs("proxy_qrcodes", exist_ok=True)
        
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config = {**self.config, **json.load(f)}
                    print(f"{Fore.GREEN}✅ Loaded configuration from {CONFIG_FILE}{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Error loading config: {str(e)}{Style.RESET_ALL}")
        else:
            self.save_config()
            
    def save_config(self):
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=4)
            print(f"{Fore.CYAN}💾 Configuration saved to {CONFIG_FILE}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to save config: {str(e)}{Style.RESET_ALL}")
            return False
            
    def load_favorites(self):
        if os.path.exists('favorites.json'):
            try:
                with open('favorites.json', 'r') as f:
                    self.favorites = json.load(f)
                print(f"{Fore.GREEN}✅ Loaded {len(self.favorites)} favorites{Style.RESET_ALL}")
            except:
                print(f"{Fore.YELLOW}⚠️ Error loading favorites{Style.RESET_ALL}")
                
    def save_favorites(self):
        try:
            with open('favorites.json', 'w') as f:
                json.dump(self.favorites, f, indent=4)
            return True
        except:
            return False
            
    def load_history(self):
        if os.path.exists('history.json'):
            try:
                with open('history.json', 'r') as f:
                    self.history = json.load(f)
            except:
                self.history = []
        else:
            self.history = []
            
    def save_history(self):
        try:
            with open('history.json', 'w') as f:
                json.dump(self.history, f, indent=4)
            return True
        except:
            return False
            
    def save_state(self):
        """Save current state for persistence"""
        state = {
            "current_proxy": self.current_proxy,
            "proxies": self.proxies,
            "traffic_stats": self.traffic_stats,
            "proxy_uptime": self.proxy_uptime,
            "blacklist": self.blacklist
        }
        try:
            with open('state.json', 'w') as f:
                json.dump(state, f, indent=4)
            print(f"{Fore.CYAN}💾 Application state saved{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to save state: {str(e)}{Style.RESET_ALL}")
            
    def load_state(self):
        """Load previous application state"""
        if os.path.exists('state.json'):
            try:
                with open('state.json', 'r') as f:
                    state = json.load(f)
                self.current_proxy = state.get("current_proxy")
                self.proxies = state.get("proxies", [])
                self.traffic_stats = state.get("traffic_stats", {"sent": 0, "received": 0})
                self.proxy_uptime = state.get("proxy_uptime", {})
                self.blacklist = state.get("blacklist", [])
                print(f"{Fore.GREEN}✅ Application state loaded{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️ Error loading state: {str(e)}{Style.RESET_ALL}")
                
    # ===== TOR INTEGRATION =====
    def install_tor(self):
        """Install Tor in Termux"""
        try:
            print(f"{Fore.BLUE}🔧 Installing Tor package...{Style.RESET_ALL}")
            subprocess.run(["pkg", "install", "tor", "-y"], check=True)
            print(f"{Fore.GREEN}✅ Tor installed successfully{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Tor installation failed: {str(e)}{Style.RESET_ALL}")
            return False

    def start_tor_service(self):
        """Start Tor service in Termux"""
        if self.tor_process and self.tor_process.poll() is None:
            print(f"{Fore.YELLOW}⚠️ Tor is already running{Style.RESET_ALL}")
            return True
            
        try:
            print(f"{Fore.BLUE}🔌 Starting Tor service...{Style.RESET_ALL}")
            self.tor_process = subprocess.Popen(["tor"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(5)  # Wait for Tor to initialize
            
            # Verify Tor is running
            if self.tor_process.poll() is None:
                print(f"{Fore.GREEN}✅ Tor service started on port {TOR_PROXY_PORT}{Style.RESET_ALL}")
                return True
            else:
                print(f"{Fore.RED}❌ Tor failed to start{Style.RESET_ALL}")
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ Tor start failed: {str(e)}{Style.RESET_ALL}")
            return False

    def stop_tor_service(self):
        """Stop Tor service"""
        if self.tor_process:
            print(f"{Fore.BLUE}🛑 Stopping Tor service...{Style.RESET_ALL}")
            self.tor_process.terminate()
            try:
                self.tor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tor_process.kill()
            self.tor_process = None
            print(f"{Fore.GREEN}✅ Tor service stopped{Style.RESET_ALL}")
            return True
        return False

    def change_tor_circuit(self):
        """Change Tor circuit to get new IP"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect(("127.0.0.1", TOR_CONTROL_PORT))
                s.sendall(b"AUTHENTICATE\r\n")
                response = s.recv(1024)
                if b"250" not in response:
                    print(f"{Fore.RED}❌ Tor authentication failed{Style.RESET_ALL}")
                    return False
                    
                s.sendall(b"signal NEWNYM\r\n")
                response = s.recv(1024)
                if b"250" in response:
                    print(f"{Fore.GREEN}🔄 Tor circuit changed successfully{Style.RESET_ALL}")
                    return True
                else:
                    print(f"{Fore.RED}❌ Tor circuit change failed{Style.RESET_ALL}")
                    return False
        except Exception as e:
            print(f"{Fore.RED}❌ Tor control failed: {str(e)}{Style.RESET_ALL}")
            return False

    def start_tor_rotation(self, interval_sec):
        """Start automatic Tor IP rotation"""
        self.tor_rotation_active = True
        print(f"{Fore.MAGENTA}🌀 Starting Tor IP rotation every {interval_sec} seconds{Style.RESET_ALL}")
        
        def rotation_loop():
            while self.tor_rotation_active:
                self.change_tor_circuit()
                # Verify new IP
                try:
                    response = requests.get(
                        IP_CHECK_URL,
                        proxies={'http': f'socks5://127.0.0.1:{TOR_PROXY_PORT}'},
                        timeout=10
                    )
                    print(f"{Fore.CYAN}🌐 New Tor IP: {response.text.strip()}{Style.RESET_ALL}")
                except:
                    print(f"{Fore.YELLOW}⚠️ Failed to verify new Tor IP{Style.RESET_ALL}")
                
                time.sleep(interval_sec)
                
        self.tor_rotation_thread = threading.Thread(target=rotation_loop)
        self.tor_rotation_thread.daemon = True
        self.tor_rotation_thread.start()

    def stop_tor_rotation(self):
        """Stop Tor IP rotation"""
        if self.tor_rotation_active:
            self.tor_rotation_active = False
            if self.tor_rotation_thread and self.tor_rotation_thread.is_alive():
                self.tor_rotation_thread.join(timeout=2)
            print(f"{Fore.GREEN}⏹ Tor IP rotation stopped{Style.RESET_ALL}")
            return True
        return False

    def set_tor_proxy(self):
        """Set Tor as the current proxy"""
        try:
            os.environ['HTTP_PROXY'] = f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
            os.environ['HTTPS_PROXY'] = f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
            
            # For curl/wget
            with open(os.path.expanduser('~/.curlrc'), 'w') as f:
                f.write(f"proxy = socks5://127.0.0.1:{TOR_PROXY_PORT}\n")
                
            # Get current IP
            try:
                response = requests.get(IP_CHECK_URL, proxies={
                    'http': f'socks5://127.0.0.1:{TOR_PROXY_PORT}',
                    'https': f'socks5://127.0.0.1:{TOR_PROXY_PORT}'
                }, timeout=10)
                current_ip = response.text.strip()
            except:
                current_ip = "Unknown"
                
            self.current_proxy = {
                'host': '127.0.0.1',
                'port': TOR_PROXY_PORT,
                'protocol': 'socks5',
                'country': 'Tor Network',
                'ip': current_ip,
                'latency': 'N/A'
            }
            
            print(f"{Fore.GREEN}🔒 Using Tor proxy | IP: {current_ip}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to set Tor proxy: {str(e)}{Style.RESET_ALL}")
            return False

    # ===== PROXY SOURCE MANAGEMENT =====
    def set_proxy_source(self, source):
        """Set current proxy source"""
        if source not in self.proxy_sources:
            print(f"{Fore.RED}❌ Invalid proxy source{Style.RESET_ALL}")
            return False
            
        self.current_source = source
        self.config['proxy_source'] = source
        self.save_config()
        
        if source == "tor":
            if not self.check_tor_installed():
                print(f"{Fore.YELLOW}⚠️ Tor not installed. Installing now...{Style.RESET_ALL}")
                if not self.install_tor():
                    return False
            if not self.start_tor_service():
                return False
            return self.set_tor_proxy()
            
        print(f"{Fore.GREEN}✅ Proxy source set to: {source.upper()}{Style.RESET_ALL}")
        return True

    def configure_online_source(self):
        """Configure online proxy source URL"""
        print(f"{Fore.CYAN}Current API URL: {self.proxy_sources['online']}{Style.RESET_ALL}")
        new_url = input(f"{Fore.YELLOW}Enter new API URL (or press Enter to keep current):{Style.RESET_ALL} ").strip()
        
        if new_url:
            # Validate URL
            try:
                result = urlparse(new_url)
                if not all([result.scheme, result.netloc]):
                    raise ValueError("Invalid URL")
                self.proxy_sources['online'] = new_url
                self.config['online_source'] = new_url
                self.save_config()
                print(f"{Fore.GREEN}✅ Online source updated{Style.RESET_ALL}")
            except:
                print(f"{Fore.RED}❌ Invalid URL format{Style.RESET_ALL}")

    def configure_custom_source(self):
        """Configure custom proxy file source"""
        print(f"{Fore.CYAN}Current custom file: {self.proxy_sources['custom'] or 'Not set'}{Style.RESET_ALL}")
        file_path = input(f"{Fore.YELLOW}Enter path to proxy file:{Style.RESET_ALL} ").strip()
        
        if not file_path:
            return
            
        if not os.path.exists(file_path):
            print(f"{Fore.RED}❌ File not found{Style.RESET_ALL}")
            return
            
        self.proxy_sources['custom'] = file_path
        self.config['custom_source'] = file_path
        self.save_config()
        print(f"{Fore.GREEN}✅ Custom source updated{Style.RESET_ALL}")

    def load_custom_proxies(self):
        """Load proxies from custom file"""
        if not self.proxy_sources['custom'] or not os.path.exists(self.proxy_sources['custom']):
            print(f"{Fore.RED}❌ Custom proxy file not configured{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}📂 Loading proxies from {self.proxy_sources['custom']}{Style.RESET_ALL}")
            self.proxies = []
            
            with open(self.proxy_sources['custom'], 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                        
                    # Parse different formats: ip:port, ip:port:protocol, json
                    if line.startswith("{"):
                        try:
                            proxy = json.loads(line)
                            self.proxies.append(proxy)
                        except:
                            continue
                    else:
                        parts = line.split(':')
                        if len(parts) >= 2:
                            proxy = {
                                'host': parts[0],
                                'port': int(parts[1]),
                                'protocol': parts[2] if len(parts) > 2 else 'http'
                            }
                            self.proxies.append(proxy)
            
            print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} proxies from custom file{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to load custom proxies: {str(e)}{Style.RESET_ALL}")
            return False

    def fetch_live_proxies(self):
        """Get fresh proxies from current source"""
        if self.current_source == "custom":
            return self.load_custom_proxies()
        elif self.current_source == "tor":
            return True  # Tor doesn't need proxy list
            
        # Online source
        try:
            url = self.proxy_sources['online']
            print(f"{Fore.BLUE}🌐 Fetching proxies from {url}{Style.RESET_ALL}")
            headers = {
                'User-Agent': self.generate_random_user_agent(),
                'Accept': 'application/json'
            }
            response = requests.get(
                url, 
                headers=headers,
                timeout=30
            )
            data = response.json()
            
            if 'data' not in data:
                print(f"{Fore.YELLOW}⚠️ API format changed! Check documentation{Style.RESET_ALL}")
                return False
                
            self.proxies = []
            for proxy in data['data']:
                # Filter by latency
                if proxy['latency'] > self.config['max_latency']:
                    continue
                    
                # Filter by country preference
                if (self.config['favorite_countries'] and 
                    proxy['country'] not in self.config['favorite_countries']):
                    continue
                    
                # Use first available protocol
                for protocol in self.config['protocol_preference']:
                    if protocol in proxy['protocols']:
                        self.proxies.append({
                            'host': proxy['ip'],
                            'port': proxy['port'],
                            'protocol': protocol,
                            'country': proxy['country'],
                            'latency': proxy['latency'],
                            'last_checked': proxy['lastChecked'],
                            'is_favorite': any(fav['host'] == proxy['ip'] for fav in self.favorites)
                        })
                        break
                        
            print(f"{Fore.GREEN}✅ Loaded {len(self.proxies)} filtered proxies{Style.RESET_ALL}")
            self.log(f"Fetched {len(self.proxies)} proxies from API")
            
            # Cache proxies
            self.cache_proxies()
            return True
            
        except Exception as e:
            self.log(f"Proxy fetch failed: {str(e)}")
            print(f"{Fore.RED}❌ Proxy fetch error: {str(e)}{Style.RESET_ALL}")
            return False

    def fetch_tor_bridges(self):
        """Fetch Tor bridges for enhanced anonymity"""
        try:
            print(f"{Fore.BLUE}🌐 Fetching Tor bridges...{Style.RESET_ALL}")
            response = requests.get(TOR_BRIDGES_URL, timeout=15)
            if response.status_code == 200:
                self.tor_bridges = response.text.strip().split('\n')
                print(f"{Fore.GREEN}✅ Loaded {len(self.tor_bridges)} Tor bridges{Style.RESET_ALL}")
                return True
        except Exception as e:
            print(f"{Fore.RED}❌ Tor bridge fetch failed: {str(e)}{Style.RESET_ALL}")
        return False

    def cache_proxies(self):
        """Cache proxies to file"""
        cache_file = f"proxy_cache/proxies_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.proxies, f, indent=4)
            print(f"{Fore.CYAN}💾 Proxies cached to {cache_file}{Style.RESET_ALL}")
        except:
            print(f"{Fore.YELLOW}⚠️ Failed to cache proxies{Style.RESET_ALL}")

    def test_proxy(self, proxy, timeout=3):
        """Test proxy connection with timeout"""
        test_url = f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}"
        proxies = {
            'http': test_url,
            'https': test_url
        }
        
        try:
            start = time.time()
            response = requests.get(
                IP_CHECK_URL,
                proxies=proxies,
                timeout=timeout,
                headers={'User-Agent': self.generate_random_user_agent()}
            )
            latency = int((time.time() - start) * 1000)
            
            if response.status_code == 200:
                # Track traffic
                self.traffic_stats['received'] += len(response.content)
                return {
                    'working': True,
                    'ip': response.text.strip(),
                    'latency': latency
                }
        except:
            pass
        return {'working': False}

    def find_working_proxy(self, max_attempts=15):
        """Find a working proxy with intelligent selection"""
        if not self.proxies:
            print(f"{Fore.YELLOW}⚠️ No proxies available! Fetching new proxies...{Style.RESET_ALL}")
            if not self.fetch_live_proxies():
                return None
                
        # Create a prioritized list (favorites first, then by latency)
        candidates = [p for p in self.proxies if p.get('is_favorite', False)]
        if not candidates:
            candidates = sorted(self.proxies, key=lambda x: x['latency'])
        
        # Ensure we don't exceed max attempts
        candidates = candidates[:max_attempts]
        random.shuffle(candidates)  # Add randomness for load distribution
        
        for i, proxy in enumerate(candidates):
            print(f"{Fore.CYAN}🔎 Testing {proxy['host']}:{proxy['port']} ({proxy['protocol'].upper()}){Style.RESET_ALL}")
            result = self.test_proxy(proxy, timeout=5)
            
            if result['working']:
                print(f"{Fore.GREEN}✅ Found working proxy: {result['ip']} | Latency: {result['latency']}ms{Style.RESET_ALL}")
                return {**proxy, **result}
        
        print(f"{Fore.RED}❌ No working proxies found in batch{Style.RESET_ALL}")
        return None

    def set_termux_proxy(self, proxy):
        """Set proxy for Termux environment"""
        if not proxy:
            return False
            
        try:
            # If in single host mode, use local proxy instead
            if self.config['single_host_mode']:
                proxy_host = LOCAL_PROXY_HOST
                proxy_port = LOCAL_PROXY_PORT
                print(f"{Fore.BLUE}🔒 Using fixed proxy: {proxy_host}:{proxy_port}{Style.RESET_ALL}")
            else:
                proxy_host = proxy['host']
                proxy_port = proxy['port']
            
            # Set environment variables
            proxy_url = f"{proxy['protocol']}://{proxy_host}:{proxy_port}"
            os.environ['HTTP_PROXY'] = proxy_url
            os.environ['HTTPS_PROXY'] = proxy_url
            
            # For curl/wget support
            with open(os.path.expanduser('~/.curlrc'), 'w') as f:
                f.write(f"proxy = {proxy_url}\n")
                
            # Save current proxy
            self.current_proxy = proxy
            self.log(f"Proxy set: {proxy_host}:{proxy_port} | IP: {proxy['ip']}")
            
            # Add to history
            self.add_to_history(proxy)
            
            # Apply proxy chain if enabled
            if self.config['proxy_chain']:
                self.setup_proxy_chain()
                
            # Apply DNS protection
            if self.config['dns_protection']:
                self.enable_dns_protection()
                
            # Apply kill switch
            if self.config['kill_switch']:
                self.enable_kill_switch()
                
            # Apply MAC randomization
            if self.config['mac_randomization']:
                self.randomize_mac_address()
                
            # Apply browser spoofing
            if self.config['browser_spoofing']:
                self.generate_browser_profile()
                
            # Enable TOR if configured
            if self.config['tor_integration']:
                self.enable_tor_service()
                
            return True
        except Exception as e:
            self.log(f"Proxy set failed: {str(e)}")
            return False

    def add_to_history(self, proxy):
        """Add proxy to history"""
        entry = {
            'host': proxy['host'],
            'port': proxy['port'],
            'protocol': proxy['protocol'],
            'country': proxy.get('country', ''),
            'ip': proxy.get('ip', ''),
            'set_time': datetime.now().isoformat(),
            'latency': proxy.get('latency', 'N/A')
        }
        
        # Add to beginning
        self.history.insert(0, entry)
        
        # Keep only last N entries
        self.history = self.history[:self.config['max_history']]
        self.save_history()

    def add_favorite(self, proxy):
        """Add proxy to favorites"""
        if not any(fav['host'] == proxy['host'] for fav in self.favorites):
            self.favorites.append({
                'host': proxy['host'],
                'port': proxy['port'],
                'protocol': proxy['protocol'],
                'country': proxy.get('country', ''),
                'added': datetime.now().isoformat()
            })
            print(f"{Fore.YELLOW}🌟 Added {proxy['host']} to favorites{Style.RESET_ALL}")
            self.save_favorites()
            return True
        return False

    def remove_favorite(self, host):
        """Remove proxy from favorites"""
        self.favorites = [fav for fav in self.favorites if fav['host'] != host]
        print(f"{Fore.YELLOW}🗑️ Removed {host} from favorites{Style.RESET_ALL}")
        self.save_favorites()
        return True

    def rotate_proxy(self):
        """Rotate to a new working proxy"""
        print(f"\n{Fore.CYAN}🔄 Rotating IP address...{Style.RESET_ALL}")
        new_proxy = self.find_working_proxy()
        if new_proxy and self.set_termux_proxy(new_proxy):
            if self.config['notifications']:
                self.show_notification("Proxy Rotated", f"New IP: {new_proxy['ip']}")
            return new_proxy
        return None

    def start_rotation(self, interval_sec, duration_sec):
        """Start automatic proxy rotation with interval in seconds"""
        self.rotation_active = True
        self.rotation_interval = interval_sec
        
        # Handle infinite rotation
        if duration_sec <= 0:
            end_time = None
            print(f"{Fore.MAGENTA}♾️ Rotation started: Runs indefinitely until manually stopped{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Rotation interval: {self.format_duration(interval_sec)}{Style.RESET_ALL}")
        else:
            end_time = datetime.now() + timedelta(seconds=duration_sec)
            duration_str = self.format_duration(duration_sec)
            interval_str = self.format_duration(interval_sec)
            print(f"{Fore.MAGENTA}⏱ Rotation started: {interval_str} intervals for {duration_str}{Style.RESET_ALL}")
        
        def rotation_loop():
            while self.rotation_active and (end_time is None or datetime.now() < end_time):
                proxy_info = self.rotate_proxy()
                if proxy_info:
                    next_rotation = self.format_duration(self.rotation_interval)
                    print(f"{Fore.CYAN}⏱ Next rotation in {next_rotation}{Style.RESET_ALL}")
                    self.show_wifi_instructions(proxy_info)
                else:
                    print(f"{Fore.YELLOW}⚠️ Rotation failed, retrying in 30 seconds{Style.RESET_ALL}")
                    time.sleep(30)
                    continue
                    
                time.sleep(self.rotation_interval)
            self.rotation_active = False
            print(f"\n{Fore.GREEN}⏹ Rotation schedule completed{Style.RESET_ALL}")
            
        self.rotation_thread = threading.Thread(target=rotation_loop)
        self.rotation_thread.daemon = True
        self.rotation_thread.start()

    def format_duration(self, seconds):
        """Convert seconds to human-readable format"""
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            return f"{seconds//60} minutes"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours} hours {minutes} minutes"

    def stop_rotation(self):
        """Stop automatic rotation"""
        if self.rotation_active:
            self.rotation_active = False
            if self.rotation_thread and self.rotation_thread.is_alive():
                self.rotation_thread.join(timeout=2)
            print(f"\n{Fore.GREEN}⏹ Proxy rotation stopped{Style.RESET_ALL}")
            return True
        return False

    def show_wifi_instructions(self, proxy):
        """Display Android Wi-Fi proxy setup instructions"""
        # Always use fixed host/port for sharing
        host = self.get_local_ip()
        port = LOCAL_PROXY_PORT
        
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📱 WI-FI PROXY SETUP INSTRUCTIONS{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Host: {host}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Port: {port}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Protocol: HTTP{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Country: {proxy.get('country', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Latency: {proxy.get('latency', 'N/A')}ms{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}1. Go to Settings > Network & Internet > Wi-Fi{Style.RESET_ALL}")
        print(f"{Fore.GREEN}2. Long-press your connected network{Style.RESET_ALL}")
        print(f"{Fore.GREEN}3. Select 'Modify network'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}4. Tap 'Advanced options'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}5. Set Proxy to 'Manual'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}6. Enter above Host and Port{Style.RESET_ALL}")
        print(f"{Fore.GREEN}7. Save configuration{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}💡 Other devices will route traffic through this fixed endpoint{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💡 The IP will change automatically behind this address{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}\n")
        
        # Generate QR code for easy sharing
        self.generate_wifi_qr(host, port)

    def generate_wifi_qr(self, host, port):
        """Generate QR code for proxy configuration"""
        try:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=2,
                border=1,
            )
            proxy_url = f"http://{host}:{port}"
            qr.add_data(proxy_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Create ASCII representation
            qr.print_ascii(invert=True)
            
            # Save to file
            img_file = f"proxy_qrcodes/proxy_{int(time.time())}.png"
            img.save(img_file)
            print(f"{Fore.CYAN}🔳 QR code saved to {img_file}{Style.RESET_ALL}")
        except ImportError:
            print(f"{Fore.YELLOW}ℹ️ Install 'qrcode' package for QR generation: pip install qrcode{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️ QR generation error: {str(e)}{Style.RESET_ALL}")

    def clear_proxy_settings(self):
        """Clear all proxy settings"""
        try:
            # Clear environment variables
            if 'HTTP_PROXY' in os.environ:
                del os.environ['HTTP_PROXY']
            if 'HTTPS_PROXY' in os.environ:
                del os.environ['HTTPS_PROXY']
                
            # Remove curl config
            curlrc = os.path.expanduser('~/.curlrc')
            if os.path.exists(curlrc):
                os.remove(curlrc)
                
            self.current_proxy = None
            print(f"{Fore.GREEN}🔌 Cleared all proxy settings{Style.RESET_ALL}")
            self.disable_kill_switch()
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Clear failed: {str(e)}{Style.RESET_ALL}")
            return False

    def toggle_single_host_mode(self):
        """Toggle single host mode"""
        self.config['single_host_mode'] = not self.config['single_host_mode']
        status = f"{Fore.GREEN}ENABLED{Style.RESET_ALL}" if self.config['single_host_mode'] else f"{Fore.RED}DISABLED{Style.RESET_ALL}"
        print(f"\n{Fore.MAGENTA}🔀 Single Host Mode: {status}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}💡 Use fixed proxy: {self.get_local_ip()}:{LOCAL_PROXY_PORT} for all connections{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    (IP changes automatically behind this address){Style.RESET_ALL}")
        self.save_config()
        
        # Start/stop local proxy as needed
        if self.config['single_host_mode']:
            self.start_local_proxy()
        else:
            self.stop_local_proxy()
            
        # Update environment if proxy is active
        if self.current_proxy:
            self.set_termux_proxy(self.current_proxy)
        return True

    def start_local_proxy(self):
        """Start local proxy server for fixed endpoint"""
        if self.local_proxy_active:
            print(f"{Fore.YELLOW}⚠️ Local proxy is already running{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}🚀 Starting local proxy server on {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}...{Style.RESET_ALL}")
            
            # Create custom server class to pass proxy_master instance
            class CustomServer(ThreadedHTTPServer):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, **kwargs)
                    self.proxy_master = proxy_master
                    
            server = CustomServer((LOCAL_PROXY_HOST, LOCAL_PROXY_PORT), FixedProxyHandler)
            
            def server_thread():
                try:
                    server.serve_forever()
                except:
                    pass
                
            self.local_proxy_server = threading.Thread(target=server_thread)
            self.local_proxy_server.daemon = True
            self.local_proxy_server.start()
            
            self.local_proxy_active = True
            print(f"{Fore.GREEN}✅ Local proxy running at {self.get_local_ip()}:{LOCAL_PROXY_PORT}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to start local proxy: {str(e)}{Style.RESET_ALL}")
            return False

    def stop_local_proxy(self):
        """Stop local proxy server"""
        if not self.local_proxy_active:
            print(f"{Fore.YELLOW}⚠️ Local proxy is not running{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}🛑 Stopping local proxy server...{Style.RESET_ALL}")
            self.local_proxy_active = False
            # The server will terminate when main thread exits
            print(f"{Fore.GREEN}✅ Local proxy stopped{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to stop local proxy: {str(e)}{Style.RESET_ALL}")
            return False

    def get_local_ip(self):
        """Get device local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    def parse_duration(self, duration_str):
        """Parse duration string with units (e.g., 30s, 5m, 2h)"""
        try:
            if duration_str.endswith('s'):
                return int(duration_str[:-1])
            elif duration_str.endswith('m'):
                return int(duration_str[:-1]) * 60
            elif duration_str.endswith('h'):
                return int(duration_str[:-1]) * 3600
            else:
                return int(duration_str)  # Default to seconds
        except:
            return 300  # Default 5 minutes if invalid

    def check_tor_installed(self):
        """Check if Tor is installed"""
        try:
            result = subprocess.run(["tor", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            return result.returncode == 0
        except:
            return False

    def generate_random_user_agent(self):
        """Generate random browser user agent"""
        browsers = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36"
        ]
        return random.choice(browsers)

    def show_proxy_source_menu(self):
        """Display proxy source selection menu"""
        print(f"\n{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🔌 PROXY SOURCE CONFIGURATION{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"1. {Fore.CYAN}🌐 Online API (Current: {self.current_source == 'online'}){Style.RESET_ALL}")
        print(f"2. {Fore.CYAN}🌀 Auto Tor IP Changer (Current: {self.current_source == 'tor'}){Style.RESET_ALL}")
        print(f"3. {Fore.CYAN}📂 Custom File (Current: {self.current_source == 'custom'}){Style.RESET_ALL}")
        print(f"4. {Fore.CYAN}⚙️ Configure Online Source{Style.RESET_ALL}")
        print(f"5. {Fore.CYAN}📝 Configure Custom Source{Style.RESET_ALL}")
        print(f"6. {Fore.CYAN}🔙 Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.YELLOW}🔍 Select option:{Style.RESET_ALL} ").strip()
        
        if choice == '1':
            self.set_proxy_source("online")
        elif choice == '2':
            self.set_proxy_source("tor")
        elif choice == '3':
            self.set_proxy_source("custom")
        elif choice == '4':
            self.configure_online_source()
        elif choice == '5':
            self.configure_custom_source()
        elif choice == '6':
            return
        else:
            print(f"{Fore.RED}❌ Invalid choice{Style.RESET_ALL}")
            
        time.sleep(1)
        self.show_proxy_source_menu()

    def log(self, message):
        """Log message to file"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        try:
            with open(LOG_FILE, "a") as f:
                f.write(log_entry)
        except:
            pass

    def show_notification(self, title, message):
        """Show system notification"""
        try:
            subprocess.run(["termux-notification", "-t", title, "-c", message])
        except:
            print(f"{Fore.YELLOW}⚠️ Could not send notification{Style.RESET_ALL}")

# ===== MAIN APPLICATION =====
def main():
    display_banner()
    
    proxy_master = IPAlchemist()
    proxy_master.load_state()
    
    # Start local proxy in single host mode
    if proxy_master.config['single_host_mode']:
        proxy_master.start_local_proxy()
    
    # Auto-start if configured
    if proxy_master.config.get('auto_start', False):
        print(f"\n{Fore.BLUE}🚀 Starting auto-rotation as per configuration...{Style.RESET_ALL}")
        proxy_master.start_rotation(
            proxy_master.config.get('rotation_interval', 300),
            proxy_master.config.get('rotation_duration', 3600)
        )
    
    while True:
        print(f"\n{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📱 MAIN MENU".center(30) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"1. {Fore.CYAN}🌐 Fetch new proxies{Style.RESET_ALL}")
        print(f"2. {Fore.CYAN}🔄 Set random proxy{Style.RESET_ALL}")
        print(f"3. {Fore.CYAN}⏱️ Start rotation{Style.RESET_ALL}")
        print(f"4. {Fore.CYAN}⏹️ Stop rotation{Style.RESET_ALL}")
        print(f"5. {Fore.CYAN}ℹ️ Show current proxy{Style.RESET_ALL}")
        print(f"6. {Fore.CYAN}📶 Wi-Fi setup{Style.RESET_ALL}")
        print(f"7. {Fore.CYAN}⚙️ Configuration{Style.RESET_ALL}")
        print(f"8. {Fore.CYAN}⭐ Favorites{Style.RESET_ALL}")
        print(f"9. {Fore.CYAN}🕰 History{Style.RESET_ALL}")
        print(f"10. {Fore.CYAN}📤 Export proxies{Style.RESET_ALL}")
        print(f"11. {Fore.CYAN}🚀 Speed test{Style.RESET_ALL}")
        print(f"12. {Fore.CYAN}🔀 Toggle Single-Host{Style.RESET_ALL}")
        print(f"13. {Fore.CYAN}🛡️ Toggle Kill Switch{Style.RESET_ALL}")
        print(f"14. {Fore.CYAN}📍 Spoof Location{Style.RESET_ALL}")
        print(f"15. {Fore.CYAN}🖥 Generate Browser Profile{Style.RESET_ALL}")
        print(f"16. {Fore.CYAN}📊 Traffic Stats{Style.RESET_ALL}")
        print(f"17. {Fore.CYAN}🌍 Network Map{Style.RESET_ALL}")
        print(f"18. {Fore.CYAN}🚀 Enterprise Features{Style.RESET_ALL}")
        print(f"19. {Fore.CYAN}🔌 Clear settings{Style.RESET_ALL}")
        print(f"20. {Fore.CYAN}🔌 Proxy Source Configuration{Style.RESET_ALL}")
        print(f"21. {Fore.CYAN}🌀 Tor IP Rotation{Style.RESET_ALL}")
        print(f"22. {Fore.CYAN}🚪 Exit{Style.RESET_ALL}")
        
        try:
            choice = input(f"\n{Fore.YELLOW}🔍 Select option:{Style.RESET_ALL} ").strip()
        except EOFError:
            print("\nExiting...")
            break
            
        if choice == '1':
            if proxy_master.fetch_live_proxies():
                print(f"{Fore.GREEN}🌟 {len(proxy_master.proxies)} proxies available{Style.RESET_ALL}")
        
        elif choice == '2':
            if not proxy_master.proxies:
                print(f"{Fore.YELLOW}⚠️ No proxies! Fetch first{Style.RESET_ALL}")
                continue
                
            proxy = proxy_master.rotate_proxy()
            if proxy:
                proxy_master.show_wifi_instructions(proxy)
        
        elif choice == '3':
            if not proxy_master.proxies:
                print(f"{Fore.YELLOW}⚠️ No proxies! Fetch first{Style.RESET_ALL}")
                continue
                
            interval = input(f"{Fore.CYAN}⏱ Rotation interval (e.g., 30s, 5m, 2h) [5m]:{Style.RESET_ALL} ").strip() or "5m"
            interval_sec = proxy_master.parse_duration(interval)
            
            duration = input(f"{Fore.CYAN}⏳ Duration (0=infinite, e.g., 1h, 30m) [1h]:{Style.RESET_ALL} ").strip() or "1h"
            duration_sec = proxy_master.parse_duration(duration)
            
            proxy_master.start_rotation(interval_sec, duration_sec)
        
        elif choice == '4':
            proxy_master.stop_rotation()
        
        elif choice == '5':
            if proxy_master.current_proxy:
                p = proxy_master.current_proxy
                print(f"\n{Fore.CYAN}🔌 Current Proxy: {p['host']}:{p['port']}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}📡 Protocol: {p['protocol'].upper()}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}🌍 Location: {p.get('country', 'N/A')}{Style.RESET_ALL}")
                print(f"{Fore.MAGENTA}📶 Your IP: {p.get('ip', 'N/A')}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⏱ Latency: {p.get('latency', 'N/A')}ms{Style.RESET_ALL}")
                if proxy_master.config['single_host_mode']:
                    print(f"\n{Fore.CYAN}💡 Single-Host Mode: ACTIVE{Style.RESET_ALL}")
                    print(f"    Fixed Endpoint: {proxy_master.get_local_ip()}:{LOCAL_PROXY_PORT}")
                if proxy_master.config['kill_switch']:
                    print(f"\n{Fore.GREEN}🛡️ Kill Switch: ACTIVE{Style.RESET_ALL}")
                if proxy_master.config['tor_integration']:
                    print(f"\n{Fore.MAGENTA}🔒 TOR Integration: ACTIVE{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}❌ No active proxy{Style.RESET_ALL}")
        
        elif choice == '6':
            if proxy_master.current_proxy:
                proxy_master.show_wifi_instructions(proxy_master.current_proxy)
            else:
                print(f"{Fore.YELLOW}⚠️ Set a proxy first{Style.RESET_ALL}")
        
        elif choice == '12':
            proxy_master.toggle_single_host_mode()
            
        elif choice == '19':
            proxy_master.clear_proxy_settings()
            
        elif choice == '20':
            proxy_master.show_proxy_source_menu()
            
        elif choice == '21':
            if proxy_master.current_source != "tor":
                print(f"{Fore.RED}❌ Tor is not the current source{Style.RESET_ALL}")
                continue
                
            interval = input(f"{Fore.CYAN}⏱ Rotation interval (seconds) [60]:{Style.RESET_ALL} ").strip() or "60"
            try:
                interval_sec = int(interval)
                proxy_master.start_tor_rotation(interval_sec)
            except:
                print(f"{Fore.RED}❌ Invalid interval{Style.RESET_ALL}")
                
        elif choice == '22':
            proxy_master.stop_rotation()
            proxy_master.stop_tor_rotation()
            proxy_master.stop_tor_service()
            proxy_master.stop_local_proxy()
            proxy_master.save_state()
            print(f"\n{Fore.MAGENTA}🔌 Exiting IP Alchemist{Style.RESET_ALL}")
            break
        
        # Placeholder for other menu options
        else:
            print(f"{Fore.RED}❌ Invalid choice. Please select a valid option.{Style.RESET_ALL}")

# ===== RUN APPLICATION =====
if __name__ == "__main__":
    main()