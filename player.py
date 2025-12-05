#!/usr/bin/env python3
"""
Generate an interactive timeline player from clinical trial JSON data.
Creates an HTML page with video-player-like controls to play through events chronologically.
"""

import json
import sys
from pathlib import Path


def load_json_data(filepath):
    """Load JSON data from file."""
    with open(filepath, 'r') as f:
        return json.load(f)


def generate_html(data, output_path='timeline_player.html'):
    """
    Generate HTML with interactive timeline player and video-like controls.
    
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
    <title>Clinical Trial Timeline Player</title>
    
    <!-- Bootstrap 5 CSS -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    
    <!-- Bootstrap Icons -->
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    
    <style>
        body {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
        }}
        
        .main-container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .page-header {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .page-header h1 {{
            color: #2d3748;
            font-weight: 700;
            margin-bottom: 10px;
        }}
        
        .page-header p {{
            color: #718096;
            margin-bottom: 0;
        }}
        
        .player-container {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        
        .visualization-area {{
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            border-radius: 15px;
            padding: 40px;
            margin-bottom: 30px;
            min-height: 500px;
            position: relative;
            overflow: hidden;
        }}
        
        .timeline-display {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 400px;
        }}
        
        .current-event {{
            text-align: center;
            animation: fadeIn 0.5s ease-in;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .event-number {{
            font-size: 14px;
            color: #718096;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .event-id {{
            font-size: 18px;
            color: #4a5568;
            font-family: 'Courier New', monospace;
            margin-bottom: 15px;
        }}
        
        .event-label {{
            font-size: 32px;
            font-weight: 700;
            color: #2d3748;
            margin-bottom: 15px;
        }}
        
        .event-time {{
            font-size: 20px;
            color: #667eea;
            font-weight: 600;
            margin-bottom: 10px;
        }}
        
        .event-tick {{
            font-size: 14px;
            color: #a0aec0;
            font-family: 'Courier New', monospace;
            margin-bottom: 20px;
        }}
        
        .event-encounter {{
            display: inline-block;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            padding: 10px 25px;
            border-radius: 25px;
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(245, 87, 108, 0.3);
        }}
        
        .event-activities {{
            max-width: 800px;
            margin: 20px auto 0;
            text-align: left;
        }}
        
        .activities-title {{
            font-size: 18px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 15px;
            text-align: center;
        }}
        
        .activity-group {{
            margin-bottom: 15px;
        }}
        
        .activity-parent {{
            font-size: 14px;
            font-weight: 600;
            color: #667eea;
            margin-bottom: 8px;
        }}
        
        .activity-item {{
            background: white;
            padding: 10px 15px;
            border-radius: 8px;
            margin-bottom: 8px;
            border-left: 3px solid #667eea;
            font-size: 14px;
            color: #4a5568;
        }}
        
        .procedure-item {{
            font-size: 12px;
            color: #718096;
            margin-top: 5px;
            padding-left: 15px;
        }}
        
        .controls-panel {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 15px;
            padding: 25px;
            color: white;
        }}
        
        .progress-section {{
            margin-bottom: 20px;
        }}
        
        .progress-info {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 10px;
            font-size: 13px;
            opacity: 0.9;
        }}
        
        .timeline-slider {{
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: rgba(255, 255, 255, 0.3);
            outline: none;
            -webkit-appearance: none;
            appearance: none;
            cursor: pointer;
        }}
        
        .timeline-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        
        .timeline-slider::-moz-range-thumb {{
            width: 20px;
            height: 20px;
            border-radius: 50%;
            background: white;
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
        }}
        
        .playback-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .control-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.5);
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            transition: all 0.3s ease;
            font-size: 20px;
        }}
        
        .control-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }}
        
        .control-btn:active {{
            transform: scale(0.95);
        }}
        
        .control-btn.primary {{
            width: 60px;
            height: 60px;
            background: white;
            color: #667eea;
            font-size: 24px;
        }}
        
        .control-btn.primary:hover {{
            background: #f7fafc;
        }}
        
        .speed-controls {{
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 10px;
        }}
        
        .speed-label {{
            font-size: 13px;
            opacity: 0.9;
            min-width: 60px;
        }}
        
        .speed-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: 1px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .speed-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
        }}
        
        .speed-btn.active {{
            background: white;
            color: #667eea;
        }}
        
        .no-events {{
            text-align: center;
            color: #a0aec0;
            padding: 60px 20px;
            font-size: 18px;
        }}
        
        .timeline-markers {{
            display: flex;
            justify-content: space-between;
            margin-top: 5px;
            font-size: 11px;
            opacity: 0.7;
        }}
        
        .stats-row {{
            display: flex;
            justify-content: space-around;
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid rgba(255, 255, 255, 0.2);
        }}
        
        .stat-item {{
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: 700;
        }}
        
        .stat-label {{
            font-size: 11px;
            opacity: 0.8;
            margin-top: 2px;
        }}
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Page Header -->
        <div class="page-header">
            <h1><i class="bi bi-play-circle-fill"></i> Clinical Trial Timeline Player</h1>
            <p>Interactive visualization with video-player controls</p>
        </div>
        
        <!-- Player Container -->
        <div class="player-container">
            <!-- Visualization Area -->
            <div class="visualization-area">
                <div class="timeline-display" id="timeline-display">
                    <div class="no-events">Load timeline to begin</div>
                </div>
            </div>
            
            <!-- Controls Panel -->
            <div class="controls-panel">
                <!-- Progress Section -->
                <div class="progress-section">
                    <div class="progress-info">
                        <span id="current-time">Event 0 of 0</span>
                        <span id="duration-time">Duration: --</span>
                    </div>
                    <input type="range" class="timeline-slider" id="timeline-slider" 
                           min="0" max="100" value="0" step="1">
                    <div class="timeline-markers">
                        <span>Start</span>
                        <span id="middle-marker">--</span>
                        <span>End</span>
                    </div>
                </div>
                
                <!-- Playback Controls -->
                <div class="playback-controls">
                    <button class="control-btn" id="first-btn" title="First Event">
                        <i class="bi bi-skip-start-fill"></i>
                    </button>
                    <button class="control-btn" id="prev-btn" title="Previous Event">
                        <i class="bi bi-chevron-left"></i>
                    </button>
                    <button class="control-btn primary" id="play-btn" title="Play/Pause">
                        <i class="bi bi-play-fill"></i>
                    </button>
                    <button class="control-btn" id="next-btn" title="Next Event">
                        <i class="bi bi-chevron-right"></i>
                    </button>
                    <button class="control-btn" id="last-btn" title="Last Event">
                        <i class="bi bi-skip-end-fill"></i>
                    </button>
                </div>
                
                <!-- Speed Controls -->
                <div class="speed-controls">
                    <span class="speed-label">Speed:</span>
                    <button class="speed-btn" data-speed="0.5">0.5x</button>
                    <button class="speed-btn active" data-speed="1">1x</button>
                    <button class="speed-btn" data-speed="2">2x</button>
                    <button class="speed-btn" data-speed="5">5x</button>
                    <button class="speed-btn" data-speed="10">10x</button>
                </div>
                
                <!-- Stats Row -->
                <div class="stats-row">
                    <div class="stat-item">
                        <div class="stat-value" id="total-events">0</div>
                        <div class="stat-label">Total Events</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="total-encounters">0</div>
                        <div class="stat-label">Encounters</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="current-speed">1x</div>
                        <div class="stat-label">Playback Speed</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Bootstrap 5 JS Bundle -->
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js"></script>
    
    <script>
        // Data from Python
        const data = {json_data};
        
        // Player state
        let nodes = [];
        let currentIndex = 0;
        let isPlaying = false;
        let playbackSpeed = 1;
        let playbackInterval = null;
        
        // Initialize player
        function initPlayer() {{
            nodes = data.nodes || [];
            
            if (nodes.length === 0) {{
                document.getElementById('timeline-display').innerHTML = 
                    '<div class="no-events">No events found in data</div>';
                return;
            }}
            
            // Update stats
            document.getElementById('total-events').textContent = nodes.length;
            const encounterCount = nodes.filter(n => n.encounter).length;
            document.getElementById('total-encounters').textContent = encounterCount;
            
            // Setup slider
            const slider = document.getElementById('timeline-slider');
            slider.max = nodes.length - 1;
            slider.value = 0;
            
            // Update middle marker
            const middleNode = nodes[Math.floor(nodes.length / 2)];
            document.getElementById('middle-marker').textContent = 
                middleNode ? middleNode.time || '--' : '--';
            
            // Display first event
            displayEvent(0);
            
            // Setup event listeners
            setupEventListeners();
            
            console.log(`Player initialized with ${{nodes.length}} events`);
        }}
        
        // Display event at given index
        function displayEvent(index) {{
            if (index < 0 || index >= nodes.length) return;
            
            currentIndex = index;
            const node = nodes[index];
            
            // Build HTML for event display
            let html = '<div class="current-event">';
            
            // Event number
            html += `<div class="event-number">Event ${{index + 1}} of ${{nodes.length}}</div>`;
            
            // Event ID
            html += `<div class="event-id">${{node.id || 'N/A'}}</div>`;
            
            // Event label
            html += `<div class="event-label">${{node.label || 'Unnamed Event'}}</div>`;
            
            // Time
            html += `<div class="event-time">${{node.time || 'Time not specified'}}</div>`;
            
            // Tick
            html += `<div class="event-tick">Tick: ${{node.tick !== undefined ? node.tick : 'N/A'}}</div>`;
            
            // Encounter
            if (node.encounter) {{
                html += `<div class="event-encounter"><i class="bi bi-calendar-event"></i> ${{node.encounter}}</div>`;
            }}
            
            // Activities
            const activities = node.activities?.items || [];
            if (activities.length > 0) {{
                html += '<div class="event-activities">';
                html += `<div class="activities-title"><i class="bi bi-list-check"></i> Activities (${{activities.length}})</div>`;
                
                // Group activities by parent
                const grouped = {{}};
                activities.forEach(activity => {{
                    const parent = activity.parent || 'Other';
                    if (!grouped[parent]) grouped[parent] = [];
                    grouped[parent].push(activity);
                }});
                
                // Display grouped activities
                Object.keys(grouped).sort().forEach(parent => {{
                    html += '<div class="activity-group">';
                    if (parent !== 'Other') {{
                        html += `<div class="activity-parent"><i class="bi bi-folder2-open"></i> ${{parent}}</div>`;
                    }}
                    grouped[parent].forEach(activity => {{
                        html += `<div class="activity-item">${{activity.label || 'Unnamed activity'}}`;
                        
                        // Procedures
                        const procedures = activity.procedures?.filter(p => p && p.trim() !== '') || [];
                        if (procedures.length > 0) {{
                            procedures.forEach(proc => {{
                                html += `<div class="procedure-item"><i class="bi bi-arrow-return-right"></i> ${{proc}}</div>`;
                            }});
                        }}
                        html += '</div>';
                    }});
                    html += '</div>';
                }});
                
                html += '</div>';
            }}
            
            html += '</div>';
            
            // Update display
            document.getElementById('timeline-display').innerHTML = html;
            
            // Update slider
            document.getElementById('timeline-slider').value = index;
            
            // Update progress info
            document.getElementById('current-time').textContent = `Event ${{index + 1}} of ${{nodes.length}}`;
            
            // Calculate duration info
            if (nodes.length > 0) {{
                const firstTick = nodes[0].tick;
                const lastTick = nodes[nodes.length - 1].tick;
                const totalSeconds = lastTick - firstTick;
                const days = Math.floor(Math.abs(totalSeconds) / 86400);
                const weeks = Math.floor(days / 7);
                document.getElementById('duration-time').textContent = 
                    `Duration: ${{weeks}} weeks (${{days}} days)`;
            }}
        }}
        
        // Play/Pause toggle
        function togglePlay() {{
            if (isPlaying) {{
                pause();
            }} else {{
                play();
            }}
        }}
        
        // Play
        function play() {{
            if (currentIndex >= nodes.length - 1) {{
                currentIndex = 0;
            }}
            
            isPlaying = true;
            updatePlayButton();
            
            const intervalTime = 1000 / playbackSpeed; // Base speed: 1 event per second
            
            playbackInterval = setInterval(() => {{
                if (currentIndex < nodes.length - 1) {{
                    displayEvent(currentIndex + 1);
                }} else {{
                    pause();
                }}
            }}, intervalTime);
        }}
        
        // Pause
        function pause() {{
            isPlaying = false;
            updatePlayButton();
            
            if (playbackInterval) {{
                clearInterval(playbackInterval);
                playbackInterval = null;
            }}
        }}
        
        // Update play button icon
        function updatePlayButton() {{
            const playBtn = document.getElementById('play-btn');
            const icon = playBtn.querySelector('i');
            
            if (isPlaying) {{
                icon.className = 'bi bi-pause-fill';
                playBtn.title = 'Pause';
            }} else {{
                icon.className = 'bi bi-play-fill';
                playBtn.title = 'Play';
            }}
        }}
        
        // Navigate to specific event
        function goToEvent(index) {{
            if (isPlaying) {{
                pause();
                displayEvent(index);
                play();
            }} else {{
                displayEvent(index);
            }}
        }}
        
        // Set playback speed
        function setSpeed(speed) {{
            playbackSpeed = speed;
            document.getElementById('current-speed').textContent = speed + 'x';
            
            // Update active button
            document.querySelectorAll('.speed-btn').forEach(btn => {{
                btn.classList.remove('active');
                if (parseFloat(btn.dataset.speed) === speed) {{
                    btn.classList.add('active');
                }}
            }});
            
            // Restart playback if playing
            if (isPlaying) {{
                pause();
                play();
            }}
        }}
        
        // Setup event listeners
        function setupEventListeners() {{
            // Play/Pause button
            document.getElementById('play-btn').addEventListener('click', togglePlay);
            
            // Previous button
            document.getElementById('prev-btn').addEventListener('click', () => {{
                if (currentIndex > 0) {{
                    goToEvent(currentIndex - 1);
                }}
            }});
            
            // Next button
            document.getElementById('next-btn').addEventListener('click', () => {{
                if (currentIndex < nodes.length - 1) {{
                    goToEvent(currentIndex + 1);
                }}
            }});
            
            // First button
            document.getElementById('first-btn').addEventListener('click', () => {{
                goToEvent(0);
            }});
            
            // Last button
            document.getElementById('last-btn').addEventListener('click', () => {{
                goToEvent(nodes.length - 1);
            }});
            
            // Slider
            const slider = document.getElementById('timeline-slider');
            slider.addEventListener('input', (e) => {{
                const index = parseInt(e.target.value);
                goToEvent(index);
            }});
            
            // Speed buttons
            document.querySelectorAll('.speed-btn').forEach(btn => {{
                btn.addEventListener('click', () => {{
                    const speed = parseFloat(btn.dataset.speed);
                    setSpeed(speed);
                }});
            }});
            
            // Keyboard shortcuts
            document.addEventListener('keydown', (e) => {{
                switch(e.key) {{
                    case ' ':
                    case 'k':
                        e.preventDefault();
                        togglePlay();
                        break;
                    case 'ArrowLeft':
                    case 'j':
                        e.preventDefault();
                        if (currentIndex > 0) goToEvent(currentIndex - 1);
                        break;
                    case 'ArrowRight':
                    case 'l':
                        e.preventDefault();
                        if (currentIndex < nodes.length - 1) goToEvent(currentIndex + 1);
                        break;
                    case 'Home':
                        e.preventDefault();
                        goToEvent(0);
                        break;
                    case 'End':
                        e.preventDefault();
                        goToEvent(nodes.length - 1);
                        break;
                }}
            }});
        }}
        
        // Initialize on load
        initPlayer();
    </script>
</body>
</html>"""
    
    # Write HTML to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    print(f"Generated timeline player: {output_path}")
    return output_path


def main():
    """Main function to generate timeline player from command line."""
    if len(sys.argv) < 2:
        print("Usage: python player.py <json_file> [output_file]")
        print("\nExample:")
        print("  python player.py expander.json")
        print("  python player.py data.json player_output.html")
        print("\nFeatures:")
        print("  - Play/pause through timeline events")
        print("  - Step forward/backward through events")
        print("  - Adjustable playback speed (0.5x to 10x)")
        print("  - Timeline slider for scrubbing")
        print("  - Keyboard shortcuts (Space/K: play/pause, Arrow keys: navigate)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'timeline_player.html'
    
    if not Path(input_file).exists():
        print(f"Error: File not found: {input_file}")
        sys.exit(1)
    
    try:
        data = load_json_data(input_file)
        generate_html(data, output_file)
        print(f"\nTimeline player generated successfully!")
        print(f"Open {output_file} in a web browser to view the interactive player.")
        print("\nControls:")
        print("  - Click Play button or press Space/K to play/pause")
        print("  - Use arrow buttons or Left/Right arrows to navigate")
        print("  - Drag timeline slider to jump to any event")
        print("  - Click speed buttons to adjust playback speed")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
