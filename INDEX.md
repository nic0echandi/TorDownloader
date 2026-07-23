# 📥 Descargador Automático de Tor

## 📋 Índice de Archivos

```
ransome/
├── tor_downloader.py      ⭐ Script principal de descarga
├── configure.py           ⚙️  Configurador interactivo
├── utils.py               🛠️  Monitor, estadísticas y limpieza
├── install.sh             📦 Instalación de dependencias
├── requirements.txt       📚 Dependencias Python
├── README.md              📖 Documentación completa
├── QUICKSTART.md          🚀 Inicio rápido
└── INDEX.md               📑 Este archivo
```

---

## 🎯 Cómo Empezar

### 1️⃣ Instalación (2 minutos)
```bash
cd /home/user/Documents/ransome
bash install.sh
```

### 2️⃣ Configurar URLs y rutas
```bash
python3 configure.py
```

### 3️⃣ Descargar
```bash
python3 tor_downloader.py
```

---

## 📚 Descripción de Archivos

### `tor_downloader.py` ⭐
**Script principal de descarga**

Características:
- ✅ Descarga recursiva de carpetas onion
- ✅ Verificación SHA256 de integridad
- ✅ Reintentos automáticos (3x con backoff)
- ✅ Logs detallados en archivo
- ✅ Resumen estadístico al final
- ✅ Manejo robusto de errores

**Configuración:**
```python
BASE_URL = "http://xxxxx.onion/carpeta/"      # Tu URL onion
DESTINATION_DIR = Path("/ruta/local")          # Donde guardar
MAX_RETRIES = 3                                # Intentos
TIMEOUT = 30                                   # Segundos por conexión
```

**Uso:**
```bash
python3 tor_downloader.py
```

---

### `configure.py` ⚙️
**Configurador interactivo**

Permite cambiar fácilmente:
- URL onion
- Carpeta de destino
- Puerto de Tor
- Número de reintentos
- Timeout de conexión

**Uso:**
```bash
python3 configure.py
```

---

### `utils.py` 🛠️
**Herramientas de monitoreo y limpieza**

Comandos disponibles:

**Monitorear en tiempo real:**
```bash
python3 utils.py monitor                    # Actualiza cada 5s
python3 utils.py monitor -i 3               # Actualiza cada 3s
python3 utils.py monitor -d /otra/carpeta   # Monitorear otra carpeta
```

**Ver estadísticas:**
```bash
python3 utils.py stats                      # Estadísticas finales
python3 utils.py stats -d /otra/carpeta     # De otra carpeta
```

**Limpiar temporales:**
```bash
python3 utils.py cleanup                    # Eliminar .tmp
python3 utils.py cleanup -d /otra/carpeta   # De otra carpeta
```

---

### `install.sh` 📦
**Script de instalación automática**

Realiza:
1. Verifica Python 3
2. Verifica Tor
3. Instala dependencias (pip)
4. Crea carpetas necesarias
5. Comprueba conexión a Tor

**Uso:**
```bash
bash install.sh
```

---

### `requirements.txt` 📚
**Dependencias Python**

```
requests>=2.31.0         # Descargas HTTP
beautifulsoup4>=4.12.0   # Parsing HTML
urllib3>=2.1.0           # Conexión SOCKS5
PySocks>=1.7.1           # Soporte Tor
```

**Instalar manualmente:**
```bash
pip install -r requirements.txt
```

---

### `README.md` 📖
**Documentación completa**

Incluye:
- Requisitos previos
- Instalación paso a paso
- Configuración detallada
- Ejemplos de uso
- Solución de problemas
- Monitoreo y logging
- Limitaciones y seguridad

---

### `QUICKSTART.md` 🚀
**Guía de inicio rápido**

Resumen ejecutivo:
- Pasos de 2 minutos
- Ejemplo de ejecución
- Troubleshooting básico
- Enlaces a documentación

---

## ⚡ Flujo de Trabajo Típico

```bash
# Día 1: Configuración inicial
bash install.sh              # Instalar todo
python3 configure.py         # Configurar URL y destino

# Día 2: Iniciar descarga
python3 tor_downloader.py    # Comienza la descarga
# (Ctrl+C para pausar, ejecutar de nuevo para reanudar)

# Mientras se descarga (en otro terminal)
python3 utils.py monitor    # Ver progreso en tiempo real

# Después de terminar
python3 utils.py stats      # Ver estadísticas finales
python3 utils.py cleanup    # Limpiar archivos temporales
```

---

## 🔧 Configuración Avanzada

### Cambiar solo URL (editar archivo)
```bash
nano tor_downloader.py
# Buscar y cambiar BASE_URL
# Ctrl+X, Y, Enter
```

### Usar puerto Tor diferente
```bash
# En tor_downloader.py
TOR_PROXY = {
    'http': 'socks5://127.0.0.1:9999',    # Tu puerto
    'https': 'socks5://127.0.0.1:9999'
}
```

### Aumentar reintentos
```bash
# En tor_downloader.py
MAX_RETRIES = 5  # Más intentos
TIMEOUT = 60     # Más tiempo por descarga
```

---

## 📊 Monitoreo

### Terminal 1: Descarga
```bash
python3 tor_downloader.py 2>&1 | tee descarga.log
```

### Terminal 2: Monitor
```bash
python3 utils.py monitor
```

### Terminal 3: Ver logs
```bash
tail -f /home/user/Documents/files_descargados/logs/*.log
```

---

## 🐛 Solución de Problemas

| Problema | Solución |
|----------|----------|
| No conecta a Tor | `sudo systemctl start tor` |
| Puerto incorrecto | Cambiar en `configure.py` o editar script |
| Archivos dañados | Reintenta automáticamente (3x) |
| Descarga lenta | Normal en Tor (~1-3 MB/s) |
| Archivos .tmp restantes | `python3 utils.py cleanup` |

---

## 📝 Logging

Los logs se guardan automáticamente en:
```
/home/user/Documents/files_descargados/logs/descarga_YYYYMMDD_HHMMSS.log
```

Contienen:
- ✓ Cada archivo descargado
- ✓ SHA256 de verificación
- ✓ Reintentos y errores
- ✓ Resumen final
- ✓ Timestamps de cada operación

---

## ✨ Características Destacadas

✅ **Tor integration** - Descarga segura a través de Tor  
✅ **Recursive download** - Explora carpetas automáticamente  
✅ **Integrity check** - Verifica SHA256 de cada archivo  
✅ **Auto-retry** - Reintentos inteligentes con backoff  
✅ **Detailed logging** - Archivo de log con timestamp  
✅ **Stats summary** - Tamaño, velocidad, tiempo total  
✅ **Error handling** - No para en errores individuales  
✅ **Progress monitor** - Observa en tiempo real  

---

## 📞 Soporte

Para problemas específicos:
1. Revisa `README.md` - Sección "Solución de problemas"
2. Verifica logs en: `/home/user/Documents/files_descargados/logs/`
3. Ejecuta `python3 configure.py` para ajustar parámetros

---

## 📋 Checklist Pre-Descarga

- [ ] Tor instalado: `command -v tor`
- [ ] Tor ejecutándose: `sudo systemctl status tor`
- [ ] Python 3 instalado: `python3 --version`
- [ ] Dependencias: `bash install.sh`
- [ ] URL correcta: verificada en `configure.py`
- [ ] Carpeta destino: existe o será creada
- [ ] Espacio disco: suficiente para descargas
- [ ] Red: conexión estable

---

## 🎯 Próximos Pasos

1. **Ejecuta:** `bash install.sh`
2. **Configura:** `python3 configure.py`
3. **Descarga:** `python3 tor_downloader.py`
4. **Monitorea:** `python3 utils.py monitor`
5. **Valida:** `python3 utils.py stats`

---

**¡Listo para descargar!** 🚀

Consulta `QUICKSTART.md` para empezar en 2 minutos.
