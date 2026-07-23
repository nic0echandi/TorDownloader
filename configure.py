#!/usr/bin/env python3
"""
Configurador interactivo para el descargador Tor
"""

import re
import subprocess
from pathlib import Path


def read_config_from_script(script_path: str) -> dict:
    """Leer configuración actual del script."""
    with open(script_path, 'r') as f:
        content = f.read()
    
    config = {}
    
    # Extraer BASE_URL
    match = re.search(r'BASE_URL = ["\']([^"\']+)["\']', content)
    if match:
        config['base_url'] = match.group(1)
    
    # Extraer DESTINATION_DIR
    match = re.search(r'DESTINATION_DIR = Path\(["\']([^"\']+)["\']\)', content)
    if match:
        config['dest_dir'] = match.group(1)
    
    # Extraer MAX_RETRIES
    match = re.search(r'MAX_RETRIES = (\d+)', content)
    if match:
        config['max_retries'] = int(match.group(1))
    
    # Extraer TIMEOUT
    match = re.search(r'TIMEOUT = (\d+)', content)
    if match:
        config['timeout'] = int(match.group(1))
    
    # Extraer TOR_PROXY puerto
    match = re.search(r"'http': 'socks5h://127.0.0.1:(\d+)'", content)
    if match:
        config['tor_port'] = int(match.group(1))
    
    return config


def write_config_to_script(script_path: str, config: dict) -> None:
    """Escribir configuración al script."""
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Reemplazar BASE_URL
    content = re.sub(
        r'BASE_URL = "[^"]+"',
        f'BASE_URL = "{config["base_url"]}"',
        content
    )
    
    # Reemplazar DESTINATION_DIR
    content = re.sub(
        r'DESTINATION_DIR = Path\("[^"]+"\)',
        f'DESTINATION_DIR = Path("{config["dest_dir"]}")',
        content
    )
    
    # Reemplazar MAX_RETRIES
    content = re.sub(
        r'MAX_RETRIES = \d+',
        f'MAX_RETRIES = {config["max_retries"]}',
        content
    )
    
    # Reemplazar TIMEOUT
    content = re.sub(
        r'TIMEOUT = \d+',
        f'TIMEOUT = {config["timeout"]}',
        content
    )
    
    # Reemplazar puerto TOR_PROXY
    if 'tor_port' in config:
        content = re.sub(
            r"'http': 'socks5h://127\.0\.0\.1:\d+'",
            f"'http': 'socks5h://127.0.0.1:{config['tor_port']}'",
            content
        )
        content = re.sub(
            r"'https': 'socks5h://127\.0\.0\.1:\d+'",
            f"'https': 'socks5h://127.0.0.1:{config['tor_port']}'",
            content
        )
    
    with open(script_path, 'w') as f:
        f.write(content)


def main():
    """Programa principal."""
    script_path = "tor_downloader.py"
    
    if not Path(script_path).exists():
        print(f"❌ Error: No se encontró {script_path}")
        return
    
    print("\n" + "=" * 60)
    print("CONFIGURADOR - Descargador Tor")
    print("=" * 60 + "\n")
    
    config = read_config_from_script(script_path)
    
    print("Configuración actual:\n")
    print(f"1. URL Onion: {config.get('base_url', 'N/A')}")
    print(f"2. Destino local: {config.get('dest_dir', 'N/A')}")
    print(f"3. Puerto Tor: {config.get('tor_port', 9050)}")
    print(f"4. Reintentos: {config.get('max_retries', 3)}")
    print(f"5. Timeout (seg): {config.get('timeout', 30)}")
    print(f"6. Ejecutar descarga")
    print(f"0. Salir\n")
    
    while True:
        choice = input("Selecciona una opción (0-6): ").strip()
        
        if choice == "0":
            print("Saliendo...")
            break
        
        elif choice == "1":
            url = input(
                f"\nNueva URL Onion [{config.get('base_url')}]: "
            ).strip()
            if url:
                if not url.startswith("http://"):
                    url = "http://" + url
                if not url.endswith("/"):
                    url += "/"
                config['base_url'] = url
                print(f"✓ URL actualizada a: {url}")
        
        elif choice == "2":
            dest = input(
                f"\nNueva carpeta destino [{config.get('dest_dir')}]: "
            ).strip()
            if dest:
                dest = dest.replace("~", str(Path.home()))
                config['dest_dir'] = dest
                print(f"✓ Destino actualizado a: {dest}")
        
        elif choice == "3":
            port = input(
                f"\nNuevo puerto Tor [{config.get('tor_port', 9050)}]: "
            ).strip()
            if port and port.isdigit():
                config['tor_port'] = int(port)
                print(f"✓ Puerto actualizado a: {port}")
        
        elif choice == "4":
            retries = input(
                f"\nNúmero de reintentos [{config.get('max_retries', 3)}]: "
            ).strip()
            if retries and retries.isdigit():
                config['max_retries'] = int(retries)
                print(f"✓ Reintentos actualizados a: {retries}")
        
        elif choice == "5":
            timeout = input(
                f"\nTimeout en segundos [{config.get('timeout', 30)}]: "
            ).strip()
            if timeout and timeout.isdigit():
                config['timeout'] = int(timeout)
                print(f"✓ Timeout actualizado a: {timeout}")
        
        elif choice == "6":
            # Guardar configuración
            write_config_to_script(script_path, config)
            print("\n✓ Configuración guardada")
            
            # Ejecutar
            print("\nIniciando descarga...\n")
            try:
                subprocess.run([
                    "python3",
                    script_path
                ], check=False)
            except KeyboardInterrupt:
                print("\n⚠ Descarga cancelada")
            except Exception as e:
                print(f"❌ Error: {e}")
            break
        
        else:
            print("❌ Opción inválida")
        
        print()
    
    # Guardar configuración final
    if choice != "0":
        write_config_to_script(script_path, config)
        print("\n✓ Configuración guardada en tor_downloader.py")
    
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
