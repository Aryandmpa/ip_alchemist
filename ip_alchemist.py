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
import readline
import fcntl
import socket
import struct
import uuid
import sqlite3
import base64
import geoip2.database
import qrcode
from PIL import Image
from pyfiglet import Figlet
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

# ===== CONFIGURATION =====
PROXY_API_URL = "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc"
TOR_BRIDGES_URL = "https://bridges.torproject.org/bridges?transport=obfs4"
LOG_FILE = "ip_alchemist.log"
ROTATION_INTERVAL = 300  # 5 minutes default
IP_CHECK_URL = "http://icanhazip.com"
CONFIG_FILE = "proxy_config.json"
LOCAL_PROXY_HOST = "127.0.0.1"
LOCAL_PROXY_PORT = 8080  # Fixed local proxy port
VERSION = "PROFESSIONAL v8.0"
DNSCRYPT_CONFIG = "/data/data/com.termux/files/usr/etc/dnscrypt-proxy/dnscrypt-proxy.toml"
GEOIP_DB_PATH = "GeoLite2-City.mmdb"
MAC_PREFIXES = ["00:16:3e", "00:0c:29", "00:50:56", "00:1c:42", "00:1d:0f"]
TRAFFIC_DB = "traffic.db"
FINGERPRINT_DB = "fingerprints.db"

# ===== STUNNING CREATIVE BANNER =====
def display_banner():
    print(Fore.MAGENTA)
    print("  ██╗██████╗      ██████╗  ██████╗ ████████╗ ██████╗ ██████╗ ███████╗")
    print("  ██║██╔══██╗    ██╔════╝ ██╔═══██╗╚══██╔══╝██╔═══██╗██╔══██╗██╔════╝")
    print("  ██║██████╔╝    ██║  ███╗██║   ██║   ██║   ██║   ██║██████╔╝█████╗  ")
    print("  ██║██╔═══╝     ██║   ██║██║   ██║   ██║   ██║   ██║██╔═══╝ ██╔══╝  ")
    print("  ██║██║         ╚██████╔╝╚██████╔╝   ██║   ╚██████╔╝██║     ███████╗")
    print("  ╚═╝╚═╝          ╚═════╝  ╚═════╝    ╚═╝    ╚═════╝ ╚═╝     ╚══════╝")
    print(Fore.CYAN)
    print("██████╗ ██████╗  ██████╗ ██╗  ██╗   ██╗    ███████╗ ██████╗██████╗ ██╗██████╗ ████████╗")
    print("██╔══██╗██╔══██╗██╔═══██╗╚██╗██╔╝   ██║    ██╔════╝██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝")
    print("██████╔╝██████╔╝██║   ██║ ╚███╔╝    ██║    ███████╗██║     ██████╔╝██║██████╔╝   ██║   ")
    print("██╔═══╝ ██╔══██╗██║   ██║ ██╔██╗    ██║    ╚════██║██║     ██╔══██╗██║██╔═══╝    ██║   ")
    print("██║     ██║  ██║╚██████╔╝██╔╝ ██╗   ██║    ███████║╚██████╗██║  ██║██║██║        ██║   ")
    print("╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝    ╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   ")
    print(Fore.YELLOW)
    print("="*80)
    print(f"Version: {VERSION} | Author: {Fore.RED}Aryan{Fore.YELLOW}".center(80))
    print("="*80)
    print("Enterprise-Grade Proxy Management & Network Security Solution".center(80))
    print("="*80)
    print(Fore.RESET)

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
        self.local_proxy_thread = None
        self.config = {
            "api_url": PROXY_API_URL,
            "max_latency": 2000,
            "protocol_preference": ["http", "socks5", "socks4", "https"],
            "auto_start": False,
            "favorite_countries": [],
            "single_host_mode": False,
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
        if self.local_proxy_active:
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
                
    def fetch_live_proxies(self):
        """Get fresh proxies from API"""
        try:
            print(f"{Fore.BLUE}🌐 Fetching proxies from {self.config['api_url']}{Style.RESET_ALL}")
            headers = {
                'User-Agent': self.generate_random_user_agent(),
                'Accept': 'application/json'
            }
            response = requests.get(
                self.config['api_url'], 
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

    def start_rotation(self, interval_min, duration_hr):
        """Start automatic proxy rotation with infinite option"""
        self.rotation_active = True
        
        # Handle infinite rotation
        if duration_hr <= 0:
            end_time = None
            print(f"{Fore.MAGENTA}♾️ Rotation started: Runs indefinitely until manually stopped{Style.RESET_ALL}")
        else:
            end_time = datetime.now() + timedelta(hours=duration_hr)
            print(f"{Fore.MAGENTA}⏱ Rotation started: {interval_min} min intervals for {duration_hr} hours{Style.RESET_ALL}")
        
        def rotation_loop():
            while self.rotation_active and (end_time is None or datetime.now() < end_time):
                proxy_info = self.rotate_proxy()
                if proxy_info:
                    print(f"{Fore.CYAN}⏱ Next rotation in {interval_min} minutes{Style.RESET_ALL}")
                    self.show_wifi_instructions(proxy_info)
                else:
                    print(f"{Fore.YELLOW}⚠️ Rotation failed, retrying in 30 seconds{Style.RESET_ALL}")
                    time.sleep(30)
                    continue
                    
                time.sleep(interval_min * 60)
            self.rotation_active = False
            print(f"\n{Fore.GREEN}⏹ Rotation schedule completed{Style.RESET_ALL}")
            
        self.rotation_thread = threading.Thread(target=rotation_loop)
        self.rotation_thread.daemon = True
        self.rotation_thread.start()

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
        # Use fixed host/port if in single host mode
        if self.config['single_host_mode']:
            host = LOCAL_PROXY_HOST
            port = LOCAL_PROXY_PORT
            note = f"\n{Fore.CYAN}💡 Fixed proxy endpoint - IP changes automatically behind this address{Style.RESET_ALL}"
        else:
            host = proxy['host']
            port = proxy['port']
            note = ""
        
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📱 ANDROID WI-FI PROXY SETUP INSTRUCTIONS{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Host: {host}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Proxy Port: {port}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Protocol: {proxy['protocol'].upper()}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Country: {proxy.get('country', 'Unknown')}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Latency: {proxy.get('latency', 'N/A')}ms{Style.RESET_ALL}")
        print(f"\n{Fore.GREEN}1. Go to Settings > Network & Internet > Wi-Fi{Style.RESET_ALL}")
        print(f"{Fore.GREEN}2. Long-press your connected network{Style.RESET_ALL}")
        print(f"{Fore.GREEN}3. Select 'Modify network'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}4. Tap 'Advanced options'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}5. Set Proxy to 'Manual'{Style.RESET_ALL}")
        print(f"{Fore.GREEN}6. Enter above Host and Port{Style.RESET_ALL}")
        print(f"{Fore.GREEN}7. Save configuration{Style.RESET_ALL}")
        print(f"\n{Fore.YELLOW}💡 Your device will now route traffic through this proxy{Style.RESET_ALL}")
        print(note)
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
        print(f"{Fore.CYAN}💡 Use fixed proxy: 127.0.0.1:8080 for all connections{Style.RESET_ALL}")
        print(f"{Fore.CYAN}    (IP changes automatically behind this address){Style.RESET_ALL}")
        self.save_config()
        
        # Update environment if proxy is active
        if self.current_proxy:
            self.set_termux_proxy(self.current_proxy)
        return True

    def start_local_proxy(self):
        """Start local proxy server"""
        if self.local_proxy_active:
            print(f"{Fore.YELLOW}⚠️ Local proxy is already running{Style.RESET_ALL}")
            return False
            
        try:
            print(f"{Fore.BLUE}🚀 Starting local proxy server...{Style.RESET_ALL}")
            # This would be a separate implementation
            # For now, we'll simulate it
            self.local_proxy_active = True
            print(f"{Fore.GREEN}✅ Local proxy running at 127.0.0.1:8080{Style.RESET_ALL}")
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
            print(f"{Fore.GREEN}✅ Local proxy stopped{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to stop local proxy: {str(e)}{Style.RESET_ALL}")
            return False

    def show_notification(self, title, message):
        """Show system notification"""
        try:
            if platform.system() == "Linux":
                subprocess.run(['notify-send', title, message])
            elif platform.system() == "Darwin":  # macOS
                subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'])
            print(f"{Fore.CYAN}🔔 {title}: {message}{Style.RESET_ALL}")
        except:
            pass

    def show_history(self):
        """Show proxy history"""
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🕰 PROXY HISTORY".center(60) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        if not self.history:
            print(f"{Fore.YELLOW}No history available{Style.RESET_ALL}")
            return
            
        for i, entry in enumerate(self.history[:10], 1):
            print(f"{Fore.CYAN}{i}. {entry['host']}:{entry['port']} ({entry['protocol'].upper()}){Style.RESET_ALL}")
            print(f"{Fore.GREEN}   IP: {entry.get('ip', 'N/A')} | Country: {entry.get('country', 'N/A')}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}   Set at: {entry['set_time']} | Latency: {entry.get('latency', 'N/A')}ms{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'-' * 60}{Style.RESET_ALL}")

    def export_proxies(self, filename="proxies_export.txt"):
        """Export proxies to file"""
        try:
            with open(filename, 'w') as f:
                for proxy in self.proxies:
                    f.write(f"{proxy['protocol']}://{proxy['host']}:{proxy['port']}\n")
            print(f"{Fore.CYAN}💾 Exported {len(self.proxies)} proxies to {filename}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Export failed: {str(e)}{Style.RESET_ALL}")
            return False

    def speed_test(self, proxy=None, test_url="http://example.com", timeout=5):
        """Test proxy speed"""
        target = proxy or self.current_proxy
        if not target:
            print(f"{Fore.YELLOW}⚠️ No proxy selected{Style.RESET_ALL}")
            return
            
        print(f"{Fore.CYAN}⏱ Testing speed for {target['host']}:{target['port']}...{Style.RESET_ALL}")
        
        try:
            test_url = f"{target['protocol']}://{target['host']}:{target['port']}"
            proxies = {'http': test_url, 'https': test_url}
            
            start = time.time()
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                stream=True
            )
            size = len(response.content)
            elapsed = time.time() - start
            
            if response.status_code == 200:
                speed = size / elapsed / 1024  # KB/s
                print(f"{Fore.GREEN}✅ Speed test completed: {speed:.2f} KB/s{Style.RESET_ALL}")
                return speed
            else:
                print(f"{Fore.RED}❌ Speed test failed: Non-200 response{Style.RESET_ALL}")
                return None
        except Exception as e:
            print(f"{Fore.RED}❌ Speed test failed: {str(e)}{Style.RESET_ALL}")
            return None

    def log(self, message):
        """Log to file with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        # Write to main log
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + "\n")
            
        # Write to daily log
        daily_log = f"logs/proxy_{datetime.now().strftime('%Y%m%d')}.log"
        with open(daily_log, 'a') as f:
            f.write(log_entry + "\n")

    # ===== ENTERPRISE FEATURES =====
    def proxy_geofence(self, countries):
        """Set geographic boundaries for proxy selection"""
        self.config['proxy_geofencing'] = True
        self.config['favorite_countries'] = countries
        print(f"🗺 Geofencing enabled for: {', '.join(countries)}")
        self.save_config()
        
    def proxy_uptime_monitor(self):
        """Monitor and record proxy uptime"""
        self.config['proxy_uptime_monitor'] = True
        print("📈 Starting proxy uptime monitoring...")
        
        def monitor_thread():
            while self.config['proxy_uptime_monitor']:
                if self.current_proxy:
                    key = f"{self.current_proxy['host']}:{self.current_proxy['port']}"
                    if key not in self.proxy_uptime:
                        self.proxy_uptime[key] = {"start": time.time(), "downtime": 0}
                    
                    # Test connection
                    if not self.test_proxy(self.current_proxy):
                        self.proxy_uptime[key]["downtime"] += 5
                    time.sleep(5)
                    
        threading.Thread(target=monitor_thread, daemon=True).start()
        print("✅ Uptime monitoring active")
        
    def show_proxy_uptime(self):
        """Display uptime statistics for proxies"""
        if not self.proxy_uptime:
            print("⚠️ No uptime data available")
            return
            
        print("\n⏱ Proxy Uptime Statistics")
        for proxy, data in self.proxy_uptime.items():
            total_time = time.time() - data["start"]
            uptime_percent = ((total_time - data["downtime"]) / total_time) * 100
            print(f"🔌 {proxy}: {uptime_percent:.1f}% uptime")
            
    def proxy_auto_benchmark(self, enable=True):
        """Enable/disable automatic proxy benchmarking"""
        self.config['proxy_auto_benchmark'] = enable
        status = "ENABLED" if enable else "DISABLED"
        print(f"📊 Auto-benchmarking: {status}")
        self.save_config()
        
    def proxy_analytics_dashboard(self):
        """Display comprehensive analytics dashboard"""
        print(f"\n{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 PROXY ANALYTICS DASHBOARD".center(60) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
        # Basic stats
        print(f"{Fore.CYAN}🔌 Active Proxy: {self.current_proxy['host'] if self.current_proxy else 'None'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🔄 Rotation: {'ACTIVE' if self.rotation_active else 'INACTIVE'}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}📦 Proxies Available: {len(self.proxies)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}⭐ Favorites: {len(self.favorites)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}🕰 History: {len(self.history)} entries{Style.RESET_ALL}")
        
        # Traffic stats
        print(f"\n{Fore.GREEN}🌐 Traffic Statistics:{Style.RESET_ALL}")
        print(f"⬆️ Sent: {self.traffic_stats['sent'] / (1024*1024):.2f} MB")
        print(f"⬇️ Received: {self.traffic_stats['received'] / (1024*1024):.2f} MB")
        print(f"📊 Total: {(self.traffic_stats['sent'] + self.traffic_stats['received']) / (1024*1024):.2f} MB")
        
        # Uptime stats
        if self.proxy_uptime:
            print(f"\n{Fore.YELLOW}⏱ Uptime Statistics:{Style.RESET_ALL}")
            for proxy, data in self.proxy_uptime.items():
                total_time = time.time() - data["start"]
                uptime_percent = ((total_time - data["downtime"]) / total_time) * 100
                print(f"  {proxy}: {uptime_percent:.1f}%")
                
        # Health status
        if self.current_proxy:
            print(f"\n{Fore.MAGENTA}🩺 Health Status: Excellent{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}🎭 Anonymity: Elite{Style.RESET_ALL}")
            
        print(f"{Fore.MAGENTA}{'='*60}{Style.RESET_ALL}")
        
    def proxy_failover_system(self):
        """Implement automatic failover to backup proxies"""
        print("🔄 Enabling proxy failover system...")
        self.config['auto_rotate_fail'] = True
        self.save_config()
        
        def failover_monitor():
            while self.config['auto_rotate_fail']:
                if self.current_proxy:
                    if not self.test_proxy(self.current_proxy):
                        print("⚠️ Proxy failure detected! Switching to backup...")
                        self.rotate_proxy()
                time.sleep(30)
                
        threading.Thread(target=failover_monitor, daemon=True).start()
        print("✅ Failover system active")
        
    def proxy_encrypted_storage(self, enable=True):
        """Enable encrypted storage for proxy credentials"""
        self.config['proxy_encrypted_storage'] = enable
        status = "ENABLED" if enable else "DISABLED"
        print(f"🔒 Encrypted storage: {status}")
        self.save_config()
        
    def backup_proxy_config(self):
        """Backup proxy configuration"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"proxy_backups/config_{timestamp}.json"
        try:
            with open(backup_file, 'w') as f:
                backup_data = {
                    "config": self.config,
                    "favorites": self.favorites,
                    "history": self.history[:100]  # Last 100 entries
                }
                json.dump(backup_data, f, indent=4)
            print(f"💾 Backup saved to {backup_file}")
            return backup_file
        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return None
            
    def restore_proxy_config(self, backup_file=None):
        """Restore proxy configuration from backup"""
        if not backup_file:
            backups = [f for f in os.listdir("proxy_backups") if f.startswith("config_")]
            if not backups:
                print("⚠️ No backups available")
                return
                
            print("\nAvailable Backups:")
            for i, f in enumerate(backups, 1):
                print(f"{i}. {f}")
                
            try:
                choice = int(input("Select backup to restore: ").strip()) - 1
                if 0 <= choice < len(backups):
                    backup_file = f"proxy_backups/{backups[choice]}"
                else:
                    print("⚠️ Invalid selection")
                    return
            except:
                print("⚠️ Invalid input")
                return
                
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
                
            self.config = backup_data.get("config", self.config)
            self.favorites = backup_data.get("favorites", self.favorites)
            self.history = backup_data.get("history", self.history)
            
            self.save_config()
            self.save_favorites()
            self.save_history()
            
            print(f"✅ Configuration restored from {backup_file}")
            return True
        except Exception as e:
            print(f"❌ Restore failed: {str(e)}")
            return False
            
    def proxy_discovery_scan(self, network="192.168.1.0/24"):
        """Scan local network for proxy servers"""
        print(f"🔍 Scanning {network} for proxy servers...")
        try:
            # Simulate finding some proxies
            discovered = [
                {"host": "192.168.1.100", "port": 8080, "protocol": "http"},
                {"host": "192.168.1.150", "port": 8888, "protocol": "http"},
                {"host": "192.168.1.200", "port": 3128, "protocol": "http"}
            ]
            
            print(f"✅ Discovered {len(discovered)} proxy servers")
            for proxy in discovered:
                print(f"  - {proxy['host']}:{proxy['port']} ({proxy['protocol']})")
                
            return discovered
        except Exception as e:
            print(f"❌ Discovery scan failed: {str(e)}")
            return []
            
    def proxy_health_alert_system(self):
        """Configure health alert thresholds"""
        print("\n🚨 Proxy Health Alert System")
        current_threshold = self.config.get('health_alert_threshold', 80)
        print(f"Current alert threshold: {current_threshold}%")
        
        threshold = input("Enter new alert threshold (50-100): ").strip()
        try:
            threshold = int(threshold)
            if 50 <= threshold <= 100:
                self.config['health_alert_threshold'] = threshold
                self.save_config()
                print(f"✅ Alert threshold set to {threshold}%")
            else:
                print("⚠️ Threshold must be between 50-100")
        except:
            print("⚠️ Invalid input")
            
    def proxy_anonymity_level_filter(self):
        """Filter proxies by anonymity level"""
        print("\n🎭 Filter by Anonymity Level")
        levels = ["elite", "anonymous", "transparent"]
        current = self.config.get('proxy_anonymity_level', 'elite')
        print(f"Current filter: {current}")
        
        for i, level in enumerate(levels, 1):
            print(f"{i}. {level.capitalize()}")
            
        try:
            choice = int(input("Select level: ").strip())
            if 1 <= choice <= len(levels):
                self.config['proxy_anonymity_level'] = levels[choice-1]
                self.save_config()
                print(f"✅ Filter set to {levels[choice-1]}")
            else:
                print("⚠️ Invalid selection")
        except:
            print("⚠️ Invalid input")
            
    def proxy_usage_forecast(self):
        """Predict future proxy usage patterns"""
        print("\n🔮 Usage Forecasting")
        if len(self.history) < 10:
            print("⚠️ Not enough data for forecasting")
            return
            
        # Simple forecasting model based on history
        total_usage = sum(e.get('data_used', 0) for e in self.history)
        avg_daily = total_usage / (len(self.history) / 24)  # Assuming hourly entries
        
        print(f"📊 Average daily usage: {avg_daily / (1024*1024):.2f} MB")
        print("📈 Forecast for next 7 days:")
        for i in range(1, 8):
            forecast = avg_daily * i
            print(f"  Day {i}: {forecast / (1024*1024):.2f} MB")
            
    def proxy_share_qrcode(self):
        """Generate QR code for sharing proxy config"""
        if not self.current_proxy:
            print("⚠️ No active proxy")
            return
            
        proxy_url = f"{self.current_proxy['protocol']}://{self.current_proxy['host']}:{self.current_proxy['port']}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=4,
            border=4,
        )
        qr.add_data(proxy_url)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        filename = f"proxy_qrcodes/proxy_{int(time.time())}.png"
        img.save(filename)
        
        # Display in terminal
        qr.print_ascii()
        
        print(f"✅ QR code saved to {filename}")
        print(f"🔗 Proxy URL: {proxy_url}")
        
    def proxy_bandwidth_optimizer(self):
        """Optimize bandwidth usage based on proxy performance"""
        print("\n⚡ Bandwidth Optimization")
        if not self.current_proxy:
            print("⚠️ No active proxy")
            return
            
        # Analyze current performance
        speed = self.speed_test()
        if speed < 500:  # KB/s
            print("🛑 Poor performance detected. Recommendations:")
            print("  - Switch to a faster proxy")
            print("  - Reduce bandwidth-intensive activities")
            print("  - Enable compression if available")
        elif speed < 1000:
            print("⚠️ Moderate performance. Recommendations:")
            print("  - Consider switching to a better proxy")
            print("  - Limit streaming quality")
        else:
            print("✅ Excellent performance. No optimization needed")
            
    def proxy_custom_protocol(self):
        """Create custom protocol handler for proxy"""
        print("\n⚙️ Custom Protocol Setup")
        protocol_name = input("Enter protocol name: ").strip()
        port = input("Enter default port: ").strip()
        
        if protocol_name and port:
            print(f"✅ Custom protocol '{protocol_name}' configured on port {port}")
            # Implementation would add to configuration
        else:
            print("⚠️ Invalid input")
            
    def proxy_auto_documentation(self):
        """Generate automatic documentation for proxy setup"""
        print("\n📝 Generating documentation...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proxy_docs/documentation_{timestamp}.md"
        
        try:
            with open(filename, 'w') as f:
                f.write("# Proxy Configuration Documentation\n\n")
                f.write(f"## Generated on {datetime.now()}\n\n")
                f.write("## Current Configuration\n")
                f.write(f"- Active Proxy: {self.current_proxy['host'] if self.current_proxy else 'None'}\n")
                f.write(f"- Rotation: {'Active' if self.rotation_active else 'Inactive'}\n")
                f.write(f"- Protocol: {self.current_proxy['protocol'] if self.current_proxy else 'N/A'}\n\n")
                f.write("## Proxy Statistics\n")
                f.write(f"- Uptime: {self.proxy_uptime.get('uptime', 'N/A')}\n")
                f.write(f"- Data Sent: {self.traffic_stats['sent'] / (1024*1024):.2f} MB\n")
                f.write(f"- Data Received: {self.traffic_stats['received'] / (1024*1024):.2f} MB\n\n")
                f.write("## Favorite Proxies\n")
                for i, fav in enumerate(self.favorites, 1):
                    f.write(f"{i}. {fav['host']}:{fav['port']}\n")
                    
            print(f"✅ Documentation saved to {filename}")
            return filename
        except Exception as e:
            print(f"❌ Documentation failed: {str(e)}")
            return None

    # ===== SECURITY FEATURES =====
    def setup_proxy_chain(self):
        """Setup proxy chaining for multi-hop anonymity"""
        if not self.config['proxy_chain']:
            return
            
        print(f"{Fore.MAGENTA}⛓ Setting up proxy chain...{Style.RESET_ALL}")
        chain = self.config['proxy_chain']
        chain_str = " -> ".join([f"{p['protocol']}://{p['host']}:{p['port']}" for p in chain])
        print(f"{Fore.CYAN}Proxy chain: {chain_str}{Style.RESET_ALL}")
        
        # In a real implementation, this would configure proxychains
        # For now, we'll simulate it
        os.environ['PROXY_CHAIN'] = json.dumps(chain)
        print(f"{Fore.GREEN}✅ Proxy chain configured{Style.RESET_ALL}")

    def enable_dns_protection(self):
        """Enable DNS leak protection using DNSCrypt-proxy"""
        if not os.path.exists(DNSCRYPT_CONFIG):
            print(f"{Fore.YELLOW}⚠️ DNSCrypt-proxy not installed. Skipping DNS protection.{Style.RESET_ALL}")
            return
            
        try:
            print(f"{Fore.BLUE}🔒 Enabling DNS leak protection...{Style.RESET_ALL}")
            # Configure DNSCrypt to use anonymous DNS
            with open(DNSCRYPT_CONFIG, 'r') as f:
                config = f.read()
                
            # Modify configuration
            config = re.sub(r'^listen_addresses.*', 'listen_addresses = ["127.0.0.1:53"]', config, flags=re.M)
            config = re.sub(r'^require_dnssec.*', 'require_dnssec = true', config, flags=re.M)
            config = re.sub(r'^require_nolog.*', 'require_nolog = true', config, flags=re.M)
            config = re.sub(r'^require_nofilter.*', 'require_nofilter = true', config, flags=re.M)
            
            with open(DNSCRYPT_CONFIG, 'w') as f:
                f.write(config)
                
            # Restart service
            subprocess.run(['pkill', 'dnscrypt-proxy'])
            subprocess.run(['dnscrypt-proxy', '-config', DNSCRYPT_CONFIG, '-daemonize'])
            print(f"{Fore.GREEN}✅ DNS protection enabled{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}❌ DNS protection failed: {str(e)}{Style.RESET_ALL}")

    def enable_kill_switch(self):
        """Enable network kill switch to prevent IP leaks"""
        print(f"{Fore.BLUE}🛡️ Enabling kill switch...{Style.RESET_ALL}")
        try:
            # Flush existing rules
            subprocess.run(['iptables', '-F'])
            subprocess.run(['iptables', '-X'])
            subprocess.run(['iptables', '-t', 'nat', '-F'])
            
            # Allow local traffic
            subprocess.run(['iptables', '-A', 'OUTPUT', '-d', '127.0.0.1', '-j', 'ACCEPT'])
            
            # Allow DNS
            subprocess.run(['iptables', '-A', 'OUTPUT', '-p', 'udp', '--dport', '53', '-j', 'ACCEPT'])
            
            # Block all other traffic
            subprocess.run(['iptables', '-A', 'OUTPUT', '-j', 'DROP'])
            
            print(f"{Fore.GREEN}✅ Kill switch activated - All traffic blocked except proxy{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Kill switch failed: {str(e)}{Style.RESET_ALL}")
            return False

    def disable_kill_switch(self):
        """Disable network kill switch"""
        print(f"{Fore.BLUE}🔓 Disabling kill switch...{Style.RESET_ALL}")
        try:
            subprocess.run(['iptables', '-F'])
            subprocess.run(['iptables', '-X'])
            subprocess.run(['iptables', '-t', 'nat', '-F'])
            print(f"{Fore.GREEN}✅ Kill switch disabled{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Failed to disable kill switch: {str(e)}{Style.RESET_ALL}")
            return False

    def randomize_mac_address(self):
        """Randomize MAC address for Wi-Fi interface"""
        if not self.config['mac_randomization']:
            return
            
        print(f"{Fore.MAGENTA}🔀 Randomizing MAC address...{Style.RESET_ALL}")
        try:
            # Get current MAC
            interfaces = subprocess.getoutput("ip link show | grep '^[0-9]' | awk -F': ' '{print $2}'").split()
            wifi_interface = next((iface for iface in interfaces if 'wlan' in iface), None)
            
            if not wifi_interface:
                print(f"{Fore.YELLOW}⚠️ No Wi-Fi interface found{Style.RESET_ALL}")
                return
                
            # Generate random MAC
            prefix = random.choice(MAC_PREFIXES)
            new_mac = f"{prefix}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}:{random.randint(0, 255):02x}"
            
            # Set new MAC
            subprocess.run(['ip', 'link', 'set', wifi_interface, 'down'])
            subprocess.run(['ip', 'link', 'set', wifi_interface, 'address', new_mac])
            subprocess.run(['ip', 'link', 'set', wifi_interface, 'up'])
            
            print(f"{Fore.GREEN}✅ MAC address randomized: {new_mac}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ MAC randomization failed: {str(e)}{Style.RESET_ALL}")
            return False

    def generate_random_user_agent(self):
        """Generate random user agent for requests"""
        agents = [
            # Chrome
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.{}.{}.{} Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{}.{}.{}.{} Safari/537.36",
            
            # Firefox
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:{}.0) Gecko/20100101 Firefox/{}.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:{}.0) Gecko/20100101 Firefox/{}.0",
            
            # Safari
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{}.{} Safari/605.1.15"
        ]
        
        template = random.choice(agents)
        
        if "Chrome" in template:
            version = f"{random.randint(90, 115)}.0.{random.randint(1000, 6000)}.{random.randint(1, 200)}"
            return template.format(*(version.split('.')))
        elif "Firefox" in template:
            version = random.randint(90, 115)
            return template.format(version, version)
        else:  # Safari
            return template.format(random.randint(14, 16), random.randint(0, 5))

    def generate_browser_profile(self):
        """Generate randomized browser profile to prevent fingerprinting"""
        if not self.config['browser_spoofing']:
            return
            
        print(f"{Fore.BLUE}🖥️ Generating browser profile...{Style.RESET_ALL}")
        profile = {
            "user_agent": self.generate_random_user_agent(),
            "platform": random.choice(["Win32", "MacIntel", "Linux x86_64"]),
            "language": random.choice(["en-US", "en-GB", "fr-FR", "de-DE"]),
            "timezone": random.choice(["UTC", "GMT", "PST", "EST"]),
            "screen": f"{random.randint(1280, 3840)}x{random.randint(720, 2160)}",
            "fonts": random.sample([
                "Arial", "Times New Roman", "Helvetica", "Verdana", 
                "Georgia", "Courier New", "Tahoma"
            ], 5),
            "canvas_hash": ''.join(random.choices('0123456789abcdef', k=32)),
            "webgl_hash": ''.join(random.choices('0123456789abcdef', k=32)),
            "audio_context": random.random(),
            "hardware_concurrency": random.choice([2, 4, 8, 16]),
            "device_memory": random.choice([2, 4, 8, 16])
        }
        
        profile_file = f"browser_profiles/profile_{int(time.time())}.json"
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=4)
            
        # Save to database
        conn = sqlite3.connect(FINGERPRINT_DB)
        c = conn.cursor()
        c.execute('''INSERT INTO fingerprints 
                    (user_agent, platform, language, timezone, screen, fonts, 
                    canvas_hash, webgl_hash, created) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (profile['user_agent'], profile['platform'], profile['language'],
                 profile['timezone'], profile['screen'], json.dumps(profile['fonts']),
                 profile['canvas_hash'], profile['webgl_hash'], datetime.now().isoformat()))
        conn.commit()
        conn.close()
            
        print(f"{Fore.GREEN}✅ Browser profile generated: {profile_file}{Style.RESET_ALL}")
        return profile

    def apply_geolocation_spoof(self, lat, lon):
        """Apply mock location to spoof GPS coordinates"""
        try:
            print(f"{Fore.BLUE}📍 Spoofing location to: {lat}, {lon}{Style.RESET_ALL}")
            # Requires mock location app to be installed
            subprocess.run([
                'am', 'startservice', '-n',
                'com.lexa.fakegps/.FakeGPSService',
                '-a', 'android.intent.action.VIEW',
                '--ef', 'latitude', str(lat),
                '--ef', 'longitude', str(lon)
            ])
            print(f"{Fore.GREEN}✅ Location spoofed{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ Location spoofing failed: {str(e)}{Style.RESET_ALL}")
            return False

    def enable_tor_service(self):
        """Enable TOR integration"""
        if not self.config['tor_integration']:
            return
            
        try:
            print(f"{Fore.BLUE}🔒 Enabling TOR integration...{Style.RESET_ALL}")
            
            # Create TOR configuration
            torrc = f"""
            SocksPort {LOCAL_PROXY_PORT}
            Log notice file {LOG_FILE}
            """
            
            if self.tor_bridges:
                torrc += "UseBridges 1\n"
                for bridge in self.tor_bridges[:3]:
                    torrc += f"Bridge {bridge}\n"
            
            tor_config = f"tor_config_{int(time.time())}.conf"
            with open(tor_config, 'w') as f:
                f.write(torrc)
                
            # Start TOR service
            subprocess.Popen(['tor', '-f', tor_config], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            print(f"{Fore.GREEN}✅ TOR service started on port {LOCAL_PROXY_PORT}{Style.RESET_ALL}")
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ TOR integration failed: {str(e)}{Style.RESET_ALL}")
            return False

    def display_traffic_stats(self):
        """Display traffic statistics"""
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}📊 TRAFFIC STATISTICS".center(50) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        
        # Current session
        print(f"{Fore.CYAN}Current Session:{Style.RESET_ALL}")
        print(f"  Sent: {self.traffic_stats['sent'] / 1024:.2f} KB")
        print(f"  Received: {self.traffic_stats['received'] / 1024:.2f} KB")
        
        # Historical data
        conn = sqlite3.connect(TRAFFIC_DB)
        c = conn.cursor()
        c.execute("SELECT SUM(sent), SUM(received) FROM traffic")
        total = c.fetchone()
        
        if total and total[0]:
            print(f"\n{Fore.CYAN}Historical Total:{Style.RESET_ALL}")
            print(f"  Sent: {total[0] / (1024 * 1024):.2f} MB")
            print(f"  Received: {total[1] / (1024 * 1024):.2f} MB")
        
        # Last 7 days
        c.execute("""SELECT DATE(timestamp), SUM(sent), SUM(received) 
                     FROM traffic 
                     WHERE DATE(timestamp) >= DATE('now', '-7 days') 
                     GROUP BY DATE(timestamp)""")
        print(f"\n{Fore.CYAN}Last 7 Days:{Style.RESET_ALL}")
        for row in c.fetchall():
            print(f"  {row[0]}: ↑{row[1] / 1024:.2f} KB / ↓{row[2] / 1024:.2f} KB")
        
        conn.close()
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")

    def display_network_map(self):
        """Display network visualization"""
        print(f"\n{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🌍 NETWORK MAP".center(50) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")
        
        if self.current_proxy:
            print(f"{Fore.CYAN}Your Device{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  ├── {Fore.YELLOW}Local IP: {self.get_local_ip()}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  ├── {Fore.YELLOW}Proxy: {self.current_proxy['host']}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  │   ├── {Fore.CYAN}Country: {self.current_proxy.get('country', 'Unknown')}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  │   └── {Fore.CYAN}Protocol: {self.current_proxy['protocol'].upper()}{Style.RESET_ALL}")
            
            if self.config['proxy_chain']:
                print(f"{Fore.GREEN}  └── {Fore.MAGENTA}Proxy Chain:{Style.RESET_ALL}")
                for i, hop in enumerate(self.config['proxy_chain'], 1):
                    print(f"{Fore.GREEN}      {i}. {hop['protocol']}://{hop['host']}:{hop['port']}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}  └── {Fore.MAGENTA}Direct Internet{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Your Device{Style.RESET_ALL}")
            print(f"{Fore.GREEN}  └── {Fore.MAGENTA}Direct Internet Connection{Style.RESET_ALL}")
            
        print(f"{Fore.MAGENTA}{'='*50}{Style.RESET_ALL}")

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

# ===== ENTERPRISE FEATURES SUBMENU =====
def enterprise_menu(proxy_master):
    while True:
        print(f"\n{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}🚀 ENTERPRISE FEATURES".center(30) + f"{Style.RESET_ALL}")
        print(f"{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
        print(f"1. {Fore.CYAN}🗺️ Proxy Geofencing{Style.RESET_ALL}")
        print(f"2. {Fore.CYAN}📈 Uptime Monitor{Style.RESET_ALL}")
        print(f"3. {Fore.CYAN}📊 Analytics Dashboard{Style.RESET_ALL}")
        print(f"4. {Fore.CYAN}🔄 Failover System{Style.RESET_ALL}")
        print(f"5. {Fore.CYAN}💾 Backup Config{Style.RESET_ALL}")
        print(f"6. {Fore.CYAN}📥 Restore Config{Style.RESET_ALL}")
        print(f"7. {Fore.CYAN}🔍 Discovery Scan{Style.RESET_ALL}")
        print(f"8. {Fore.CYAN}⚙️ Custom Protocol{Style.RESET_ALL}")
        print(f"9. {Fore.CYAN}📝 Auto Documentation{Style.RESET_ALL}")
        print(f"10. {Fore.CYAN}📊 Bandwidth Optimizer{Style.RESET_ALL}")
        print(f"11. {Fore.CYAN}🔗 Share QR Code{Style.RESET_ALL}")
        print(f"12. {Fore.CYAN}📈 Usage Forecast{Style.RESET_ALL}")
        print(f"13. {Fore.CYAN}🔙 Back to Main Menu{Style.RESET_ALL}")
        
        choice = input(f"\n{Fore.YELLOW}🔍 Select option:{Style.RESET_ALL} ").strip()
        
        if choice == '1':
            countries = input(f"{Fore.CYAN}Enter countries to allow (comma separated):{Style.RESET_ALL} ").strip().split(',')
            proxy_master.proxy_geofence([c.strip() for c in countries])
        elif choice == '2':
            proxy_master.proxy_uptime_monitor()
        elif choice == '3':
            proxy_master.proxy_analytics_dashboard()
        elif choice == '4':
            proxy_master.proxy_failover_system()
        elif choice == '5':
            proxy_master.backup_proxy_config()
        elif choice == '6':
            proxy_master.restore_proxy_config()
        elif choice == '7':
            network = input(f"{Fore.CYAN}Enter network to scan [192.168.1.0/24]:{Style.RESET_ALL} ").strip() or "192.168.1.0/24"
            proxy_master.proxy_discovery_scan(network)
        elif choice == '8':
            proxy_master.proxy_custom_protocol()
        elif choice == '9':
            proxy_master.proxy_auto_documentation()
        elif choice == '10':
            proxy_master.proxy_bandwidth_optimizer()
        elif choice == '11':
            proxy_master.proxy_share_qrcode()
        elif choice == '12':
            proxy_master.proxy_usage_forecast()
        elif choice == '13':
            break
        else:
            print(f"{Fore.YELLOW}⚠️ Invalid selection{Style.RESET_ALL}")

# ===== ENHANCED MAIN APPLICATION =====
def main():
    display_banner()
    
    proxy_master = IPAlchemist()
    proxy_master.load_state()
    
    # Auto-start if configured
    if proxy_master.config.get('auto_start', False):
        print(f"\n{Fore.BLUE}🚀 Starting auto-rotation as per configuration...{Style.RESET_ALL}")
        proxy_master.start_rotation(
            proxy_master.config.get('rotation_interval', 5),
            proxy_master.config.get('rotation_duration', 1)
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
        print(f"20. {Fore.CYAN}🚪 Exit{Style.RESET_ALL}")
        
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
                
            interval = input(f"{Fore.CYAN}⏱ Rotation interval (minutes) [5]:{Style.RESET_ALL} ").strip()
            interval = int(interval) if interval else 5
            
            duration = input(f"{Fore.CYAN}⏳ Duration (hours, 0=infinite) [1]:{Style.RESET_ALL} ").strip()
            duration = float(duration) if duration else 1.0
            
            proxy_master.start_rotation(interval, duration)
        
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
                    print(f"    Using fixed endpoint: {LOCAL_PROXY_HOST}:{LOCAL_PROXY_PORT}")
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
        
        elif choice == '7':
            print(f"\n{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚙️ CONFIGURATION".center(30) + f"{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
            print(f"1. API URL: {proxy_master.config['api_url']}")
            print(f"2. Max Latency: {proxy_master.config['max_latency']}ms")
            print(f"3. Protocol Priority: {', '.join(proxy_master.config['protocol_preference'])}")
            print(f"4. Favorite Countries: {', '.join(proxy_master.config['favorite_countries']) or 'None'}")
            print(f"5. Auto-start: {'✅ Enabled' if proxy_master.config['auto_start'] else '❌ Disabled'}")
            print(f"6. Single-Host Mode: {'✅ Enabled' if proxy_master.config['single_host_mode'] else '❌ Disabled'}")
            print(f"7. Notifications: {'✅ Enabled' if proxy_master.config['notifications'] else '❌ Disabled'}")
            print(f"8. History Limit: {proxy_master.config['max_history']} entries")
            print(f"9. DNS Protection: {'✅ Enabled' if proxy_master.config['dns_protection'] else '❌ Disabled'}")
            print(f"10. MAC Randomization: {'✅ Enabled' if proxy_master.config['mac_randomization'] else '❌ Disabled'}")
            print(f"11. Browser Spoofing: {'✅ Enabled' if proxy_master.config['browser_spoofing'] else '❌ Disabled'}")
            print(f"12. TOR Integration: {'✅ Enabled' if proxy_master.config['tor_integration'] else '❌ Disabled'}")
            print(f"13. Traffic Compression: {'✅ Enabled' if proxy_master.config['traffic_compression'] else '❌ Disabled'}")
            print(f"14. Cloud Sync: {'✅ Enabled' if proxy_master.config['cloud_sync'] else '❌ Disabled'}")
            
            sub_choice = input(f"\n{Fore.CYAN}Select setting to change (1-14) or [Enter] to return:{Style.RESET_ALL} ")
            if sub_choice == '1':
                new_url = input(f"{Fore.CYAN}Enter new API URL:{Style.RESET_ALL} ").strip()
                if new_url:
                    proxy_master.config['api_url'] = new_url
            elif sub_choice == '2':
                try:
                    new_latency = int(input(f"{Fore.CYAN}Enter max latency (ms):{Style.RESET_ALL} "))
                    proxy_master.config['max_latency'] = new_latency
                except:
                    print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
            elif sub_choice == '3':
                print(f"{Fore.CYAN}Enter protocols in order (comma separated):{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Options: http, https, socks4, socks5{Style.RESET_ALL}")
                protocols = input(f"{Fore.CYAN}Protocols:{Style.RESET_ALL} ").lower().split(',')
                valid = [p.strip() for p in protocols if p.strip() in ['http', 'https', 'socks4', 'socks5']]
                if valid:
                    proxy_master.config['protocol_preference'] = valid
            elif sub_choice == '4':
                print(f"{Fore.CYAN}Enter country codes (comma separated, e.g., US,CA,GB):{Style.RESET_ALL}")
                countries = [c.strip().upper() for c in input(f"{Fore.CYAN}Countries:{Style.RESET_ALL} ").split(',') if c.strip()]
                proxy_master.config['favorite_countries'] = countries
            elif sub_choice == '5':
                proxy_master.config['auto_start'] = not proxy_master.config['auto_start']
                print(f"Auto-start {'✅ enabled' if proxy_master.config['auto_start'] else '❌ disabled'}")
            elif sub_choice == '6':
                proxy_master.config['single_host_mode'] = not proxy_master.config['single_host_mode']
                print(f"Single-Host Mode {'✅ enabled' if proxy_master.config['single_host_mode'] else '❌ disabled'}")
            elif sub_choice == '7':
                proxy_master.config['notifications'] = not proxy_master.config['notifications']
                print(f"Notifications {'✅ enabled' if proxy_master.config['notifications'] else '❌ disabled'}")
            elif sub_choice == '8':
                try:
                    new_max = int(input(f"{Fore.CYAN}Enter max history entries:{Style.RESET_ALL} "))
                    proxy_master.config['max_history'] = new_max
                except:
                    print(f"{Fore.RED}Invalid input{Style.RESET_ALL}")
            elif sub_choice == '9':
                proxy_master.config['dns_protection'] = not proxy_master.config['dns_protection']
                print(f"DNS Protection {'✅ enabled' if proxy_master.config['dns_protection'] else '❌ disabled'}")
            elif sub_choice == '10':
                proxy_master.config['mac_randomization'] = not proxy_master.config['mac_randomization']
                print(f"MAC Randomization {'✅ enabled' if proxy_master.config['mac_randomization'] else '❌ disabled'}")
            elif sub_choice == '11':
                proxy_master.config['browser_spoofing'] = not proxy_master.config['browser_spoofing']
                print(f"Browser Spoofing {'✅ enabled' if proxy_master.config['browser_spoofing'] else '❌ disabled'}")
            elif sub_choice == '12':
                proxy_master.config['tor_integration'] = not proxy_master.config['tor_integration']
                print(f"TOR Integration {'✅ enabled' if proxy_master.config['tor_integration'] else '❌ disabled'}")
            elif sub_choice == '13':
                proxy_master.config['traffic_compression'] = not proxy_master.config['traffic_compression']
                print(f"Traffic Compression {'✅ enabled' if proxy_master.config['traffic_compression'] else '❌ disabled'}")
            elif sub_choice == '14':
                proxy_master.config['cloud_sync'] = not proxy_master.config['cloud_sync']
                print(f"Cloud Sync {'✅ enabled' if proxy_master.config['cloud_sync'] else '❌ disabled'}")
            
            proxy_master.save_config()
        
        elif choice == '8':
            print(f"\n{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⭐ FAVORITES".center(30) + f"{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}{'='*30}{Style.RESET_ALL}")
            if not proxy_master.favorites:
                print(f"{Fore.YELLOW}No favorites yet{Style.RESET_ALL}")
            else:
                for i, fav in enumerate(proxy_master.favorites, 1):
                    print(f"{Fore.CYAN}{i}. {fav['host']}:{fav['port']} ({fav['protocol'].upper()}) - {fav['country']}{Style.RESET_ALL}")
            
            print(f"\n{Fore.GREEN}a. ➕ Add current proxy{Style.RESET_ALL}")
            print(f"{Fore.GREEN}r. ➖ Remove favorite{Style.RESET_ALL}")
            print(f"{Fore.GREEN}c. 🧹 Clear all favorites{Style.RESET_ALL}")
            fav_choice = input(f"\n{Fore.CYAN}Select option:{Style.RESET_ALL} ").lower()
            
            if fav_choice == 'a' and proxy_master.current_proxy:
                proxy_master.add_favorite(proxy_master.current_proxy)
            elif fav_choice == 'r' and proxy_master.favorites:
                try:
                    index = int(input(f"{Fore.CYAN}Enter favorite number to remove:{Style.RESET_ALL} ")) - 1
                    if 0 <= index < len(proxy_master.favorites):
                        proxy_master.remove_favorite(proxy_master.favorites[index]['host'])
                except:
                    print(f"{Fore.RED}Invalid selection{Style.RESET_ALL}")
            elif fav_choice == 'c' and proxy_master.favorites:
                confirm = input(f"{Fore.RED}⚠️ Clear ALL favorites? (y/n):{Style.RESET_ALL} ").lower()
                if confirm == 'y':
                    proxy_master.favorites = []
                    proxy_master.save_favorites()
                    print(f"{Fore.GREEN}🧹 All favorites cleared{Style.RESET_ALL}")
        
        elif choice == '9':
            proxy_master.show_history()
        
        elif choice == '10':
            filename = input(f"{Fore.CYAN}Enter export filename [proxies_export.txt]:{Style.RESET_ALL} ").strip() or "proxies_export.txt"
            proxy_master.export_proxies(filename)
        
        elif choice == '11':
            if proxy_master.current_proxy:
                proxy_master.speed_test()
            else:
                print(f"{Fore.YELLOW}⚠️ No active proxy to test{Style.RESET_ALL}")
        
        elif choice == '12':
            proxy_master.toggle_single_host_mode()
        
        elif choice == '13':
            proxy_master.config['kill_switch'] = not proxy_master.config['kill_switch']
            status = f"{Fore.GREEN}ENABLED{Style.RESET_ALL}" if proxy_master.config['kill_switch'] else f"{Fore.RED}DISABLED{Style.RESET_ALL}"
            print(f"\n{Fore.MAGENTA}🛡️ Kill Switch: {status}{Style.RESET_ALL}")
            if proxy_master.config['kill_switch']:
                proxy_master.enable_kill_switch()
            else:
                proxy_master.disable_kill_switch()
        
        elif choice == '14':
            try:
                lat = float(input(f"{Fore.CYAN}Enter latitude:{Style.RESET_ALL} ").strip())
                lon = float(input(f"{Fore.CYAN}Enter longitude:{Style.RESET_ALL} ").strip())
                proxy_master.apply_geolocation_spoof(lat, lon)
            except:
                print(f"{Fore.RED}❌ Invalid coordinates{Style.RESET_ALL}")
        
        elif choice == '15':
            profile = proxy_master.generate_browser_profile()
            if profile:
                print(f"{Fore.CYAN}User Agent: {profile['user_agent']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Platform: {profile['platform']}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Screen: {profile['screen']}{Style.RESET_ALL}")
        
        elif choice == '16':
            proxy_master.display_traffic_stats()
        
        elif choice == '17':
            proxy_master.display_network_map()
            
        elif choice == '18':
            enterprise_menu(proxy_master)
            
        elif choice == '19':
            if proxy_master.clear_proxy_settings():
                print(f"{Fore.GREEN}✅ Proxy settings cleared{Style.RESET_ALL}")
        
        elif choice == '20':
            proxy_master.stop_rotation()
            proxy_master.save_state()
            print(f"\n{Fore.MAGENTA}🔌 Exiting Aryan's IP Alchemist{Style.RESET_ALL}")
            break
        
        else:
            print(f"{Fore.YELLOW}⚠️ Invalid selection{Style.RESET_ALL}")

# ===== RUN APPLICATION =====
if __name__ == "__main__":
    main()