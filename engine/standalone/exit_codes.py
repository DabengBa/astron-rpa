from __future__ import annotations

from enum import IntEnum


class ExitCode(IntEnum):
    OK = 0

    MANIFEST_MISSING = 10
    MANIFEST_INVALID = 11

    BLOCKED_IMPORT = 20
    SCRIPT_ERROR = 30

    INTERNAL_ERROR = 90

