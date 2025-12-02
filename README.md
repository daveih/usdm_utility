# Overview

A set of USDM and other utilities

- Excel to USDM JSON Converter (from_excel.py)
- USDM to M11 Inclusion/Exclusion Criteria Converter (to_m11.py)
- Visit-Based Timeline Visualization (to_pj.py)
- D3 Timeline Visualization (to_timeline.py)
- OCR Text Extraction from Images (to_text.py)
- Image Renamer that renames image files based on their metadata timestamps (rename_images.py)

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




# Visit-Based Timeline Visualization (to_pj.py)

A Python program that generates interactive HTML pages with Bootstrap 5 cards and D3.js vertical serpentine timeline visualizations for clinical trial data.

## Overview

This tool creates a detailed view of clinical trial visits, displaying each visit as a separate Bootstrap card. Each card contains a vertical serpentine timeline of the activities performed during that visit. The visualization is interactive with tooltips showing detailed information about procedures and notes.

## Features

- **Bootstrap 5 Cards**: Each visit displayed in a professional, styled card
- **Vertical Serpentine Layout**: Activities flow vertically down and up alternating columns (like reading a newspaper)
- **Interactive Tooltips**: Hover over activity nodes to see:
  - Activity title
  - Associated procedures
  - Notes and details
- **Responsive Design**: Modern gradient headers and professional styling
- **Visit Information Panel**: Displays visit type, duration, timing, and notes
- **D3.js Powered**: Uses D3.js v7 for smooth, interactive visualizations

## Serpentine Layout (Vertical)

The vertical serpentine layout arranges activities in columns, alternating direction:

```
Column 1:  Column 2:  Column 3:
   ↓          ↑          ↓
Activity 1   Activity 7  Activity 13
   ↓          ↑          ↓
Activity 2   Activity 6  Activity 14
   ↓          ↑          ↓
Activity 3   Activity 5  Activity 15
   ↓       ↙  ↑          ↓
Activity 4   Activity 8  ...
      ↘      ↑
```

This creates a continuous vertical path through all activities, making it easy to follow the sequence while efficiently using space.

## Data Format

The input data should be a JSON object with a `visits` array:

```json
{
  "visits": [
    {
      "title": "Visit 1",
      "type": "In Person",
      "timing": "Day 1",
      "duration": "P1D",
      "notes": "Optional notes about the visit",
      "activities": [
        {
          "title": "Activity name",
          "procedures": ["Procedure 1", "Procedure 2"],
          "notes": "Optional activity notes"
        }
      ]
    }
  ]
}
```

## Usage

### Command Line

Generate an HTML file from JSON data:

```bash
python3 to_pj.py <input_json_file> [output_html_file]
```

**Examples:**

```bash
# Generate with default output filename (visit_timeline.html)
python3 to_pj.py pj/pj_p1.json

# Specify custom output filename
python3 to_pj.py pj/pj_p1.json my_visits.html

# Test with example data
python3 to_pj.py pj/pj_p2.json clinical_visits.html
```

The script creates a self-contained HTML file that can be opened directly in any web browser.

### Integration with Python/Jinja2 Applications

The `generate_html()` function can be used within your Python application:

```python
from to_pj import load_json_data, generate_html

# Load your data
data = load_json_data('pj/pj_p1.json')

# Generate HTML visualization
generate_html(data, 'output.html')
```

Or integrate with Flask/Django:

```python
from flask import Flask, render_template_string
import json
from to_pj import generate_html

app = Flask(__name__)

@app.route('/visits')
def show_visits():
    with open('data.json', 'r') as f:
        data = json.load(f)
    
    # Generate and serve the HTML
    html_content = generate_html(data, 'temp_visits.html')
    with open('temp_visits.html', 'r') as f:
        return f.read()
```

## Customization

You can customize the visualization by modifying the `config` object in the JavaScript:

```javascript
const config = {
    nodeRadius: 6,        // Size of activity circles
    colWidth: 120,        // Horizontal spacing between columns
    nodeSpacing: 70,      // Vertical spacing between nodes
    nodesPerCol: 6,       // Number of activities per column
    margin: { top: 20, right: 30, bottom: 20, left: 30 }
};
```

### Styling Customization

Modify the CSS to customize:

**Colors:**
- Visit card headers: Change gradient colors in `.card-header` background
- Activity nodes: Modify `.activity-circle` fill and stroke colors
- Timeline path: Adjust `.timeline-path` stroke color

**Layout:**
- Card spacing: Modify `.visit-card` margin-bottom
- Card shadows: Adjust box-shadow properties
- Timeline container height: Change `.timeline-container` min-height

**Tooltips:**
- Background: Modify `.tooltip` background-color
- Border and shadow: Adjust border and box-shadow properties

## File Structure

```
.
├── to_pj.py                      # Main program
├── README_TO_PJ.md              # This documentation
├── pj/
│   ├── data_v2.json             # Data schema
│   ├── pj_p1.json               # Example data file 1
│   ├── pj_p2.json               # Example data file 2
│   └── pj_p3.json, etc.         # Additional example files
├── pj_p1_visits_vertical.html   # Generated example output
└── pj_p2_visits.html            # Generated example output
```

## Dependencies

- **D3.js v7**: Loaded from CDN (https://d3js.org/d3.v7.min.js)
- **Bootstrap 5**: Loaded from CDN (https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/)
- **Python 3.6+**: For running the generator script

No installation required - all libraries are loaded from CDNs.

## Browser Compatibility

The visualization requires a modern web browser with:
- ES6 JavaScript support
- SVG rendering capabilities
- CSS3 support (gradients, transitions)
- D3.js v7 compatibility

Tested on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Features Breakdown

### Visit Cards
- **Header**: Gradient background with visit title and badge showing visit number
- **Info Panel**: Displays visit metadata (type, duration, timing, notes)
- **Timeline Section**: Interactive D3.js visualization of activities
- **Hover Effects**: Cards lift and enhance shadow on hover

### Activity Timeline
- **Vertical Serpentine Path**: Connects all activities in a continuous flow
- **Activity Nodes**: Interactive circles that respond to hover events
- **Text Labels**: Activity titles with automatic text wrapping
- **No Activities State**: Friendly message when no activities are recorded

### Tooltips
- **Rich Information**: Shows activity title, procedures, and notes
- **Smart Positioning**: Appears next to cursor, automatically positioned
- **Styled Content**: Formatted with headers, bullet points, and sections

## Examples

Example visualizations have been generated:
- `pj_p1_visits_vertical.html` - 20 visits from pj/pj_p1.json
- `pj_p2_visits.html` - 12 visits from pj/pj_p2.json

Open these files in a web browser to see the visualization in action.

## Troubleshooting

**Issue**: Cards don't appear
- Check browser console for JavaScript errors
- Verify data format matches expected schema
- Ensure D3.js and Bootstrap CDNs are accessible

**Issue**: Vertical layout looks cramped
- Adjust `colWidth` to increase horizontal spacing
- Modify `nodeSpacing` to increase vertical spacing
- Change `nodesPerCol` to show fewer activities per column

**Issue**: Tooltips don't show
- Ensure you're hovering over activity circles (not just near them)
- Check that tooltip CSS isn't being overridden by other styles
- Verify JavaScript console for errors

**Issue**: Text labels overlap
- Increase `colWidth` in config
- Modify font size in `.activity-label` CSS
- Adjust text wrapping logic in the label creation code

## Comparison with generate_timeline.py

| Feature | to_pj.py | generate_timeline.py |
|---------|----------|---------------------|
| Layout | Vertical serpentine per visit | Horizontal serpentine for all visits |
| Organization | Bootstrap cards (one per visit) | Single timeline page |
| Focus | Detailed activity view per visit | Overview of all visits |
| Best for | Activity-level analysis | Study timeline overview |

## License

See LICENSE file for details.

## Support

For issues or questions, please refer to the project repository.




# D3 Timeline Visualization (to_timeline.py)

A Python program that generates interactive HTML pages with D3.js visualizations displaying USDM (Unified Study Definitions Model) study timelines in a horizontal flowchart format.

## Overview

This tool reads USDM JSON study definition files and creates sophisticated timeline visualizations showing the flow of scheduled activities, decisions, timing relationships, and conditional branches. The visualization uses D3.js to create interactive flowchart-style diagrams that clearly represent the structure and logic of clinical trial schedules.

## Features

- **Horizontal Flowchart Layout**: Activities arranged in a left-to-right timeline
- **Multiple Node Types**: 
  - **Activity nodes** (circles): Scheduled activities
  - **Decision nodes** (diamonds): Branching points with conditions
  - **Entry/Exit nodes** (rounded rectangles): Timeline start and end points
  - **Timing nodes** (circles with icon/text): Timing relationships between activities
  - **Anchor nodes** (ship's anchor icon): Fixed reference points for timing
- **Conditional Branches**: Visual representation of decision logic with labeled paths above the main timeline
- **Orphan Node Support**: Handles off-timeline activities connected via conditional links
- **Timing Relationships**: Visual "from/to" connections showing relative timing between activities
- **Interactive Tooltips**: Hover over nodes to see detailed information
- **Multiple Timelines**: Generates separate visualizations for each timeline in the study
- **Entry Conditions**: Displays entry criteria for each timeline

## Node Types Explained

### Activity Nodes (Circles)
- Represent scheduled activities in the study
- Gray filled circles with black border
- Display activity label with automatic text wrapping
- Tooltip shows: title, type, description

### Decision Nodes (Diamonds)
- Represent branching points in the timeline
- Diamond-shaped with gray fill and black border
- Can have multiple conditional outgoing links
- Tooltip shows: title, type, description

### Entry/Exit Nodes (Rounded Rectangles)
- Mark the beginning and end of a timeline
- Light gray rounded rectangles
- Entry appears at the start, Exit at the end
- Height is half of regular nodes for visual distinction

### Timing Nodes (Circles)
- Show timing relationships between activities
- White circles with blue border
- Display timing value and window information
- Connected to "from" and "to" activity nodes with blue arrows
- Can display as anchor icon for Fixed Reference timing

### Anchor Nodes (Special Timing)
- Represent fixed timing references (CDISC code C201358)
- Display as ship's anchor icon instead of text
- Blue colored to match timing theme
- Used for absolute timing references in the study

## Timeline Flow

```
Entry → Activity 1 → Decision → Activity 2 → Exit
                        ↓
                    (Condition A)
                        ↓
                    Activity 3 → Activity 4
                        ↓
                    (rejoin main timeline)
```

**Conditional branches** appear above the main timeline with labeled paths showing which condition leads where.

**Timing relationships** appear below the main timeline, showing relative timing between activities.

## Prerequisites

### Required Python Packages

```bash
pip install usdm4
pip install simple-error-log
```

### Dependencies

- **usdm4**: USDM data model and builder for parsing study definitions
- **simple-error-log**: Error logging and reporting
- **D3.js v7**: Loaded from CDN in generated HTML

## Usage

### Command Line

Basic usage:

```bash
python3 to_timeline.py <usdm_json_file>
```

### Examples

```bash
# Generate timeline from USDM JSON file
python3 to_timeline.py test_data/NCT12345678.json

# Process file in specific directory
python3 to_timeline.py phuse_eu/M11_USDM.json

# Output file created with "_timeline" suffix
# Input:  M11_USDM.json
# Output: M11_USDM_timeline.html
```

The program automatically creates the output file in the same directory as the input, with `_timeline` appended to the filename.

## Input Format

The program expects a USDM4-compliant JSON file containing:

### Study Structure
```json
{
  "study": {
    "versions": [{
      "studyDesigns": [{
        "scheduleTimelines": [...]
      }]
    }]
  }
}
```

### Schedule Timeline Objects
Each timeline contains:
- **id**: Unique identifier
- **label**: Timeline name/description
- **entryCondition**: Condition required to enter this timeline
- **entryId**: Reference to the first scheduled instance
- **timings**: Array of timing relationships
- **Scheduled instances**: Activities and decisions in sequence

### Scheduled Instance Types

**ScheduledActivityInstance:**
```json
{
  "id": "...",
  "instanceType": "ScheduledActivityInstance",
  "label": "Screening Visit",
  "description": "Initial screening procedures",
  "defaultConditionId": "next_instance_id",
  "timelineExitId": "exit_id"
}
```

**ScheduledDecisionInstance:**
```json
{
  "id": "...",
  "instanceType": "ScheduledDecisionInstance",
  "label": "Eligibility Decision",
  "description": "Determine patient eligibility",
  "defaultConditionId": "default_path_id",
  "conditionAssignments": [
    {
      "condition": "Eligible",
      "conditionTargetId": "target_instance_id"
    }
  ]
}
```

## Output Format

Generates a self-contained HTML file with:

### Structure
```html
<!DOCTYPE html>
<html>
  <head>
    <title>USDM Timeline Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <!-- Embedded CSS styling -->
  </head>
  <body>
    <h1>USDM Timeline Visualization</h1>
    <div id="timelines">
      <!-- Timeline containers created dynamically -->
    </div>
    <div class="tooltip" id="tooltip"></div>
    <!-- Embedded JavaScript with D3 visualization -->
  </body>
</html>
```

### Visual Elements

1. **Timeline Container**: White card with rounded corners and shadow
2. **Timeline Title**: Bold heading with timeline label
3. **Entry Condition**: Italic text showing entry requirements
4. **Main Timeline**: Horizontal flow of nodes and links
5. **Conditional Links**: Orthogonal paths above main timeline
6. **Timing Links**: Blue connections below main timeline
7. **Orphan Nodes**: Additional nodes connected via conditions
8. **Interactive Tooltips**: Information on hover

## Technical Details

### Class Structure

#### Timeline Class

Main class handling timeline processing and HTML generation:

```python
class Timeline:
    def __init__(self, file_path: str, errors: Errors)
    def to_html(self) -> str
    def _generate_html(self, study_design: StudyDesign) -> str
    def _process_timeline(self, timeline) -> dict
    def _format_timelines_data(self, timelines_data) -> str
    def _get_cross_reference(self, id) -> dict
```

### Processing Flow

1. **Load USDM Data**: Parse JSON using USDM4 Builder
2. **Extract Study Design**: Get first study version and design
3. **Process Each Timeline**:
   - Build main timeline chain (entry → activities → exit)
   - Identify conditional branches and targets
   - Collect orphan nodes (off-timeline activities)
   - Process timing relationships
   - Calculate node positions
4. **Generate HTML**: Embed data and D3.js visualization code
5. **Save Output**: Write HTML to file with `_timeline` suffix

### Layout Algorithm

**Horizontal Positioning:**
- Nodes spaced evenly left-to-right
- Fixed horizontal spacing (250px default)
- Entry/exit nodes have half height

**Vertical Organization:**
- Orphan nodes: Top row (Y=20)
- Conditional links: Above main timeline with staggered heights
- Main timeline: Center horizontal line
- Timing nodes: Below main timeline

**Dynamic Spacing:**
- SVG height calculated based on number of orphan nodes and conditional links
- Automatic margin adjustments to prevent clipping
- Horizontal scrolling enabled for wide timelines

### D3.js Visualization

**Shapes:**
- Activities: `<circle>` elements
- Decisions: `<path>` elements (diamond shape)
- Entry/Exit: `<rect>` elements with rounded corners
- Timing: `<circle>` elements or custom anchor SVG paths

**Links:**
- Main flow: Gray dashed lines with black arrowheads
- Timing: Blue solid lines with blue arrowheads labeled "from" and "to"
- Conditional: Black solid orthogonal lines with condition labels

**Interaction:**
- Hover events on all nodes
- Tooltip positioning relative to cursor
- Node cursor changes to pointer on hover

## Configuration

The D3 visualization behavior can be customized by modifying constants in the JavaScript:

```javascript
const activityNodeRadius = 40;   // Radius of activity circles
const nodeWidth = 80;             // Width for rectangular nodes
const nodeHeight = 80;            // Height for rectangular nodes
const timingNodeRadius = 40;      // Radius of timing circles
const horizontalSpacing = 250;    // Space between nodes horizontally
const verticalSpacing = 150;      // Space for timing nodes below
const marginLeft = 50;            // Left page margin
const marginTop = 50;             // Top page margin (plus dynamic adjustments)
const marginRight = 50;           // Right page margin
const marginBottom = 200;         // Bottom page margin
```

## Error Handling

Comprehensive error tracking using `simple-error-log`:

### Exception Types

**Timeline Processing Errors:**
```
Failed processing timeline {timeline.label}
- Missing required instances
- Invalid cross-references
- Malformed condition assignments
```

**HTML Generation Errors:**
```
Failed generating HTML page
- Invalid study design structure
- Missing timeline data
- JSON serialization issues
```

### Error Output

```
Input file: test_data/NCT12345678.json
Output path: test_data
Output file: test_data/NCT12345678_timeline.html

Errors: {...}
```

If errors occur, they are printed to console with details. Otherwise, success message is shown.

## Visual Styling

### Colors

- **Activity nodes**: Gray (#C0C0C0) fill, black stroke
- **Decision nodes**: Gray fill, black stroke
- **Entry/Exit nodes**: Light gray (#D3D3D3) fill, black stroke
- **Timing nodes**: White fill, blue (#003366) stroke
- **Anchor icons**: Blue (#003366)
- **Links**: Gray (#999) main flow, blue (#003366) timing
- **Conditional links**: Black (#000000)
- **Background**: White (#FFFFFF) cards on light gray (#F5F5F5) page

### Typography

- **Timeline title**: 24px bold, dark gray (#333)
- **Entry condition**: 14px italic, medium gray (#666)
- **Node labels**: 12px, dark gray (#333), auto-wrapped
- **Link labels**: 10px, medium gray (#666)
- **Conditional labels**: 10px bold, black
- **Timing labels**: 10px bold, blue

### Layout

- **Card container**: White background, rounded corners (8px), shadow
- **Card padding**: 20px all around
- **Card margin**: 40px bottom spacing between timelines
- **Horizontal scrolling**: Enabled for wide timelines

## Limitations

1. **USDM4 Dependency**: Requires valid USDM4 JSON structure
2. **Single Study Design**: Processes first study design only
3. **Cross-Reference Integrity**: Assumes all referenced IDs exist
4. **Performance**: Very complex timelines (100+ nodes) may render slowly
5. **Browser Dependency**: Requires modern browser with SVG and ES6 support

## Example Use Cases

### Simple Linear Timeline
```
Entry → Screening → Baseline → Treatment → Follow-up → Exit
```

### Timeline with Decision Point
```
Entry → Screening → Eligibility Decision
                              ↓ (Eligible)
                          Treatment → Follow-up → Exit
                              ↓ (Not Eligible)
                          Screen Failure → Exit
```

### Timeline with Timing Relationships
```
Entry → Visit 1 → Visit 2 → Visit 3 → Exit
           ↓         ↑
          (2 weeks from Visit 1 to Visit 2)
```

### Complex Timeline with Orphans
```
Entry → Activity 1 → Decision A
                         ↓ (main path)
                     Activity 2 → Exit
                         ↓ (condition X)
                     Orphan 1 → Orphan 2
                                    ↓
                              (rejoins at Activity 2)
```

## Comparison with Other Utilities

| Feature | to_timeline.py | to_pj.py | to_visit.py |
|---------|---------------|----------|-------------|
| Data Source | USDM JSON | Custom JSON | USDM JSON |
| Layout | Horizontal flowchart | Vertical serpentine cards | Table format |
| Focus | Timeline structure & logic | Visit activities | Visit details |
| Interaction | Tooltips only | Tooltips | Filterable table |
| Best For | Understanding flow | Activity sequences | Detailed visit info |
| Complexity | High (decisions, timings) | Medium (activities) | Low (data display) |

## File Naming Convention

```
Input:  study_definition.json
Output: study_definition_timeline.html

Input:  test_data/NCT12345678.json
Output: test_data/NCT12345678_timeline.html
```

## Troubleshooting

### Common Issues

**Issue**: "Failed generating HTML page"
- **Solution**: Verify USDM JSON has proper study structure with versions and studyDesigns
- Check that all cross-references (IDs) are valid

**Issue**: Missing nodes in visualization
- **Solution**: Verify `defaultConditionId` creates valid chain from entry to exit
- Check that `entryId` references a valid scheduled instance

**Issue**: Conditional links don't appear
- **Solution**: Verify `conditionAssignments` array is populated in decision nodes
- Ensure `conditionTargetId` references valid instances

**Issue**: Timing node missing anchor icon
- **Solution**: Check that timing has `type.code` == "C201358" for Fixed Reference
- Verify timing type object is properly formed

**Issue**: Timeline too wide
- **Solution**: Reduce `horizontalSpacing` constant in JavaScript
- Consider breaking into multiple timelines if appropriate

**Issue**: Overlapping conditional links
- **Solution**: Algorithm automatically staggers heights; may need manual adjustment for extreme cases
- Check that conditional assignments are in reasonable order

### Debug Tips

1. **Check Console**: Open browser developer tools to see JavaScript errors
2. **Inspect Data**: The `timelinesData` variable in generated HTML shows processed data
3. **Validate JSON**: Use USDM4 validator before processing
4. **Enable Error Log**: Check console output for detailed error messages
5. **Simplify Test**: Start with simple linear timeline before adding complexity

## Best Practices

1. **Organize Timelines**: Use separate timelines for different study phases
2. **Label Clearly**: Use descriptive labels for activities and decisions
3. **Condition Naming**: Use clear, distinct names for conditional branches
4. **Timing Types**: Use appropriate CDISC codes for timing relationships
5. **Cross-Reference Integrity**: Ensure all IDs are unique and properly referenced
6. **Testing**: Validate output in multiple browsers
7. **Complexity Management**: Keep timelines reasonably sized (< 50 nodes ideal)

## Integration with Other Tools

```
USDM JSON → to_timeline.py → Study Timeline HTML (flowchart view)
         → to_visit.py → Visit Table HTML (detailed view)
         → to_pj.py → Visit Cards HTML (activity view)
         → to_m11.py → Criteria HTML (regulatory view)
```

Each tool provides a different perspective on the study data:
- **to_timeline.py**: High-level flow and structure
- **to_visit.py**: Detailed visit information
- **to_pj.py**: Activity-focused visualization
- **to_m11.py**: Regulatory document format

## Browser Compatibility

Tested and verified on:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

Requirements:
- SVG rendering
- ES6 JavaScript (arrow functions, const/let, template literals)
- D3.js v7 compatibility
- CSS3 (flexbox, gradients, transforms)

## Performance Considerations

### Timeline Complexity

| Nodes | Rendering | User Experience |
|-------|-----------|-----------------|
| < 20  | Instant   | Excellent |
| 20-50 | < 1s      | Good |
| 50-100| 1-2s      | Acceptable |
| > 100 | > 2s      | May need optimization |

### Optimization Tips

1. **Break Large Timelines**: Split into logical phases
2. **Reduce Orphan Chains**: Simplify conditional branches
3. **Limit Timing Nodes**: Show only critical timing relationships
4. **Simplify Labels**: Keep node labels concise
5. **Test Performance**: Verify rendering time with real data

## License

See LICENSE file for details.

## Support

For issues or questions, please refer to the project repository or contact the development team.

## Related Files

- **to_timeline.py**: Main program file
- **test_data/**: Example USDM JSON files
- **phuse_eu/**: Additional example files and outputs
- **to_visit.py**: Complementary visit details tool
- **to_pj.py**: Activity timeline visualization tool
- **to_m11.py**: Regulatory criteria extraction tool




# OCR Text Extraction from Images (to_text.py)

A lightweight Python program that extracts text from images using Tesseract OCR (Optical Character Recognition) technology. This utility converts images containing text into plain text files.

## Overview

This tool uses the Tesseract OCR engine through the pytesseract Python wrapper to extract text from image files. It's designed to be simple and straightforward - provide an image file and get a text file with the extracted content. Useful for digitizing scanned documents, extracting text from screenshots, or processing image-based data.

## Features

- **Simple Command-Line Interface**: Single command execution with minimal arguments
- **Automatic File Naming**: Output text file automatically named based on input filename
- **Tesseract OCR**: Leverages powerful open-source OCR engine
- **Multiple Format Support**: Works with common image formats (PNG, JPEG, TIFF, BMP, etc.)
- **Preserves Directory Structure**: Outputs text file to same directory as input image
- **Status Reporting**: Displays input and output filenames for confirmation

## Prerequisites

### Required Software

**Tesseract OCR Engine:**

The Tesseract OCR engine must be installed on your system:

**macOS (using Homebrew):**
```bash
brew install tesseract
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tesseract-ocr
```

**Linux (Fedora/RHEL):**
```bash
sudo yum install tesseract
```

**Windows:**
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- Follow installation wizard
- Add Tesseract to system PATH

### Required Python Packages

```bash
pip install Pillow
pip install pytesseract
```

### Dependencies

- **Pillow (PIL)**: Python Imaging Library for image file handling
- **pytesseract**: Python wrapper for Tesseract OCR engine
- **Tesseract**: The actual OCR engine (system-level dependency)

## Usage

### Command Line

Basic usage:

```bash
python3 to_text.py <image_file>
```

### Examples

```bash
# Extract text from a screenshot
python3 to_text.py screenshot.png

# Process a scanned document
python3 to_text.py /path/to/scanned_document.jpg

# Extract text from image in current directory
python3 to_text.py meeting_notes.jpeg

# The output will be automatically created with .txt extension
# Input:  screenshot.png
# Output: screenshot.txt
```

### Program Output

When you run the program, it displays the file paths:

```
Input filename:  /path/to/image.png
Output filename: /path/to/image.txt
```

## Input Format

### Supported Image Formats

The program supports all image formats that PIL/Pillow can open:

- **PNG** (.png) - Recommended for screenshots and digital images
- **JPEG** (.jpg, .jpeg) - Common photograph format
- **TIFF** (.tif, .tiff) - Often used for scanned documents
- **BMP** (.bmp) - Windows bitmap format
- **GIF** (.gif) - Graphics interchange format
- **WebP** (.webp) - Modern web image format

### Image Quality Recommendations

For best OCR results:
- **Resolution**: Minimum 300 DPI for scanned documents
- **Contrast**: High contrast between text and background
- **Clarity**: Clear, non-blurry text
- **Orientation**: Text should be right-side up and not rotated
- **Language**: Tesseract defaults to English (additional languages can be configured)

## Output Format

The program creates a plain text file containing the extracted text:

### File Naming

```
Input:  document.png
Output: document.txt

Input:  /path/to/scan.jpg
Output: /path/to/scan.txt
```

### Output Content

The text file contains:
- All text extracted from the image
- Original line breaks and spacing (as detected by OCR)
- No formatting (plain text only)
- UTF-8 encoding

### Example

**Input Image** (screenshot.png):
```
Meeting Notes
Date: November 26, 2025
Attendees: John, Sarah, Mike
```

**Output Text** (screenshot.txt):
```
Meeting Notes
Date: November 26, 2025
Attendees: John, Sarah, Mike
```

## Technical Details

### Program Structure

```python
def save_text(file_path, data):
    # Saves extracted text to file

if __name__ == "__main__":
    # 1. Parse command-line arguments
    # 2. Determine input/output file paths
    # 3. Open image using PIL
    # 4. Extract text using pytesseract
    # 5. Save text to output file
```

### Processing Flow

1. **Parse Arguments**: Extract filename from command line
2. **Path Processing**: 
   - Split path into directory and filename
   - Extract root filename and extension
   - Construct output filename with .txt extension
3. **Image Loading**: Use PIL to open and load image
4. **OCR Processing**: Call Tesseract via pytesseract to extract text
5. **Save Output**: Write extracted text to .txt file

### File Path Handling

The program intelligently handles file paths:
- Preserves original directory structure
- Works with relative and absolute paths
- Uses current working directory if no path specified
- Automatically creates appropriate .txt filename

## Configuration

### Tesseract Language

To extract text in languages other than English, you can modify the code:

```python
# English (default)
extracted_text = pytesseract.image_to_string(image)

# Spanish
extracted_text = pytesseract.image_to_string(image, lang='spa')

# French
extracted_text = pytesseract.image_to_string(image, lang='fra')

# German
extracted_text = pytesseract.image_to_string(image, lang='deu')

# Multiple languages
extracted_text = pytesseract.image_to_string(image, lang='eng+fra')
```

**Note**: Additional language packs must be installed for Tesseract.

### Tesseract Path (Windows)

If Tesseract is not in your system PATH on Windows, specify the path:

```python
# Add this line before calling image_to_string
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

## Limitations

1. **OCR Accuracy**: 
   - Not 100% accurate, especially with poor image quality
   - May misread similar characters (e.g., '0' vs 'O', '1' vs 'l')
   
2. **Formatting**: 
   - Does not preserve complex formatting (tables, columns, etc.)
   - No font, color, or style information retained
   
3. **Language Support**: 
   - Defaults to English only
   - Additional languages require language pack installation
   
4. **Handwriting**: 
   - Not optimized for handwritten text
   - Best results with printed or digital text
   
5. **Single Image**: 
   - Processes one image at a time
   - No batch processing capability

6. **Simple Output**: 
   - Plain text only (no PDF, Word, or formatted output)

## Troubleshooting

### Common Issues

**Issue**: "pytesseract.pytesseract.TesseractNotFoundError"
- **Cause**: Tesseract OCR is not installed or not in PATH
- **Solution**: 
  ```bash
  # macOS
  brew install tesseract
  
  # Verify installation
  tesseract --version
  ```

**Issue**: Poor OCR accuracy
- **Solution**: 
  - Improve image resolution (use 300+ DPI)
  - Increase image contrast
  - Ensure text is not rotated or skewed
  - Clean up image (remove noise, enhance clarity)
  - Try image preprocessing before OCR

**Issue**: "No such file or directory"
- **Cause**: Image file path is incorrect
- **Solution**: 
  - Verify file exists
  - Use absolute path or ensure correct relative path
  - Check filename spelling and extension

**Issue**: No text extracted (empty output file)
- **Cause**: Image doesn't contain recognizable text
- **Solution**:
  - Check image actually contains text
  - Verify image is not corrupted
  - Try preprocessing image (brightness, contrast, rotation)
  - Check if text language matches Tesseract configuration

**Issue**: ImportError for PIL or pytesseract
- **Solution**: 
  ```bash
  pip install Pillow pytesseract
  ```

### Image Preprocessing Tips

For better results, preprocess images before OCR:

```python
from PIL import Image, ImageEnhance

# Increase contrast
image = Image.open('input.png')
enhancer = ImageEnhance.Contrast(image)
image = enhancer.enhance(2.0)

# Convert to grayscale
image = image.convert('L')

# Increase sharpness
enhancer = ImageEnhance.Sharpness(image)
image = enhancer.enhance(2.0)

# Then perform OCR
extracted_text = pytesseract.image_to_string(image)
```

## Use Cases

### Document Digitization
```bash
# Scan paper document to image, then extract text
python3 to_text.py scanned_contract.pdf.png
```

### Screenshot Text Extraction
```bash
# Extract text from application screenshot
python3 to_text.py app_error_message.png
```

### Data Entry Automation
```bash
# Extract text from form images
python3 to_text.py filled_form.jpg
```

### Archive Processing
```bash
# Convert old image-based documents to searchable text
python3 to_text.py archive_1985_report.tiff
```

## Comparison with Other Tools

| Feature | to_text.py | Adobe Acrobat OCR | Google Cloud Vision | ABBYY FineReader |
|---------|-----------|-------------------|---------------------|------------------|
| Cost | Free | Paid | Paid (after quota) | Paid |
| Offline | Yes | Yes | No | Yes |
| Simplicity | Very Simple | Complex | Complex | Complex |
| Accuracy | Good | Excellent | Excellent | Excellent |
| Format Support | Images | PDF, Images | Images | PDF, Images, Docs |
| Batch Processing | No | Yes | Yes | Yes |

## Best Practices

1. **Use High-Quality Images**: Start with clear, high-resolution images (300+ DPI)
2. **Preprocess When Needed**: Adjust contrast, brightness, or orientation before OCR
3. **Verify Output**: Always review extracted text for accuracy
4. **Batch Multiple Files**: For multiple images, create a shell script to process them
5. **Choose Right Format**: PNG is generally better than JPEG for OCR
6. **Language Configuration**: Configure correct language if text is not in English
7. **Test First**: Try with a small sample before processing large batches

## Batch Processing Example

For processing multiple images, create a shell script:

```bash
#!/bin/bash
# batch_ocr.sh

for img in *.png; do
    echo "Processing $img..."
    python3 to_text.py "$img"
done

echo "Batch processing complete!"
```

Usage:
```bash
chmod +x batch_ocr.sh
./batch_ocr.sh
```

## Integration with Workflows

This tool can be integrated into larger workflows:

```
Image Source → to_text.py → Text File → Further Processing
                                ↓
                          (Text Analysis)
                          (Data Extraction)
                          (Translation)
                          (Keyword Search)
```

## Related Tools

- **to_m11.py**: For processing structured clinical trial documents
- **to_timeline.py**: For visualizing trial timelines
- **to_pj.py**: For visit-based visualizations

## External Resources

- **Tesseract OCR**: https://github.com/tesseract-ocr/tesseract
- **Pytesseract Documentation**: https://pypi.org/project/pytesseract/
- **Pillow Documentation**: https://pillow.readthedocs.io/
- **OCR Best Practices**: https://tesseract-ocr.github.io/tessdoc/ImproveQuality.html

## License

See LICENSE file for details.

## Support

For issues or questions, please refer to the project repository or contact the development team.

## Version History

- **Current**: Initial release
  - Basic OCR text extraction from images
  - Support for common image formats
  - Simple command-line interface
  - Automatic output file naming




# Excel to USDM JSON Converter (from_excel.py)

A Python program that converts USDM-conformant Excel workbooks into USDM JSON format. This utility bridges the gap between Excel-based study definitions and the USDM (Unified Study Definitions Model) standard, enabling transformation of tabular data into structured JSON documents.

## Overview

This tool reads specially formatted Excel workbooks containing clinical study definitions and transforms them into valid USDM JSON files. It leverages the USDM database package to parse Excel sheets, validate data structure, and generate conformant JSON output. The program also produces a CSV file containing any validation errors or warnings encountered during the conversion process.

## Features

- **Excel to JSON Transformation**: Converts USDM-conformant Excel workbooks to USDM JSON
- **USDM Compliance**: Uses official USDM database package for proper data handling
- **Error Tracking**: Generates detailed CSV error report with sheet, row, and column references
- **Version Information**: Displays USDM package version and supported model version
- **Automatic Output Naming**: Creates output files based on input filename
- **Validation**: Built-in validation during conversion process
- **Simple Interface**: Single command execution with minimal configuration

## Prerequisites

### Required Python Packages

```bash
pip install usdm-db
pip install usdm-info
```

### Dependencies

- **usdm_db (USDMDb)**: Core USDM database package for Excel parsing and JSON generation
- **usdm_info**: Provides package and model version information
- **Python 3.7+**: Required for modern Python features

## Usage

### Command Line

Basic usage:

```bash
python3 from_excel.py <excel_file>
```

### Examples

```bash
# Convert Excel workbook to USDM JSON
python3 from_excel.py study_definition.xlsx

# Process file in specific directory
python3 from_excel.py phuse_eu/Excel.xlsx

# The program creates two output files:
# Input:  Excel.xlsx
# Output: Excel.json (USDM JSON data)
# Output: Excel.csv (validation errors/warnings)
```

### Program Output

When you run the program, it displays:

```
Test Utility, using USDM Python Package v1.2.3 supporting USDM version v3.0.0
Output path is: /path/to/directory

JSON: /path/to/directory/Excel.json
CSV: /path/to/directory/Excel.csv
```

## Input Format

### Excel Workbook Structure

The Excel workbook must be USDM-conformant with specific sheet structures. The exact sheet requirements depend on the USDM database package specifications, but typically include:

**Common Sheets:**
- **Study**: Basic study information
- **StudyVersion**: Version details
- **StudyDesign**: Design elements
- **ScheduleTimeline**: Timeline definitions
- **Activities**: Activity definitions
- **Visits**: Visit schedules
- **Eligibility**: Inclusion/exclusion criteria
- **And other USDM entities**

### Excel Format Requirements

- **File Extension**: Must be `.xlsx` (Excel 2007+)
- **Sheet Names**: Must match USDM entity names exactly
- **Column Headers**: Must match USDM attribute names
- **Data Types**: Must conform to USDM specifications
- **References**: Must use valid cross-references between entities

### Example Excel Structure

```
Sheet: Study
-----------------------------------------
| id       | name              | type  |
-----------------------------------------
| study_1  | Phase III Trial   | ...   |

Sheet: StudyDesign
-----------------------------------------
| id       | studyId  | name           |
-----------------------------------------
| design_1 | study_1  | Primary Design |
```

## Output Format

### JSON Output

The program generates a complete USDM JSON file:

```json
{
  "study": {
    "id": "study_1",
    "name": "Phase III Clinical Trial",
    "versions": [
      {
        "id": "version_1",
        "studyDesigns": [
          {
            "id": "design_1",
            "scheduleTimelines": [...]
          }
        ]
      }
    ]
  }
}
```

**Characteristics:**
- Properly indented (2 spaces)
- Valid JSON structure
- Complete USDM schema compliance
- UTF-8 encoding
- All cross-references resolved

### CSV Error Report

The program generates a CSV file containing validation issues:

```csv
sheet,row,column,message,level
Study,2,name,"Required field missing",ERROR
Activities,5,description,"Value exceeds maximum length",WARNING
```

**CSV Columns:**
- **sheet**: Excel sheet name where issue occurred
- **row**: Row number (1-indexed)
- **column**: Column name/identifier
- **message**: Description of the issue
- **level**: Severity level (ERROR, WARNING, INFO)

### File Naming Convention

```
Input:  study_definition.xlsx
Output: study_definition.json
Output: study_definition.csv

Input:  phuse_eu/Excel.xlsx
Output: phuse_eu/Excel.json
Output: phuse_eu/Excel.csv
```

## Technical Details

### Program Structure

```python
def save_as_csv_file(errors, output_path, filename):
    # Saves validation errors to CSV file

def save_as_json_file(raw_json, output_path, filename):
    # Saves formatted JSON to file

if __name__ == "__main__":
    # 1. Parse command-line arguments
    # 2. Display version information
    # 3. Load Excel using USDMDb
    # 4. Convert to JSON
    # 5. Save JSON and error files
```

### Processing Flow

1. **Parse Arguments**: Extract Excel filename from command line
2. **Path Processing**: 
   - Split path into directory and filename components
   - Remove .xlsx extension for output naming
   - Determine output directory
3. **Version Display**: Show USDM package and model versions
4. **Excel Loading**: Initialize USDMDb and load Excel workbook
5. **Conversion**: Transform Excel data to USDM JSON structure
6. **Error Collection**: Gather validation errors during conversion
7. **Output Generation**: 
   - Save formatted JSON file
   - Save error report CSV file

### USDMDb Integration

The program relies on the `USDMDb` class from the usdm_db package:

```python
usdm = USDMDb()
errors = usdm.from_excel(full_filename)  # Returns list of errors
raw_json = usdm.to_json()                # Returns JSON string
```

**Key Methods:**
- **from_excel()**: Parses Excel and returns validation errors
- **to_json()**: Generates USDM JSON representation

## Error Handling

### Validation Errors

The program tracks various types of issues:

**ERROR Level:**
- Required fields missing
- Invalid data types
- Constraint violations
- Invalid cross-references

**WARNING Level:**
- Optional fields missing
- Data quality concerns
- Deprecated attributes
- Format inconsistencies

**INFO Level:**
- Informational messages
- Processing notes
- Conversion details

### Error Report Example

```csv
sheet,row,column,message,level
Study,1,id,"Duplicate ID found",ERROR
StudyDesign,3,studyId,"Referenced study not found",ERROR
Activities,10,duration,"Invalid ISO 8601 duration format",WARNING
Visits,5,notes,"Field is empty",INFO
```

## Limitations

1. **Excel Format**: Only supports .xlsx files (Excel 2007+), not .xls
2. **Schema Compliance**: Excel structure must strictly conform to USDM schema
3. **Single File**: Processes one workbook at a time (no batch processing)
4. **Memory**: Large Excel files may consume significant memory
5. **Validation Only**: Does not fix errors automatically, only reports them
6. **Package Dependency**: Functionality depends on usdm_db package capabilities
7. **Version Compatibility**: Excel structure must match supported USDM model version

## Troubleshooting

### Common Issues

**Issue**: "No module named 'usdm_db'"
- **Cause**: USDM database package not installed
- **Solution**: 
  ```bash
  pip install usdm-db usdm-info
  ```

**Issue**: Many validation errors in CSV
- **Cause**: Excel structure doesn't match USDM schema
- **Solution**:
  - Review CSV error report carefully
  - Check sheet names match USDM entities
  - Verify column headers match USDM attributes
  - Ensure data types are correct
  - Validate cross-references are complete

**Issue**: Empty JSON output
- **Cause**: Critical errors prevented JSON generation
- **Solution**:
  - Review error CSV file
  - Fix all ERROR-level issues
  - Rerun conversion

**Issue**: "File not found" error
- **Cause**: Incorrect file path or missing .xlsx extension
- **Solution**:
  - Verify file exists and path is correct
  - Ensure filename includes .xlsx extension
  - Use absolute path if needed

**Issue**: Invalid JSON structure
- **Cause**: Conversion errors or data inconsistencies
- **Solution**:
  - Check error CSV for structural issues
  - Validate Excel data completeness
  - Ensure all required entities are present

### Debug Tips

1. **Check Versions**: Ensure USDM package version matches your Excel structure
2. **Review CSV First**: Always examine error CSV before using JSON
3. **Incremental Testing**: Start with minimal Excel structure and add complexity
4. **Validate References**: Ensure all ID cross-references are valid
5. **Check Data Types**: Verify dates, durations, and numbers are properly formatted

## Excel Template

### Recommended Approach

1. **Start with Example**: Use provided example workbooks as templates
2. **Add Data Incrementally**: Build up study definition gradually
3. **Validate Frequently**: Run conversion after each major change
4. **Document Structure**: Keep track of entity relationships
5. **Review Errors**: Address validation errors as they appear

### Example Workbooks

The program is designed to work with example files in the repository:

- **phuse_eu/Excel.xlsx**: Comprehensive example workbook
- **test_data/**: Additional test cases

## Use Cases

### Study Protocol Definition
```bash
# Convert protocol definition from Excel to USDM JSON
python3 from_excel.py protocol_definition.xlsx
```

### Data Migration
```bash
# Migrate legacy Excel studies to USDM format
python3 from_excel.py legacy_study.xlsx
```

### Regulatory Submission
```bash
# Prepare USDM JSON for regulatory submission
python3 from_excel.py submission_study.xlsx
```

### System Integration
```bash
# Generate USDM JSON for integration with clinical systems
python3 from_excel.py integrated_study.xlsx
```

## Integration with Other Tools

This tool serves as the starting point for the USDM utility workflow:

```
Excel Workbook → from_excel.py → USDM JSON → Other Tools
                                      ↓
                                 to_m11.py → Criteria HTML
                                      ↓
                              to_timeline.py → Timeline HTML
                                      ↓
                                 to_visit.py → Visit Tables
                                      ↓
                                   to_pj.py → Visit Cards
```

**Workflow Benefits:**
- Single source Excel workbook
- Multiple output formats
- Consistent study definition
- Automated generation of visualizations

## Comparison with Other Approaches

| Feature | from_excel.py | Manual JSON | Direct Database |
|---------|--------------|-------------|-----------------|
| Ease of Use | High | Low | Medium |
| Error Prevention | High (validation) | Low | Medium |
| Collaboration | Excellent (Excel) | Poor | Good |
| Version Control | Good | Excellent | Good |
| Learning Curve | Low | High | Medium |
| Data Entry Speed | Fast | Slow | Medium |

## Best Practices

1. **Validate Early**: Run conversion frequently during Excel development
2. **Address Errors**: Fix ERROR-level issues immediately
3. **Review Warnings**: Consider WARNING-level issues for data quality
4. **Backup Files**: Keep copies of Excel files before major changes
5. **Document Structure**: Maintain documentation of your Excel structure
6. **Use Templates**: Start with validated example workbooks
7. **Test Iterations**: Test conversion with small changes incrementally
8. **Version Management**: Track both Excel and generated JSON versions

## Batch Processing Example

For processing multiple Excel files:

```bash
#!/bin/bash
# batch_convert.sh

for excel in *.xlsx; do
    echo "Converting $excel..."
    python3 from_excel.py "$excel"
    echo "---"
done

echo "Batch conversion complete!"
```

Usage:
```bash
chmod +x batch_convert.sh
./batch_convert.sh
```

## Python Integration Example

Using from_excel.py functionality in Python scripts:

```python
from usdm_db import USDMDb
import json

# Load Excel file
usdm = USDMDb()
errors = usdm.from_excel('study.xlsx')

# Check for critical errors
critical_errors = [e for e in errors if e['level'] == 'ERROR']
if critical_errors:
    print(f"Found {len(critical_errors)} critical errors!")
    for error in critical_errors:
        print(f"  {error['sheet']}, row {error['row']}: {error['message']}")
else:
    # Generate JSON
    raw_json = usdm.to_json()
    json_obj = json.loads(raw_json)
    
    # Process JSON as needed
    print(f"Study: {json_obj['study']['name']}")
```

## Version Compatibility

The program displays version information at runtime:

```
Test Utility, using USDM Python Package v1.2.3 supporting USDM version v3.0.0
```

**Important Notes:**
- Excel structure must match the supported USDM model version
- Package updates may change supported features
- Always check compatibility before conversion
- Refer to usdm_db package documentation for version details

## Related Tools

- **to_m11.py**: Converts USDM JSON to M11 criteria HTML
- **to_timeline.py**: Generates timeline visualizations from USDM JSON
- **to_visit.py**: Creates visit detail tables from USDM JSON
- **to_pj.py**: Produces visit activity card visualizations

## External Resources

- **USDM Specification**: https://www.cdisc.org/standards/usdm
- **CDISC Standards**: https://www.cdisc.org/
- **Python Package Index**: https://pypi.org/ (search for usdm-db)
- **Excel USDM Templates**: Check repository examples in phuse_eu/

## License

See LICENSE file for details.

## Support

For issues or questions, please refer to the project repository or contact the development team.

## Version History

- **Current**: Initial release
  - Excel to USDM JSON conversion
  - Validation error reporting (CSV format)
  - Support for USDM-conformant Excel workbooks
  - Version information display
  - Automatic output file naming

# Image Renamer

A Python utility that renames image files based on their metadata timestamps.

## Overview

This script renames JPG and PNG image files in a directory to a standardized format: `YYYY-MM-DD_<index>.<ext>`, where `<index>` is the chronological order of images taken on the same day.

## Features

- Reads EXIF metadata from images (DateTimeOriginal or DateTime fields)
- Falls back to file modification time if no EXIF data is available
- Groups images by date and assigns chronological indices
- Supports both JPG and PNG formats (case-insensitive)
- Includes dry-run mode to preview changes before applying
- Handles duplicate filenames and edge cases gracefully

## Requirements

- Python 3.6+
- Pillow library

Install Pillow if not already installed:
```bash
pip install Pillow
```

## Usage

### Basic Usage

Rename all images in a directory:
```bash
python rename_images.py /path/to/images
```

### Dry Run Mode

Preview what changes would be made without actually renaming files:
```bash
python rename_images.py /path/to/images --dry-run
```

### Current Directory

Rename images in the current directory:
```bash
python rename_images.py .
```

## Examples

### Input
```
vacation/
├── IMG_1234.jpg  (taken 2024-07-15 10:30:00)
├── IMG_1235.jpg  (taken 2024-07-15 14:20:00)
├── IMG_1236.jpg  (taken 2024-07-16 09:15:00)
└── photo.png     (taken 2024-07-16 16:45:00)
```

### Output
```
vacation/
├── 2024-07-15_1.jpg
├── 2024-07-15_2.jpg
├── 2024-07-16_1.jpg
└── 2024-07-16_2.png
```

## How It Works

1. **Scans Directory**: Finds all `.jpg`, `.jpeg`, and `.png` files (case-insensitive)
2. **Extracts Timestamps**: Reads EXIF metadata (DateTimeOriginal or DateTime)
3. **Fallback**: Uses file modification time if no EXIF data exists
4. **Groups by Date**: Organizes images by the date they were taken
5. **Assigns Indices**: Numbers images chronologically within each day
6. **Renames Files**: Updates filenames to `YYYY-MM-DD_<index>.<ext>` format

## Edge Cases Handled

- **No EXIF Data**: Falls back to file modification timestamp
- **Duplicate Names**: Skips renaming if target filename already exists
- **Already Correct**: Skips files that already have the correct name
- **Missing Timestamps**: Warns and skips files with no available timestamp
- **Mixed Case Extensions**: Handles `.jpg`, `.JPG`, `.jpeg`, `.JPEG`, `.png`, `.PNG`

## Command Line Options

```
usage: rename_images.py [-h] [--dry-run] directory

Rename image files based on metadata timestamps

positional arguments:
  directory   Directory containing image files to rename

optional arguments:
  -h, --help  show this help message and exit
  --dry-run   Show what would be renamed without actually renaming files
```

## Output Messages

The script provides detailed feedback:
- Shows total number of images found
- Reports each rename operation or reason for skipping
- Displays final summary of renamed and skipped files
- Warns about any errors or issues encountered

## Notes

- The script only processes files in the specified directory (non-recursive)
- Original file extensions are preserved
- The script will not overwrite existing files
- Always use `--dry-run` first to preview changes
- EXIF data is preferred over file modification time for accuracy

## Safety

- Use `--dry-run` to preview changes before committing
- The script will never overwrite an existing file
- Files are renamed, not copied, so no disk space is wasted
- Original files are not modified, only renamed
