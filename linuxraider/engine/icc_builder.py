"""LittleCMS (liblcms2) wrapper for compiling Tone Reproduction Curves into ICC profiles."""

import ctypes
import ctypes.util
import os
from typing import List


class cmsCIExyY(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_double),
        ("y", ctypes.c_double),
        ("Y", ctypes.c_double),
    ]


class cmsCIExyYTRIPLE(ctypes.Structure):
    _fields_ = [
        ("Red", cmsCIExyY),
        ("Green", cmsCIExyY),
        ("Blue", cmsCIExyY),
    ]


class ICCBuilder:
    """Builds standard display ICC profiles with custom tone curves."""

    def __init__(self):
        lib_name = ctypes.util.find_library("lcms2") or "liblcms2.so.2"
        try:
            self.lcms = ctypes.CDLL(lib_name)
        except OSError as e:
            raise RuntimeError(
                f"No se pudo cargar la biblioteca LittleCMS ({lib_name}): {e}"
            )

        # Set up prototypes
        self.lcms.cmsBuildTabulatedToneCurveFloat.restype = ctypes.c_void_p
        self.lcms.cmsBuildTabulatedToneCurveFloat.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_float),
        ]

        self.lcms.cmsCreateRGBProfile.restype = ctypes.c_void_p
        self.lcms.cmsCreateRGBProfile.argtypes = [
            ctypes.POINTER(cmsCIExyY),
            ctypes.POINTER(cmsCIExyYTRIPLE),
            ctypes.POINTER(ctypes.c_void_p),
        ]

        self.lcms.cmsSaveProfileToFile.restype = ctypes.c_int
        self.lcms.cmsSaveProfileToFile.argtypes = [ctypes.c_void_p, ctypes.c_char_p]

        self.lcms.cmsCloseProfile.argtypes = [ctypes.c_void_p]
        self.lcms.cmsFreeToneCurve.argtypes = [ctypes.c_void_p]

    def create_display_profile(
        self,
        curve_values: List[float],
        output_filepath: str,
        profile_desc: str = "LinuxRaider Profile",
    ) -> bool:
        """Compiles a curve into a standard ICC display profile.

        Args:
            curve_values: List of float values in [0.0, 1.0].
            output_filepath: Target .icc file path.
            profile_desc: Profile description text.

        Returns:
            True if successfully saved, False otherwise.
        """
        n = len(curve_values)
        float_array = (ctypes.c_float * n)(*curve_values)

        # 1. Build tabulated tone curve
        curve = self.lcms.cmsBuildTabulatedToneCurveFloat(None, n, float_array)
        if not curve:
            raise RuntimeError("Error al generar la curva de tono en LittleCMS")

        # Assign same curve to Red, Green, Blue channels
        curves = (ctypes.c_void_p * 3)(curve, curve, curve)

        # 2. Standard D65 White Point
        white_point = cmsCIExyY(0.3127, 0.3290, 1.0)

        # 3. Standard sRGB primaries (Rec.709)
        primaries = cmsCIExyYTRIPLE(
            cmsCIExyY(0.6400, 0.3300, 1.0),
            cmsCIExyY(0.3000, 0.6000, 1.0),
            cmsCIExyY(0.1500, 0.0600, 1.0),
        )

        # 4. Create the RGB ICC profile
        profile = self.lcms.cmsCreateRGBProfile(
            ctypes.byref(white_point), ctypes.byref(primaries), curves
        )

        if not profile:
            self.lcms.cmsFreeToneCurve(curve)
            raise RuntimeError("Error al crear la estructura del perfil ICC")

        # Ensure target directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_filepath)), exist_ok=True)

        # 5. Save to disk
        res = self.lcms.cmsSaveProfileToFile(
            profile, output_filepath.encode("utf-8")
        )

        # Cleanup LittleCMS handles
        self.lcms.cmsCloseProfile(profile)
        self.lcms.cmsFreeToneCurve(curve)

        return res == 1
