# Arquitectura Técnica de LinuxRaider

Este documento describe cómo funciona **LinuxRaider** internamente y el flujo de datos desde la interfaz hasta el compositor gráfico de KDE Plasma 6.

---

## Visión general del flujo

```text
┌─────────────────────────┐      ┌──────────────────────────────┐
│  GUI PyQt6 / Tray / CLI │ ───▶ │ ProfileManager (profiles.py) │
└─────────────────────────┘      └──────────────┬───────────────┘
          ▲                                     │ curva de 256 puntos
          │ D-Bus (windowChanged)               ▼
┌─────────┴───────────────┐      ┌──────────────────────────────┐
│ KWinWindowWatcher       │      │ CurveGen + ICCBuilder        │
│ (window_watcher.py)     │      │ (curves.py + liblcms2.so.2)  │
└─────────▲───────────────┘      └──────────────┬───────────────┘
          │                                     │ archivo .icc
          │ workspace.windowActivated           ▼
┌─────────┴─────────────────────────────────────────────────────┐
│ KDE Plasma 6 Wayland (KWin + kscreen-doctor)                  │
│ Shader de gestión de color en GPU -> Monitor (p. ej. DP-1)    │
└───────────────────────────────────────────────────────────────┘
```

---

## Módulos principales

### 1. Generador de curvas tonales (`linuxraider/engine/curves.py`)
`generate_tone_curve()` calcula una tabla de 256 puntos en el rango `[0.0, 1.0]` con dos propiedades clave:
- **Monotonía estricta:** garantiza `curve[i] >= curve[i - 1]` y extremos exactos en `0.0` y `1.0`, evitando solarización o inversiones de color.
- **Elevación progresiva de sombras:** combina el exponente base (`2.2 * gamma^0.85 * brightness`) con un incremento dinámico proporcional a `shadow_boost * (1.0 - x) * 1.35`, levantando las sombras bajas mientras conserva intactas las altas luces.
- **Contraste suavizado:** aplica una modulación centrada en `0.5` atenuada cerca de `0.0` y `1.0` para no recortar negros ni blancos.

### 2. Compilador ICC (`linuxraider/engine/icc_builder.py`)
`ICCBuilder` carga dinámicamente `liblcms2` (`ctypes.util.find_library("lcms2") or "liblcms2.so.2"`) sin depender de binarios externos:
- Construye una curva tabular flotante con `cmsBuildTabulatedToneCurveFloat`.
- Crea un perfil RGB estándar con punto blanco **D65** `(0.3127, 0.3290)` y primarios **sRGB / Rec.709** (`cmsCreateRGBProfile`), asignando la misma curva TRC a los canales R, G y B.
- Escribe el archivo `.icc` en `~/.config/linuxraider/icc/`.

### 3. Controlador de pantalla (`linuxraider/engine/display_manager.py`)
`DisplayManager` interactúa con `kscreen-doctor`:
- **Descubrimiento de monitores:** `get_outputs()` analiza la salida JSON de `kscreen-doctor -j` y ordena las pantallas conectadas y activas por prioridad para detectar el monitor principal.
- **Consulta de estado:** `get_output_status()` parsea `kscreen-doctor -o` para saber si la fuente de color activa es `ICC` o `sRGB`.
- **Aplicación y reversión:**
  - `apply_icc_profile()` ejecuta `kscreen-doctor output.<nombre>.iccprofile.<ruta> output.<nombre>.colorProfileSource.ICC`.
  - `reset_to_srgb()` ejecuta `kscreen-doctor output.<nombre>.colorProfileSource.sRGB`.

#### Recarga en tiempo real sin caché de ruta (*Ping-Pong*)
Al arrastrar sliders en la GUI (`main_window.py`), un temporizador *debounce* de `40 ms` alterna la escritura entre dos archivos (`live_mode_0.icc` y `live_mode_1.icc`). Cambiar la ruta del archivo fuerza a KWin a recargar la nueva tabla de color inmediatamente en lugar de ignorar un archivo con el mismo nombre.

De forma similar, al desactivar el modo ICC (`_disable_display_icc()`), se aplica brevemente `neutral_reset.icc` antes de cambiar la fuente a `sRGB` para asegurar que el compositor limpie cualquier LUT previa.

### 4. Detección de foco en Wayland (`linuxraider/engine/window_watcher.py`)
Dado que Wayland aísla las aplicaciones e impide consultar libremente qué ventana está enfocada desde otro proceso, `KWinWindowWatcher` utiliza la interfaz oficial de scripting de KWin sobre D-Bus:
- Registra un receptor D-Bus de sesión en `org.linuxraider.WindowWatcher.p<PID>` (`/Watcher`).
- Carga un script JavaScript temporal en `org.kde.KWin /Scripting` (`loadScript` + `run`) que escucha `workspace.windowActivated` y `captionChanged` sobre la ventana activa.
- Cada cambio envía por `callDBus` los metadatos de la ventana (`caption`, `resourceClass`, `resourceName`, `desktopFileName`) a la aplicación PyQt6.
- En la GUI, al perder el foco del juego se aplica un *debounce* de `150 ms` antes de revertir a `sRGB`, evitando parpadeos transitorios durante `Alt+Tab`.
- Al desactivar la opción o cerrar la aplicación (`aboutToQuit`), `stop()` descarga el script con `unloadScript`, elimina el archivo `.js` temporal y libera el servicio D-Bus.

### 5. Almacenamiento de configuración y perfiles (`linuxraider/core/profiles.py`)
`ProfileManager` gestiona el directorio `~/.config/linuxraider/`:
- `profiles/*.json`: definiciones de perfiles (`night_vision`, `neutral` y los creados por el usuario).
- `icc/*.icc`: perfiles ICC compilados.
- `settings.json`: estado persistente de detección automática (`auto_detect_enabled`).
