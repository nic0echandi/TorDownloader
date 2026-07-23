#!/usr/bin/env python3
"""
Wrapper CLI - Ejecuta tor_downloader.py con entrada simulada
"""

import sys
import subprocess

url = "http://pifk3xu3vad6cuxsjll4qjomyaaaoyvnyqppro75pazadzctrrvpdnyd.onion/5618a8ba9fb25e88e8d315420b539638-transvill/"
dest = "/home/user/Documents/files_descargados"

# Entrada simulada para el script
entrada = f"{url}\n\n"

try:
    proc = subprocess.Popen(
        [sys.executable, '/home/user/Documents/ransome/tor_downloader.py'],
        stdin=subprocess.PIPE,
        text=True,
        cwd='/home/user/Documents/ransome'
    )
    proc.communicate(input=entrada, timeout=600)
    sys.exit(proc.returncode)
except subprocess.TimeoutExpired:
    proc.kill()
    print("⏱ Tiempo de espera agotado")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
