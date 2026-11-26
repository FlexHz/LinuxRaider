# LinuxRaider 🎮

**LinuxRaider** es una utilidad de post-procesamiento visual por GPU para juegos en Linux (optimizada para **CachyOS / KDE Plasma 6 Wayland**). Permite mejorar la visibilidad en zonas oscuras, cuevas e interiores —como en *ARC Raiders*— mediante curvas tonales aplicadas con perfiles ICC nativos de KWin, **sin impacto en FPS, sin latencia adicional y sin tocar los archivos o memoria del juego**.

---

## 🤔 ¿Qué problema resuelve?

Muchos juegos competitivos o de extracción tienen interiores muy oscuros donde es difícil distinguir detalles o enemigos. Subir el brillo físico del monitor lava toda la imagen, y usar inyectores o *overlays* puede afectar el rendimiento o generar incompatibilidades con sistemas anticheat.

**LinuxRaider** resuelve esto usando el propio compositor gráfico de KDE Plasma 6 (**KWin**):
- Compila una curva de respuesta tonal (TRC) en un perfil **ICC** usando `liblcms2`.
- Le indica a KWin que aplique ese perfil en el *shader* de salida de la GPU mediante `kscreen-doctor`.
- Cuando sales del juego o desactivas el modo juego, restaura el perfil **sRGB estándar** al instante.

---

## ⚡ Características principales

- **0 FPS de impacto y 0 ms de *input lag*:** el cálculo de la curva se compila una vez y la GPU aplica la tabla de color directamente en el compositor.
- **Seguro frente a Anticheat:** funciona completamente fuera del proceso del juego, a nivel de pantalla/compositor.
- **Interfaz gráfica en PyQt6 + Bandeja del sistema:**
  - Botón rápido **Activar / Desactivar Modo Juego** que conserva tu perfil y ajustes seleccionados al desactivar.
  - Sliders en tiempo real para **Brillo**, **Shadow Boost**, **Curva Gamma** y **Contraste**.
  - Guardado y selección de perfiles personalizados.
- **Detección automática de ventana (KWin Wayland):** detecta en tiempo real cuándo el juego tiene el foco del sistema (por defecto configurado para *ARC Raiders*) y desactiva el filtro automáticamente al hacer `Alt+Tab`.
- **CLI y atajos globales:** permite controlar perfiles desde consola o asignarlos a una tecla en KDE.

---

## 📋 Requisitos

- **Entorno:** Linux con **KDE Plasma 6 en Wayland** (`kscreen-doctor` y servicio D-Bus `org.kde.KWin /Scripting`).
- **Python:** 3.10 o superior.
- **Dependencias:**
  - `PyQt6` (con soporte `QtDBus`, p. ej. `pip install -r requirements.txt` o paquete `python-pyqt6`).
  - `liblcms2` (LittleCMS 2, p. ej. paquete `lcms2`).

---

## 🛠️ Instalación

```bash
git clone https://github.com/<tu-usuario>/LinuxRaider.git
cd LinuxRaider
pip install -r requirements.txt
./install.sh
```

El script [`install.sh`](install.sh) crea el comando `~/.local/bin/linuxraider`, instala el ícono de la aplicación y registra el lanzador de escritorio en `~/.local/share/applications/linuxraider.desktop`.

---

## 🚀 Uso rápido

### Interfaz gráfica (GUI)
```bash
linuxraider
```
Al cerrar la ventana, la aplicación sigue ejecutándose minimizada en la bandeja del sistema (*System Tray*).

### Línea de comandos (CLI)
```bash
linuxraider status                     # Ver monitor activo y si hay perfil ICC aplicado
linuxraider list                       # Listar perfiles guardados
linuxraider toggle                     # Alternar entre 'night_vision' y sRGB estándar
linuxraider apply night_vision         # Aplicar un perfil específico
linuxraider test night_vision -d 4     # Probar un perfil 4 segundos y volver a sRGB
linuxraider reset                      # Restaurar la pantalla a sRGB estándar
```

---

## 📚 Documentación adicional

- 📖 **[Guía de uso y configuración](docs/usage.md):** explicación de cada slider, detección automática de ventanas, referencia completa del CLI, atajos en KDE y solución de problemas.
- ⚙️ **[Arquitectura técnica](docs/architecture.md):** cómo funciona la curva matemática de *Shadow Boost*, el compilador ICC con LittleCMS, el puente con `kscreen-doctor` y el watcher D-Bus de KWin.

---

## 📁 Estructura del proyecto

```text
LinuxRaider/
├── main.py                         # Punto de entrada (GUI o CLI según argumentos)
├── install.sh                      # Instalador local (CLI, ícono y .desktop)
├── requirements.txt                # Dependencias Python (PyQt6)
├── docs/                           # Documentación detallada de uso y arquitectura
├── resources/
│   └── linuxraider.png             # Ícono oficial del proyecto
└── linuxraider/
    ├── cli.py                      # Subcomandos de línea de comandos
    ├── core/
    │   └── profiles.py             # Carga/guardado de perfiles y settings.json
    ├── engine/
    │   ├── curves.py               # Generación monotónica de curvas tonales
    │   ├── icc_builder.py          # Compilación de perfiles ICC vía liblcms2
    │   ├── display_manager.py      # Control de salidas de pantalla con kscreen-doctor
    │   └── window_watcher.py       # Detección de foco en KWin Wayland vía D-Bus
    └── ui/
        └── main_window.py          # Ventana principal PyQt6 y bandeja del sistema
```

---

## 📄 Licencia

Distribuido bajo la licencia [MIT](LICENSE).
