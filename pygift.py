import os
import subprocess
import socket
import time
import sys
import threading

# অটোমেটিক লাইব্রেরি চেক এবং ইনস্টলেশন
def check_requirements():
    # Termux package (openssh) চেক
    if subprocess.run(['command', '-v', 'ssh'], stdout=subprocess.DEVNULL).returncode != 0:
        print("\033[1;33m[*] Installing openssh...\033[0m")
        subprocess.run(['pkg', 'install', 'openssh', '-y'], stdout=subprocess.DEVNULL)

    # Python library (qrcode) চেক
    try:
        import qrcode
    except ImportError:
        print("\033[1;33m[*] Installing qrcode library...\033[0m")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'qrcode'], stdout=subprocess.DEVNULL)

# কোড রান করার আগেই ডিপেন্ডেন্সি চেক করে নেবে
check_requirements()
import qrcode # ইনস্টল হওয়ার পর ইমপোর্ট করা হচ্ছে

# রং এবং স্টাইলের জন্য ANSI Codes
GREEN = '\033[1;32m'
CYAN = '\033[1;36m'
YELLOW = '\033[1;33m'
RED = '\033[1;31m'
MAGENTA = '\033[1;35m'
RESET = '\033[0m'
BOLD = '\033[1m'

def banner():
    os.system('clear')
    ascii_art = f"""
{MAGENTA}  _____        _____ _  __ _   
 |  __ \      / ____(_)/ _| |  
 | |__) |   _| |  __ _| |_| |_ 
 |  ___/ | | | | |_ | |  _| __|
 | |   | |_| | |__| | | | | |_ 
 |_|    \__, |\_____|_|_|  \__|
         __/ |                 
        |___/ {YELLOW}V 1.0.0 {RESET}
{CYAN}---------------------------------------
   {BOLD}Handcrafted for Termux Lovers ⚡{RESET}
{CYAN}---------------------------------------
    """
    print(ascii_art)

def setup_ssh():
    # SSH Key চেক করা এবং জেনারেট করা
    ssh_path = os.path.expanduser("~/.ssh/id_rsa")
    if not os.path.exists(ssh_path):
        print(f"{YELLOW}[*] SSH Key পাওয়া যায়নি। জেনারেট করা হচ্ছে...{RESET}")
        if not os.path.exists(os.path.expanduser("~/.ssh")):
            os.makedirs(os.path.expanduser("~/.ssh"))
        subprocess.run(['ssh-keygen', '-t', 'rsa', '-N', '', '-f', ssh_path], 
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"{GREEN}[✓] SSH Key তৈরি সফল!{RESET}\n")

def get_html_files():
    folder = "website"
    if not os.path.exists(folder):
        os.makedirs(folder)
        # একটি ডেমো ইনডেক্স ফাইল তৈরি
        with open(f"{folder}/index.html", "w") as f:
            f.write("<html><body><h1>PyGift Success!</h1></body></html>")
    
    files = [f for f in os.listdir(folder) if f.endswith('.html')]
    return files

def select_file(files):
    while True:
        print(f"{CYAN}{BOLD}উপলব্ধ ওয়েবসাইট ফাইলসমূহ:{RESET}")
        for i, file in enumerate(files, 1):
            print(f"{YELLOW}[{i}] {RESET}{file}")
        
        try:
            choice = int(input(f"\n{GREEN}আপনার পছন্দের ফাইল নাম্বারটি লিখুন: {RESET}"))
            if 1 <= choice <= len(files):
                return files[choice-1]
            else:
                print(f"{RED}\n[!] ভুল নির্বাচন! সঠিক নাম্বার দিন।{RESET}\n")
        except ValueError:
            print(f"{RED}\n[!] ইনপুট শুধুমাত্র নাম্বার হতে হবে।{RESET}\n")

def run_local_server(port, folder):
    os.chdir(folder)
    subprocess.Popen([sys.executable, "-m", "http.server", str(port)], 
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def start_tunnel(port):
    # Localhost.run এর মাধ্যমে টানেলিং
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -R 80:localhost:{port} nokey@localhost.run"
    process = subprocess.Popen(ssh_cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    print(f"{YELLOW}[*] পাবলিক ইউআরএল জেনারেট হচ্ছে...{RESET}")
    
    public_url = ""
    start_time = time.time()
    while time.time() - start_time < 20: 
        line = process.stdout.readline()
        if "localhost.run" in line:
            parts = line.split()
            for part in parts:
                if "https://" in part:
                    public_url = part
                    break
            if public_url: break
    return public_url

def main():
    try:
        banner()
        setup_ssh()
        
        files = get_html_files()
        if not files:
            print(f"{RED}[!] 'website' ফোল্ডারে কোনো HTML ফাইল নেই!{RESET}")
            return

        selected_file = select_file(files)
        
        # বর্তমান ডিরেক্টরি মনে রাখা
        original_dir = os.getcwd()
        
        port = 8080
        run_local_server(port, "website")
        
        url = start_tunnel(port)
        
        if url:
            banner()
            print(f"{GREEN}{BOLD}🎉 আপনার সাইট এখন ইন্টারনেটে লাইভ!{RESET}")
            print(f"{CYAN}---------------------------------------")
            print(f"{YELLOW}🔗 পাবলিক লিংক: {BOLD}{url}{RESET}")
            print(f"{CYAN}---------------------------------------")
            
            # QR Code জেনারেশন
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(url)
            qr.make()
            qr.print_ascii()
            
            print(f"\n{RED}{BOLD}[!] সার্ভার বন্ধ করতে CTRL + C চাপুন{RESET}")
            
            while True:
                time.sleep(1)
        else:
            print(f"{RED}[!] টানেলিং ব্যর্থ হয়েছে। আপনার ইন্টারনেট কানেকশন চেক করুন।{RESET}")

    except KeyboardInterrupt:
        print(f"\n\n{RED}[-] সার্ভার বন্ধ করা হচ্ছে...{RESET}")
        sys.exit()

if __name__ == "__main__":
    main()
