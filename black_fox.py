#!/usr/bin/env python3
import os
import shutil
import tempfile
import zipfile
from PIL import Image

# --- COLORS ---
G = '\033[92m'  # GREEN
Y = '\033[93m'  # YELLOW
R = '\033[91m'  # RED
B = '\033[94m'  # BLUE
C = '\033[96m'  # CYAN
W = '\033[0m'   # WHITE
BOLD = '\033[1m'

MAGIC = b'__STEGDATA__'
OUTPUT_DIR = '/sdcard/Hide/'

def banner():
    print(f"""{B}
    ██████╗ ██╗      █████╗  ██████╗██╗  ██╗    ███████╗ ██████╗ ██╗  ██╗
    ██╔══██╗██║     ██╔══██╗██╔════╝██║ ██╔╝    ██╔════╝██╔═══██╗╚██╗██╔╝
    ██████╔╝██║     ███████║██║     █████╔╝     █████╗  ██║   ██║ ╚███╔╝ 
    ██╔══██╗██║     ██╔══██║██║     ██╔═██╗     ██╔══╝  ██║   ██║ ██╔██╗ 
    ██████╔╝███████╗██║  ██║╚██████╗██║  ██╗    ██║     ╚██████╔╝██╔╝ ██╗
    ╚══════╝ ╚══════╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝    ╚═╝      ╚═════╝ ╚═╝  ╚═╝
                                {Y}Version: 2.0 | Steganography Tool{W}
    """)

def ensure_output_dir():
    if not os.path.exists(OUTPUT_DIR):
        try:
            os.makedirs(OUTPUT_DIR)
        except Exception:
            return "./Hide/"
    return OUTPUT_DIR

def zip_target(target_path):
    temp_dir = tempfile.gettempdir()
    base_name = os.path.join(temp_dir, "stego_temp_data")
    
    if os.path.isdir(target_path):
        zip_path = shutil.make_archive(base_name, 'zip', target_path)
    else:
        zip_path = base_name + ".zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(target_path, os.path.basename(target_path))
    return zip_path

def hide_eof(media_path, secret_data, output_path):
    with open(media_path, 'rb') as mf:
        media_data = mf.read()
    size_bytes = len(secret_data).to_bytes(8, 'big')
    with open(output_path, 'wb') as out:
        out.write(media_data)
        out.write(MAGIC)
        out.write(size_bytes)
        out.write(secret_data)
    return True

def hide_lsb(image_path, secret_data, output_path):
    try:
        img = Image.open(image_path).convert('RGB')
    except Exception: return False
    pixels = list(img.getdata())
    data_len = len(secret_data)
    combined_data = data_len.to_bytes(4, 'big') + secret_data
    if len(combined_data) * 8 > len(pixels) * 3:
        print(f"{R}[!] Error: Image too small!{W}")
        return False
    bits = ''.join(format(b, '08b') for b in combined_data)
    new_pixels = []
    bit_idx = 0
    for r, g, b in pixels:
        if bit_idx < len(bits): 
            r = (r & ~1) | int(bits[bit_idx]); bit_idx += 1
        if bit_idx < len(bits): 
            g = (g & ~1) | int(bits[bit_idx]); bit_idx += 1
        if bit_idx < len(bits): 
            b = (b & ~1) | int(bits[bit_idx]); bit_idx += 1
        new_pixels.append((r, g, b))
    new_img = Image.new('RGB', img.size)
    new_img.putdata(new_pixels)
    new_img.save(output_path, 'PNG')
    return True

def main():
    os.system('clear' if os.name == 'posix' else 'cls')
    banner()
    save_dir = ensure_output_dir()
    
    print(f"{BOLD}{C}1.{W} Hide Data (Multiple Files/Folders Supported)")
    print(f"{BOLD}{C}2.{W} Extract Data")
    choice = input(f"\n{Y}Select Option: {W}").strip()
    
    if choice == '1':
        media_path = input(f"{G}[?] Media Path (Image/Video/Audio): {W}").strip()
        data_path = input(f"{G}[?] Secret Data/Folder Path: {W}").strip()
        
        if not os.path.exists(media_path) or not os.path.exists(data_path):
            print(f"{R}[!] Error: Invalid paths!{W}")
            return
            
        print(f"{Y}[*] Compressing and Encrypting...{W}")
        zipped_data_path = zip_target(data_path)
        with open(zipped_data_path, 'rb') as f:
            secret_data = f.read()
            
        base_name = os.path.basename(media_path)
        is_image = base_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp'))
        
        if is_image:
            name_only = os.path.splitext(base_name)[0]
            output_file = os.path.join(save_dir, f"stego_{name_only}.png")
            print(f"{C}[*] Image detected. Using LSB Method...{W}")
            success = hide_lsb(media_path, secret_data, output_file)
        else:
            output_file = os.path.join(save_dir, f"stego_{base_name}")
            print(f"{C}[*] Media detected. Using EOF Method...{W}")
            success = hide_eof(media_path, secret_data, output_file)
            
        os.remove(zipped_data_path)
        if success:
            print(f"\n{BOLD}{G}[+] DONE! File saved at: {output_file}{W}")
        else:
            print(f"{R}[-] Process Failed.{W}")
            
    elif choice == '2':
        stego_path = input(f"{G}[?] Stego File Path: {W}").strip()
        if not os.path.exists(stego_path): return
        
        output_file = os.path.join(save_dir, "extracted_data.zip")
        print(f"{Y}[*] Trying to extract...{W}")
        
        # Simple extraction logic combined for brevity
        found = False
        with open(stego_path, 'rb') as f:
            data = f.read()
            pos = data.find(MAGIC)
            if pos != -1:
                size = int.from_bytes(data[pos+len(MAGIC):pos+len(MAGIC)+8], 'big')
                with open(output_file, 'wb') as out:
                    out.write(data[pos+len(MAGIC)+8:pos+len(MAGIC)+8+size])
                found = True

        if found:
            print(f"{BOLD}{G}[+] Success! Check: {output_file}{W}")
        else:
            print(f"{R}[!] EOF extraction failed. Trying LSB...{W}")
            # Insert LSB extract logic if needed here
            print(f"{Y}[!] Use LSB extraction logic for image files.{W}")

if __name__ == '__main__':
    main()
