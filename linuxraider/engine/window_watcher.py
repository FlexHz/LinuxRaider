"""Automatic active-window focus detection for KDE Plasma 6 Wayland via KWin Scripting."""

import os
import tempfile
from typing import List, Optional

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot
from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage

DEFAULT_GAME_PATTERNS = "ARC Raiders, steam_app_1808500, PioneerGame"


def parse_patterns(patterns_text: str) -> List[str]:
    """Parse a comma-separated pattern string into normalized lowercase tokens."""
    return [token.strip().lower() for token in patterns_text.split(",") if token.strip()]


def window_matches_patterns(
    caption: str,
    resource_class: str,
    resource_name: str,
    desktop_file: str,
    patterns: List[str],
) -> bool:
    """Return True if any pattern matches one of the active window's identifiers."""
    if not patterns:
        return False
    fields = [
        (caption or "").lower(),
        (resource_class or "").lower(),
        (resource_name or "").lower(),
        (desktop_file or "").lower(),
    ]
    return any(pattern in field for pattern in patterns for field in fields if field)


class KWinWindowWatcher(QObject):
    """Watches active window focus changes in KDE Plasma 6 KWin via D-Bus scripting."""

    windowChanged = pyqtSignal(str, str, str, str)

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        pid = os.getpid()
        self._service_name = f"org.linuxraider.WindowWatcher.p{pid}"
        self._object_path = "/Watcher"
        self._plugin_name = f"linuxraider_watcher_{pid}"
        self._script_path: Optional[str] = None
        self._running = False
        self._bus = QDBusConnection.sessionBus()

    @property
    def is_running(self) -> bool:
        return self._running

    @pyqtSlot(str, str, str, str)
    def onWindowChanged(
        self, caption: str, resource_class: str, resource_name: str, desktop_file: str
    ):
        """D-Bus slot invoked by KWin script when active window or its title changes."""
        self.windowChanged.emit(caption, resource_class, resource_name, desktop_file)

    def _build_kwin_script(self) -> str:
        return f"""
var trackedWin = null;
function report(win) {{
    if (!win) {{
        callDBus("{self._service_name}", "{self._object_path}", "", "onWindowChanged", "", "", "", "");
        return;
    }}
    callDBus(
        "{self._service_name}",
        "{self._object_path}",
        "",
        "onWindowChanged",
        String(win.caption || ""),
        String(win.resourceClass || ""),
        String(win.resourceName || ""),
        String(win.desktopFileName || "")
    );
}}
function onCaptionChanged() {{
    report(workspace.activeWindow);
}}
function onWindowActivated(win) {{
    if (trackedWin) {{
        try {{ trackedWin.captionChanged.disconnect(onCaptionChanged); }} catch (e) {{}}
        trackedWin = null;
    }}
    if (win) {{
        trackedWin = win;
        try {{ trackedWin.captionChanged.connect(onCaptionChanged); }} catch (e) {{}}
    }}
    report(win);
}}
workspace.windowActivated.connect(onWindowActivated);
onWindowActivated(workspace.activeWindow);
""".lstrip()

    def start(self) -> bool:
        """Register D-Bus receiver and load the KWin scripting watcher."""
        if self._running:
            return True

        if not self._bus.isConnected():
            return False

        if not self._bus.registerService(self._service_name):
            return False

        if not self._bus.registerObject(
            self._object_path, self, QDBusConnection.RegisterOption.ExportAllSlots
        ):
            self._bus.unregisterService(self._service_name)
            return False

        try:
            fd, script_path = tempfile.mkstemp(suffix=".js", prefix="linuxraider_kwin_")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(self._build_kwin_script())
            self._script_path = script_path

            scripting = QDBusInterface(
                "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", self._bus
            )
            if not scripting.isValid():
                self.stop()
                return False

            scripting.call("unloadScript", self._plugin_name)
            reply = scripting.call("loadScript", script_path, self._plugin_name)
            if reply.type() == QDBusMessage.MessageType.ErrorMessage or not reply.arguments():
                self.stop()
                return False

            script_id = reply.arguments()[0]
            if not isinstance(script_id, int) or script_id < 0:
                self.stop()
                return False

            script_obj = QDBusInterface(
                "org.kde.KWin",
                f"/Scripting/Script{script_id}",
                "org.kde.kwin.Script",
                self._bus,
            )
            run_reply = script_obj.call("run")
            if run_reply.type() == QDBusMessage.MessageType.ErrorMessage:
                self.stop()
                return False

            self._running = True
            return True
        except Exception:
            self.stop()
            return False

    def stop(self):
        """Unload the KWin script and unregister D-Bus resources."""
        try:
            scripting = QDBusInterface(
                "org.kde.KWin", "/Scripting", "org.kde.kwin.Scripting", self._bus
            )
            if scripting.isValid():
                scripting.call("unloadScript", self._plugin_name)
        except Exception:
            pass

        self._running = False

        try:
            self._bus.unregisterObject(self._object_path)
            self._bus.unregisterService(self._service_name)
        except Exception:
            pass

        if self._script_path and os.path.exists(self._script_path):
            try:
                os.remove(self._script_path)
            except OSError:
                pass
        self._script_path = None
