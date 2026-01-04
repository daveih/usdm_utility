#!/usr/bin/env python3
"""
Clinical Study Journey Visualizer
Generates a mobile-friendly HTML visualization of a clinical study timeline
for patient/participant use.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

def load_study_data(json_path: str) -> dict:
    """Load the study JSON data."""
    with open(json_path, 'r') as f:
        return json.load(f)

def categorize_activities(activities: list) -> dict:
    """Group activities by category for patient journey."""
    categories = defaultdict(list)
    for activity in activities:
        desc = activity.get('description_for_patient', '')
        category = activity.get('category_for_patient_journey', 'Other')
        if desc and category:
            categories[category].append({
                'label': activity.get('label', ''),
                'description': desc,
                'time': activity.get('costs', {}).get('burden_participant_time', 0)
            })
    return dict(categories)

def get_encounter_info(encounter: str) -> dict:
    """Get display information for each encounter type."""
    info = {
        'SCR': {'name': 'Screening Visit', 'icon': '🔍', 'color': '#6366f1'},
        'BL': {'name': 'Baseline Visit', 'icon': '🎯', 'color': '#8b5cf6'},
        'W1': {'name': 'Week 1', 'icon': '💊', 'color': '#0ea5e9'},
        'W2': {'name': 'Week 2', 'icon': '💊', 'color': '#0ea5e9'},
        'W4': {'name': 'Week 4', 'icon': '📊', 'color': '#10b981'},
        'W8': {'name': 'Week 8', 'icon': '📊', 'color': '#10b981'},
        'W12': {'name': 'Week 12', 'icon': '🔬', 'color': '#f59e0b'},
        'W18': {'name': 'Week 18', 'icon': '📋', 'color': '#f59e0b'},
        'W24': {'name': 'Week 24', 'icon': '🎯', 'color': '#ef4444'},
        'W30': {'name': 'Week 30', 'icon': '📋', 'color': '#ec4899'},
        'W36': {'name': 'Week 36', 'icon': '📊', 'color': '#ec4899'},
        'W42': {'name': 'Week 42', 'icon': '📋', 'color': '#8b5cf6'},
        'W48': {'name': 'Week 48 (Final)', 'icon': '🏁', 'color': '#059669'},
    }
    return info.get(encounter, {'name': encounter, 'icon': '📍', 'color': '#64748b'})

def calculate_total_time(activities: list) -> int:
    """Calculate total participant time in minutes."""
    total = 0
    for activity in activities:
        total += activity.get('costs', {}).get('burden_participant_time', 0)
    return total

def generate_site_visit_card(node: dict) -> str:
    """Generate HTML for a site visit card."""
    encounter = node.get('encounter', '')
    info = get_encounter_info(encounter)
    activities = node.get('activities', {}).get('items', [])
    categories = categorize_activities(activities)
    total_time = calculate_total_time(activities)
    time_str = node.get('time', '')
    label = node.get('label', '')

    # Build activity sections
    activity_html = ""
    for category, items in categories.items():
        if items:
            items_html = "".join([
                f'<li>{item["description"]}</li>'
                for item in items if item["description"]
            ])
            if items_html:
                activity_html += f'''
                <div class="category">
                    <div class="category-name">{category}</div>
                    <ul>{items_html}</ul>
                </div>
                '''

    return f'''
    <div class="visit-card" style="--accent-color: {info['color']}">
        <div class="card-header">
            <div class="visit-icon">{info['icon']}</div>
            <div class="visit-info">
                <h2>{info['name']}</h2>
                <div class="visit-timing">
                    <span class="timing-badge">{time_str}</span>
                    <span class="duration">~{total_time} min</span>
                </div>
            </div>
        </div>
        <div class="card-body">
            <div class="visit-summary">
                <div class="summary-title">What to Expect</div>
                {activity_html}
            </div>
        </div>
        <div class="card-footer">
            <div class="footer-note">Clinic Visit Required</div>
        </div>
    </div>
    '''

def generate_diary_summary(diary_nodes: list) -> str:
    """Generate a compact summary for diary entries between site visits."""
    if not diary_nodes:
        return ""

    count = len(diary_nodes)
    first_time = diary_nodes[0].get('time', '')
    last_time = diary_nodes[-1].get('time', '') if count > 1 else first_time

    return f'''
    <div class="diary-summary">
        <div class="diary-icon">📱</div>
        <div class="diary-info">
            <div class="diary-title">Daily Diary Entries</div>
            <div class="diary-details">
                <span class="diary-count">{count} days</span>
                <span class="diary-range">{first_time} → {last_time}</span>
            </div>
            <div class="diary-task">Complete DiSSA questionnaire at home (~3 min)</div>
        </div>
    </div>
    '''

def generate_html(data: dict, output_path: str):
    """Generate the complete HTML visualization."""
    nodes = data.get('nodes', [])

    # Sort nodes by tick (time)
    sorted_nodes = sorted(nodes, key=lambda x: x.get('tick', 0))

    # Separate site visits from diary entries
    site_visits = []
    diary_buffer = []
    content_html = ""

    for node in sorted_nodes:
        encounter = node.get('encounter')
        label = node.get('label', '')

        if encounter:  # This is a site visit
            # First, output any buffered diary entries
            if diary_buffer:
                content_html += generate_diary_summary(diary_buffer)
                diary_buffer = []
            # Then output the site visit card
            content_html += generate_site_visit_card(node)
            site_visits.append(node)
        elif label == 'diary':
            diary_buffer.append(node)

    # Don't forget any remaining diary entries
    if diary_buffer:
        content_html += generate_diary_summary(diary_buffer)

    # Calculate study statistics
    total_site_visits = len(site_visits)
    total_diary_days = len([n for n in sorted_nodes if n.get('label') == 'diary'])

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Study Journey</title>
    <style>
        :root {{
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-card: #334155;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --border-color: #475569;
            --success: #10b981;
            --warning: #f59e0b;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, #1a1a2e 100%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 20px;
            line-height: 1.5;
        }}

        .container {{
            max-width: 420px;
            margin: 0 auto;
        }}

        .header {{
            text-align: center;
            margin-bottom: 30px;
            padding: 20px;
        }}

        .header h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: linear-gradient(135deg, #60a5fa, #a78bfa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .header p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
        }}

        .stats-bar {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 20px;
        }}

        .stat {{
            text-align: center;
            padding: 12px 20px;
            background: var(--bg-secondary);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }}

        .stat-value {{
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--success);
        }}

        .stat-label {{
            font-size: 0.75rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .timeline {{
            position: relative;
            padding-left: 20px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 8px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, #6366f1, #8b5cf6, #0ea5e9, #10b981, #f59e0b, #ef4444, #ec4899);
            border-radius: 2px;
        }}

        .visit-card {{
            background: var(--bg-card);
            border-radius: 16px;
            margin-bottom: 20px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            position: relative;
        }}

        .visit-card::before {{
            content: '';
            position: absolute;
            left: -14px;
            top: 30px;
            width: 12px;
            height: 12px;
            background: var(--accent-color);
            border-radius: 50%;
            border: 3px solid var(--bg-primary);
            z-index: 1;
        }}

        .card-header {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 20px;
            background: linear-gradient(135deg, var(--accent-color)22, transparent);
            border-bottom: 1px solid var(--border-color);
        }}

        .visit-icon {{
            font-size: 2rem;
            width: 50px;
            height: 50px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--bg-secondary);
            border-radius: 12px;
        }}

        .visit-info h2 {{
            font-size: 1.1rem;
            font-weight: 600;
            margin-bottom: 5px;
        }}

        .visit-timing {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .timing-badge {{
            background: var(--accent-color);
            color: white;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}

        .duration {{
            color: var(--text-muted);
            font-size: 0.85rem;
        }}

        .card-body {{
            padding: 20px;
        }}

        .summary-title {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
            margin-bottom: 15px;
            font-weight: 600;
        }}

        .category {{
            margin-bottom: 15px;
        }}

        .category-name {{
            font-size: 0.85rem;
            font-weight: 600;
            color: var(--accent-color);
            margin-bottom: 8px;
            padding-left: 10px;
            border-left: 3px solid var(--accent-color);
        }}

        .category ul {{
            list-style: none;
            padding-left: 15px;
        }}

        .category li {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-bottom: 5px;
            position: relative;
            padding-left: 15px;
        }}

        .category li::before {{
            content: '•';
            position: absolute;
            left: 0;
            color: var(--text-muted);
        }}

        .card-footer {{
            padding: 12px 20px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--border-color);
        }}

        .footer-note {{
            font-size: 0.75rem;
            color: var(--warning);
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 5px;
        }}

        .footer-note::before {{
            content: '📍';
        }}

        .diary-summary {{
            display: flex;
            align-items: center;
            gap: 15px;
            padding: 15px 20px;
            margin-bottom: 20px;
            background: linear-gradient(135deg, #1e3a5f 0%, #1e293b 100%);
            border-radius: 12px;
            border: 1px dashed var(--border-color);
            position: relative;
        }}

        .diary-summary::before {{
            content: '';
            position: absolute;
            left: -14px;
            top: 50%;
            transform: translateY(-50%);
            width: 8px;
            height: 8px;
            background: var(--text-muted);
            border-radius: 50%;
        }}

        .diary-icon {{
            font-size: 1.5rem;
            opacity: 0.8;
        }}

        .diary-info {{
            flex: 1;
        }}

        .diary-title {{
            font-size: 0.9rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 3px;
        }}

        .diary-details {{
            display: flex;
            gap: 10px;
            margin-bottom: 5px;
        }}

        .diary-count {{
            font-size: 0.75rem;
            background: #3b82f6;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .diary-range {{
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .diary-task {{
            font-size: 0.8rem;
            color: var(--text-secondary);
        }}

        .footer-info {{
            margin-top: 30px;
            padding: 20px;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.8rem;
        }}

        @media (max-width: 480px) {{
            body {{
                padding: 10px;
            }}

            .header h1 {{
                font-size: 1.5rem;
            }}

            .visit-card {{
                border-radius: 12px;
            }}

            .card-header {{
                padding: 15px;
            }}

            .card-body {{
                padding: 15px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Study Journey</h1>
            <p>A guide to your clinical study participation</p>
            <div class="stats-bar">
                <div class="stat">
                    <div class="stat-value">{total_site_visits}</div>
                    <div class="stat-label">Clinic Visits</div>
                </div>
                <div class="stat">
                    <div class="stat-value">{total_diary_days}</div>
                    <div class="stat-label">Diary Days</div>
                </div>
            </div>
        </div>

        <div class="timeline">
            {content_html}
        </div>

        <div class="footer-info">
            <p>Questions? Contact your study coordinator.</p>
            <p style="margin-top: 10px; font-size: 0.7rem;">
                Generated for participant reference only.
            </p>
        </div>
    </div>
</body>
</html>
'''

    with open(output_path, 'w') as f:
        f.write(html)

    print(f"Generated: {output_path}")
    print(f"  - {total_site_visits} clinic visits")
    print(f"  - {total_diary_days} diary days")

def main():
    if len(sys.argv) < 2:
        # Default to the example file
        json_path = "/Users/daveih/Documents/python/sdw_test/Other/xl_example_amended_expansion.json"
    else:
        json_path = sys.argv[1]

    # Generate output path
    input_path = Path(json_path)
    output_path = input_path.parent / f"{input_path.stem}_journey.html"

    # Load and process
    data = load_study_data(json_path)
    generate_html(data, str(output_path))

if __name__ == "__main__":
    main()
