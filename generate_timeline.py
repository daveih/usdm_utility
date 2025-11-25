#!/usr/bin/env python3
"""
Generate a serpentine timeline visualization from JSON data.
Creates an HTML page with D3.js visualization suitable for a Jinja2 application.
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def load_json_data(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_html(data, output_path='timeline_visualization.html'):
    """
    Generate HTML with D3.js serpentine timeline visualization.
    
    Args:
        data: Dictionary containing 'visits' list
        output_path: Output HTML file path
    """
    
    # Convert Python dict to JSON string for embedding in JavaScript
    json_data = json.dumps(data, indent=2)
    
    html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clinical Trial Timeline - Serpentine Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
        }}
        
        #timeline {{
            width: 100%;
            overflow-x: auto;
        }}
        
        .visit-node {{
            cursor: pointer;
        }}
        
        .visit-circle {{
            fill: #3498db;
            stroke: #2980b9;
            stroke-width: 2;
            transition: all 0.3s;
        }}
        
        .visit-circle:hover {{
            fill: #2980b9;
            r: 12;
        }}
        
        .visit-label {{
            fill: #2c3e50;
            font-size: 12px;
            font-weight: 600;
            text-anchor: middle;
            pointer-events: none;
        }}
        
        .timeline-path {{
            fill: none;
            stroke: #bdc3c7;
            stroke-width: 3;
            stroke-dasharray: 5, 5;
        }}
        
        .activity-list {{
            background-color: #ecf0f1;
            border-left: 4px solid #3498db;
            padding: 10px;
            margin: 5px 0;
            border-radius: 4px;
        }}
        
        .activity-title {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .activity-procedures {{
            font-size: 12px;
            color: #7f8c8d;
            margin-left: 15px;
        }}
        
        .tooltip {{
            position: absolute;
            background-color: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 400px;
            max-height: 500px;
            overflow-y: auto;
            z-index: 1000;
        }}
        
        .tooltip.visible {{
            opacity: 1;
        }}
        
        .tooltip-title {{
            font-weight: bold;
            font-size: 16px;
            color: #2c3e50;
            margin-bottom: 10px;
            border-bottom: 2px solid #3498db;
            padding-bottom: 5px;
        }}
        
        .tooltip-info {{
            font-size: 13px;
            color: #7f8c8d;
            margin-bottom: 10px;
        }}
        
        .info-label {{
            font-weight: 600;
            color: #34495e;
        }}
        
        .legend {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 4px;
        }}
        
        .legend-item {{
            display: inline-block;
            margin-right: 20px;
        }}
        
        .legend-circle {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 5px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Clinical Trial Timeline</h1>
        <p class="subtitle">Serpentine visualization of study visits and activities</p>
        
        <div id="timeline"></div>
        
        <div class="legend">
            <div class="legend-item">
                <span class="legend-circle" style="background-color: #3498db;"></span>
                <span>Study Visit</span>
            </div>
            <div class="legend-item">
                <span>Hover over visits to see activities and details</span>
            </div>
        </div>
    </div>
    
    <div class="tooltip" id="tooltip"></div>

    <script>
        // Data from Python
        const data = {json_data};
        
        // Configuration
        const config = {{
            width: 1200,
            margin: {{ top: 50, right: 50, bottom: 50, left: 50 }},
            nodeRadius: 8,
            rowHeight: 120,
            nodeSpacing: 100,
            nodesPerRow: 10
        }};
        
        // Process visits data
        const visits = data.visits || [];
        const validVisits = visits.filter(v => v.title && v.title.trim() !== '');
        
        // Calculate serpentine layout
        function calculateSerpentineLayout(visits, config) {{
            const positions = [];
            const nodesPerRow = config.nodesPerRow;
            
            visits.forEach((visit, index) => {{
                const row = Math.floor(index / nodesPerRow);
                const col = index % nodesPerRow;
                
                // Alternate direction for serpentine effect
                const x = row % 2 === 0 
                    ? col * config.nodeSpacing 
                    : (nodesPerRow - 1 - col) * config.nodeSpacing;
                const y = row * config.rowHeight;
                
                positions.push({{ x, y, visit, index }});
            }});
            
            return positions;
        }}
        
        // Create serpentine path
        function createSerpentinePath(positions, config) {{
            if (positions.length === 0) return '';
            
            let path = `M ${{positions[0].x}},${{positions[0].y}}`;
            
            for (let i = 1; i < positions.length; i++) {{
                const prev = positions[i - 1];
                const curr = positions[i];
                
                // Check if we're at a row transition
                const prevRow = Math.floor(prev.index / config.nodesPerRow);
                const currRow = Math.floor(curr.index / config.nodesPerRow);
                
                if (prevRow !== currRow) {{
                    // Create a curved transition
                    const midY = (prev.y + curr.y) / 2;
                    path += ` C ${{prev.x}},${{midY}} ${{curr.x}},${{midY}} ${{curr.x}},${{curr.y}}`;
                }} else {{
                    // Straight line within row
                    path += ` L ${{curr.x}},${{curr.y}}`;
                }}
            }}
            
            return path;
        }}
        
        // Calculate positions
        const positions = calculateSerpentineLayout(validVisits, config);
        
        // Calculate SVG dimensions
        const maxX = Math.max(...positions.map(p => p.x), 0);
        const maxY = Math.max(...positions.map(p => p.y), 0);
        const svgWidth = maxX + config.margin.left + config.margin.right + 100;
        const svgHeight = maxY + config.margin.top + config.margin.bottom + 100;
        
        // Create SVG
        const svg = d3.select("#timeline")
            .append("svg")
            .attr("width", svgWidth)
            .attr("height", svgHeight);
        
        const g = svg.append("g")
            .attr("transform", `translate(${{config.margin.left}},${{config.margin.top}})`);
        
        // Draw serpentine path
        g.append("path")
            .attr("class", "timeline-path")
            .attr("d", createSerpentinePath(positions, config));
        
        // Tooltip
        const tooltip = d3.select("#tooltip");
        
        // Create visit nodes
        const nodes = g.selectAll(".visit-node")
            .data(positions)
            .enter()
            .append("g")
            .attr("class", "visit-node")
            .attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        
        // Add circles
        nodes.append("circle")
            .attr("class", "visit-circle")
            .attr("r", config.nodeRadius)
            .on("mouseover", function(event, d) {{
                showTooltip(event, d.visit);
            }})
            .on("mouseout", function() {{
                hideTooltip();
            }});
        
        // Add labels
        nodes.append("text")
            .attr("class", "visit-label")
            .attr("y", -15)
            .text(d => d.visit.title || "");
        
        // Add visit type/timing below
        nodes.append("text")
            .attr("class", "visit-label")
            .attr("y", 25)
            .style("font-size", "10px")
            .style("fill", "#7f8c8d")
            .text(d => d.visit.type || "");
        
        // Tooltip functions
        function showTooltip(event, visit) {{
            const activities = visit.activities || [];
            
            let html = `
                <div class="tooltip-title">${{visit.title || 'Visit'}}</div>
                <div class="tooltip-info">
                    <div><span class="info-label">Type:</span> ${{visit.type || 'N/A'}}</div>
                    <div><span class="info-label">Duration:</span> ${{visit.duration || 'N/A'}}</div>
                    ${{visit.timing ? `<div><span class="info-label">Timing:</span> ${{visit.timing}}</div>` : ''}}
                    ${{visit.notes ? `<div><span class="info-label">Notes:</span> ${{visit.notes}}</div>` : ''}}
                </div>
            `;
            
            if (activities.length > 0) {{
                html += '<div style="margin-top: 10px;"><strong>Activities:</strong></div>';
                activities.forEach(activity => {{
                    if (activity.title) {{
                        html += `<div class="activity-list">
                            <div class="activity-title">${{activity.title}}</div>`;
                        
                        if (activity.procedures && activity.procedures.length > 0) {{
                            html += '<div class="activity-procedures">';
                            activity.procedures.forEach(proc => {{
                                html += `<div>• ${{proc}}</div>`;
                            }});
                            html += '</div>';
                        }}
                        
                        if (activity.notes) {{
                            html += `<div class="activity-procedures" style="font-style: italic;">Note: ${{activity.notes}}</div>`;
                        }}
                        
                        html += '</div>';
                    }}
                }});
            }}
            
            tooltip.html(html)
                .style("left", (event.pageX + 15) + "px")
                .style("top", (event.pageY - 15) + "px")
                .classed("visible", true);
        }}
        
        function hideTooltip() {{
            tooltip.classed("visible", false);
        }}
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on("zoom", function(event) {{
                g.attr("transform", `translate(${{config.margin.left + event.transform.x}},${{config.margin.top + event.transform.y}}) scale(${{event.transform.k}})`);
            }});
        
        svg.call(zoom);
        
        console.log(`Loaded ${{validVisits.length}} visits with serpentine timeline visualization`);
    </script>
</body>
</html>"""
    
    # Write HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Generated timeline visualization: {output_path}")
    return output_path


def main():
    """Main function to generate timeline from command line."""
    if len(sys.argv) < 2:
        print("Usage: python generate_timeline.py <json_file> [output_file]")
        print("\nExample:")
        print("  python generate_timeline.py pj/pj_p1.json")
        print("  python generate_timeline.py pj/pj_p2.json timeline_output.html")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'timeline_visualization.html'
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        data = load_json_data(input_file)
        generate_html(data, output_file)
        print(f"\nVisualization generated successfully!")
        print(f"Open {output_file} in a web browser to view the timeline.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
