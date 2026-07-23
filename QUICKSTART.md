# Quick Start - Descargador Tor

## 🚀 Inicio Rápido (2 minutos)

### Paso 1: Instalar
```bash
cd /home/user/Documents/ransome
bash install.sh
```

### Paso 2: Configurar (opcional)
Si necesitas cambiar URL o carpeta de destino:
```bash
python3 configure.py
```

O edita directamente `tor_downloader.py`:
```python
BASE_URL = "http://xxxxx.onion/tu-carpeta/"
DESTINATION_DIR = Path("/ruta/local")
```

### Paso 3: Ejecutar
```bash
python3 tor_downloader.py
```

---

## ⚡ Requisitos

✅ Tor ejecutándose: `sudo systemctl start tor`  
✅ Python 3.8+  
✅ Dependencias instaladas (por `install.sh`)  

---

## 📊 Ejemplo de Ejecución

```
2024-01-15 14:32:10 - INFO - INICIANDO DESCARGA DESDE TOR
2024-01-15 14:32:10 - INFO - Verificando conexión a Tor...
2024-01-15 14:32:15 - INFO - ✓ Conexión a Tor confirmada
2024-01-15 14:32:15 - INFO - Explorando: http://xxxxx.onion/files/
2024-01-15 14:32:18 - INFO - Descargando: archivo1.zip (45.2 MB)
2024-01-15 14:32:24 - INFO - ✓ archivo1.zip (45.2 MB) SHA256: a1b2c3d4e5f6...
...
2024-01-15 15:45:30 - INFO - RESUMEN DE DESCARGA
2024-01-15 15:45:30 - INFO - Total de archivos: 247
2024-01-15 15:45:30 - INFO - Descargados: 245
2024-01-15 15:45:30 - INFO - Fallidos: 2
2024-01-15 15:45:30 - INFO - Tamaño total: 12.5 GB
2024-01-15 15:45:30 - INFO - Tiempo: 1h 13m
2024-01-15 15:45:30 - INFO - Velocidad: 2.84 MB/s
```

---

## 🛠️ Troubleshooting

| Problema | Solución |
|----------|----------|
| "Cannot connect to Tor" | Inicia Tor: `sudo systemctl start tor` |
| "Connection timeout" | Aumenta `TIMEOUT` en configure.py |
| "socks5 requires urllib3" | `pip install urllib3[socks]` |
| Archivos parciales | Script reintentar automáticamente |

---

## 📝 Logs

Los logs se guardan en:
```
/home/user/Documents/files_descargados/logs/descarga_YYYYMMDD_HHMMSS.log
```

Ver en tiempo real:
```bash
tail -f /home/user/Documents/files_descargados/logs/*.log
```

---

## ✨ Características

- ✅ Descarga recursiva de carpetas
- ✅ Verificación SHA256 de integridad
- ✅ Reintentos automáticos (3x)
- ✅ Backoff exponencial
- ✅ Logs detallados
- ✅ Resumen estadístico
- ✅ Anulable con Ctrl+C

---

## 📚 Más información

```bash
cat README.md           # Documentación completa
cat requirements.txt    # Dependencias
python3 tor_downloader.py --help  # Ayuda del script
```

---

**¡Listo!** Ya puedes descargar tus archivos automáticamente.
