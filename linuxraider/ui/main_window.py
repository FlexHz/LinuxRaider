"""PyQt6 Graphical User Interface for LinuxRaider."""

import os
import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QSlider,
    QPushButton,
    QComboBox,
    QFrame,
    QSystemTrayIcon,
    QMenu,
    QInputDialog,
    QCheckBox,
    QSizePolicy,
)

from ..core.profiles import ProfileManager
from ..engine.display_manager import DisplayManager
from ..engine.window_watcher import (
    KWinWindowWatcher,
    GAME_WINDOW_TITLE,
    is_game_window,
)


def _get_icon_path() -> str:
    """Return the path to the LinuxRaider application icon."""
    return os.path.join(
        os.path.dirname(__file__), "..", "..", "resources", "linuxraider.png"
    )


DARK_STYLESHEET = """
QMainWindow {
    background-color: #0e1217;
}
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', 'Ubuntu', 'Noto Sans', sans-serif;
    font-size: 13px;
}
QFrame#card {
    background-color: #171d26;
    border: 1px solid #232c3b;
    border-radius: 12px;
    padding: 16px;
}
QLabel#title {
    font-size: 20px;
    font-weight: bold;
    color: #00f2fe;
}
QLabel#subtitle {
    font-size: 12px;
    color: #94a3b8;
}
QLabel#sectionHeader {
    font-size: 14px;
    font-weight: bold;
    color: #38bdf8;
    margin-bottom: 4px;
}
QLabel#sliderLabel {
    font-size: 13px;
    font-weight: 500;
    color: #f1f5f9;
}
QLabel#sliderValue {
    font-size: 13px;
    font-weight: bold;
    color: #00f2fe;
    min-width: 50px;
}
QPushButton#mainToggleActive {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
    color: #0a0c10;
    font-size: 15px;
    font-weight: bold;
    border-radius: 10px;
    padding: 12px;
    border: none;
}
QPushButton#mainToggleInactive {
    background-color: #232c3b;
    color: #94a3b8;
    font-size: 15px;
    font-weight: bold;
    border-radius: 10px;
    padding: 12px;
    border: 1px solid #334155;
}
QPushButton#mainToggleInactive:hover {
    background-color: #2d384a;
    color: #f8fafc;
}
QPushButton#secondaryBtn {
    background-color: #1f2733;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 500;
    color: #cbd5e1;
}
QPushButton#secondaryBtn:hover {
    background-color: #2b3647;
    color: #ffffff;
}
QComboBox {
    background-color: #1a222d;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 8px 12px;
    color: #f8fafc;
    font-weight: 500;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #171d26;
    border: 1px solid #334155;
    selection-background-color: #00f2fe;
    selection-color: #0a0c10;
    padding: 4px;
}
QSlider::groove:horizontal {
    height: 6px;
    background: #232c3b;
    border-radius: 3px;
}
QSlider::sub-page:horizontal {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00f2fe, stop:1 #4facfe);
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #ffffff;
    border: 2px solid #00f2fe;
    width: 18px;
    margin-top: -6px;
    margin-bottom: -6px;
    border-radius: 9px;
}
QSlider::handle:horizontal:hover {
    background: #00f2fe;
}
QCheckBox {
    spacing: 8px;
    font-weight: 500;
    color: #f1f5f9;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 5px;
    border: 1px solid #334155;
    background-color: #1a222d;
}
QCheckBox::indicator:checked {
    background-color: #00f2fe;
    border-color: #00f2fe;
}
"""


class LinuxRaiderApp(QMainWindow):
    """Main Application Window for LinuxRaider with real-time sliders."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("LinuxRaider - Visual Enhancer")
        self.setMinimumSize(540, 800)
        self.resize(540, 840)

        self.profile_mgr = ProfileManager()
        self.display_mgr = DisplayManager()
        self.settings = self.profile_mgr.get_settings()

        self.is_active = False
        self.current_output = self.display_mgr.get_primary_output_name()
        self._last_focus_info = ("", "", "", "")

        # Ping-pong alternating file index to force KWin to reload ICC on slider drag
        self._ping_pong = 0

        # Debounce timer for smooth slider live-updates
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(40)  # 40ms for fast responsive feedback
        self.update_timer.timeout.connect(self._apply_current_settings)

        # Debounce timer for Alt-Tab focus transitions away from the game
        self._unfocus_timer = QTimer(self)
        self._unfocus_timer.setSingleShot(True)
        self._unfocus_timer.setInterval(150)
        self._unfocus_timer.timeout.connect(self._apply_unfocus_deactivation)

        self.window_watcher = KWinWindowWatcher(self)
        self.window_watcher.windowChanged.connect(self._on_active_window_changed)

        self._init_ui()
        self._init_tray()
        self._refresh_status()
        self._sync_auto_detect_state()

        app = QApplication.instance()
        if app is not None:
            app.aboutToQuit.connect(self.cleanup)

    def _init_ui(self):
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # 1. Header
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("LINUXRAIDER", self)
        title.setObjectName("title")
        title.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        subtitle = QLabel("Control de Visibilidad y Sombras para ARC Raiders", self)
        subtitle.setObjectName("subtitle")
        subtitle.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        header_layout.addLayout(title_box)
        header_layout.addStretch()

        self.monitor_badge = QLabel(f"🖥 {self.current_output}", self)
        self.monitor_badge.setStyleSheet(
            "background-color: #1e293b; color: #38bdf8; border-radius: 8px; padding: 6px 12px; font-weight: bold;"
        )
        self.monitor_badge.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        header_layout.addWidget(self.monitor_badge, alignment=Qt.AlignmentFlag.AlignVCenter)
        main_layout.addLayout(header_layout)

        # 2. Master Switch Button
        self.btn_toggle = QPushButton("ACTIVAR MODO JUEGO", self)
        self.btn_toggle.setObjectName("mainToggleInactive")
        self.btn_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle.clicked.connect(self.toggle_mode)
        main_layout.addWidget(self.btn_toggle)

        # 3. Profile Selector Card
        card_profile = QFrame(self)
        card_profile.setObjectName("card")
        card_profile.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_prof = QVBoxLayout(card_profile)
        layout_prof.setSpacing(10)

        lbl_prof = QLabel("Perfil de Visibilidad", self)
        lbl_prof.setObjectName("sectionHeader")
        layout_prof.addWidget(lbl_prof)

        row_prof = QHBoxLayout()
        self.combo_profiles = QComboBox(self)
        self.combo_profiles.setCursor(Qt.CursorShape.PointingHandCursor)
        self._populate_profiles()
        self.combo_profiles.currentIndexChanged.connect(self._on_profile_selected)
        row_prof.addWidget(self.combo_profiles, stretch=3)

        self.btn_save_profile = QPushButton("Guardar", self)
        self.btn_save_profile.setObjectName("secondaryBtn")
        self.btn_save_profile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_profile.clicked.connect(self._save_custom_profile)
        row_prof.addWidget(self.btn_save_profile, stretch=1)

        layout_prof.addLayout(row_prof)
        main_layout.addWidget(card_profile)

        # 4. Sliders Card (Interactive Sliders)
        card_sliders = QFrame(self)
        card_sliders.setObjectName("card")
        layout_sliders = QVBoxLayout(card_sliders)
        layout_sliders.setSpacing(12)

        lbl_sliders = QLabel("Ajustes en Tiempo Real (Mueve para ver cambios)", self)
        lbl_sliders.setObjectName("sectionHeader")
        lbl_sliders.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        layout_sliders.addWidget(lbl_sliders)

        # A. Brillo (Brightness)
        self.slider_bright, self.val_bright = self._create_slider_row(
            layout_sliders,
            label="Brillo de Imagen:",
            min_val=60,
            max_val=160,
            initial=115,
            scale=0.01,
            unit="x",
        )

        # B. Shadow Boost (Black Equalizer)
        self.slider_boost, self.val_boost = self._create_slider_row(
            layout_sliders,
            label="Shadow Boost (Cuevas / Zonas Oscuras):",
            min_val=0,
            max_val=100,
            initial=65,
            unit="%",
        )

        # C. Gamma (Iluminación de tonos medios)
        self.slider_gamma, self.val_gamma = self._create_slider_row(
            layout_sliders,
            label="Curva Gamma (Tonos Medios):",
            min_val=80,
            max_val=180,
            initial=120,
            scale=0.01,
            unit="x",
        )

        # D. Contraste
        self.slider_contrast, self.val_contrast = self._create_slider_row(
            layout_sliders,
            label="Contraste:",
            min_val=70,
            max_val=130,
            initial=100,
            scale=0.01,
            unit="x",
        )

        # Sync sliders with initial selected profile without activating Game Mode
        initial_prof = self.combo_profiles.currentData()
        if initial_prof:
            self._load_profile_to_sliders(initial_prof, activate=False)

        main_layout.addWidget(card_sliders, stretch=1)

        # 5. Auto Window Detection Card
        card_auto = QFrame(self)
        card_auto.setObjectName("card")
        card_auto.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        layout_auto = QVBoxLayout(card_auto)
        layout_auto.setSpacing(8)

        lbl_auto = QLabel("Detección Automática de Ventana", self)
        lbl_auto.setObjectName("sectionHeader")
        layout_auto.addWidget(lbl_auto)

        self.chk_auto_detect = QCheckBox(
            f'Activar Modo Juego solo cuando "{GAME_WINDOW_TITLE}" tiene el foco', self
        )
        self.chk_auto_detect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_auto_detect.setChecked(bool(self.settings.get("auto_detect_enabled", True)))
        self.chk_auto_detect.toggled.connect(self._on_auto_detect_toggled)
        layout_auto.addWidget(self.chk_auto_detect)

        self.lbl_auto_status = QLabel("Detección automática desactivada", self)
        self.lbl_auto_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout_auto.addWidget(self.lbl_auto_status)

        main_layout.addWidget(card_auto)

        # 6. Bottom Shortcut Info Bar
        info_box = QHBoxLayout()
        lbl_shortcut = QLabel("💡 Atajo rápido: <b>linuxraider toggle</b>", self)
        lbl_shortcut.setStyleSheet("color: #64748b; font-size: 12px;")
        info_box.addWidget(lbl_shortcut)
        info_box.addStretch()

        btn_reset = QPushButton("Restablecer", self)
        btn_reset.setObjectName("secondaryBtn")
        btn_reset.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_reset.clicked.connect(self.reset_to_normal)
        info_box.addWidget(btn_reset)

        main_layout.addLayout(info_box)

    def _create_slider_row(self, parent_layout, label, min_val, max_val, initial, scale=1.0, unit=""):
        header_row = QHBoxLayout()
        lbl = QLabel(label, self)
        lbl.setObjectName("sliderLabel")
        val_lbl = QLabel(f"{initial * scale:.2f}{unit}" if scale != 1.0 else f"{initial}{unit}", self)
        val_lbl.setObjectName("sliderValue")
        val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_row.addWidget(lbl)
        header_row.addWidget(val_lbl)
        parent_layout.addLayout(header_row)

        slider = QSlider(Qt.Orientation.Horizontal, self)
        slider.setRange(min_val, max_val)
        slider.setValue(initial)
        slider.setCursor(Qt.CursorShape.PointingHandCursor)

        def on_change(val):
            formatted = f"{val * scale:.2f}{unit}" if scale != 1.0 else f"{val}{unit}"
            val_lbl.setText(formatted)
            # Auto-activate when moving sliders so the user immediately sees the effect!
            if not self.is_active:
                self.is_active = True
                self._update_button_style()
            self.update_timer.start()

        slider.valueChanged.connect(on_change)
        parent_layout.addWidget(slider)

        return slider, val_lbl

    def _init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("LinuxRaider")
        icon_path = _get_icon_path()
        if os.path.exists(icon_path):
            icon = QIcon(icon_path)
            self.tray.setIcon(icon)
            self.setWindowIcon(icon)

        tray_menu = QMenu()
        act_toggle = tray_menu.addAction("Alternar Modo Juego")
        act_toggle.triggered.connect(self.toggle_mode)

        act_show = tray_menu.addAction("Abrir LinuxRaider")
        act_show.triggered.connect(self.show_window)

        tray_menu.addSeparator()
        act_quit = tray_menu.addAction("Salir")
        act_quit.triggered.connect(QApplication.instance().quit)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_click)
        self.tray.show()

    def _on_tray_click(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        event.ignore()
        self.hide()
        self.tray.showMessage(
            "LinuxRaider",
            "La app sigue activa en la bandeja junto al reloj.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    def _populate_profiles(self):
        self.combo_profiles.blockSignals(True)
        self.combo_profiles.clear()
        profiles = self.profile_mgr.list_profiles()
        for p in profiles:
            self.combo_profiles.addItem(p.get("description") or p["name"], userData=p["name"])

        idx = self.combo_profiles.findData("night_vision")
        if idx >= 0:
            self.combo_profiles.setCurrentIndex(idx)
        self.combo_profiles.blockSignals(False)

    def _load_profile_to_sliders(self, prof_name: str, activate: bool = True):
        p = self.profile_mgr.get_profile(prof_name)
        if not p:
            return
        brightness = round(p.get("brightness", 1.0) * 100)
        shadow_boost = round(p.get("shadow_boost", 0.5) * 100)
        gamma = round(p.get("gamma", 1.0) * 100)
        contrast = round(p.get("contrast", 1.0) * 100)

        sliders = (self.slider_bright, self.slider_boost, self.slider_gamma, self.slider_contrast)
        if not activate:
            for s in sliders:
                s.blockSignals(True)
        self.slider_bright.setValue(brightness)
        self.val_bright.setText(f"{brightness * 0.01:.2f}x")
        self.slider_boost.setValue(shadow_boost)
        self.val_boost.setText(f"{shadow_boost}%")
        self.slider_gamma.setValue(gamma)
        self.val_gamma.setText(f"{gamma * 0.01:.2f}x")
        self.slider_contrast.setValue(contrast)
        self.val_contrast.setText(f"{contrast * 0.01:.2f}x")
        if not activate:
            for s in sliders:
                s.blockSignals(False)
        elif self.is_active:
            self._apply_current_settings()

    def _on_profile_selected(self, index):
        prof_name = self.combo_profiles.itemData(index)
        if not prof_name:
            return
        self._load_profile_to_sliders(prof_name, activate=True)

    def _save_custom_profile(self):
        name, ok = QInputDialog.getText(
            self, "Guardar Perfil", "Introduce el nombre del nuevo perfil (ej. arc_noche):"
        )
        if ok and name.strip():
            clean_name = name.strip().lower().replace(" ", "_")
            self.profile_mgr.save_profile(
                name=clean_name,
                brightness=self.slider_bright.value() / 100.0,
                shadow_boost=self.slider_boost.value() / 100.0,
                gamma=self.slider_gamma.value() / 100.0,
                contrast=self.slider_contrast.value() / 100.0,
                description=name.strip(),
            )
            self._populate_profiles()
            idx = self.combo_profiles.findData(clean_name)
            if idx >= 0:
                self.combo_profiles.setCurrentIndex(idx)

    def _refresh_status(self):
        status = self.display_mgr.get_output_status()
        self.is_active = status["is_icc_active"]
        self._update_button_style()

    def _update_button_style(self):
        if self.is_active:
            self.btn_toggle.setText("✓ MODO JUEGO ACTIVADO")
            self.btn_toggle.setObjectName("mainToggleActive")
        else:
            self.btn_toggle.setText("ACTIVAR MODO JUEGO")
            self.btn_toggle.setObjectName("mainToggleInactive")
        self.btn_toggle.setStyle(self.btn_toggle.style())

    def toggle_mode(self):
        if self.is_active:
            self._disable_display_icc()
        else:
            self.is_active = True
            self._apply_current_settings()
            self._update_button_style()

    def _disable_display_icc(self):
        """Restores display to standard neutral sRGB while keeping current profile and sliders intact."""
        self.update_timer.stop()

        # Hardware/Compositor reset: apply neutral linear profile, then switch to sRGB
        try:
            neutral_profile = {
                "name": "neutral",
                "shadow_boost": 0.0,
                "gamma": 1.0,
                "contrast": 1.0,
                "brightness": 1.0,
            }
            icc_path = self.profile_mgr.compile_profile_to_icc(
                neutral_profile, custom_filename="neutral_reset"
            )
            self.display_mgr.apply_icc_profile(icc_path, self.current_output)
        except Exception:
            pass

        self.display_mgr.reset_to_srgb(self.current_output)
        self.is_active = False
        self._update_button_style()

    def _apply_current_settings(self):
        if not self.is_active:
            return

        profile_data = {
            "name": "live_settings",
            "description": "Ajuste en vivo",
            "brightness": self.slider_bright.value() / 100.0,
            "shadow_boost": self.slider_boost.value() / 100.0,
            "gamma": self.slider_gamma.value() / 100.0,
            "contrast": self.slider_contrast.value() / 100.0,
        }

        # Alternate between live_a and live_b to guarantee KWin reloads the ICC profile path!
        self._ping_pong = 1 - self._ping_pong
        target_filename = f"live_mode_{self._ping_pong}"

        icc_path = self.profile_mgr.compile_profile_to_icc(profile_data, custom_filename=target_filename)
        self.display_mgr.apply_icc_profile(icc_path, self.current_output)
        self._update_button_style()

    def reset_to_normal(self):
        """Completely restores display to standard neutral sRGB and resets all sliders."""
        # 1. Stop any pending update timer
        self.update_timer.stop()

        # 2. Reset sliders to neutral without triggering valueChanged events
        self.slider_bright.blockSignals(True)
        self.slider_boost.blockSignals(True)
        self.slider_gamma.blockSignals(True)
        self.slider_contrast.blockSignals(True)

        self.slider_bright.setValue(100)
        self.val_bright.setText("1.00x")

        self.slider_boost.setValue(0)
        self.val_boost.setText("0%")

        self.slider_gamma.setValue(100)
        self.val_gamma.setText("1.00x")

        self.slider_contrast.setValue(100)
        self.val_contrast.setText("1.00x")

        self.slider_bright.blockSignals(False)
        self.slider_boost.blockSignals(False)
        self.slider_gamma.blockSignals(False)
        self.slider_contrast.blockSignals(False)

        # 3. Select neutral in profile selector
        self.combo_profiles.blockSignals(True)
        idx = self.combo_profiles.findData("neutral")
        if idx >= 0:
            self.combo_profiles.setCurrentIndex(idx)
        self.combo_profiles.blockSignals(False)

        # 4. Hardware/Compositor reset: apply neutral linear profile, then switch to sRGB
        self._disable_display_icc()

    def _save_auto_settings(self):
        self.settings["auto_detect_enabled"] = self.chk_auto_detect.isChecked()
        self.settings.pop("auto_detect_patterns", None)
        self.profile_mgr.save_settings(self.settings)

    def _on_auto_detect_toggled(self, _checked: bool):
        self._save_auto_settings()
        self._sync_auto_detect_state()

    def _sync_auto_detect_state(self):
        if self.chk_auto_detect.isChecked():
            started = self.window_watcher.start()
            if started:
                self.lbl_auto_status.setText("Escuchando foco de ventana en KWin...")
                self.lbl_auto_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
            else:
                self.lbl_auto_status.setText("⚠ No se pudo iniciar la detección en KWin (Wayland)")
                self.lbl_auto_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
        else:
            self._unfocus_timer.stop()
            self.window_watcher.stop()
            self.lbl_auto_status.setText("Detección automática desactivada (modo manual)")
            self.lbl_auto_status.setStyleSheet("color: #64748b; font-size: 12px;")

    def _is_game_focused(self, focus_info) -> bool:
        return is_game_window(*focus_info)

    def _on_active_window_changed(
        self, caption: str, resource_class: str, resource_name: str, desktop_file: str
    ):
        self._last_focus_info = (caption, resource_class, resource_name, desktop_file)
        if not self.chk_auto_detect.isChecked():
            return

        focus_raw = caption or resource_class or resource_name or "Ninguna"
        focus_label = focus_raw if len(focus_raw) <= 38 else focus_raw[:35] + "..."

        if self._is_game_focused(self._last_focus_info):
            self._unfocus_timer.stop()
            self.lbl_auto_status.setText(f"✓ Juego en foco: {focus_label}")
            self.lbl_auto_status.setStyleSheet("color: #00f2fe; font-size: 12px;")
            if not self.is_active:
                self.is_active = True
                self._apply_current_settings()
                self._update_button_style()
        else:
            self.lbl_auto_status.setText(f"En espera (foco: {focus_label})")
            self.lbl_auto_status.setStyleSheet("color: #94a3b8; font-size: 12px;")
            if self.is_active:
                self._unfocus_timer.start()

    def _apply_unfocus_deactivation(self):
        if (
            self.chk_auto_detect.isChecked()
            and self.is_active
            and not self._is_game_focused(self._last_focus_info)
        ):
            self._disable_display_icc()

    def cleanup(self):
        """Release KWin scripting watcher cleanly on application exit."""
        self._unfocus_timer.stop()
        self.window_watcher.stop()


def run_gui():
    app = QApplication(sys.argv)
    app.setApplicationName("LinuxRaider")
    app.setApplicationDisplayName("LinuxRaider")
    app.setDesktopFileName("linuxraider")
    icon_path = _get_icon_path()
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    app.setStyleSheet(DARK_STYLESHEET)
    window = LinuxRaiderApp()
    window.show()
    sys.exit(app.exec())
