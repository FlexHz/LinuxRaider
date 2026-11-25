"""Display Manager interface with KDE Plasma 6 Wayland via kscreen-doctor."""

import json
import os
import re
import shutil
import subprocess
from typing import Dict, List, Optional


class DisplayManager:
    """Controls outputs and color profiles through kscreen-doctor."""

    def __init__(self):
        self._check_dependency()

    def _check_dependency(self):
        if not shutil.which("kscreen-doctor"):
            raise RuntimeError(
                "kscreen-doctor no se encuentra instalado o no está en el PATH. "
                "Este componente es requerido para KDE Plasma 6 Wayland."
            )

    def get_outputs(self) -> List[Dict]:
        """Returns a list of connected and active outputs."""
        result = subprocess.run(
            ["kscreen-doctor", "-j"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        data = json.loads(result.stdout)
        active_outputs = []
        for out in data.get("outputs", []):
            if out.get("connected") and out.get("enabled"):
                active_outputs.append({
                    "id": out.get("id"),
                    "name": out.get("name"),
                    "priority": out.get("priority", 99),
                    "icc_path": out.get("iccProfilePath", ""),
                })
        # Sort by priority (1 is primary)
        active_outputs.sort(key=lambda x: x["priority"])
        return active_outputs

    def get_primary_output_name(self) -> str:
        """Returns the name of the primary/active display (e.g. 'DP-1')."""
        outputs = self.get_outputs()
        if not outputs:
            raise RuntimeError("No se detectaron salidas de pantalla activas.")
        return outputs[0]["name"]

    def get_output_status(self, output_name: Optional[str] = None) -> Dict:
        """Queries the current color source and active ICC profile for an output."""
        target_name = output_name or self.get_primary_output_name()
        res = subprocess.run(
            ["kscreen-doctor", "-o"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        
        # Strip any ANSI escape sequences from output
        clean_stdout = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", res.stdout)
        
        source = "sRGB"
        icc_path = ""
        
        # Regex search for current color profile source
        m_src = re.search(r"Color profile source:\s*([^\n\r]+)", clean_stdout)
        if m_src:
            source = m_src.group(1).strip()
            
        m_icc = re.search(r"ICC profile:\s*([^\n\r]+)", clean_stdout)
        if m_icc:
            icc_path = m_icc.group(1).strip()
            if icc_path == "none":
                icc_path = ""

        return {
            "output": target_name,
            "source": source,
            "is_icc_active": source.upper() == "ICC",
            "icc_path": icc_path,
        }

    def apply_icc_profile(self, icc_filepath: str, output_name: Optional[str] = None) -> bool:
        """Applies an ICC profile file to the specified or primary display output."""
        abs_path = os.path.abspath(icc_filepath)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"El archivo ICC '{abs_path}' no existe.")

        target = output_name or self.get_primary_output_name()

        # kscreen-doctor output.<name>.iccprofile.<path> output.<name>.colorProfileSource.ICC
        cmd = [
            "kscreen-doctor",
            f"output.{target}.iccprofile.{abs_path}",
            f"output.{target}.colorProfileSource.ICC",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error al aplicar perfil en kscreen-doctor: {res.stderr}")
        return True

    def reset_to_srgb(self, output_name: Optional[str] = None) -> bool:
        """Reverts the display to standard SDR sRGB color source."""
        target = output_name or self.get_primary_output_name()
        cmd = [
            "kscreen-doctor",
            f"output.{target}.colorProfileSource.sRGB",
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error al restablecer a sRGB: {res.stderr}")
        return True
