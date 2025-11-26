# USDM to M11 Inclusion/Exclusion Criteria Converter (to_m11.py)

A Python program that converts USDM (Unified Study Definitions Model) JSON files into HTML documents displaying inclusion and exclusion criteria in M11 ICH format.

## Overview

This tool reads USDM JSON study definition files and generates a formatted HTML page containing the inclusion and exclusion criteria sections (5.2 and 5.3) in a format suitable for M11 regulatory documentation. The program intelligently resolves USDM references and tags to create human-readable criteria statements.

## Features

- **USDM4 Compliance**: Built using the USDM4 library for proper study definition handling
- **Reference Resolution**: Automatically resolves `usdm:ref` and `usdm:tag` references within criteria text
- **M11 Formatting**: Outputs criteria in standard M11 section format (5.2 for Inclusion, 5.3 for Exclusion)
- **Times New Roman Styling**: Uses Times New Roman font at 12pt for regulatory document compliance
- **Bootstrap UI**: Clean, professional styling with Bootstrap 5 (Zephyr theme)
- **Error Handling**: Comprehensive error logging and reporting
- **Recursive Translation**: Handles nested references within criteria text

## Prerequisites

### Required Python Packages

```bash
pip install beautifulsoup4
pip install yattag
pip install usdm4
pip install simple-error-log
```

### Dependencies

- **BeautifulSoup4**: HTML parsing and manipulation
- **yattag**: HTML document generation
- **usdm4**: USDM data model and builder
- **simple-error-log**: Error logging and reporting

## Usage

### Command Line

Basic usage:

```bash
python3 to_m11.py <usdm_json_file>
```

### Examples

```bash
# Generate HTML from a USDM JSON file
python3 to_m11.py study_definition.json

# Process a file in a specific directory
python3 to_m11.py /path/to/phuse_eu/M11_USDM.json

# The output file will be created in the same directory with "_criterion" suffix
# Input:  M11_USDM.json
# Output: M11_USDM_criterion.html
```

## Input Format

The program expects a USDM JSON file containing:

### EligibilityCriterion Objects

```json
{
  "id": "...",
  "identifier": "1",
  "category": {
    "code": "C25532",  // For inclusion criteria
    // OR
    "code": "C25370"   // For exclusion criteria
  },
  "criterionItemId": "..."
}
```

### EligibilityCriterionItem Objects

```json
{
  "id": "...",
  "text": "Patient must be ≥18 years of age",
  "dictionaryId": "..."  // Optional, for parameter references
}
```

### USDM References

The program handles special USDM markup within criterion text:

- **`<usdm:ref id="..." attribute="..." />`**: References to other USDM objects
- **`<usdm:tag name="..." />`**: Dictionary parameter references
- **`<u>...</u>`**: Underlined text
- **`<i>...</i>`**: Italic text

## Output Format

The program generates a self-contained HTML file with:

### Structure

```html
<!DOCTYPE html>
<html>
  <head>
    <!-- Bootstrap 5 CSS (Zephyr theme) -->
    <!-- Bootstrap Icons -->
    <!-- Custom styling for M11 format -->
  </head>
  <body>
    <div class="container-fluid">
      <h2>5.2 Inclusion Criteria</h2>
      <p>To be eligible to participate in this trial...</p>
      <table>
        <!-- Numbered inclusion criteria -->
      </table>
      
      <h2>5.3 Exclusion Criteria</h2>
      <p>An individual who meets any of the following criteria...</p>
      <table>
        <!-- Numbered exclusion criteria -->
      </table>
    </div>
  </body>
</html>
```

### Styling

- **Font**: Times New Roman, 12pt (body text), 14pt (headings)
- **Layout**: Full-width container with padding
- **Theme**: Bootstrap 5 Zephyr theme with gradient header
- **Responsive**: Mobile-friendly design

## Technical Details

### Class Structure

#### IE Class

Main class handling the conversion process:

```python
class IE:
    def __init__(self, file_path: str, errors: Errors)
    def to_html(self) -> str
    def _ie_data(self) -> tuple[list, list]
    def _generate_html(self, inclusion: str, exclusion: str)
    def _ie_table(self, doc, criteria: list)
    def _translate_references(self, instance: dict, text: str) -> str
    def _translate_references_recurse(self, instance: dict, text: str) -> str
    def _resolve_usdm_ref(self, instance, ref) -> str
    def _resolve_usdm_tag(self, instance, ref) -> str
```

### Processing Flow

1. **Load USDM Data**: Parse JSON file using USDM4 Builder
2. **Extract Criteria**: Filter EligibilityCriterion objects by category code
3. **Resolve References**: Process `usdm:ref` and `usdm:tag` elements
4. **Generate HTML**: Create formatted HTML document with Bootstrap styling
5. **Save Output**: Write prettified HTML to file

### Category Codes

- **C25532**: Inclusion Criteria (from CDISC CT)
- **C25370**: Exclusion Criteria (from CDISC CT)

### Reference Resolution

The program recursively resolves nested references:

1. **Step 1**: Wrap underline and italic tags around references
2. **Step 2**: Resolve `usdm:ref` by looking up referenced object and attribute
3. **Step 3**: Resolve `usdm:tag` by looking up dictionary parameter map
4. **Step 4**: Recursively process resolved text for nested references

## Error Handling

The program uses the `simple-error-log` library for comprehensive error tracking:

- **Exception Handling**: All exceptions are caught and logged
- **Warning Capture**: BeautifulSoup warnings are captured and logged
- **Debug Information**: Detailed debug messages for troubleshooting
- **Error Summary**: Final error report printed to console

### Example Error Output

```
Errors: {
  "errors": [],
  "warnings": [
    "Warning raised within Soup package..."
  ],
  "debug": []
}
```

## Limitations

1. **USDM4 Dependency**: Requires properly formatted USDM4 JSON files
2. **Category Codes**: Only processes criteria with standard CDISC category codes
3. **Reference Types**: Limited to `usdm:ref` and `usdm:tag` reference types
4. **Single File**: Processes one file at a time (no batch processing)

## Example Output

Given a USDM JSON file with the following criteria:

```json
{
  "identifier": "1",
  "text": "Patient must be ≥<usdm:ref id='age_param' attribute='value'/> years of age"
}
```

The program generates:

```html
<table>
  <tr>
    <td style="vertical-align: top;">1:</td>
    <td style="vertical-align: top;">Patient must be ≥18 years of age</td>
  </tr>
</table>
```

## Integration with Workflow

This program is part of a larger USDM utility suite:

```
USDM JSON → to_m11.py → M11 Criteria HTML
                ↓
        (Also available:)
            to_pj.py → Visit Timeline HTML
         to_visit.py → Visit Details HTML
       to_timeline.py → Study Timeline HTML
```

## Troubleshooting

### Common Issues

**Issue**: "Failed generating HTML page"
- **Solution**: Verify USDM JSON file is well-formed and contains valid USDM4 data

**Issue**: Missing dictionary reference
- **Solution**: Ensure dictionaryId is set and dictionary contains required parameterMaps

**Issue**: Unresolved references
- **Solution**: Check that all referenced IDs exist in the USDM data

**Issue**: Import errors
- **Solution**: Install all required dependencies:
  ```bash
  pip install beautifulsoup4 yattag usdm4 simple-error-log
  ```

## File Naming Convention

The program automatically generates output filenames:

```
Input:  study_definition.json
Output: study_definition_criterion.html

Input:  /path/to/M11_USDM.json
Output: /path/to/M11_USDM_criterion.html
```

## Best Practices

1. **Validate Input**: Ensure USDM JSON is valid before processing
2. **Check Output**: Review generated HTML for proper reference resolution
3. **Monitor Errors**: Check error log output for warnings or issues
4. **Test References**: Verify all `usdm:ref` and `usdm:tag` elements resolve correctly
5. **Browser Testing**: Open generated HTML in multiple browsers to verify rendering

## Related Files

- **to_pj.py**: Visit-based timeline visualization
- **to_visit.py**: Visit details and activities
- **to_timeline.py**: Study timeline visualization
- **phuse_eu/**: Example USDM files and generated outputs

## License

See LICENSE file for details.

## Support

For issues or questions, please refer to the project repository or contact the development team.

## Version History

- **Current**: Initial release with USDM4 support
  - Inclusion/Exclusion criteria extraction
  - Reference resolution (usdm:ref and usdm:tag)
  - M11 formatting with Times New Roman styling
  - Bootstrap 5 UI with Zephyr theme
