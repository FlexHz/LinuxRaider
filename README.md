# LinuxRaider 🎮

Herramienta de post-procesamiento digital de curvas de color, brillo, gamma, contraste y ecualización de sombras (*Shadow Boost / Black Equalizer*) para juegos en Linux (optimizada para **CachyOS / KDE Plasma 6 Wayland**).

Inspirado en *BrightRaider*, utiliza el pipeline de gestión de color por GPU nativo de KDE Plasma 6 a través de perfiles ICC generados algorítmicamente con `liblcms2` y aplicados mediante `kscreen-doctor`.

---

## ⚡ Características

* **0 FPS de impacto:** La curva tonal (TRC) se compila en un perfil ICC y la GPU la aplica directamente en su shader de salida.
* **0 ms de latencia (*input lag*):** No añade colas de cuadros ni intercepta el proceso del juego.
* **Seguro contra Anticheat:** Opera a nivel de compositor gráfico (KWin), completamente fuera del proceso del juego.
* **Interfaz gráfica + Bandeja del sistema (PyQt6):** Sliders en tiempo real para Brillo, Shadow Boost, Gamma y Contraste, con perfiles guardables.
* **Detección automática de ventana (KWin Wayland):** Activa el modo juego automáticamente cuando *ARC Raiders* (o las ventanas configuradas) recibe el foco del sistema y vuelve a sRGB estándar al hacer Alt-Tab.
* **Control por CLI y atajos de teclado:** Alterna o aplica perfiles desde consola o atajos globales de KDE.

---

## 📋 Requisitos

* **Sistema:** KDE Plasma 6 en Wayland (`kscreen-doctor` y `org.kde.KWin /Scripting`)
* **Bibliotecas:** Python 3.10+, `PyQt6` (`pip install -r requirements.txt` o paquete del sistema `python-pyqt6`), `liblcms2` (`lcms2`)

---

## 🛠️ Instalación

```bash
git clone https://github.com/<tu-usuario>/LinuxRaider.git
cd LinuxRaider
pip install -r requirements.txt
chmod +x install.sh && ./install.sh
```

El script `install.sh` crea el enlace simbólico en `~/.local/bin/linuxraider`, instala el ícono y registra el lanzador `.desktop` en tu menú de aplicaciones.

---

## 🚀 Uso Rápido (GUI y CLI)

```bash
# Abrir interfaz gráfica
linuxraider

# Ver estado actual de la pantalla y el perfil activo
linuxraider status

# Listar perfiles disponibles
linuxraider list

# Probar el perfil 'night_vision' durante 4 segundos (vuelve solo a sRGB)
linuxraider test night_vision

# Activar o desactivar con un solo comando (ideal para atajos de teclado)
linuxraider toggle

# Aplicar un perfil específico
linuxraider apply night_vision
linuxraider apply neutral

# Restablecer la pantalla al modo normal
linuxraider reset

# Probar ajustes personalizados al vuelo
linuxraider quick --boost 0.7 --gamma 1.25 --contrast 1.05
```

---

## ⌨️ Configurar atajo de teclado en KDE Plasma 6

1. Abre **Preferencias del Sistema** en KDE.
2. Ve a **Atajos** -> **Atajos de teclado**.
3. Haz clic en **Añadir nuevo** -> **Comando o script**.
4. En comando, escribe:
   ```bash
   linuxraider toggle
   ```
5. Asígnale la tecla que prefieras (por ejemplo: `F1`, `Pause`, o `Meta + B`) y haz clic en **Aplicar**.
