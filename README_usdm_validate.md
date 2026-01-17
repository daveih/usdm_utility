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

**Problem**: Many "Column not found in data" errors reported as validation issues.

**Root Cause**: Some rules (CORE-000414, CORE-000416, CORE-000419, CORE-000849) are configured to apply to `ALL` entities but check for fields like `nextId` and `previousId` that only exist on certain entity types (Encounter, ScheduledActivityInstance, etc.).

**Solution**: Separate execution errors from validation findings:

```python
def _is_execution_error(error: dict) -> bool:
    if isinstance(error, dict):
        return error.get("error") == "Column not found in data"
    return False
```

The output now shows:
```
Found 609 validation issue(s):
(Plus 225 rule execution errors from 4 rules)
```

### 7. XSD Schema Files Missing

**Problem**: Rules that validate XHTML content fail with:
```
XSD file could not be found: Error reading file 'resources/schema/xml/cdisc-usdm-xhtml-1.0/usdm-xhtml-1.0.xsd'
```

**Status**: These XSD files are not included in the pip package. Rules CORE-000945 and CORE-001069 will report execution errors until the schema files are available.

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

### Configuration/Rule Issues

| Category | Description |
|----------|-------------|
| Column not found | Rules checking nextId/previousId on entities that don't have these fields |
| XSD not found | XHTML validation rules missing schema files |
| Preprocessing failed | Rules expecting entities (e.g., StudyCohort) not in the data |

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
