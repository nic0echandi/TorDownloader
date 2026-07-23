#!/usr/bin/env python3
"""
Utilidades para monitorear y limpiar descargas
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime


def human_readable_size(size):
    """Convertir bytes a formato legible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def monitor_downloads(dest_dir="/home/user/Documents/files_descargados", interval=5):
    """Monitorear progreso de descargas en tiempo real."""
    dest_path = Path(dest_dir)
    
    if not dest_path.exists():
        print(f"❌ Carpeta no existe: {dest_dir}")
        return
    
    print("=" * 70)
    print(f"Monitor de Descargas - {dest_path}")
    print("=" * 70)
    print(f"Actualización cada {interval} segundos (Ctrl+C para salir)\n")
    
    previous_size = 0
    
    try:
        while True:
            # Contar archivos
            total_files = sum(1 for _ in dest_path.rglob('*') if _.is_file())
            
            # Contar archivos .tmp (incompletos)
            tmp_files = sum(1 for _ in dest_path.rglob('*.tmp'))
            
            # Calcular tamaño total
            total_size = sum(
                f.stat().st_size 
                for f in dest_path.rglob('*') 
                if f.is_file() and not f.name.endswith('.tmp')
            )
            
            # Calcular tamaño de temporales
            tmp_size = sum(
                f.stat().st_size 
                for f in dest_path.rglob('*.tmp') 
                if f.is_file()
            )
            
            # Velocidad de descarga
            speed = total_size - previous_size
            previous_size = total_size
            speed_str = human_readable_size(speed)
            
            # Timestamp
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Limpiar pantalla y mostrar
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print("=" * 70)
            print(f"Monitor de Descargas - {dest_path}")
            print("=" * 70)
            print(f"Actualizado: {timestamp}\n")
            
            print("📊 ESTADÍSTICAS:")
            print(f"  Archivos completados: {total_files - tmp_files}")
            print(f"  Archivos descargándose: {tmp_files}")
            print(f"  Tamaño completado: {human_readable_size(total_size)}")
            print(f"  Tamaño temporal: {human_readable_size(tmp_size)}")
            print(f"  Velocidad actual: {speed_str}/s")
            
            # Mostrar logs recientes
            log_dir = dest_path / "logs"
            if log_dir.exists():
                log_files = sorted(log_dir.glob("*.log"), reverse=True)
                if log_files:
                    print(f"\n📝 LOG MÁS RECIENTE: {log_files[0].name}")
                    # Mostrar últimas 5 líneas
                    with open(log_files[0], 'r') as f:
                        lines = f.readlines()[-5:]
                        print("  Últimas líneas:")
                        for line in lines:
                            print(f"  {line.rstrip()}")
            
            print("\n" + "=" * 70)
            print("Presiona Ctrl+C para salir")
            print("=" * 70)
            
            time.sleep(interval)
    
    except KeyboardInterrupt:
        print("\n\n✓ Monitor detenido")


def cleanup_temp_files(dest_dir="/home/user/Documents/files_descargados"):
    """Limpiar archivos temporales incompletos."""
    dest_path = Path(dest_dir)
    
    if not dest_path.exists():
        print(f"❌ Carpeta no existe: {dest_dir}")
        return
    
    tmp_files = list(dest_path.rglob('*.tmp'))
    
    if not tmp_files:
        print("✓ No hay archivos temporales")
        return
    
    print(f"⚠️  Se encontraron {len(tmp_files)} archivos temporales:")
    
    total_size = sum(f.stat().st_size for f in tmp_files)
    print(f"   Tamaño total: {human_readable_size(total_size)}\n")
    
    for f in tmp_files[:5]:  # Mostrar primeros 5
        print(f"   - {f.relative_to(dest_path)} ({human_readable_size(f.stat().st_size)})")
    
    if len(tmp_files) > 5:
        print(f"   ... y {len(tmp_files) - 5} más")
    
    response = input("\n¿Eliminar estos archivos? (s/n): ").strip().lower()
    
    if response in ['s', 'yes', 'si']:
        for f in tmp_files:
            f.unlink()
        print(f"✓ {len(tmp_files)} archivos eliminados")
    else:
        print("Cancelado")


def show_statistics(dest_dir="/home/user/Documents/files_descargados"):
    """Mostrar estadísticas finales."""
    dest_path = Path(dest_dir)
    
    if not dest_path.exists():
        print(f"❌ Carpeta no existe: {dest_dir}")
        return
    
    # Recopilar datos
    files = [f for f in dest_path.rglob('*') if f.is_file()]
    total_files = len([f for f in files if not f.name.endswith('.tmp')])
    tmp_files = len([f for f in files if f.name.endswith('.tmp')])
    total_size = sum(
        f.stat().st_size 
        for f in files 
        if not f.name.endswith('.tmp')
    )
    
    # Archivos por carpeta
    folders = {}
    for f in files:
        if f.name.endswith('.tmp'):
            continue
        folder = f.parent.relative_to(dest_path)
        if str(folder) not in folders:
            folders[str(folder)] = {'count': 0, 'size': 0}
        folders[str(folder)]['count'] += 1
        folders[str(folder)]['size'] += f.stat().st_size
    
    # Mostrar
    print("=" * 70)
    print(f"ESTADÍSTICAS DE DESCARGA - {dest_path}")
    print("=" * 70 + "\n")
    
    print(f"Total de archivos: {total_files}")
    print(f"Archivos incompletos: {tmp_files}")
    print(f"Tamaño total: {human_readable_size(total_size)}\n")
    
    print("📁 POR CARPETA:")
    for folder in sorted(folders.keys()):
        stats = folders[folder]
        print(f"  {folder or 'raíz'}: {stats['count']} archivos ({human_readable_size(stats['size'])})")
    
    print("\n" + "=" * 70)


def main():
    """Menú principal."""
    if len(sys.argv) < 2:
        print("Utilidades de Descarga Tor\n")
        print("Uso:")
        print("  python3 utils.py monitor          Monitorear progreso en tiempo real")
        print("  python3 utils.py cleanup          Limpiar archivos temporales")
        print("  python3 utils.py stats            Mostrar estadísticas finales")
        print("\nOpciones:")
        print("  -d, --dir PATH                    Especificar carpeta (default: /home/user/Documents/files_descargados)")
        print("  -i, --interval N                  Intervalo monitor en segundos (default: 5)")
        return
    
    cmd = sys.argv[1].lower()
    dest_dir = "/home/user/Documents/files_descargados"
    interval = 5
    
    # Parsear argumentos
    if '-d' in sys.argv or '--dir' in sys.argv:
        idx = sys.argv.index('-d') if '-d' in sys.argv else sys.argv.index('--dir')
        if idx + 1 < len(sys.argv):
            dest_dir = sys.argv[idx + 1]
    
    if '-i' in sys.argv or '--interval' in sys.argv:
        idx = sys.argv.index('-i') if '-i' in sys.argv else sys.argv.index('--interval')
        if idx + 1 < len(sys.argv):
            try:
                interval = int(sys.argv[idx + 1])
            except ValueError:
                print("❌ Intervalo debe ser un número")
                return
    
    if cmd == 'monitor':
        monitor_downloads(dest_dir, interval)
    elif cmd == 'cleanup':
        cleanup_temp_files(dest_dir)
    elif cmd == 'stats':
        show_statistics(dest_dir)
    else:
        print(f"❌ Comando desconocido: {cmd}")


if __name__ == "__main__":
    main()
