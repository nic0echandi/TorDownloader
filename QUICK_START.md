# 🚀 GUÍA RÁPIDA: Uso de Reanudación de Descargas

## 📋 En 3 Pasos

### **Paso 1: Primera ejecución**
```bash
python3 tor_downloader.py
# Ingresa URL onion
# Ingresa directorio destino
```

### **Paso 2: Se interrumpe la descarga**
```
(Ctrl+C o corte de conexión/Tor)
```

### **Paso 3: Reanudar**
```bash
# Ejecuta el MISMO COMANDO
python3 tor_downloader.py
# Automáticamente:
# ✓ Detecta archivos previos
# ✓ Reanuda con Range si posible
# ✓ Salta ya descargados
```

---

## 🎯 Resultados Esperados

### **Primera Ejecución**
```
✓ URL configurada
✓ Directorio configurado
✓ Explorando: http://xxx.onion/

  Descargando: archivo1.zip [████████████░░░░░░] 60%
  Descargando: archivo2.pdf [████████████████░░] 80%
  ...
```

### **Reanudación Automática**
```
📂 Estado previo cargado: 5 archivos
⏭️  Saltando (ya descargado): archivo1.zip
📥 Reanudando: archivo2.pdf (500.00 MB/1000.00 MB)
  archivo2.pdf [██████░░░░░░░░░░░░] 40% (continuando)
```

---

## 📊 Dónde Ver el Progreso

### **Archivos de log**
```bash
# Ver últimos logs en tiempo real
tail -f <DESTINATION_DIR>/logs/descarga_*.log

# Ver todos los logs
ls -la <DESTINATION_DIR>/logs/
```

### **Estado persistente**
```bash
# Ver qué archivos están guardados
cat <DESTINATION_DIR>/.download_state/download_state.json

# Bonito con indentación
python3 -m json.tool <DESTINATION_DIR>/.download_state/download_state.json
```

### **Monitor en vivo** (script incluido)
```bash
# (Si quieres usar el monitor de utils.py)
python3 utils.py
```

---

## ⚙️ Configuración Avanzada

### **Cambiar puerto Tor** (si no es 9050)
```python
# Editar en tor_downloader.py:
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9051',    # ← Cambiar puerto
    'https': 'socks5h://127.0.0.1:9051'
}
```

### **Cambiar límites de Range** (FASE 2)
```python
# Editar en tor_downloader.py:
MIN_RANGE_SIZE = 512 * 1024      # Usar Range desde 512KB
RANGE_TIMEOUT = 5                 # Timeout más corto
```

### **Forzar redescarga completa**
```bash
# Opción 1: Borrar estado
rm -rf <DESTINATION_DIR>/.download_state/

# Opción 2: Mover estado viejo
mv <DESTINATION_DIR>/.download_state/ \
   <DESTINATION_DIR>/.download_state.backup/
```

---

## 🧪 Verificar que Funciona

### **Prueba 1: Reanudación sin Range**
```bash
# 1. Descargar un archivo pequeño (<1MB)
python3 tor_downloader.py
# Ingresa URL onion
# (Deja que descargue un archivo)

# 2. Presiona Ctrl+C después del primer archivo

# 3. Ejecuta de nuevo
python3 tor_downloader.py
# Debería ver: ⏭️  Saltando (ya descargado)
```

### **Prueba 2: Reanudación con Range**
```bash
# 1. Busca un archivo >100MB en el onion

# 2. Inicia descarga
python3 tor_downloader.py
# (Deja que empiece)

# 3. Presiona Ctrl+C a los 10-30 segundos

# 4. Ejecuta de nuevo
python3 tor_downloader.py
# Debería ver: 📥 Reanudando: (con porcentaje)
```

### **Prueba 3: Ver estado guardado**
```bash
# 1. Después de primera descarga
cat <DESTINATION_DIR>/.download_state/download_state.json

# 2. Verifica que contiene:
#    - "timestamp": fecha/hora
#    - "status": "completed" o "partial"
#    - "downloaded_files": lista de archivos
```

---

## 🔧 Solución de Problemas

### **Problema: No carga estado previo**
```
❌ Estado no se carga

✅ Solución:
# Verificar que el directorio existe
ls -la <DESTINATION_DIR>/.download_state/

# Verificar que el JSON es válido
python3 -m json.tool <DESTINATION_DIR>/.download_state/download_state.json
```

### **Problema: No detecta Range support**
```
❌ Siempre descarga completo

✅ Verificar:
# 1. Servidor Tor soporta Range (algunos no)
# 2. Archivo es >1MB (MIN_RANGE_SIZE = 1MB)
# 3. Ver en log: "Range support para..."

# Es normal si algunos servidores no soportan.
# El sistema fallback a descarga completa automáticamente.
```

### **Problema: JSON corrupto**
```
❌ Error al cargar estado

✅ Solución automática:
# El sistema carga automáticamente desde backup
# Ver log: "Estado recuperado desde backup"

✅ Si backup también está corrupto:
rm -rf <DESTINATION_DIR>/.download_state/
python3 tor_downloader.py
# Comienza desde cero
```

### **Problema: Archivo temporal corrupto**
```
❌ "Archivo temporal corrupto, reiniciando"

✅ Sistema automáticamente:
# 1. Detecta que .tmp es inválido
# 2. Lo elimina
# 3. Descarga completo desde cero
# Esto es seguro y no causará pérdida de datos
```

---

## 📊 Interpretando el Resumen Final

```
======================================================================
RESUMEN DE DESCARGA
======================================================================
Total de archivos encontrados: 150         ← Archivos en total
Archivos descargados exitosamente: 142    ← Completados
Archivos reanudados (Range): 8             ← Reanudados con Range
Archivos fallidos: 0                       ← Con error
Tamaño total descargado: 50.25 GB
Tiempo total: 2.5h
Velocidad promedio: 5.60 MB/s

📊 ESTADÍSTICAS DE PERSISTENCIA:
  Archivos en caché: 142                   ← Guardados en estado
  Archivos fallidos registrados: 0         ← Registrados para retry
  Estado guardado: completed               ← Estado final
```

---

## 💡 Tips y Trucos

### **Acelerar reanudación** 
- Archivos pequeños: Sin Range (automático)
- Archivos grandes: Con Range (automático si servidor soporta)
- Mix: El sistema lo maneja automáticamente

### **Monitorear varias descargas**
```bash
# Terminal 1: Descarga
python3 tor_downloader.py

# Terminal 2: Ver logs en vivo
tail -f /home/user/Documents/files_descargados/logs/descarga_*.log

# Terminal 3: Ver estado (si paras y reanuder)
watch -n 5 'python3 -m json.tool /home/user/Documents/files_descargados/.download_state/download_state.json | head -20'
```

### **Forzar reintento de archivos fallidos**
```bash
# Los archivos fallidos se guardan en:
# ~/.download_state/download_state.json

# Para reintentar: Simplemente ejecuta de nuevo
python3 tor_downloader.py
# Automáticamente reintentará todos los fallidos
```

---

## 📞 Soporte Rápido

| Situación | Comando |
|-----------|---------|
| Ver logs actuales | `tail -f <DIR>/logs/descarga_*.log` |
| Ver estado guardado | `cat <DIR>/.download_state/download_state.json` |
| Limpiar estado | `rm -rf <DIR>/.download_state/` |
| Ver archivos descargados | `ls -lR <DIR>/` |
| Contar archivos | `find <DIR> -type f \| wc -l` |
| Tamaño total | `du -sh <DIR>/` |

---

## ✅ Checklist Reanudación

- [ ] Tor está corriendo en puerto 9050
- [ ] Directorio destino existe y es accesible
- [ ] Conexión a URL onion es estable
- [ ] Hay espacio en disco suficiente
- [ ] Primera descarga se completó o fue interrumpida
- [ ] Archivo `.download_state/download_state.json` existe
- [ ] Ejecuto el mismo comando para reanudar

---

**¡Listo! La reanudación está completamente integrada y funcionando.**
