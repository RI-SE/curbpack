"""Report assembly.

Review calls this module when the user compiles a report. Each name is the
existing function in ``review.compile``. This module does not compile a second way.
"""

from review.compile import compile_report, write_report

__all__ = ["compile_report", "write_report"]
