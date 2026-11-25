#!/usr/bin/env python3
"""LinuxRaider entry point.

- If launched without arguments (or with --gui): Launches the graphical user interface.
- If launched with CLI subcommands (e.g. toggle, apply, status): Executes CLI action.
"""

import sys

def main():
    # If no arguments or explicitly requesting GUI, start the graphical application
    if len(sys.argv) == 1 or (len(sys.argv) == 2 and sys.argv[1] in ["--gui", "-g"]):
        from linuxraider.ui.main_window import run_gui
        run_gui()
    else:
        from linuxraider.cli import main as cli_main
        cli_main()

if __name__ == "__main__":
    main()
