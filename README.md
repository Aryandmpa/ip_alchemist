# IP Alchemist 🔧🛰️

**Version:** PROFESSIONAL v8.1  
**Author:** Aryandmpa  
**License:** MIT

## 🌐 What Is It?

A Python-based command-line Swiss Army knife for privacy-focused networking in **Termux**. IP Alchemist empowers users to:

- Obfuscate identity (MAC, IP)
- Scan LAN devices
- Launch a rotating proxy server
- Query DNS & geolocate IPs
- Analyze logs, spoof browser fingerprints
- Integrate TOR bridges

---

## 🚀 Features

| Category              | Description                                     |
|-----------------------|-------------------------------------------------|
| 🔐 Privacy Tools       | MAC rotation, DNSCrypt, TOR bridge support     |
| 📊 Traffic Analysis    | Log and analyze packet flow                    |
| 🌍 Geolocation         | Find location of any IP (GeoLite2)             |
| 📦 Proxy Management    | Fetch, test, and serve proxies (HTTP)          |
| 🧪 Scanning & DNS      | Use nmap, do DNS lookups                       |
| 🧾 QR Code Generator   | Share proxy config securely                    |

---

## 🧰 Prerequisites (Termux)

Ensure you have [Termux](https://f-droid.org/en/packages/com.termux/) installed.

```bash
pkg update && pkg upgrade -y
pkg install python git nmap dnscrypt-proxy macchanger tor -y

📥 Installation
git clone https://github.com/Aryandmpa/ip_alchemist.git
cd ip_alchemist
pip install -r requirements.txt


📦 If requirements.txt fails, manually run:
pip install requests colorama pyfiglet geoip2 qrcode

🗺️ GeoIP Setup
Manually download the GeoLite2-City.mmdb file (registration required) and place it in the project root directory.

Or use:
wget -O GeoLite2-City.mmdb "<VALID_URL_FROM_MAXMIND>"
Replace the placeholder URL in ip_alchemist.py with your download link if you prefer automatic setup.

⚙️ Running The Tool
python ip_alchemist.py


🧪 Example Menu Interface
====== IP Alchemist Menu ======
1. Get Public IP
2. Get Network Interfaces Info
3. Rotate MAC Address
...
12. Generate/Compare Fingerprint
0. Exit
==============================

🧾 Configuration Files

| File                | Purpose                            |
| ------------------- | ---------------------------------- |
| `proxy_config.json` | Stores proxy preferences           |
| `favorites.json`    | Your starred proxies               |
| `state.json`        | Runtime state between sessions     |
| `*.db`              | SQLite DB for traffic, fingerprint |


💡 Usage Notes

Rooted Android gives access to all features (e.g., macchanger, nmap)

Proxy runs on port 8080 by default

Logs stored in ip_alchemist.log

QR codes saved in proxy_qrcodes/

Kill-switch & TOR integration are configurable

🤝 Contributing
git checkout -b feature/YourFeature
# make changes
git commit -m "Add new feature"
git push origin feature/YourFeature
Pull requests welcome!


🛑 Disclaimer
This tool is intended for ethical & educational purposes only. The author is not liable for any misuse.

📞 Contact
For support or collaboration, open an issue on GitHub.


---

## ⚙️ Shell Script (Optional Setup Script: `install.sh`)

```bash
#!/data/data/com.termux/files/usr/bin/bash

echo "📦 Installing IP Alchemist"

pkg update && pkg upgrade -y
pkg install python git nmap dnscrypt-proxy macchanger tor -y

echo "📁 Cloning Repository..."
git clone https://github.com/Aryandmpa/ip_alchemist.git
cd ip_alchemist || exit

echo "🐍 Installing Python Requirements"
pip install -r requirements.txt

echo "📄 Done! To start:"
echo "➡️ cd ip_alchemist && python ip_alchemist.py"

🧠 Pro Tips
✨ QR Code Proxies: Share proxy config by scanning QR!

⚠️ Avoid port conflicts: If port 8080 is in use, change in ip_alchemist.py

🔐 Use with Termux:API for advanced automation



