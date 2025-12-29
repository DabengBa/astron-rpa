from __future__ import annotations

from typing import Any

MANIFEST_SCHEMA_V1: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AstronRPA Standalone Manifest",
    "type": "object",
    "additionalProperties": True,
    "required": ["schemaVersion", "appId", "buildId", "createdAt", "python", "entrypoint", "paths", "astronverse", "pythonPackages"],
    "properties": {
        "schemaVersion": {"type": "string"},
        "appId": {"type": "string", "minLength": 1},
        "buildId": {"type": "string", "minLength": 1},
        "createdAt": {"type": "string", "minLength": 1},
        "python": {
            "type": "object",
            "required": ["version", "distribution", "arch"],
            "properties": {
                "version": {"type": "string", "minLength": 1},
                "distribution": {"type": "string", "minLength": 1},
                "arch": {"type": "string", "minLength": 1},
            },
        },
        "entrypoint": {
            "type": "object",
            "required": ["module", "path"],
            "properties": {
                "module": {"type": "string", "minLength": 1},
                "path": {"type": "string", "minLength": 1},
            },
        },
        "paths": {
            "type": "object",
            "required": ["runtimeDir", "packagesDir", "scriptsDir", "resourcesDir"],
            "properties": {
                "runtimeDir": {"type": "string", "minLength": 1},
                "packagesDir": {"type": "string", "minLength": 1},
                "scriptsDir": {"type": "string", "minLength": 1},
                "resourcesDir": {"type": "string", "minLength": 1},
            },
        },
        "astronverse": {
            "type": "object",
            "required": ["baselineVersion", "includedComponents", "excludedComponents"],
            "properties": {
                "baselineVersion": {"type": "string", "minLength": 1},
                "includedComponents": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "excludedComponents": {"type": "array", "items": {"type": "string"}},
            },
        },
        "pythonPackages": {
            "type": "object",
            "required": ["locked", "requirements", "wheelFiles"],
            "properties": {
                "locked": {"type": "boolean"},
                "requirements": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                "wheelFiles": {"type": "array", "items": {"type": "string"}},
            },
        },
        "blockedImports": {"type": "array", "items": {"type": "string"}},
        "nativeArtifacts": {"type": "object"},
        "runtimeOptions": {"type": "object"},
    },
}

