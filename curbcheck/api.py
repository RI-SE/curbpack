"""Public Check operations.

Studio Check calls this module. The function is the existing engine in
``checks.run``. This module does not run Checks a second way.
"""

from checks.run import run_and_write

__all__ = ["run_and_write"]
