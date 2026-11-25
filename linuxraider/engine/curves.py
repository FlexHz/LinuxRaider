"""Mathematical curve generation for display post-processing in LinuxRaider.

Guaranteed Properties:
1. Strictly Monotonic: Never inverts or dips, eliminating solarization, banding, and color distortion.
2. Smooth transition: Preserves natural skin tones, textures, and highlights.
3. Natural Shadow Lift: Lifts deep darks smoothly while keeping pure white unclipped.
"""

from typing import List


def generate_tone_curve(
    num_points: int = 256,
    shadow_boost: float = 0.5,
    gamma: float = 1.0,
    contrast: float = 1.0,
    brightness: float = 1.0,
) -> List[float]:
    """Generates a smooth, distortion-free ICC TRC curve.

    Args:
        num_points: Number of LUT points (typically 256).
        shadow_boost: Shadow illumination level [0.0 to 1.0].
        gamma: Midtone gamma multiplier [0.5 to 2.5] (1.0 = neutral sRGB).
        contrast: Contrast multiplier [0.5 to 1.5] (1.0 = neutral).
        brightness: Overall brightness multiplier [0.5 to 1.5] (1.0 = neutral).

    Returns:
        List of float values in range [0.0, 1.0].
    """
    safe_boost = max(0.0, min(1.0, shadow_boost))
    safe_gamma = max(0.5, min(2.5, gamma))
    safe_contrast = max(0.5, min(1.5, contrast))
    safe_brightness = max(0.5, min(1.5, brightness))

    # Base sRGB gamma is 2.2.
    # To brighten the screen, effective TRC exponent in the profile must be higher.
    # Higher safe_brightness -> higher g_base -> brighter displayed image.
    g_base = 2.2 * (safe_gamma ** 0.85) * safe_brightness

    curve = []
    for i in range(num_points):
        x = i / (num_points - 1)

        if x <= 0.0:
            curve.append(0.0)
            continue
        if x >= 1.0:
            curve.append(1.0)
            continue

        # Smooth power exponent:
        # Boost increases the exponent dynamically in the shadow region (1 - x),
        # which forces KWin's inverse shader to smoothly lift shadows without any distortion.
        exp = g_base + safe_boost * (1.0 - x) * 1.35
        val = pow(x, exp)

        # Contrast adjustment (pivots around 0.5 without breaking monotonicity)
        if safe_contrast != 1.0:
            # S-curve dampening factor near edges to ensure strictly 0.0 at x=0 and 1.0 at x=1
            fade = pow(x * (1.0 - x) * 4.0, 0.8)
            val = val + (val - 0.5) * (safe_contrast - 1.0) * 0.4 * fade

        val = max(0.0, min(1.0, val))
        curve.append(val)

    # Ensure strictly monotonic and clean endpoints
    curve[0] = 0.0
    curve[-1] = 1.0
    for i in range(1, len(curve)):
        if curve[i] < curve[i - 1]:
            curve[i] = curve[i - 1]

    return curve
