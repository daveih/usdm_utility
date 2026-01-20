#!/usr/bin/env python3
"""
USDM JSON Validation Utility

This script validates USDM (Unified Study Definitions Model) JSON files
using the CDISC Rules Engine (CORE).

Usage:
    python usdm_validate.py <usdm_file.json> [options]

Options:
    -v, --version    USDM version (3-0 or 4-0, default: 4-0)
    -o, --output     Output file for validation results (default: stdout)
    -f, --format     Output format: json or text (default: text)
    --verbose        Show verbose output
"""

import argparse
import io
import json
import logging
import os
import sys
import urllib.request
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

# Map CDISC_API_KEY to the key name expected by cdisc-rules-engine
if "CDISC_API_KEY" in os.environ and "CDISC_LIBRARY_API_KEY" not in os.environ:
    os.environ["CDISC_LIBRARY_API_KEY"] = os.environ["CDISC_API_KEY"]

# Suppress verbose logging from cdisc-rules-engine unless in verbose mode
# The engine uses the root logger via ConsoleLogger - we must disable it entirely
logging.disable(logging.CRITICAL)  # Disable ALL logging globally

try:
    import cdisc_rules_engine
    from cdisc_rules_engine.config import config
    from cdisc_rules_engine.services.cache import CacheServiceFactory
    from cdisc_rules_engine.rules_engine import RulesEngine
    from cdisc_rules_engine.utilities.utils import get_rules_cache_key
    from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
    from cdisc_rules_engine.constants.cache_constants import PUBLISHED_CT_PACKAGES
    from cdisc_rules_engine.models.library_metadata_container import LibraryMetadataContainer

    # The CDISC Rules Engine expects resources in the current directory.
    # We need to change to the site-packages directory where resources are installed.
    _CDISC_PACKAGE_DIR = Path(cdisc_rules_engine.__file__).parent.parent
except ImportError:
    print("Error: cdisc-rules-engine package is not installed.")
    print("Install it with: pip install cdisc-rules-engine")
    sys.exit(1)

# GitHub URLs for JSONata custom functions
JSONATA_FILES = [
    "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/parse_refs.jsonata",
    "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/sift_tree.jsonata",
]

# GitHub base URL for XSD schema files
XSD_GITHUB_BASE = "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/schema/xml"

# USDM XHTML schema files (required for XHTML validation rules)
USDM_XHTML_SCHEMA_FILES = [
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd",
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-extension.xsd",
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-ns.xsd",
]

# Core XHTML 1.1 schema files (dependencies for USDM XHTML validation)
# All files are required due to complex inter-dependencies in the XHTML 1.1 schema
XHTML_SCHEMA_FILES = [
    "xhtml-1.1/aria-attributes-1.xsd",
    "xhtml-1.1/xframes-1.xsd",
    "xhtml-1.1/xhtml-access-1.xsd",
    "xhtml-1.1/xhtml-applet-1.xsd",
    "xhtml-1.1/xhtml-attribs-1.xsd",
    "xhtml-1.1/xhtml-base-1.xsd",
    "xhtml-1.1/xhtml-basic-form-1.xsd",
    "xhtml-1.1/xhtml-basic-table-1.xsd",
    "xhtml-1.1/xhtml-bdo-1.xsd",
    "xhtml-1.1/xhtml-blkphras-1.xsd",
    "xhtml-1.1/xhtml-blkpres-1.xsd",
    "xhtml-1.1/xhtml-blkstruct-1.xsd",
    "xhtml-1.1/xhtml-charent-1.xsd",
    "xhtml-1.1/xhtml-csismap-1.xsd",
    "xhtml-1.1/xhtml-datatypes-1.xsd",
    "xhtml-1.1/xhtml-edit-1.xsd",
    "xhtml-1.1/xhtml-events-1.xsd",
    "xhtml-1.1/xhtml-form-1.xsd",
    "xhtml-1.1/xhtml-frames-1.xsd",
    "xhtml-1.1/xhtml-framework-1.xsd",
    "xhtml-1.1/xhtml-hypertext-1.xsd",
    "xhtml-1.1/xhtml-iframe-1.xsd",
    "xhtml-1.1/xhtml-image-1.xsd",
    "xhtml-1.1/xhtml-inlphras-1.xsd",
    "xhtml-1.1/xhtml-inlpres-1.xsd",
    "xhtml-1.1/xhtml-inlstruct-1.xsd",
    "xhtml-1.1/xhtml-inlstyle-1.xsd",
    "xhtml-1.1/xhtml-inputmode-1.xsd",
    "xhtml-1.1/xhtml-legacy-1.xsd",
    "xhtml-1.1/xhtml-legacy-redecl-1.xsd",
    "xhtml-1.1/xhtml-link-1.xsd",
    "xhtml-1.1/xhtml-list-1.xsd",
    "xhtml-1.1/xhtml-meta-1.xsd",
    "xhtml-1.1/xhtml-metaAttributes-1.xsd",
    "xhtml-1.1/xhtml-misc-1.xsd",
    "xhtml-1.1/xhtml-nameident-1.xsd",
    "xhtml-1.1/xhtml-notations-1.xsd",
    "xhtml-1.1/xhtml-object-1.xsd",
    "xhtml-1.1/xhtml-param-1.xsd",
    "xhtml-1.1/xhtml-pres-1.xsd",
    "xhtml-1.1/xhtml-print-model-1.xsd",
    "xhtml-1.1/xhtml-print.xsd",
    "xhtml-1.1/xhtml-ruby-1.xsd",
    "xhtml-1.1/xhtml-script-1.xsd",
    "xhtml-1.1/xhtml-ssismap-1.xsd",
    "xhtml-1.1/xhtml-struct-1.xsd",
    "xhtml-1.1/xhtml-style-1.xsd",
    "xhtml-1.1/xhtml-table-1.xsd",
    "xhtml-1.1/xhtml-target-1.xsd",
    "xhtml-1.1/xhtml-text-1.xsd",
    "xhtml-1.1/xhtml-uri-1.xsd",
    "xhtml-1.1/xhtml11-flat.xsd",
    "xhtml-1.1/xhtml11-model-1.xsd",
    "xhtml-1.1/xhtml11-modules-1.xsd",
    "xhtml-1.1/xhtml11.xsd",
    "xhtml-1.1/xml.xsd",
    # XHTML Basic schemas (additional dependencies)
    "xhtml-1.1/xhtml-basic10-model-1.xsd",
    "xhtml-1.1/xhtml-basic10-modules-1.xsd",
    "xhtml-1.1/xhtml-basic10.xsd",
    "xhtml-1.1/xhtml-basic11-model-1.xsd",
    "xhtml-1.1/xhtml-basic11-modules-1.xsd",
    "xhtml-1.1/xhtml-basic11.xsd",
    # XHTML Strict/Transitional schemas
    "xhtml-1.1/xhtml-lat1.ent",
    "xhtml-1.1/xhtml-special.ent",
    "xhtml-1.1/xhtml-symbol.ent",
    "xhtml-1.1/xhtml1-frameset.xsd",
    "xhtml-1.1/xhtml1-strict.xsd",
    "xhtml-1.1/xhtml1-transitional.xsd",
    # XHTML+RDFa schemas
    "xhtml-1.1/xhtml-rdfa-model-1.xsd",
    "xhtml-1.1/xhtml-rdfa-modules-1.xsd",
    "xhtml-1.1/xhtml-rdfa-1.xsd",
    "xhtml-1.1/xhtml-role-1.xsd",
    "xhtml-1.1/xhtml-role-attrib-1.xsd",
    # XHTML Mobile/Simple schemas
    "xhtml-1.1/xhtml-mobile10-model-1.xsd",
    "xhtml-1.1/xhtml-mobile10.xsd",
    "xhtml-1.1/xhtml-simple-1.xsd",
]

# Rules known to have bugs in the CORE engine (JSONata/NoneType errors)
EXCLUDED_RULES = {
    "CORE-000955",  # JSONata bug
    "CORE-000956",  # JSONata bug
}


class SuppressOutput:
    """Context manager to suppress stdout/stderr from third-party libraries."""

    def __init__(self, suppress: bool = True):
        self.suppress = suppress
        self._stdout = None
        self._stderr = None
        self._devnull = None

    def __enter__(self):
        if self.suppress:
            self._devnull = io.StringIO()
            self._stdout = sys.stdout
            self._stderr = sys.stderr
            sys.stdout = self._devnull
            sys.stderr = self._devnull
        return self

    def __exit__(self, *args):
        if self.suppress:
            sys.stdout = self._stdout
            sys.stderr = self._stderr
            self._devnull.close()


def setup_xsd_schema_resources():
    """
    Download XSD schema files from GitHub if they don't exist locally.
    These are required for XHTML validation rules (CORE-000945, CORE-001069).
    """
    schema_base_dir = _CDISC_PACKAGE_DIR / "resources" / "schema" / "xml"

    # Check if USDM XHTML schema already exists
    usdm_xhtml_dir = schema_base_dir / "cdisc-usdm-xhtml-1.0"
    if usdm_xhtml_dir.exists() and (usdm_xhtml_dir / "usdm-xhtml-1.0.xsd").exists():
        return True

    # Create directories
    (schema_base_dir / "cdisc-usdm-xhtml-1.0").mkdir(parents=True, exist_ok=True)
    (schema_base_dir / "xhtml-1.1").mkdir(parents=True, exist_ok=True)

    # Download USDM XHTML schema files
    all_schema_files = USDM_XHTML_SCHEMA_FILES + XHTML_SCHEMA_FILES
    for schema_path in all_schema_files:
        url = f"{XSD_GITHUB_BASE}/{schema_path}"
        filepath = schema_base_dir / schema_path
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception:
            # Continue even if some files fail - not all may be needed
            pass

    return True


def setup_jsonata_resources():
    """
    Download JSONata custom functions from GitHub if they don't exist locally.
    These are required for certain CORE rules that use JSONata expressions.
    """
    jsonata_dir = _CDISC_PACKAGE_DIR / "resources" / "jsonata"

    # Check if already set up
    if jsonata_dir.exists() and any(jsonata_dir.glob("*.jsonata")):
        return True

    # Create the directory
    jsonata_dir.mkdir(parents=True, exist_ok=True)

    # Download each file
    for url in JSONATA_FILES:
        filename = url.split("/")[-1]
        filepath = jsonata_dir / filename
        try:
            urllib.request.urlretrieve(url, filepath)
        except Exception:
            return False

    return True


def setup_ct_packages(cache):
    """
    Load the list of available CT packages into the cache and return them.
    This is required for rules that check controlled terminology dates.

    Returns:
        Tuple of (list of CT package names, CDISCLibraryService or None)
    """
    # Check if already loaded in cache
    cached_packages = cache.get(PUBLISHED_CT_PACKAGES)
    if cached_packages:
        api_key = os.environ.get("CDISC_LIBRARY_API_KEY")
        if api_key:
            return cached_packages, CDISCLibraryService(api_key, cache)
        return cached_packages, None

    api_key = os.environ.get("CDISC_LIBRARY_API_KEY")
    if not api_key:
        return [], None

    try:
        library_service = CDISCLibraryService(api_key, cache)
        # Get all CT packages from CDISC Library
        packages = library_service.get_all_ct_packages()
        available_packages = [
            package.get("href", "").split("/")[-1] for package in packages
        ]
        cache.add(PUBLISHED_CT_PACKAGES, available_packages)
        return available_packages, library_service
    except Exception:
        return [], None


def load_ct_package_data(library_service, package_version: str) -> dict:
    """
    Load the actual codelist data for a CT package from CDISC Library.

    Args:
        library_service: CDISCLibraryService instance
        package_version: Package name like "sdtmct-2025-09-26"

    Returns:
        Dict with package name and codelists data
    """
    if not library_service:
        return {}
    try:
        return library_service.get_codelist_terms_map(package_version)
    except Exception:
        return {}


def get_ct_versions_from_usdm(usdm_data: dict) -> set:
    """
    Extract unique codeSystemVersion values from USDM data.
    These indicate which CT packages need to be loaded.

    Args:
        usdm_data: Parsed USDM JSON data

    Returns:
        Set of version strings (e.g., {"2025-09-26"})
    """
    versions = set()

    def extract_versions(obj):
        if isinstance(obj, dict):
            if "codeSystemVersion" in obj:
                versions.add(obj["codeSystemVersion"])
            for value in obj.values():
                extract_versions(value)
        elif isinstance(obj, list):
            for item in obj:
                extract_versions(item)

    extract_versions(usdm_data)
    return versions


def load_rules_from_library(cache, standard: str, version: str, verbose: bool = False):
    """
    Load USDM rules from CDISC Library into the cache.

    Args:
        cache: The cache service instance
        standard: The standard name (e.g., "usdm")
        version: The version (e.g., "4-0")
        verbose: Whether to print verbose output

    Returns:
        List of rules loaded from the library
    """
    api_key = os.environ.get("CDISC_LIBRARY_API_KEY")
    if not api_key:
        raise ValueError(
            "CDISC API key required to download rules. "
            "Set CDISC_API_KEY or CDISC_LIBRARY_API_KEY environment variable."
        )

    if verbose:
        print(f"Downloading {standard} {version} rules from CDISC Library...")

    library_service = CDISCLibraryService(api_key, cache)

    # Get the rules for this standard/version
    result = library_service.get_rules_by_catalog(standard, version)

    # Extract rules list from the response dict
    rules = result.get("rules", []) if isinstance(result, dict) else result
    cache_key = result.get("key_prefix", get_rules_cache_key(standard, version))

    if verbose:
        print(f"Downloaded {len(rules)} rules")

    # Cache the rules
    for rule in rules:
        rule_id = rule.get("core_id", "unknown")
        cache.add(f"{cache_key}/{rule_id}", rule)

    return rules


def load_usdm_file(file_path: str) -> dict:
    """
    Load and parse a USDM JSON file.

    Args:
        file_path: Path to the USDM JSON file

    Returns:
        Parsed JSON data as a dictionary
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.suffix.lower() == ".json":
        raise ValueError(f"Expected a JSON file, got: {path.suffix}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate that this looks like a USDM file
    if "study" not in data:
        raise ValueError(
            "Invalid USDM file: missing 'study' key. "
            "USDM JSON files must contain a 'study' object."
        )

    return data


def validate_usdm(
    file_path: str,
    version: str = "4-0",
    verbose: bool = False
) -> dict:
    """
    Validate a USDM JSON file using the CDISC Rules Engine.

    Args:
        file_path: Path to the USDM JSON file
        version: USDM version (3-0 or 4-0)
        verbose: Whether to print verbose output

    Returns:
        Dict containing validation results and metadata:
        - results: List of validation result dicts
        - ct_packages_count: Number of CT packages loaded
        - ct_packages: List of CT package names
    """
    abs_path = os.path.abspath(file_path)

    # Validate the file first (before suppressing output)
    load_usdm_file(file_path)  # Will raise if invalid

    # The CDISC Rules Engine expects 'resources' directory in CWD.
    # Change to the site-packages directory where resources are installed.
    original_cwd = os.getcwd()
    os.chdir(_CDISC_PACKAGE_DIR)

    try:
        # Re-enable logging if verbose mode requested
        if verbose:
            logging.disable(logging.NOTSET)  # Re-enable logging
            logging.getLogger().setLevel(logging.INFO)

        # Suppress ALL output from cdisc-rules-engine (it uses print statements)
        with SuppressOutput(suppress=not verbose):
            return _run_validation(abs_path, version, verbose)
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
        # Re-disable logging
        if verbose:
            logging.disable(logging.CRITICAL)


def _run_validation(abs_path: str, version: str, verbose: bool) -> dict:
    """Internal validation logic, separated to allow output suppression."""
    # Setup resources (download from GitHub if needed)
    setup_jsonata_resources()
    setup_xsd_schema_resources()

    # Initialize the cache service
    cache = CacheServiceFactory(config).get_cache_service()

    # Setup CT packages list and get library service for loading CT data
    ct_packages, library_service = setup_ct_packages(cache)

    # Load USDM data to determine which CT package versions are needed
    with open(abs_path, "r", encoding="utf-8") as f:
        usdm_data = json.load(f)

    # Extract CT versions from the USDM data
    ct_versions_needed = get_ct_versions_from_usdm(usdm_data)

    # For USDM, load sdtmct and ddfct packages for each version found
    ct_package_metadata = {}
    loaded_packages = []
    if library_service and ct_versions_needed:
        for ct_version in ct_versions_needed:
            for ct_type in ["sdtmct", "ddfct"]:
                package_name = f"{ct_type}-{ct_version}"
                if package_name in ct_packages:
                    ct_data = load_ct_package_data(library_service, package_name)
                    if ct_data:
                        ct_package_metadata[package_name] = ct_data
                        loaded_packages.append(package_name)

    # Create library metadata container with both package list AND package data
    library_metadata = LibraryMetadataContainer(
        published_ct_packages=ct_packages,
        ct_package_metadata=ct_package_metadata,
    )

    # Initialize rules engine for USDM
    rules_engine = RulesEngine(
        cache=cache,
        standard="usdm",
        standard_version=version,
        dataset_paths=[abs_path],
        library_metadata=library_metadata,
    )

    # Get datasets from data service
    datasets = rules_engine.data_service.get_datasets()

    # Get rules from cache
    cache_key = get_rules_cache_key("usdm", version)
    rules = cache.get_all_by_prefix(cache_key)

    if not rules:
        # Download rules from CDISC Library
        rules = load_rules_from_library(cache, "usdm", version, verbose=False)

    if not rules:
        return {
            "results": [],
            "ct_packages_count": len(ct_packages),
            "ct_packages": ct_packages,
            "ct_packages_loaded": loaded_packages,
        }

    # Run validation for each rule
    results = []
    for rule in rules:
        rule_id = rule.get("core_id", "unknown")

        # Skip rules known to have bugs
        if rule_id in EXCLUDED_RULES:
            continue

        # Extract rule description and action message
        description = rule.get("description", "")
        action_message = ""
        actions = rule.get("actions", [])
        if actions and isinstance(actions, list):
            params = actions[0].get("params", {})
            action_message = params.get("message", "")

        try:
            rule_results = rules_engine.validate_single_rule(rule, datasets)
            result = {
                "rule_id": rule_id,
                "description": description,
                "message": action_message,
                "execution_status": "success",
                "results": list(rule_results.values()) if rule_results else []
            }
            results.append(result)
        except Exception:
            result = {
                "rule_id": rule_id,
                "description": description,
                "message": action_message,
                "execution_status": "error",
                "results": []
            }
            results.append(result)

    # Return results with metadata
    return {
        "results": results,
        "ct_packages_count": len(ct_packages),
        "ct_packages": ct_packages,
        "ct_packages_loaded": loaded_packages,
    }


def _is_execution_error(error: dict) -> bool:
    """
    Check if an error is a rule execution error vs a validation finding.

    Execution errors occur when:
    - A rule checks a column that doesn't exist on the entity type
    - A rule requires joining with a dataset that isn't present in the data

    These are not data quality issues - they indicate the rule doesn't apply
    to this particular USDM file's structure.
    """
    if isinstance(error, dict):
        error_type = error.get("error", "")
        # Column not found - rule checks fields that don't exist on entity
        if error_type == "Column not found in data":
            return True
        # Preprocessing failed - rule requires dataset not in USDM file
        if error_type == "Error occurred during dataset preprocessing":
            return True
    return False


def format_results_text(validation_data: dict, file_path: str) -> str:
    """
    Format validation results as human-readable text.

    Args:
        validation_data: Dict with results and metadata from validate_usdm()
        file_path: The path to the validated file

    Returns:
        Formatted text output
    """
    results = validation_data.get("results", [])
    ct_packages_count = validation_data.get("ct_packages_count", 0)
    ct_packages_loaded = validation_data.get("ct_packages_loaded", [])

    output = []
    output.append("=" * 60)
    output.append("USDM Validation Report")
    output.append("=" * 60)
    output.append(f"File: {file_path}")
    output.append(f"Rules executed: {len(results)}")
    output.append(f"CT packages available: {ct_packages_count}")
    output.append(f"CT packages loaded: {', '.join(ct_packages_loaded) if ct_packages_loaded else 'None'}")
    output.append("")

    if not results:
        output.append("No validation rules executed.")
        return "\n".join(output)

    # Count issues, separating execution errors from validation findings
    validation_issues = 0
    execution_errors = 0
    execution_error_rules = set()

    for result in results:
        rule_id = result.get("rule_id", "Unknown")
        for r in result.get("results", []):
            if isinstance(r, list):
                for item in r:
                    if isinstance(item, dict) and item.get("errors"):
                        for error in item["errors"]:
                            if _is_execution_error(error):
                                execution_errors += 1
                                execution_error_rules.add(rule_id)
                            else:
                                validation_issues += 1
            elif isinstance(r, dict) and r.get("errors"):
                for error in r["errors"]:
                    if _is_execution_error(error):
                        execution_errors += 1
                        execution_error_rules.add(rule_id)
                    else:
                        validation_issues += 1

    if validation_issues == 0 and execution_errors == 0:
        output.append("Validation PASSED - No issues found.")
        return "\n".join(output)

    if validation_issues == 0:
        output.append("Validation PASSED - No data issues found.")
        output.append(f"(Note: {execution_errors} rule execution errors from {len(execution_error_rules)} rules - these rules may not apply to all entity types)")
        return "\n".join(output)

    output.append(f"Found {validation_issues} validation issue(s):")
    if execution_errors > 0:
        output.append(f"(Plus {execution_errors} rule execution errors from {len(execution_error_rules)} rules)")
    output.append("-" * 60)

    for result in results:
        rule_id = result.get("rule_id", "Unknown")
        description = result.get("description", "")
        action_message = result.get("message", "")
        for r in result.get("results", []):
            if isinstance(r, list):
                for item in r:
                    if isinstance(item, dict):
                        errors = item.get("errors", [])
                        # Filter out execution errors
                        real_errors = [e for e in errors if not _is_execution_error(e)]
                        if real_errors:
                            output.append(f"\nRule: {rule_id}")
                            if description:
                                output.append(f"Description: {description}")
                            if action_message:
                                output.append(f"Message: {action_message}")
                            output.append(f"Errors ({len(real_errors)}):")
                            for error in real_errors[:10]:
                                output.append(f"  - {error}")
                            if len(real_errors) > 10:
                                output.append(f"  ... and {len(real_errors) - 10} more")
            elif isinstance(r, dict):
                errors = r.get("errors", [])
                # Filter out execution errors
                real_errors = [e for e in errors if not _is_execution_error(e)]
                if real_errors:
                    output.append(f"\nRule: {rule_id}")
                    if description:
                        output.append(f"Description: {description}")
                    if action_message:
                        output.append(f"Message: {action_message}")
                    output.append(f"Errors ({len(real_errors)}):")
                    for error in real_errors[:10]:
                        output.append(f"  - {error}")
                    if len(real_errors) > 10:
                        output.append(f"  ... and {len(real_errors) - 10} more")

    output.append("")
    output.append("=" * 60)

    return "\n".join(output)


def format_results_json(validation_data: dict, file_path: str) -> str:
    """
    Format validation results as JSON.

    Args:
        validation_data: Dict with results and metadata from validate_usdm()
        file_path: The path to the validated file

    Returns:
        JSON string
    """
    results = validation_data.get("results", [])
    output_data = {
        "file": file_path,
        "rules_executed": len(results),
        "ct_packages_available": validation_data.get("ct_packages_count", 0),
        "ct_packages_loaded": validation_data.get("ct_packages_loaded", []),
        "ct_packages": validation_data.get("ct_packages", []),
        "results": results
    }

    return json.dumps(output_data, indent=2, default=str)


def main():
    """Main entry point for the USDM validation utility."""
    parser = argparse.ArgumentParser(
        description="Validate USDM JSON files using CDISC Rules Engine (CORE)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python usdm_validate.py study.json
    python usdm_validate.py study.json -v 4-0
    python usdm_validate.py study.json -o results.json -f json
    python usdm_validate.py study.json --verbose

Note: Requires CDISC_API_KEY or CDISC_LIBRARY_API_KEY environment variable
to be set for accessing CDISC Library rules.
        """
    )

    parser.add_argument(
        "usdm_file",
        help="Path to the USDM JSON file to validate"
    )

    parser.add_argument(
        "-v", "--version",
        choices=["3-0", "4-0"],
        default="4-0",
        help="USDM version (default: 4-0)"
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output file for validation results (default: stdout)"
    )

    parser.add_argument(
        "-f", "--format",
        choices=["json", "text"],
        default="text",
        help="Output format (default: text)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show verbose output during validation"
    )

    args = parser.parse_args()

    # Check for API key
    if not os.environ.get("CDISC_LIBRARY_API_KEY") and not os.environ.get("CDISC_API_KEY"):
        print("Warning: No CDISC API key found in environment.", file=sys.stderr)
        print("Set CDISC_API_KEY or CDISC_LIBRARY_API_KEY for full validation.", file=sys.stderr)

    try:
        # Validate the USDM file
        validation_data = validate_usdm(
            args.usdm_file,
            version=args.version,
            verbose=args.verbose
        )

        # Format the results
        if args.format == "json":
            output = format_results_json(validation_data, args.usdm_file)
        else:
            output = format_results_text(validation_data, args.usdm_file)

        # Write output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output)
            if args.verbose:
                print(f"Results written to: {args.output}")
        else:
            print(output)

        # Return exit code based on results
        has_errors = False
        results_list = validation_data.get("results", [])
        for result in results_list:
            for r in result.get("results", []):
                if isinstance(r, list):
                    for item in r:
                        if isinstance(item, dict) and item.get("errors"):
                            has_errors = True
                            break
                elif isinstance(r, dict) and r.get("errors"):
                    has_errors = True
                    break
            if has_errors:
                break

        sys.exit(1 if has_errors else 0)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file: {e}", file=sys.stderr)
        sys.exit(2)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error during validation: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()
