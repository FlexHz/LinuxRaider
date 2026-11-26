# Guía de Uso y Configuración

Esta guía explica cómo usar todas las funciones de **LinuxRaider** tanto desde la interfaz gráfica como desde la terminal.

---

## 1. Interfaz Gráfica (GUI)

Al ejecutar `linuxraider` (o abrir **LinuxRaider** desde el menú de aplicaciones) verás los siguientes controles:

### Botón principal: Modo Juego
- **ACTIVAR MODO JUEGO / ✓ MODO JUEGO ACTIVADO:** activa o desactiva la aplicación del perfil ICC en tu monitor principal.
- Al **desactivar** el modo juego, la pantalla vuelve a `sRGB` estándar pero **se conservan tu perfil seleccionado y los valores de los sliders**, de modo que puedas volver a activarlo con un solo clic.

### Perfil de Visibilidad
- Incluye dos perfiles integrados por defecto:
  - **`night_vision`** (*Visión Nocturna*): eleva sombras profundas y tonos medios (`Shadow Boost: 85%`, `Gamma: 1.40x`, `Brillo: 1.20x`, `Contraste: 1.00x`).
  - **`neutral`** (*Estándar / Neutral*): curva lineal estándar sin alteraciones.
- **Guardar:** guarda los valores actuales de los 4 sliders como un nuevo perfil `.json` en `~/.config/linuxraider/profiles/`.

### Ajustes en Tiempo Real (Sliders)
Mover cualquier slider activa la vista previa en vivo automáticamente:

| Ajuste | Rango | Efecto |
| :--- | :---: | :--- |
| **Brillo de Imagen** | `0.60x` – `1.60x` | Escala la luminosidad general de la curva tonal. |
| **Shadow Boost** | `0%` – `100%` | Levanta selectivamente las zonas más oscuras (cuevas, sombras) sin quemar los blancos puros. |
| **Curva Gamma** | `0.80x` – `1.80x` | Ajusta la exposición de los tonos medios. |
| **Contraste** | `0.70x` – `1.30x` | Modula la pendiente entre luces y sombras mediante una curva suavizada alrededor del punto medio. |

### Restablecer vs. Desactivar
- **Desactivar Modo Juego:** apaga temporalmente el perfil en el monitor (`sRGB`), pero deja tus ajustes listos en la ventana.
- **Restablecer:** devuelve el monitor a `sRGB`, selecciona el perfil `neutral` y reinicia los sliders a `1.00x / 0%`.

### Bandeja del sistema (*System Tray*)
Al cerrar la ventana con la `X`, LinuxRaider no se cierra: permanece en la bandeja junto al reloj con opciones rápidas para **Alternar Modo Juego**, **Abrir LinuxRaider** o **Salir**.

---

## 2. Detección Automática de Ventana

LinuxRaider puede activar y desactivar el Modo Juego automáticamente según qué ventana tenga el foco del sistema operativo en **KDE Plasma 6 Wayland**:

1. Marca la casilla **Activar Modo Juego solo cuando "ARC Raiders" tiene el foco**.
2. LinuxRaider comprueba de forma exacta que el título de la ventana activa sea `ARC Raiders`, evitando falsos positivos con pestañas del navegador (como wikis o guías abiertas).
3. La línea de estado inferior te muestra qué ventana tiene el foco en cada momento:
   - Si el juego recibe el foco, el Modo Juego se activa al instante con tu perfil actual.
   - Si cambias a otra ventana (por ejemplo con `Alt+Tab`), tras un breve margen de `150 ms` se restaura `sRGB` estándar para que el escritorio se vea con colores normales.

Tu preferencia se guarda automáticamente en `~/.config/linuxraider/settings.json`.

---

## 3. Referencia de Línea de Comandos (CLI)

Si pasas argumentos al ejecutable `linuxraider`, funciona en modo CLI sin abrir la ventana gráfica:

```bash
# Opcional: especificar salida de monitor en cualquier comando
linuxraider --output DP-1 status
```

| Comando | Descripción |
| :--- | :--- |
| `linuxraider status` | Muestra la salida activa, fuente de color (`sRGB` o `ICC`) y ruta del archivo ICC si aplica. |
| `linuxraider list` | Lista todos los perfiles disponibles en `~/.config/linuxraider/profiles/`. |
| `linuxraider apply <perfil>` | Compila y aplica el perfil indicado (ej. `linuxraider apply night_vision`). |
| `linuxraider toggle [perfil]` | Alterna entre el perfil indicado (por defecto `night_vision`) y `sRGB`. |
| `linuxraider test [perfil] [-d N]` | Aplica temporalmente el perfil durante `N` segundos (por defecto `4`) y luego restaura `sRGB`. |
| `linuxraider quick [-b B] [-g G] [-c C]` | Aplica valores al vuelo sin guardar perfil (`--boost`, `--gamma`, `--contrast`). |
| `linuxraider reset` | Restablece el monitor a `sRGB` estándar. |

---

## 4. Atajos de teclado en KDE Plasma 6

1. Abre **Preferencias del Sistema** -> **Atajos de teclado**.
2. Pulsa **Añadir nuevo** -> **Comando o script**.
3. Escribe `linuxraider toggle` como comando.
4. Asígnale la tecla deseada (por ejemplo `Pause`, `F9` o `Meta+B`) y guarda los cambios.

---

## 5. Solución de problemas

- **Error `kscreen-doctor no se encuentra instalado`:** asegúrate de estar ejecutando KDE Plasma 6 Wayland (`kscreen` / `libkscreen` instalado).
- **Error al cargar `liblcms2`:** instala el paquete de LittleCMS 2 de tu distribución (en Arch/CachyOS: `sudo pacman -S lcms2`).
- **La detección automática no reconoce el juego:** asegúrate de que el título de la ventana del juego sea exactamente `ARC Raiders` (puedes comprobar el título detectado en la línea `En espera (foco: ...)`).
