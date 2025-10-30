import os
import argparse
import json
from uuid import uuid4
from usdm4.api.scheduled_instance import (
    ScheduledActivityInstance,
    ScheduledDecisionInstance,
)
from usdm4.api.wrapper import Wrapper
from usdm4.api.study_design import StudyDesign
from usdm4 import USDM4
from usdm4.builder.builder import Builder
from simple_error_log.errors import Errors

class Timeline:
    def __init__(self, file_path: str, errors: Errors):
        self._errors = errors
        self._usdm = USDM4()
        self._file_path = file_path
        self._builder: Builder = self._usdm.builder(errors)

    def to_html(self):
        """Generate HTML with D3 visualization for all timelines."""
        self._builder.seed(self._file_path)
        wrapper_dict: dict = self._builder._data_store.data
        wrapper_dict['study']['id'] = uuid4()
        wrapper = Wrapper.model_validate(wrapper_dict)
        
        try:
            study_design = wrapper.study.versions[0].studyDesigns[0]
            return self._generate_html(study_design)
        except Exception as e:
            self._errors.exception(
                f"Failed generating HTML page", e
            )
            return ""

    def _generate_html(self, study_design: StudyDesign):
        """Generate complete HTML with embedded D3 visualization."""
        
        # Collect all timeline data
        timelines_data = []
        for timeline in study_design.scheduleTimelines:
            timeline_data = self._process_timeline(timeline)
            if timeline_data:
                timelines_data.append(timeline_data)
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>USDM Timeline Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .timeline-container {{
            background-color: white;
            margin-bottom: 40px;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .timeline-title {{
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }}
        .timeline-condition {{
            font-size: 14px;
            color: #666;
            margin-bottom: 20px;
            font-style: italic;
        }}
        .node {{
            cursor: pointer;
        }}
        .node rect {{
            stroke-width: 2;
        }}
        .node-activity circle {{
            fill: #C0C0C0;
            stroke: #000000;
            stroke-width: 2;
        }}
        .node-decision circle {{
            fill: #FFD700;
            stroke: #DAA520;
        }}
        .node-exit rect {{
            fill: #D3D3D3;
            stroke: #000000;
            rx: 15;
            ry: 15;
        }}
        .node-entry rect {{
            fill: #D3D3D3;
            stroke: #000000;
            rx: 15;
            ry: 15;
        }}
        .node-timing circle {{
            fill: #FFFFFF;
            stroke: #003366;
            stroke-width: 2;
        }}
        .node text {{
            fill: #333;
            font-size: 12px;
            pointer-events: none;
        }}
        .link {{
            fill: none;
            stroke: #999;
            stroke-width: 2;
            marker-end: url(#arrowhead);
        }}
        .link-timing {{
            fill: none;
            stroke: #003366;
            stroke-width: 2;
        }}
        .link-label {{
            font-size: 10px;
            fill: #666;
        }}
        .tooltip {{
            position: absolute;
            background-color: rgba(0, 0, 0, 0.8);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        }}
    </style>
</head>
<body>
    <h1>USDM Timeline Visualization</h1>
    <div id="timelines"></div>
    <div class="tooltip" id="tooltip"></div>
    
    <script>
        const timelinesData = {self._format_timelines_data(timelines_data)};
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        function showTooltip(event, text) {{
            tooltip
                .style("display", "block")
                .style("left", (event.pageX + 10) + "px")
                .style("top", (event.pageY - 10) + "px")
                .html(text);
        }}
        
        function hideTooltip() {{
            tooltip.style("display", "none");
        }}
        
        // Create visualization for each timeline
        timelinesData.forEach((timelineData, index) => {{
            const container = d3.select("#timelines")
                .append("div")
                .attr("class", "timeline-container")
                .attr("id", `timeline-${{index}}`);
            
            container.append("div")
                .attr("class", "timeline-title")
                .text(timelineData.label);
            
            container.append("div")
                .attr("class", "timeline-condition")
                .text("Entry Condition: " + timelineData.entryCondition);
            
            const svgContainer = container.append("div")
                .style("overflow-x", "auto");
            
            renderTimeline(svgContainer, timelineData);
        }});
        
        function renderTimeline(container, data) {{
            const activityNodeRadius = 40;
            const nodeWidth = activityNodeRadius * 2;
            const nodeHeight = activityNodeRadius * 2;
            const timingNodeRadius = 40;
            const horizontalSpacing = 250;
            const verticalSpacing = 150;
            const marginLeft = 50;
            const marginTop = 50;
            const marginRight = 50;
            const marginBottom = 200;
            
            // Calculate positions for nodes in a straight horizontal line
            const nodes = data.nodes.map((node, i) => {{
                // Entry and exit nodes should be half height
                const isEntryOrExit = node.type === 'entry' || node.type === 'exit';
                const height = isEntryOrExit ? nodeHeight / 2 : nodeHeight;
                const yPos = isEntryOrExit ? marginTop + nodeHeight / 4 : marginTop;
                
                return {{
                    ...node,
                    x: marginLeft + i * horizontalSpacing,
                    y: yPos,
                    width: nodeWidth,
                    height: height
                }};
            }});
            
            // Create a map of node IDs to their positions for timing lookups
            const nodeMap = {{}};
            nodes.forEach(node => {{
                nodeMap[node.id] = node;
            }});
            
            // Process timing nodes and position them below the main timeline
            const timingNodes = [];
            if (data.timings) {{
                data.timings.forEach((timing, idx) => {{
                    const fromNode = nodeMap[timing.relativeFromScheduledInstanceId];
                    const toNode = nodeMap[timing.relativeToScheduledInstanceId];
                    
                    if (fromNode && toNode) {{
                        // Position timing node directly under the from node
                        const timingX = fromNode.x + fromNode.width/2;
                        const timingY = marginTop + nodeHeight + verticalSpacing;
                        
                        timingNodes.push({{
                            ...timing,
                            x: timingX,
                            y: timingY,
                            radius: timingNodeRadius,
                            fromNode: fromNode,
                            toNode: toNode
                        }});
                    }}
                }});
            }}
            
            // Calculate SVG dimensions
            const svgWidth = nodes.length * horizontalSpacing + marginLeft + marginRight;
            const svgHeight = marginTop + nodeHeight + verticalSpacing + timingNodeRadius * 2 + marginBottom;
            
            const svg = container.append("svg")
                .attr("width", svgWidth)
                .attr("height", svgHeight);
            
            // Define arrowhead markers
            const defs = svg.append("defs");
            
            // Gray arrowhead for regular links
            defs.append("marker")
                .attr("id", `arrowhead-${{data.id}}`)
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 8)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "#999");
            
            // Blue arrowhead for timing links
            defs.append("marker")
                .attr("id", `arrowhead-timing-${{data.id}}`)
                .attr("viewBox", "0 -5 10 10")
                .attr("refX", 8)
                .attr("refY", 0)
                .attr("markerWidth", 6)
                .attr("markerHeight", 6)
                .attr("orient", "auto")
                .append("path")
                .attr("d", "M0,-5L10,0L0,5")
                .attr("fill", "#003366");
            
            // Create links
            const links = [];
            nodes.forEach((node, i) => {{
                if (i < nodes.length - 1) {{
                    links.push({{
                        source: node,
                        target: nodes[i + 1],
                        label: node.linkLabel || ""
                    }});
                }}
            }});
            
            // Draw links
            const linkGroup = svg.append("g").attr("class", "links");
            
            linkGroup.selectAll("path")
                .data(links)
                .join("path")
                .attr("class", "link")
                .attr("d", d => {{
                    // Calculate connection points based on node type
                    let sourceX, sourceY, targetX, targetY;
                    
                    // Source node
                    if (d.source.type === 'activity') {{
                        // For circles, connect from the right edge
                        const radius = Math.min(d.source.width, d.source.height) / 2;
                        sourceX = d.source.x + d.source.width / 2 + radius;
                        sourceY = d.source.y + d.source.height / 2;
                    }} else {{
                        // For rectangles, connect from the right edge
                        sourceX = d.source.x + d.source.width;
                        sourceY = d.source.y + d.source.height / 2;
                    }}
                    
                    // Target node
                    if (d.target.type === 'activity') {{
                        // For circles, connect to the left edge
                        const radius = Math.min(d.target.width, d.target.height) / 2;
                        targetX = d.target.x + d.target.width / 2 - radius;
                        targetY = d.target.y + d.target.height / 2;
                    }} else {{
                        // For rectangles, connect to the left edge
                        targetX = d.target.x;
                        targetY = d.target.y + d.target.height / 2;
                    }}
                    
                    return `M${{sourceX}},${{sourceY}} L${{targetX}},${{targetY}}`;
                }})
                .attr("marker-end", `url(#arrowhead-${{data.id}})`);
            
            // Draw link labels
            linkGroup.selectAll("text")
                .data(links)
                .join("text")
                .attr("class", "link-label")
                .attr("x", d => (d.source.x + d.source.width + d.target.x) / 2)
                .attr("y", d => (d.source.y + d.target.y) / 2 - 5)
                .attr("text-anchor", "middle")
                .text(d => d.label);
            
            // Draw nodes
            const nodeGroup = svg.append("g").attr("class", "nodes");
            
            const nodeElements = nodeGroup.selectAll("g")
                .data(nodes)
                .join("g")
                .attr("class", d => `node node-${{d.type}}`)
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`)
                .on("mouseover", (event, d) => {{
                    const tooltipText = `
                        <strong>${{d.label}}</strong><br/>
                        Type: ${{d.type}}<br/>
                        ${{d.description ? 'Description: ' + d.description : ''}}
                    `;
                    showTooltip(event, tooltipText);
                }})
                .on("mouseout", hideTooltip);
            
            // Add shapes based on node type
            nodeElements.each(function(d) {{
                const node = d3.select(this);
                
                if (d.type === 'activity') {{
                    // Activity nodes are circles
                    const radius = Math.min(d.width, d.height) / 2;
                    node.append("circle")
                        .attr("cx", d.width / 2)
                        .attr("cy", d.height / 2)
                        .attr("r", radius);
                }} else {{
                    // Entry, exit, and decision nodes are rectangles
                    node.append("rect")
                        .attr("width", d.width)
                        .attr("height", d.height);
                }}
            }});
            
            // Add text labels (with wrapping)
            nodeElements.each(function(d) {{
                const node = d3.select(this);
                const words = d.label.split(/\\s+/);
                const lineHeight = 14;
                const maxWidth = d.width - 10;
                
                let line = [];
                let lineNumber = 0;
                const text = node.append("text")
                    .attr("x", d.width / 2)
                    .attr("y", d.height / 2)
                    .attr("text-anchor", "middle")
                    .attr("dominant-baseline", "central");
                
                words.forEach((word, i) => {{
                    line.push(word);
                    const testLine = line.join(" ");
                    const tspan = text.append("tspan")
                        .attr("x", d.width / 2)
                        .attr("dy", i === 0 ? 0 : lineHeight)
                        .text(testLine);
                    
                    if (tspan.node().getComputedTextLength() > maxWidth && line.length > 1) {{
                        line.pop();
                        tspan.text(line.join(" "));
                        line = [word];
                        text.append("tspan")
                            .attr("x", d.width / 2)
                            .attr("dy", lineHeight)
                            .text(word);
                    }}
                }});
                
                // Center the text vertically
                const bbox = text.node().getBBox();
                const offset = (d.height - bbox.height) / 2 - bbox.y;
                text.attr("transform", `translate(0, ${{offset}})`);
            }});
            
            // Draw timing links with arrows and labels
            const timingLinkGroup = svg.append("g").attr("class", "timing-links");
            
            timingNodes.forEach(timing => {{
                // Line from "from" node to timing node (with arrow pointing UP at activity node)
                const fromX = timing.fromNode.x + timing.fromNode.width / 2;
                const fromY = timing.fromNode.y + timing.fromNode.height;
                const fromPath = timingLinkGroup.append("path")
                    .attr("class", "link-timing")
                    .attr("d", `M${{timing.x}},${{timing.y}} L${{fromX}},${{fromY}}`)
                    .attr("marker-end", `url(#arrowhead-timing-${{data.id}})`);
                
                // Label for "from" link
                const fromMidX = (timing.x + fromX) / 2;
                const fromMidY = (timing.y + fromY) / 2;
                timingLinkGroup.append("text")
                    .attr("class", "link-label")
                    .attr("x", fromMidX - 10)
                    .attr("y", fromMidY)
                    .attr("text-anchor", "end")
                    .style("fill", "#003366")
                    .style("font-size", "10px")
                    .style("font-weight", "bold")
                    .text("from");
                
                // Line from timing node to "to" node (with arrow pointing UP at activity node)
                const toX = timing.toNode.x + timing.toNode.width / 2;
                const toY = timing.toNode.y + timing.toNode.height;
                const toPath = timingLinkGroup.append("path")
                    .attr("class", "link-timing")
                    .attr("d", `M${{timing.x}},${{timing.y}} L${{toX}},${{toY}}`)
                    .attr("marker-end", `url(#arrowhead-timing-${{data.id}})`);
                
                // Label for "to" link
                const toMidX = (timing.x + toX) / 2;
                const toMidY = (timing.y + toY) / 2;
                timingLinkGroup.append("text")
                    .attr("class", "link-label")
                    .attr("x", toMidX + 10)
                    .attr("y", toMidY)
                    .attr("text-anchor", "start")
                    .style("fill", "#003366")
                    .style("font-size", "10px")
                    .style("font-weight", "bold")
                    .text("to");
            }});
            
            // Draw timing nodes
            const timingNodeGroup = svg.append("g").attr("class", "timing-nodes");
            
            const timingElements = timingNodeGroup.selectAll("g")
                .data(timingNodes)
                .join("g")
                .attr("class", "node node-timing")
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`)
                .on("mouseover", (event, d) => {{
                    const tooltipText = `
                        <strong>${{d.label}}</strong><br/>
                        Type: ${{d.type}}<br/>
                        Value: ${{d.valueLabel}}<br/>
                        ${{d.windowLabel ? 'Window: ' + d.windowLabel : ''}}
                    `;
                    showTooltip(event, tooltipText);
                }})
                .on("mouseout", hideTooltip);
            
            // Add circles for timing nodes
            timingElements.append("circle")
                .attr("r", d => d.radius);
            
            // Add text labels or anchor icon for timing nodes
            timingElements.each(function(d) {{
                const node = d3.select(this);
                
                if (d.isAnchor) {{
                    // Draw ship's anchor icon matching the reference design
                    const anchorGroup = node.append("g")
                        .attr("transform", "scale(1.4)");
                    
                    // Ring at top
                    anchorGroup.append("circle")
                        .attr("cx", 0)
                        .attr("cy", -18)
                        .attr("r", 5)
                        .attr("fill", "none")
                        .attr("stroke", "#003366")
                        .attr("stroke-width", 3);
                    
                    // Vertical shaft
                    anchorGroup.append("line")
                        .attr("x1", 0)
                        .attr("y1", -13)
                        .attr("x2", 0)
                        .attr("y2", 18)
                        .attr("stroke", "#003366")
                        .attr("stroke-width", 3)
                        .attr("stroke-linecap", "round");
                    
                    // Horizontal crossbar (stock)
                    anchorGroup.append("rect")
                        .attr("x", -12)
                        .attr("y", -3)
                        .attr("width", 24)
                        .attr("height", 5)
                        .attr("rx", 2.5)
                        .attr("ry", 2.5)
                        .attr("fill", "#003366");
                    
                    // Left fluke
                    const leftFlukePath = "M 0,18 Q -8,18 -15,12 Q -18,9 -16,5 L -12,8 Q -10,10 -8,11 L 0,18";
                    anchorGroup.append("path")
                        .attr("d", leftFlukePath)
                        .attr("fill", "#003366");
                    
                    // Right fluke
                    const rightFlukePath = "M 0,18 Q 8,18 15,12 Q 18,9 16,5 L 12,8 Q 10,10 8,11 L 0,18";
                    anchorGroup.append("path")
                        .attr("d", rightFlukePath)
                        .attr("fill", "#003366");
                }} else {{
                    // Draw text for non-anchor nodes
                    const text = node.append("text")
                        .attr("text-anchor", "middle")
                        .attr("dominant-baseline", "central")
                        .style("font-size", "10px");
                    
                    // Create multi-line text
                    const lines = [d.label, d.type, d.valueLabel];
                    if (d.windowLabel) {{
                        lines.push(d.windowLabel);
                    }}
                    
                    lines.forEach((line, i) => {{
                        text.append("tspan")
                            .attr("x", 0)
                            .attr("dy", i === 0 ? 0 : 12)
                            .text(line);
                    }});
                    
                    // Center the text vertically
                    const bbox = text.node().getBBox();
                    const offset = -bbox.height / 2 - bbox.y;
                    text.attr("transform", `translate(0, ${{offset}})`);
                }}
            }});
        }}
    </script>
</body>
</html>"""
        return html

    def _process_timeline(self, timeline):
        """Process a timeline and extract node data."""
        try:
            nodes = []
            
            # Get the entry instance
            instance = self._get_cross_reference(timeline.entryId)
            if not instance:
                return None
            
            # Collect all instances in order
            while instance:
                node_data = {
                    'id': instance['id'],
                    'label': instance.get('label', instance.get('name', 'Unknown')),
                    'description': instance.get('description', ''),
                    'type': 'activity' if instance['instanceType'] == ScheduledActivityInstance.__name__ else ScheduledDecisionInstance.__name__
                }
                
                # Determine if this is the first or last node
                if len(nodes) == 0:
                    node_data['type'] = 'entry'
                
                nodes.append(node_data)
                
                # Get next instance
                next_id = instance.get('defaultConditionId')
                if next_id:
                    instance = self._get_cross_reference(next_id)
                else:
                    # This is the last instance, check for exit
                    exit_id = instance.get('timelineExitId')
                    if exit_id:
                        exit_obj = self._get_cross_reference(exit_id)
                        if exit_obj:
                            nodes.append({
                                'id': exit_obj['id'],
                                'label': 'Exit',
                                'description': 'Timeline Exit',
                                'type': 'exit'
                            })
                    instance = None
            
            # Process timings
            timings = []
            for timing in timeline.timings:
                # Check if this is an anchor node (Fixed Reference type)
                is_anchor = timing.type and timing.type.code == 'C201358'
                
                timing_data = {
                    'id': timing.id,
                    'label': timing.label,
                    'type': timing.type.decode if timing.type else 'Unknown',
                    'typeCode': timing.type.code if timing.type else '',
                    'isAnchor': is_anchor,
                    'value': timing.value,
                    'valueLabel': timing.valueLabel if timing.valueLabel else timing.value,
                    'windowLower': timing.windowLower if timing.windowLower else '',
                    'windowUpper': timing.windowUpper if timing.windowUpper else '',
                    'windowLabel': timing.windowLabel if timing.windowLabel else '',
                    'relativeFromScheduledInstanceId': timing.relativeFromScheduledInstanceId,
                    'relativeToScheduledInstanceId': timing.relativeToScheduledInstanceId
                }
                timings.append(timing_data)
            
            return {
                'id': timeline.id,
                'label': timeline.label,
                'entryCondition': timeline.entryCondition,
                'nodes': nodes,
                'timings': timings
            }
        except Exception as e:
            self._errors.exception(
                f"Failed processing timeline {timeline.label}", e
            )
            return None

    def _format_timelines_data(self, timelines_data):
        """Format timeline data as JSON for embedding in HTML."""
        return json.dumps(timelines_data)

    def _get_cross_reference(self, id):
        """Get cross reference by ID."""
        return self._builder._data_store.instance_by_id(id)


def save_html(file_path, result):
    """Save HTML content to file."""
    with open(file_path, "w") as f:
        f.write(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog='USDM D3 Timeline Program',
        description='Display USDM timelines using D3 in a horizontal layout',
        epilog='Creates a single HTML file with all timelines'
    )
    parser.add_argument('filename', help="The name of the USDM JSON file.") 
    args = parser.parse_args()
    filename = args.filename
    
    input_path, tail = os.path.split(filename)
    root_filename = tail.replace(".json", "")
    full_filename = filename
    output_path = input_path if input_path else "."
    full_output_filename = os.path.join(output_path, f"{root_filename}_timeline.html")

    print("")
    print(f"Input file: {full_filename}")
    print(f"Output path: {output_path}")
    print(f"Output file: {full_output_filename}")
    print("")
    
    errors = Errors()
    timeline = Timeline(full_filename, errors)
    html = timeline.to_html()
    
    if errors.error_count() > 0:
        print(f"Errors: {errors.dump(0)}")
    else:
        save_html(full_output_filename, html)
        print(f"Successfully created: {full_output_filename}")
        print("")
        print("Open this file in your browser to view the timeline visualization.")
