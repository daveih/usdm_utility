# USDM Validation Utility

A Python utility that validates USDM (Unified Study Definitions Model) JSON files using the CDISC Rules Engine (CORE).

## Installation

### Prerequisites

1. Python 3.10+
2. CDISC Library API key (obtain from [CDISC Library](https://www.cdisc.org/cdisc-library))

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install cdisc-rules-engine
```

### Environment Variables

Set your CDISC Library API key:

```bash
export CDISC_API_KEY="your-api-key-here"
# or
export CDISC_LIBRARY_API_KEY="your-api-key-here"
```

The utility automatically maps `CDISC_API_KEY` to `CDISC_LIBRARY_API_KEY` if needed.

## Usage

```bash
python usdm_validate.py <usdm_file.json> [options]
```

### Options

| Option | Description |
|--------|-------------|
| `-v, --version` | USDM version: `3-0` or `4-0` (default: `4-0`) |
| `-o, --output` | Output file for validation results (default: stdout) |
| `-f, --format` | Output format: `json` or `text` (default: `text`) |
| `--verbose` | Show verbose output during validation |

### Examples

```bash
# Basic validation (USDM 4.0, text output)
python usdm_validate.py study.json

# Validate USDM 3.0 file
python usdm_validate.py study.json -v 3-0

# Output to JSON file
python usdm_validate.py study.json -o results.json -f json

# Verbose mode (shows library logging)
python usdm_validate.py study.json --verbose
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Validation passed (no issues found) |
| 1 | Validation completed with issues found |
| 2 | Error during validation (file not found, invalid JSON, etc.) |

## Output Format

### Text Output

```
============================================================
USDM Validation Report
============================================================
File: study.json
Rules executed: 205
CT packages available: 200
CT packages loaded: sdtmct-2025-09-26, ddfct-2025-09-26

Found 609 validation issue(s):
(Plus 225 rule execution errors from 4 rules)
------------------------------------------------------------

Rule: CORE-000996
Message: The planned sex includes more than a single entry...
Errors (1):
  - {'value': {...}, 'dataset': 'StudyDesignPopulation', ...}
```

### JSON Output

```json
{
  "file": "study.json",
  "rules_executed": 205,
  "ct_packages_available": 200,
  "ct_packages_loaded": ["sdtmct-2025-09-26", "ddfct-2025-09-26"],
  "ct_packages": ["adamct-2014-09-26", ...],
  "results": [...]
}
```

## Technical Architecture

### How It Works

1. **Initialization**: Sets up the CDISC Rules Engine with in-memory cache
2. **CT Package Loading**: Extracts `codeSystemVersion` values from the USDM file and loads corresponding SDTM and DDF CT packages
3. **Rule Download**: Downloads USDM validation rules from CDISC Library (cached after first run)
4. **JSONata Setup**: Downloads required JSONata custom functions from GitHub
5. **Validation**: Executes each rule against the USDM data
6. **Reporting**: Formats and outputs results, separating validation issues from execution errors

### Key Components

```
usdm_validate.py
├── setup_ct_packages()      # Load CT package list and service
├── load_ct_package_data()   # Load actual codelist terms
├── get_ct_versions_from_usdm()  # Extract CT versions from data
├── setup_jsonata_resources()    # Download JSONata functions
├── load_rules_from_library()    # Download USDM rules
├── validate_usdm()          # Main validation entry point
├── _run_validation()        # Internal validation logic
├── format_results_text()    # Text output formatter
└── format_results_json()    # JSON output formatter
```

## Lessons Learned

### 1. Verbose Output Suppression

The CDISC Rules Engine produces extensive logging and print output that overwhelms the terminal. The solution:

```python
# Disable all logging globally
logging.disable(logging.CRITICAL)

# Suppress stdout/stderr during validation
class SuppressOutput:
    def __enter__(self):
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    def __exit__(self, *args):
        # Restore original streams
```

### 2. Working Directory Requirements

The rules engine expects resources in the current working directory. The utility changes to the site-packages directory during validation:

```python
_CDISC_PACKAGE_DIR = Path(cdisc_rules_engine.__file__).parent.parent
os.chdir(_CDISC_PACKAGE_DIR)  # Before validation
os.chdir(original_cwd)        # After validation
```

### 3. CT Package Loading (Critical)

**Problem**: CT validation fails with "codeSystemVersion is not a valid terminology package date" even when the packages exist.

**Root Cause**: `LibraryMetadataContainer` needs both:
- `published_ct_packages`: List of available package names (for date validation)
- `ct_package_metadata`: Actual codelist content (for code/decode validation)

**Solution**: Load both from CDISC Library:

```python
# Get package list
ct_packages = library_service.get_all_ct_packages()

# Load actual codelist data for versions used in the USDM file
for ct_version in get_ct_versions_from_usdm(usdm_data):
    for ct_type in ["sdtmct", "ddfct"]:
        package_name = f"{ct_type}-{ct_version}"
        ct_data = library_service.get_codelist_terms_map(package_name)
        ct_package_metadata[package_name] = ct_data

# Pass both to the container
library_metadata = LibraryMetadataContainer(
    published_ct_packages=ct_packages,
    ct_package_metadata=ct_package_metadata,
)
```

### 4. USDM CT Package Types

For USDM validation, the relevant CT package types are (from `valid_codelist_dates.py`):
- `sdtmct` - SDTM Controlled Terminology
- `ddfct` - DDF (Digital Data Flow) Controlled Terminology

### 5. JSONata Custom Functions

Some CORE rules use JSONata expressions that require custom functions. These are downloaded from GitHub:

```python
JSONATA_FILES = [
    "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/parse_refs.jsonata",
    "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/sift_tree.jsonata",
]
```

### 6. Rule Execution Errors vs Validation Findings

**Problem**: Many errors reported as validation issues are actually rule execution errors - they occur because the rule doesn't apply to this particular USDM file's structure.

**Types of Execution Errors**:

1. **Column not found in data**: Rules like CORE-000414, CORE-000416, CORE-000419, CORE-000849 are configured to apply to `ALL` entities but check for fields like `nextId` and `previousId` that only exist on certain entity types (Encounter, ScheduledActivityInstance, etc.).

2. **Preprocessing failed**: Rules like CORE-000815 and CORE-000875 require joining with a `StudyCohort` dataset, but studies without cohorts defined will fail preprocessing. The error message is: `Failed to find related dataset for 'StudyCohort' in preprocessor`.

**Solution**: Separate execution errors from validation findings:

```python
def _is_execution_error(error: dict) -> bool:
    if isinstance(error, dict):
        error_type = error.get("error", "")
        # Column not found - rule checks fields that don't exist on entity
        if error_type == "Column not found in data":
            return True
        # Preprocessing failed - rule requires dataset not in USDM file
        if error_type == "Error occurred during dataset preprocessing":
            return True
    return False
```

The output now shows:
```
Found 609 validation issue(s):
(Plus 227 rule execution errors from 6 rules)
```

### 7. XSD Schema Files Missing (Solved)

**Problem**: Rules that validate XHTML content (CORE-000945, CORE-001069) fail with:
```
XSD file could not be found: Error reading file 'resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd'
```

**Root Cause**: The XSD schema files required for XHTML validation are not included in the pip package. The XHTML 1.1 schema is complex with 70+ interdependent files.

**Solution**: The utility automatically downloads the required XSD schema files from the CDISC Rules Engine GitHub repository on first run:

```python
# GitHub base URL for XSD schema files
XSD_GITHUB_BASE = "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/schema/xml"

# USDM XHTML schema files (required for XHTML validation rules)
USDM_XHTML_SCHEMA_FILES = [
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd",
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-extension.xsd",
    "cdisc-usdm-xhtml-1.0/usdm-xhtml-ns.xsd",
]

# Core XHTML 1.1 schema files (70+ files with complex dependencies)
XHTML_SCHEMA_FILES = [
    "xhtml-1.1/xhtml11.xsd",
    "xhtml-1.1/xhtml-hypertext-1.xsd",
    # ... all 70+ XHTML 1.1 schema files
]

def setup_xsd_schema_resources():
    """Download XSD schema files from GitHub if they don't exist locally."""
    # Creates directories and downloads all schema files
    for schema_path in USDM_XHTML_SCHEMA_FILES + XHTML_SCHEMA_FILES:
        url = f"{XSD_GITHUB_BASE}/{schema_path}"
        urllib.request.urlretrieve(url, filepath)
```

**Key Insight**: The XHTML 1.1 schema uses `xs:redefine` and `xs:include` extensively, requiring all schema files to be present. Partial downloads fail with errors like:
```
Failed to load the document 'xhtml-hypertext-1.xsd' for redefinition
```

**Result**: Rules CORE-000945 and CORE-001069 now execute successfully and validate XHTML content in eligibility criteria and narrative content items.

### 8. Rules with Known Bugs

Some rules have bugs in the CDISC Rules Engine (JSONata/NoneType errors):

```python
EXCLUDED_RULES = {
    "CORE-000955",  # JSONata bug
    "CORE-000956",  # JSONata bug
}
```

### 9. CachePopulator Import Issue

**Problem**: `from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator` fails with `ModuleNotFoundError: No module named 'scripts'`.

**Root Cause**: CachePopulator imports from a `scripts` module that isn't part of the pip package.

**Solution**: Implement CT package loading directly using `CDISCLibraryService.get_codelist_terms_map()` instead of using CachePopulator.

## Common Validation Findings

### Real Data Issues

| Rule | Description |
|------|-------------|
| CORE-001013 | Duplicate names across instances of the same class |
| CORE-001051 | NarrativeContent missing child or content item |
| CORE-000427 | Code/decode mismatch within codeSystem/version |
| CORE-000996 | Invalid planned sex configuration |
| CORE-001077 | Study intervention count mismatch for model type |

### Configuration/Rule Issues (Filtered as Execution Errors)

| Category | Rules | Description |
|----------|-------|-------------|
| Column not found | CORE-000414, CORE-000416, CORE-000419, CORE-000849 | Rules checking nextId/previousId on entities that don't have these fields |
| Preprocessing failed | CORE-000815, CORE-000875 | Rules requiring StudyCohort dataset for studies without cohorts defined |

### XHTML Validation Findings

Rules CORE-000945 and CORE-001069 validate XHTML content against the USDM XHTML schema. Common validation errors include:

| Error Type | Example |
|------------|---------|
| Invalid attribute | `Element 'ol', attribute 'type': The attribute 'type' is not allowed` |
| Unexpected element | `Element 'style': This element is not expected` |
| Tag mismatch | `Opening and ending tag mismatch: p line 33 and td` |

## Troubleshooting

### "No CDISC API key found"

Set the environment variable:
```bash
export CDISC_API_KEY="your-key"
```

### Excessive terminal output

The utility suppresses most output by default. Use `--verbose` only when debugging.

### CT validation failures

Ensure your USDM file's `codeSystemVersion` values correspond to published CT packages. Check the "CT packages loaded" line in the output.

### Slow first run

The first run downloads rules and CT packages from CDISC Library. Subsequent runs use cached data.

## Integration Guide

This section documents everything needed to embed USDM CORE validation into another Python program.

### Required Imports

```python
import io
import json
import logging
import os
import sys
import urllib.request
from pathlib import Path

# CRITICAL: Map API key BEFORE importing the engine
if "CDISC_API_KEY" in os.environ and "CDISC_LIBRARY_API_KEY" not in os.environ:
    os.environ["CDISC_LIBRARY_API_KEY"] = os.environ["CDISC_API_KEY"]

# CRITICAL: Disable logging BEFORE importing the engine
# The engine attaches a ConsoleLogger to the root logger on import.
# logging.getLogger().setLevel() does NOT work - it must be disabled globally.
logging.disable(logging.CRITICAL)

import cdisc_rules_engine
from cdisc_rules_engine.config import config
from cdisc_rules_engine.services.cache import CacheServiceFactory
from cdisc_rules_engine.rules_engine import RulesEngine
from cdisc_rules_engine.utilities.utils import get_rules_cache_key
from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
from cdisc_rules_engine.constants.cache_constants import PUBLISHED_CT_PACKAGES
from cdisc_rules_engine.models.library_metadata_container import LibraryMetadataContainer
```

### Critical Path: Working Directory

The rules engine resolves resource paths (JSONata functions, XSD schemas) relative to `os.getcwd()`. It expects a `resources/` directory in the current working directory. The pip-installed package places resources under the site-packages root:

```python
_CDISC_PACKAGE_DIR = Path(cdisc_rules_engine.__file__).parent.parent
# e.g. /path/to/site-packages/

# You MUST chdir before running validation:
original_cwd = os.getcwd()
os.chdir(_CDISC_PACKAGE_DIR)
try:
    # ... run validation ...
finally:
    os.chdir(original_cwd)

# File paths passed to the engine must be absolute because of the chdir:
abs_path = os.path.abspath(file_path)
```

### Critical Path: Output Suppression

The engine produces enormous stdout/stderr output (progress bars, debug prints, library logs). You must suppress it:

```python
class SuppressOutput:
    """Context manager to suppress stdout/stderr from the rules engine."""
    def __init__(self, suppress=True):
        self.suppress = suppress
        self._stdout = self._stderr = self._devnull = None
    def __enter__(self):
        if self.suppress:
            self._devnull = io.StringIO()
            self._stdout, self._stderr = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = self._devnull
        return self
    def __exit__(self, *args):
        if self.suppress:
            sys.stdout, sys.stderr = self._stdout, self._stderr
            self._devnull.close()
```

### Critical Path: CT Package Loading

**This is the most subtle gotcha.** `LibraryMetadataContainer` has TWO separate mechanisms:

1. `published_ct_packages` - a **list of package name strings** (e.g. `["sdtmct-2025-09-26", ...]`). Used to validate that `codeSystemVersion` dates are valid published dates.
2. `ct_package_metadata` - a **dict mapping package names to actual codelist content**. Used to validate that codes/decodes are correct within a codelist.

If you only set `published_ct_packages`, date validation works but code/decode validation silently fails, producing false positives (marking valid codes as errors).

```python
# Step 1: Get the full list of published CT packages
library_service = CDISCLibraryService(api_key, cache)
packages = library_service.get_all_ct_packages()
ct_packages = [p.get("href", "").split("/")[-1] for p in packages]
cache.add(PUBLISHED_CT_PACKAGES, ct_packages)

# Step 2: Determine which CT versions the USDM file actually uses
def get_ct_versions_from_usdm(usdm_data: dict) -> set:
    versions = set()
    def extract(obj):
        if isinstance(obj, dict):
            if "codeSystemVersion" in obj:
                versions.add(obj["codeSystemVersion"])
            for v in obj.values(): extract(v)
        elif isinstance(obj, list):
            for item in obj: extract(item)
    extract(usdm_data)
    return versions

# Step 3: Load actual codelist data for each needed version
# USDM uses TWO CT package types: sdtmct and ddfct
ct_package_metadata = {}
for ct_version in get_ct_versions_from_usdm(usdm_data):
    for ct_type in ["sdtmct", "ddfct"]:
        package_name = f"{ct_type}-{ct_version}"
        if package_name in ct_packages:
            data = library_service.get_codelist_terms_map(package_name)
            if data:
                ct_package_metadata[package_name] = data

# Step 4: Create the container with BOTH
library_metadata = LibraryMetadataContainer(
    published_ct_packages=ct_packages,
    ct_package_metadata=ct_package_metadata,
)
```

### Critical Path: Resource Downloads

Three sets of resources are NOT included in the pip package and must be downloaded from the CDISC Rules Engine GitHub repository on first use:

**1. JSONata custom functions** (2 files):
```
resources/jsonata/parse_refs.jsonata
resources/jsonata/sift_tree.jsonata
```
Source: `https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/`

**2. USDM XHTML schema** (3 files):
```
resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd
resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-extension.xsd
resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-ns.xsd
```

**3. XHTML 1.1 schema** (70+ files - ALL are required):
```
resources/schema/xml/xhtml-1.1/*.xsd
resources/schema/xml/xhtml-1.1/*.ent
```
Source: `https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/schema/xml/xhtml-1.1/`

**WARNING**: The XHTML 1.1 schema uses `xs:redefine` and `xs:include` extensively. If ANY file is missing, the schema parser fails with errors like `Failed to load the document 'xhtml-hypertext-1.xsd' for redefinition`. You must download ALL files.

These are downloaded into the site-packages directory (alongside the engine's existing `resources/` directory). Check for existence before downloading to avoid re-downloading on every run.

### Validation Execution

```python
# Initialize cache (in-memory by default)
cache = CacheServiceFactory(config).get_cache_service()

# Initialize the rules engine
rules_engine = RulesEngine(
    cache=cache,
    standard="usdm",               # Must be "usdm"
    standard_version="4-0",         # "3-0" or "4-0"
    dataset_paths=[abs_path],       # List of absolute paths to USDM JSON files
    library_metadata=library_metadata,
)

# Get datasets (the engine's internal representation of the USDM data)
datasets = rules_engine.data_service.get_datasets()

# Load rules from cache or download from CDISC Library
cache_key = get_rules_cache_key("usdm", "4-0")
rules = cache.get_all_by_prefix(cache_key)
if not rules:
    result = library_service.get_rules_by_catalog("usdm", "4-0")
    rules = result.get("rules", [])
    cache_key = result.get("key_prefix", cache_key)
    for rule in rules:
        cache.add(f"{cache_key}/{rule.get('core_id', 'unknown')}", rule)

# Execute each rule
for rule in rules:
    rule_id = rule.get("core_id", "unknown")
    try:
        rule_results = rules_engine.validate_single_rule(rule, datasets)
        # rule_results is a dict: {dataset_name: result_dict_or_list}
    except Exception:
        # Some rules crash with JSONata/NoneType errors
        pass
```

### Rule Structure

Each rule downloaded from CDISC Library has this structure:

```python
{
    "core_id": "CORE-000996",           # Unique rule identifier
    "description": "A planned sex ...",  # Human-readable rule description
    "rule_type": "Record Data",          # Type of rule
    "executability": "fully executable", # Whether the rule can be run
    "status": "Published",               # Publication status
    "entities": {                        # Which USDM entities the rule applies to
        "Include": ["StudyDesignPopulation"]
    },
    "conditions": { ... },               # Rule logic (all/any/operator tree)
    "actions": [                         # What to do on failure
        {
            "name": "generate_dataset_error_objects",
            "params": {
                "message": "The planned sex includes..."  # Error message text
            }
        }
    ],
    "datasets": [ ... ],                 # Optional: datasets to join (e.g. StudyCohort)
    "output_variables": [ ... ],         # Fields included in error output
    "authorities": [ ... ],              # Standards references
    "standards": [
        {"Name": "USDM", "Version": "4.0"}
    ]
}
```

**Key fields for integration**:
- `rule.get("description")` - the rule description (what it checks)
- `rule.get("actions", [{}])[0].get("params", {}).get("message", "")` - the error message (what it reports on failure)
- `rule.get("core_id")` - the unique rule ID

### Result Structure

`validate_single_rule()` returns a dict. The values are lists or dicts containing:

```python
{
    "errors": [                          # List of error dicts
        {
            "value": {                   # The data that triggered the error
                "instanceType": "StudyDesignPopulation",
                "id": "StudyDesignPopulation_1",
                "path": "/study/versions/0/studyDesigns/0/population",
                "name": "POP1",
                # ... other fields from output_variables
            },
            "dataset": "StudyDesignPopulation",
            "entity": "StudyDesignPopulation",
            "instance_id": "StudyDesignPopulation_1",
            "path": "/study/versions/0/studyDesigns/0/population"
        }
    ],
    "message": "..."                     # May or may not be present
}
```

**Execution error dicts** (not data issues - rule doesn't apply) have a different shape:

```python
# "Column not found" - rule checks fields that don't exist on the entity
{
    "error": "Column not found in data",
    "dataset": "Code.json",
    "row": 1,
    ...
}

# "Preprocessing failed" - rule requires a dataset not in the USDM file
{
    "error": "Error occurred during dataset preprocessing",
    "message": "Failed to find related dataset for 'StudyCohort' in preprocessor",
    "dataset": "StudyDesignPopulation.json"
}
```

### Filtering Execution Errors from Validation Findings

This is essential for clean output. The `error` field distinguishes execution errors from real findings:

```python
def _is_execution_error(error: dict) -> bool:
    if isinstance(error, dict):
        error_type = error.get("error", "")
        if error_type == "Column not found in data":
            return True
        if error_type == "Error occurred during dataset preprocessing":
            return True
    return False
```

**Known execution error rules**:
| Rule | Error Type | Reason |
|------|-----------|--------|
| CORE-000414 | Column not found | Checks `nextId` on ALL entities; only exists on ordered types |
| CORE-000416 | Column not found | Checks `previousId` on ALL entities |
| CORE-000419 | Column not found | Checks `nextId` on ALL entities |
| CORE-000849 | Column not found | Checks `nextId`/`previousId` on ALL entities |
| CORE-000815 | Preprocessing failed | Requires `StudyCohort` dataset join |
| CORE-000875 | Preprocessing failed | Requires `StudyCohort` dataset join |

### Rules to Exclude

These rules crash the engine with unrecoverable errors:

```python
EXCLUDED_RULES = {
    "CORE-000955",  # JSONata bug - crashes with NoneType error
    "CORE-000956",  # JSONata bug - crashes with NoneType error
}
```

### CachePopulator - Do NOT Use

`from cdisc_rules_engine.services.cache.cache_populator_service import CachePopulator` fails with `ModuleNotFoundError: No module named 'scripts'`. The `CachePopulator` class imports from a `scripts` module that is part of the CLI tool, not the pip package. Use `CDISCLibraryService` methods directly instead.

### Complete Minimal Integration Example

```python
import io, json, logging, os, sys, urllib.request
from pathlib import Path

if "CDISC_API_KEY" in os.environ and "CDISC_LIBRARY_API_KEY" not in os.environ:
    os.environ["CDISC_LIBRARY_API_KEY"] = os.environ["CDISC_API_KEY"]
logging.disable(logging.CRITICAL)

import cdisc_rules_engine
from cdisc_rules_engine.config import config
from cdisc_rules_engine.services.cache import CacheServiceFactory
from cdisc_rules_engine.rules_engine import RulesEngine
from cdisc_rules_engine.utilities.utils import get_rules_cache_key
from cdisc_rules_engine.services.cdisc_library_service import CDISCLibraryService
from cdisc_rules_engine.constants.cache_constants import PUBLISHED_CT_PACKAGES
from cdisc_rules_engine.models.library_metadata_container import LibraryMetadataContainer

CDISC_PKG_DIR = Path(cdisc_rules_engine.__file__).parent.parent
EXCLUDED = {"CORE-000955", "CORE-000956"}


def validate(usdm_path: str, version: str = "4-0") -> list[dict]:
    """
    Validate a USDM JSON file. Returns list of dicts:
    [{"rule_id", "description", "message", "errors": [...]}]
    """
    abs_path = os.path.abspath(usdm_path)
    with open(abs_path) as f:
        usdm_data = json.load(f)

    original_cwd = os.getcwd()
    os.chdir(CDISC_PKG_DIR)
    _stdout, _stderr = sys.stdout, sys.stderr
    sys.stdout = sys.stderr = io.StringIO()

    try:
        # Download resources if needed (JSONata + XSD schemas)
        _setup_resources()

        cache = CacheServiceFactory(config).get_cache_service()
        api_key = os.environ.get("CDISC_LIBRARY_API_KEY", "")
        library_service = CDISCLibraryService(api_key, cache)

        # Load CT packages
        packages = library_service.get_all_ct_packages()
        ct_packages = [p.get("href", "").split("/")[-1] for p in packages]
        cache.add(PUBLISHED_CT_PACKAGES, ct_packages)

        # Load CT data for versions used in file
        ct_metadata = {}
        versions = _extract_ct_versions(usdm_data)
        for v in versions:
            for ct_type in ["sdtmct", "ddfct"]:
                pkg = f"{ct_type}-{v}"
                if pkg in ct_packages:
                    data = library_service.get_codelist_terms_map(pkg)
                    if data:
                        ct_metadata[pkg] = data

        metadata = LibraryMetadataContainer(
            published_ct_packages=ct_packages,
            ct_package_metadata=ct_metadata,
        )

        engine = RulesEngine(
            cache=cache, standard="usdm", standard_version=version,
            dataset_paths=[abs_path], library_metadata=metadata,
        )
        datasets = engine.data_service.get_datasets()

        # Load rules
        cache_key = get_rules_cache_key("usdm", version)
        rules = cache.get_all_by_prefix(cache_key)
        if not rules:
            result = library_service.get_rules_by_catalog("usdm", version)
            rules = result.get("rules", [])
            pfx = result.get("key_prefix", cache_key)
            for r in rules:
                cache.add(f"{pfx}/{r.get('core_id')}", r)

        # Execute rules and collect findings
        findings = []
        for rule in rules:
            rid = rule.get("core_id", "")
            if rid in EXCLUDED:
                continue
            desc = rule.get("description", "")
            msg = ""
            actions = rule.get("actions", [])
            if actions:
                msg = actions[0].get("params", {}).get("message", "")
            try:
                results = engine.validate_single_rule(rule, datasets)
                errors = _extract_errors(results)
                if errors:
                    findings.append({
                        "rule_id": rid, "description": desc,
                        "message": msg, "errors": errors,
                    })
            except Exception:
                pass
        return findings

    finally:
        sys.stdout, sys.stderr = _stdout, _stderr
        os.chdir(original_cwd)


def _extract_ct_versions(data):
    versions = set()
    def walk(obj):
        if isinstance(obj, dict):
            if "codeSystemVersion" in obj:
                versions.add(obj["codeSystemVersion"])
            for v in obj.values(): walk(v)
        elif isinstance(obj, list):
            for i in obj: walk(i)
    walk(data)
    return versions


def _extract_errors(results):
    """Extract real validation errors, filtering out execution errors."""
    real = []
    for val in (results or {}).values():
        items = val if isinstance(val, list) else [val]
        for item in items:
            if not isinstance(item, dict):
                continue
            for err in item.get("errors", []):
                if isinstance(err, dict):
                    etype = err.get("error", "")
                    if etype in ("Column not found in data",
                                 "Error occurred during dataset preprocessing"):
                        continue
                real.append(err)
    return real


def _setup_resources():
    """Download JSONata + XSD resources if not already present."""
    # JSONata
    jdir = CDISC_PKG_DIR / "resources" / "jsonata"
    if not (jdir.exists() and any(jdir.glob("*.jsonata"))):
        jdir.mkdir(parents=True, exist_ok=True)
        for name in ["parse_refs.jsonata", "sift_tree.jsonata"]:
            url = f"https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/jsonata/{name}"
            urllib.request.urlretrieve(url, jdir / name)

    # XSD schemas (check for USDM XHTML schema as sentinel)
    xdir = CDISC_PKG_DIR / "resources" / "schema" / "xml"
    sentinel = xdir / "cdisc-usdm-xhtml-1.0" / "usdm-xhtml-1.0.xsd"
    if not sentinel.exists():
        base = "https://raw.githubusercontent.com/cdisc-org/cdisc-rules-engine/main/resources/schema/xml"
        # See USDM_XHTML_SCHEMA_FILES and XHTML_SCHEMA_FILES constants
        # in usdm_validate.py for the full list of 70+ files
        for subdir in ["cdisc-usdm-xhtml-1.0", "xhtml-1.1"]:
            (xdir / subdir).mkdir(parents=True, exist_ok=True)
        for path in USDM_XHTML_SCHEMA_FILES + XHTML_SCHEMA_FILES:
            try:
                urllib.request.urlretrieve(f"{base}/{path}", xdir / path)
            except Exception:
                pass
```

### Full List of XSD Schema Files Required

The USDM XHTML schemas (3 files):
```
cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd
cdisc-usdm-xhtml-1.0/usdm-xhtml-extension.xsd
cdisc-usdm-xhtml-1.0/usdm-xhtml-ns.xsd
```

The XHTML 1.1 schemas (all required due to xs:redefine/xs:include chains):
```
xhtml-1.1/aria-attributes-1.xsd
xhtml-1.1/xframes-1.xsd
xhtml-1.1/xhtml-access-1.xsd
xhtml-1.1/xhtml-applet-1.xsd
xhtml-1.1/xhtml-attribs-1.xsd
xhtml-1.1/xhtml-base-1.xsd
xhtml-1.1/xhtml-basic-form-1.xsd
xhtml-1.1/xhtml-basic-table-1.xsd
xhtml-1.1/xhtml-basic10-model-1.xsd
xhtml-1.1/xhtml-basic10-modules-1.xsd
xhtml-1.1/xhtml-basic10.xsd
xhtml-1.1/xhtml-basic11-model-1.xsd
xhtml-1.1/xhtml-basic11-modules-1.xsd
xhtml-1.1/xhtml-basic11.xsd
xhtml-1.1/xhtml-bdo-1.xsd
xhtml-1.1/xhtml-blkphras-1.xsd
xhtml-1.1/xhtml-blkpres-1.xsd
xhtml-1.1/xhtml-blkstruct-1.xsd
xhtml-1.1/xhtml-charent-1.xsd
xhtml-1.1/xhtml-csismap-1.xsd
xhtml-1.1/xhtml-datatypes-1.xsd
xhtml-1.1/xhtml-edit-1.xsd
xhtml-1.1/xhtml-events-1.xsd
xhtml-1.1/xhtml-form-1.xsd
xhtml-1.1/xhtml-frames-1.xsd
xhtml-1.1/xhtml-framework-1.xsd
xhtml-1.1/xhtml-hypertext-1.xsd
xhtml-1.1/xhtml-iframe-1.xsd
xhtml-1.1/xhtml-image-1.xsd
xhtml-1.1/xhtml-inlphras-1.xsd
xhtml-1.1/xhtml-inlpres-1.xsd
xhtml-1.1/xhtml-inlstruct-1.xsd
xhtml-1.1/xhtml-inlstyle-1.xsd
xhtml-1.1/xhtml-inputmode-1.xsd
xhtml-1.1/xhtml-lat1.ent
xhtml-1.1/xhtml-legacy-1.xsd
xhtml-1.1/xhtml-legacy-redecl-1.xsd
xhtml-1.1/xhtml-link-1.xsd
xhtml-1.1/xhtml-list-1.xsd
xhtml-1.1/xhtml-meta-1.xsd
xhtml-1.1/xhtml-metaAttributes-1.xsd
xhtml-1.1/xhtml-misc-1.xsd
xhtml-1.1/xhtml-mobile10-model-1.xsd
xhtml-1.1/xhtml-mobile10.xsd
xhtml-1.1/xhtml-nameident-1.xsd
xhtml-1.1/xhtml-notations-1.xsd
xhtml-1.1/xhtml-object-1.xsd
xhtml-1.1/xhtml-param-1.xsd
xhtml-1.1/xhtml-pres-1.xsd
xhtml-1.1/xhtml-print-model-1.xsd
xhtml-1.1/xhtml-print.xsd
xhtml-1.1/xhtml-rdfa-1.xsd
xhtml-1.1/xhtml-rdfa-model-1.xsd
xhtml-1.1/xhtml-rdfa-modules-1.xsd
xhtml-1.1/xhtml-role-1.xsd
xhtml-1.1/xhtml-role-attrib-1.xsd
xhtml-1.1/xhtml-ruby-1.xsd
xhtml-1.1/xhtml-script-1.xsd
xhtml-1.1/xhtml-simple-1.xsd
xhtml-1.1/xhtml-special.ent
xhtml-1.1/xhtml-ssismap-1.xsd
xhtml-1.1/xhtml-struct-1.xsd
xhtml-1.1/xhtml-style-1.xsd
xhtml-1.1/xhtml-symbol.ent
xhtml-1.1/xhtml-table-1.xsd
xhtml-1.1/xhtml-target-1.xsd
xhtml-1.1/xhtml-text-1.xsd
xhtml-1.1/xhtml-uri-1.xsd
xhtml-1.1/xhtml1-frameset.xsd
xhtml-1.1/xhtml1-strict.xsd
xhtml-1.1/xhtml1-transitional.xsd
xhtml-1.1/xhtml11-flat.xsd
xhtml-1.1/xhtml11-model-1.xsd
xhtml-1.1/xhtml11-modules-1.xsd
xhtml-1.1/xhtml11.xsd
xhtml-1.1/xml.xsd
```

## Dependencies

- `cdisc-rules-engine` - CDISC CORE validation engine
- `jsonata` - JSONata expression evaluator (transitive)
- Standard library: `argparse`, `json`, `logging`, `os`, `sys`, `io`, `urllib`

## License

This utility is provided as-is for validating USDM files against CDISC conformance rules.

## References

- [CDISC Rules Engine (CORE)](https://github.com/cdisc-org/cdisc-rules-engine)
- [CDISC Library](https://www.cdisc.org/cdisc-library)
- [USDM Specification](https://www.cdisc.org/standards/foundational/usdm)
- [PyPI: cdisc-rules-engine](https://pypi.org/project/cdisc-rules-engine/)
