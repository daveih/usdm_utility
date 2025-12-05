#!/usr/bin/env python3
"""
Generate expanded timeline visualization from JSON data.
Creates an HTML page with a D3.js vertical timeline displaying nodes with hover details.
"""

import json
import sys
from pathlib import Path


def load_json_data(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_html(data, output_path='expanded_timeline.html'):
    """
    Generate HTML with D3.js vertical timeline visualization.
    
    Args:
        data: Dictionary containing 'nodes' list
        output_path: Output HTML file path
    """
    
    # Convert Python dict to JSON string for embedding in JavaScript
    json_data = json.dumps(data, indent=2)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Expanded Timeline Visualization</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- D3.js -->
    <script src="https://d3js.org/d3.v7.min.js"></script>
    
    <style>
        body {{
            background-color: #f8f9fa;
            padding: 20px 0;
        }}
        
        .page-header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 40px 0;
            margin-bottom: 40px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .timeline-container {{
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .timeline-svg {{
            width: 100%;
            overflow: visible;
        }}
        
        .timeline-line {{
            stroke: #3498db;
            stroke-width: 4;
            fill: none;
        }}
        
        .timeline-node {{
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .timeline-node:hover .node-circle {{
            transform: scale(1.3);
        }}
        
        .node-circle {{
            fill: #3498db;
            stroke: #2c3e50;
            stroke-width: 2;
            transition: all 0.3s ease;
        }}
        
        .node-circle.has-encounter {{
            fill: #e74c3c;
        }}
        
        .node-label {{
            font-size: 13px;
            font-weight: 600;
            fill: #2c3e50;
        }}
        
        .node-time {{
            font-size: 11px;
            fill: #7f8c8d;
            font-family: 'Courier New', monospace;
        }}
        
        .tooltip {{
            position: fixed;
            background-color: white;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px 18px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
            max-width: 400px;
            z-index: 1000;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
        
        .tooltip-title {{
            font-weight: 700;
            font-size: 15px;
            color: #2c3e50;
            margin-bottom: 10px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 6px;
        }}
        
        .tooltip-time {{
            font-size: 12px;
            color: #7f8c8d;
            margin-bottom: 10px;
            font-family: 'Courier New', monospace;
        }}
        
        .tooltip-encounter {{
            font-size: 13px;
            color: #e74c3c;
            font-weight: 600;
            margin-bottom: 10px;
            padding: 6px 10px;
            background-color: #fdf2f2;
            border-radius: 4px;
        }}
        
        .tooltip-section {{
            font-size: 12px;
            color: #34495e;
            margin-top: 8px;
        }}
        
        .tooltip-section-title {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .activity-item {{
            padding: 4px 0 4px 15px;
            border-left: 2px solid #3498db;
            margin: 4px 0;
            font-size: 11px;
        }}
        
        .activity-parent {{
            font-size: 10px;
            color: #95a5a6;
            font-style: italic;
        }}
        
        .procedure-item {{
            font-size: 10px;
            color: #7f8c8d;
            padding-left: 10px;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 13px;
            color: #2c3e50;
        }}
        
        .legend-dot {{
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid #2c3e50;
        }}
        
        .legend-dot.regular {{
            background-color: #3498db;
        }}
        
        .legend-dot.encounter {{
            background-color: #e74c3c;
        }}
        
        .scroll-indicator {{
            text-align: center;
            color: #95a5a6;
            font-size: 12px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <!-- Page Header -->
    <div class="page-header">
        <div class="container">
            <h1 class="display-4 mb-2">Expanded Timeline</h1>
            <p class="lead mb-0">Vertical timeline visualization of study events</p>
        </div>
    </div>
    
    <!-- Main Content -->
    <div class="container">
        <!-- Legend -->
        <div class="legend">
            <div class="legend-item">
                <div class="legend-dot regular"></div>
                <span>Standard Node</span>
            </div>
            <div class="legend-item">
                <div class="legend-dot encounter"></div>
                <span>Encounter Node</span>
            </div>
        </div>
        
        <div class="scroll-indicator">Hover over nodes to see details</div>
        
        <!-- Timeline Container -->
        <div class="timeline-container" id="timeline-container">
            <svg class="timeline-svg" id="timeline-svg"></svg>
        </div>
    </div>
    
    <!-- Global Tooltip -->
    <div class="tooltip" id="tooltip"></div>
    
    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Data from Python
        const data = {json_data};
        
        // Configuration
        const config = {{
            nodeRadius: 10,
            nodeSpacingY: 80,
            lineX: 120,
            labelOffsetX: 25,
            timeOffsetX: -20,
            margin: {{ top: 40, right: 40, bottom: 40, left: 40 }}
        }};
        
        // Get nodes data
        const nodes = data.nodes || [];
        
        // Global tooltip
        const tooltip = d3.select("#tooltip");
        
        // Create vertical timeline
        function createTimeline() {{
            const container = d3.select("#timeline-container");
            const svg = d3.select("#timeline-svg");
            
            if (nodes.length === 0) {{
                container.html('<div class="text-center text-muted p-5">No nodes to display</div>');
                return;
            }}
            
            // Calculate SVG dimensions
            const svgHeight = config.margin.top + (nodes.length * config.nodeSpacingY) + config.margin.bottom;
            const svgWidth = 800;
            
            svg.attr("viewBox", `0 0 ${{svgWidth}} ${{svgHeight}}`)
               .attr("height", svgHeight);
            
            const g = svg.append("g")
                .attr("transform", `translate(${{config.margin.left}},${{config.margin.top}})`);
            
            // Create node positions
            const nodePositions = nodes.map((node, index) => ({{
                ...node,
                x: config.lineX,
                y: index * config.nodeSpacingY,
                index: index
            }}));
            
            // Draw the timeline line
            const lineGenerator = d3.line()
                .x(d => d.x)
                .y(d => d.y)
                .curve(d3.curveMonotoneY);
            
            g.append("path")
                .datum(nodePositions)
                .attr("class", "timeline-line")
                .attr("d", lineGenerator);
            
            // Create node groups
            const nodeGroups = g.selectAll(".timeline-node")
                .data(nodePositions)
                .enter()
                .append("g")
                .attr("class", "timeline-node")
                .attr("transform", d => `translate(${{d.x}},${{d.y}})`)
                .on("mouseover", function(event, d) {{
                    showTooltip(event, d);
                }})
                .on("mousemove", function(event, d) {{
                    moveTooltip(event);
                }})
                .on("mouseout", function() {{
                    hideTooltip();
                }});
            
            // Add circles
            nodeGroups.append("circle")
                .attr("class", d => `node-circle ${{d.encounter ? 'has-encounter' : ''}}`)
                .attr("r", config.nodeRadius)
                .attr("cx", 0)
                .attr("cy", 0);
            
            // Add labels (right side)
            nodeGroups.append("text")
                .attr("class", "node-label")
                .attr("x", config.labelOffsetX)
                .attr("y", 0)
                .attr("dy", "0.35em")
                .text(d => d.label || 'Unnamed');
            
            // Add time (left side)
            nodeGroups.append("text")
                .attr("class", "node-time")
                .attr("x", config.timeOffsetX)
                .attr("y", 0)
                .attr("dy", "0.35em")
                .attr("text-anchor", "end")
                .text(d => d.time || '');
        }}
        
        // Show tooltip
        function showTooltip(event, node) {{
            let html = `<div class="tooltip-title">${{node.label || 'Unnamed'}}</div>`;
            html += `<div class="tooltip-time">Time: ${{node.time || 'N/A'}}</div>`;
            
            // Encounter info
            if (node.encounter) {{
                html += `<div class="tooltip-encounter">Encounter: ${{node.encounter}}</div>`;
            }}
            
            // Activities info
            const activities = node.activities?.items || [];
            if (activities.length > 0) {{
                html += '<div class="tooltip-section">';
                html += `<div class="tooltip-section-title">Activities (${{activities.length}}):</div>`;
                
                // Group activities by parent
                const groupedActivities = {{}};
                activities.forEach(activity => {{
                    const parent = activity.parent || 'Other';
                    if (!groupedActivities[parent]) {{
                        groupedActivities[parent] = [];
                    }}
                    groupedActivities[parent].push(activity);
                }});
                
                // Display grouped activities
                Object.keys(groupedActivities).forEach(parent => {{
                    if (parent !== 'Other') {{
                        html += `<div class="activity-parent">${{parent}}</div>`;
                    }}
                    groupedActivities[parent].forEach(activity => {{
                        html += `<div class="activity-item">${{activity.label || 'Unnamed activity'}}`;
                        
                        // Show procedures if any
                        const procedures = activity.procedures?.filter(p => p && p.trim() !== '') || [];
                        if (procedures.length > 0) {{
                            procedures.forEach(proc => {{
                                html += `<div class="procedure-item">→ ${{proc}}</div>`;
                            }});
                        }}
                        html += '</div>';
                    }});
                }});
                
                html += '</div>';
            }} else {{
                html += '<div class="tooltip-section"><em>No activities</em></div>';
            }}
            
            tooltip.html(html)
                .classed("visible", true);
            
            moveTooltip(event);
        }}
        
        // Move tooltip with mouse
        function moveTooltip(event) {{
            const tooltipNode = tooltip.node();
            const tooltipRect = tooltipNode.getBoundingClientRect();
            const windowWidth = window.innerWidth;
            const windowHeight = window.innerHeight;
            
            let left = event.clientX + 15;
            let top = event.clientY - 15;
            
            // Prevent tooltip from going off screen right
            if (left + tooltipRect.width > windowWidth - 10) {{
                left = event.clientX - tooltipRect.width - 15;
            }}
            
            // Prevent tooltip from going off screen bottom
            if (top + tooltipRect.height > windowHeight - 10) {{
                top = windowHeight - tooltipRect.height - 10;
            }}
            
            // Prevent tooltip from going off screen top
            if (top < 10) {{
                top = 10;
            }}
            
            tooltip
                .style("left", left + "px")
                .style("top", top + "px");
        }}
        
        // Hide tooltip
        function hideTooltip() {{
            tooltip.classed("visible", false);
        }}
        
        // Initialize
        createTimeline();
        
        console.log(`Created vertical timeline with ${{nodes.length}} nodes`);
    </script>
</body>
</html>"""
    
    # Write HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Generated expanded timeline visualization: {output_path}")
    return output_path


def main():
    """Main function to generate timeline from command line."""
    if len(sys.argv) < 2:
        print("Usage: python to_expanded.py <json_file> [output_file]")
        print("\nExample:")
        print("  python to_expanded.py expander.json")
        print("  python to_expanded.py data.json expanded_output.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'expanded_timeline.html'
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        data = load_json_data(input_file)
        generate_html(data, output_file)
        print(f"\nVisualization generated successfully!")
        print(f"Open {output_file} in a web browser to view the expanded timeline.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
