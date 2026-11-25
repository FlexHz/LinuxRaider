"""Command Line Interface for LinuxRaider."""

import argparse
import sys
import time
from .core.profiles import ProfileManager
from .engine.display_manager import DisplayManager


def cmd_status(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Shows the current status of the display."""
    status = display_mgr.get_output_status(args.output)
    print("=" * 45)
    print("           ESTADO DE LINUXRAIDER")
    print("=" * 45)
    print(f" Salida activa:       {status['output']}")
    print(f" Modo de color:       {status['source']}")
    print(f" Perfil activo:       {'SÍ (ICC)' if status['is_icc_active'] else 'NO (sRGB estándar)'}")
    if status["icc_path"]:
        print(f" Archivo ICC:         {status['icc_path']}")
    print("=" * 45)


def cmd_list(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Lists available profiles."""
    profiles = profile_mgr.list_profiles()
    print("=" * 65)
    print(" PERFILES DISPONIBLES EN LINUXRAIDER")
    print("=" * 65)
    for p in profiles:
        print(f" • {p['name']:<15} | Boost: {p.get('shadow_boost', 0):<4} | Gamma: {p.get('gamma', 1.0):<4} | Contraste: {p.get('contrast', 1.0):<4}")
        if p.get("description"):
            print(f"   └─ {p['description']}")
    print("=" * 65)


def cmd_apply(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Applies a profile by name."""
    profile_data = profile_mgr.get_profile(args.name)
    if not profile_data:
        print(f"Error: Perfil '{args.name}' no encontrado. Usa 'linuxraider list' para ver perfiles disponibles.")
        sys.exit(1)

    print(f"Compilando y aplicando perfil '{args.name}'...")
    icc_path = profile_mgr.compile_profile_to_icc(profile_data)
    display_mgr.apply_icc_profile(icc_path, args.output)
    print(f"✓ Perfil '{args.name}' aplicado con éxito en {args.output or display_mgr.get_primary_output_name()}.")


def cmd_reset(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Resets display to default sRGB."""
    display_mgr.reset_to_srgb(args.output)
    print(f"✓ Pantalla restablecida a sRGB estándar.")


def cmd_toggle(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Toggles between a profile and default sRGB (ideal for shortcuts)."""
    status = display_mgr.get_output_status(args.output)
    target_profile = args.name or "night_vision"

    if status["is_icc_active"]:
        # Revert to standard
        display_mgr.reset_to_srgb(args.output)
        print("✓ Modo normal (sRGB) activado.")
    else:
        # Activate profile
        profile_data = profile_mgr.get_profile(target_profile)
        if not profile_data:
            print(f"Error: Perfil '{target_profile}' no encontrado.")
            sys.exit(1)
        icc_path = profile_mgr.compile_profile_to_icc(profile_data)
        display_mgr.apply_icc_profile(icc_path, args.output)
        print(f"✓ Perfil '{target_profile}' activado.")


def cmd_test(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Temporarily applies a profile for N seconds, then reverts."""
    target_profile = args.name or "night_vision"
    duration = max(1, args.duration)

    profile_data = profile_mgr.get_profile(target_profile)
    if not profile_data:
        print(f"Error: Perfil '{target_profile}' no encontrado.")
        sys.exit(1)

    print(f"Aplicando perfil de prueba '{target_profile}' durante {duration} segundos...")
    icc_path = profile_mgr.compile_profile_to_icc(profile_data)
    display_mgr.apply_icc_profile(icc_path, args.output)

    try:
        for i in range(duration, 0, -1):
            print(f"  Volviendo a la normalidad en {i}s... (Ctrl+C para cancelar antes)", end="\r", flush=True)
            time.sleep(1)
    finally:
        display_mgr.reset_to_srgb(args.output)
        print("\n✓ Prueba finalizada. Pantalla restaurada a sRGB.")


def cmd_quick(display_mgr: DisplayManager, profile_mgr: ProfileManager, args):
    """Applies custom settings on the fly."""
    profile_data = {
        "name": "quick_custom",
        "description": "Perfil rápido personalizado",
        "shadow_boost": args.boost,
        "gamma": args.gamma,
        "contrast": args.contrast,
    }
    icc_path = profile_mgr.compile_profile_to_icc(profile_data)
    display_mgr.apply_icc_profile(icc_path, args.output)
    print(f"✓ Ajustes aplicados: Boost={args.boost}, Gamma={args.gamma}, Contraste={args.contrast}")


def main():
    parser = argparse.ArgumentParser(
        prog="linuxraider",
        description="LinuxRaider - Control de visibilidad, gamma y sombras para juegos en Linux",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Salida de pantalla específica (ej. DP-1). Por defecto usa la pantalla principal.",
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # status
    p_status = subparsers.add_parser("status", help="Muestra el estado actual del monitor y perfil de color")
    p_status.set_defaults(func=cmd_status)

    # list
    p_list = subparsers.add_parser("list", help="Lista los perfiles configurados")
    p_list.set_defaults(func=cmd_list)

    # apply
    p_apply = subparsers.add_parser("apply", help="Aplica un perfil por su nombre")
    p_apply.add_argument("name", type=str, help="Nombre del perfil (ej. night_vision)")
    p_apply.set_defaults(func=cmd_apply)

    # reset
    p_reset = subparsers.add_parser("reset", help="Restablece la pantalla a color sRGB estándar")
    p_reset.set_defaults(func=cmd_reset)

    # toggle
    p_toggle = subparsers.add_parser("toggle", help="Alterna entre un perfil y el modo normal (ideal para shortcuts)")
    p_toggle.add_argument("name", nargs="?", default="night_vision", help="Nombre del perfil (por defecto: night_vision)")
    p_toggle.set_defaults(func=cmd_toggle)

    # test
    p_test = subparsers.add_parser("test", help="Aplica un perfil durante unos segundos de prueba y luego vuelve a la normalidad")
    p_test.add_argument("name", nargs="?", default="night_vision", help="Nombre del perfil (por defecto: night_vision)")
    p_test.add_argument("--duration", "-d", type=int, default=4, help="Duración en segundos (por defecto: 4)")
    p_test.set_defaults(func=cmd_test)

    # quick
    p_quick = subparsers.add_parser("quick", help="Aplica valores personalizados al vuelo")
    p_quick.add_argument("--boost", "-b", type=float, default=0.6, help="Shadow Boost [0.0 a 1.0]")
    p_quick.add_argument("--gamma", "-g", type=float, default=1.2, help="Gamma [0.5 a 2.5]")
    p_quick.add_argument("--contrast", "-c", type=float, default=1.0, help="Contraste [0.5 a 1.5]")
    p_quick.set_defaults(func=cmd_quick)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        display_mgr = DisplayManager()
        profile_mgr = ProfileManager()
        args.func(display_mgr, profile_mgr, args)
    except Exception as e:
        print(f"\n[Error] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
