import streamlit as st
import streamlit.components.v1 as components

def create_layout_designer():
    """Create a drag and drop layout designer for UI components"""
    
    st.set_page_config(page_title="Layout Designer", layout="wide")
    
    st.title("🎨 Activity Dashboard Layout Designer")
    st.markdown("**Drag and drop components to design your perfect layout!**")
    
    # Available components
    components_list = {
        "📊 Activity Table": {
            "description": "Interactive table with all activities",
            "size": "large",
            "color": "#3b82f6"
        },
        "🗺️ Route Map": {
            "description": "GPS route visualization",
            "size": "medium", 
            "color": "#10b981"
        },
        "📈 Lap Analysis Chart": {
            "description": "Variable width pace bars",
            "size": "large",
            "color": "#f59e0b"
        },
        "🎯 Activity Details": {
            "description": "Advanced metrics and analysis",
            "size": "medium",
            "color": "#8b5cf6"
        },
        "📋 Quick Stats": {
            "description": "Essential metrics only",
            "size": "small",
            "color": "#ef4444"
        },
        "🔍 Search/Filter": {
            "description": "Find activities quickly",
            "size": "small",
            "color": "#06b6d4"
        },
        "📊 Overview Stats": {
            "description": "Monthly summary banner",
            "size": "medium",
            "color": "#84cc16"
        },
        "⚡ Performance Insights": {
            "description": "AI-generated insights",
            "size": "medium",
            "color": "#f97316"
        }
    }
    
    # CSS for drag and drop
    st.markdown("""
    <style>
    .component-item {
        padding: 12px;
        margin: 8px;
        border-radius: 8px;
        border: 2px dashed #666;
        cursor: move;
        text-align: center;
        transition: all 0.3s ease;
        background: rgba(255,255,255,0.1);
    }
    
    .component-item:hover {
        border-color: #3b82f6;
        transform: scale(1.02);
    }
    
    .drop-zone {
        min-height: 200px;
        border: 3px dashed #666;
        border-radius: 12px;
        padding: 20px;
        margin: 10px 0;
        background: rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .drop-zone:hover {
        border-color: #3b82f6;
        background: rgba(59, 130, 246, 0.1);
    }
    
    .layout-container {
        display: grid;
        grid-template-columns: 1fr 1fr 1fr;
        gap: 20px;
        margin: 20px 0;
    }
    
    .size-large { min-height: 150px; }
    .size-medium { min-height: 100px; }
    .size-small { min-height: 60px; }
    
    .instructions {
        background: rgba(59, 130, 246, 0.1);
        padding: 20px;
        border-radius: 12px;
        border-left: 4px solid #3b82f6;
        margin: 20px 0;
    }
    
    .component.dragging {{
        opacity: 0.5;
    }}
    
    .component[data-component^="custom"] {{
        background: rgba(139, 92, 246, 0.1);
        border-color: #8b5cf6;
        border-style: dotted;
    }}
    
    .component[data-component^="custom"]:hover {{
        background: rgba(139, 92, 246, 0.2);
        border-color: #a855f7;
        transform: scale(1.05);
    }}
    
    .dropped-component[data-component^="custom"] {{
        background: rgba(139, 92, 246, 0.15);
        border-color: #8b5cf6;
        border-style: dotted;
    }}
    
    .custom-note {{
        background: rgba(251, 191, 36, 0.1);
        border: 2px dashed #f59e0b;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        color: #f59e0b;
        text-align: center;
        font-style: italic;
    }}
    
    .layout-area {{
        display: grid;
        grid-template-columns: 2fr 1fr;
        gap: 20px;
        height: 100%;
    }}
    </style>
    """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    <div class="instructions">
        <h3>🎯 How to use:</h3>
        <ol>
            <li><strong>Drag components</strong> from the Component Library below</li>
            <li><strong>Drop them</strong> into your preferred layout areas</li>
            <li><strong>Rearrange</strong> until you're happy with the design</li>
            <li><strong>Tell me</strong> "I like this layout!" when ready</li>
        </ol>
    </div>
    """, unsafe_allow_html=True)
    
    # Create drag and drop interface
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #0e1117; color: white; }}
            
            .designer-container {{ 
                display: grid; 
                grid-template-rows: auto 1fr; 
                gap: 30px; 
                height: 80vh; 
            }}
            
            .component-library {{
                background: rgba(255,255,255,0.05);
                padding: 20px;
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
            
            .library-title {{
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 15px;
                color: #3b82f6;
            }}
            
            .components-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
            }}
            
            .component {{
                padding: 15px;
                border-radius: 8px;
                border: 2px dashed #666;
                cursor: move;
                text-align: center;
                transition: all 0.3s ease;
                background: rgba(255,255,255,0.05);
            }}
            
            .component:hover {{
                border-color: #3b82f6;
                transform: scale(1.05);
            }}
            
            .component.dragging {{
                opacity: 0.5;
            }}
            
            .component[data-component^="custom"] {{
                background: rgba(139, 92, 246, 0.1);
                border-color: #8b5cf6;
                border-style: dotted;
            }}
            
            .component[data-component^="custom"]:hover {{
                background: rgba(139, 92, 246, 0.2);
                border-color: #a855f7;
                transform: scale(1.05);
            }}
            
            .dropped-component[data-component^="custom"] {{
                background: rgba(139, 92, 246, 0.15);
                border-color: #8b5cf6;
                border-style: dotted;
            }}
            
            .custom-note {{
                background: rgba(251, 191, 36, 0.1);
                border: 2px dashed #f59e0b;
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
                color: #f59e0b;
                text-align: center;
                font-style: italic;
            }}
            
            .layout-area {{
                display: grid;
                grid-template-columns: 2fr 1fr;
                gap: 20px;
                height: 100%;
            }}
            
            .drop-zone {{
                min-height: 150px;
                border: 3px dashed #444;
                border-radius: 12px;
                padding: 20px;
                background: rgba(255,255,255,0.02);
                transition: all 0.3s ease;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }}
            
            .drop-zone.drag-over {{
                border-color: #3b82f6;
                background: rgba(59, 130, 246, 0.1);
            }}
            
            .drop-zone h3 {{
                margin: 0 0 15px 0;
                color: #9ca3af;
                font-size: 1.1em;
            }}
            
            .dropped-component {{
                padding: 12px;
                border-radius: 8px;
                border: 1px solid #666;
                background: rgba(255,255,255,0.08);
                cursor: move;
                transition: all 0.3s ease;
            }}
            
            .dropped-component:hover {{
                border-color: #3b82f6;
            }}
            
            .component-name {{
                font-weight: bold;
                margin-bottom: 5px;
            }}
            
            .component-desc {{
                font-size: 0.9em;
                color: #9ca3af;
            }}
            
            .layout-left {{
                display: grid;
                grid-template-rows: 1fr 1fr;
                gap: 20px;
            }}
            
            .layout-right {{
                display: grid;
                grid-template-rows: 1fr 1fr 1fr;
                gap: 15px;
            }}
            
            .reset-btn {{
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 20px;
                background: #ef4444;
                color: white;
                border: none;
                border-radius: 8px;
                cursor: pointer;
            }}
        </style>
    </head>
    <body>
        <button class="reset-btn" onclick="resetLayout()">🗑️ Reset</button>
        
        <div class="designer-container">
            <!-- Component Library -->
            <div class="component-library">
                <div class="library-title">📦 Component Library - Drag these to your layout</div>
                <div class="custom-note">
                    💡 <strong>Custom Components:</strong> Use the purple dotted boxes below to represent your own ideas! 
                    Drag them around and imagine what functionality you'd want there.
                </div>
                <div class="components-grid" id="componentLibrary">
                    <div class="component" draggable="true" data-component="table">
                        <div class="component-name">📊 Activity Table</div>
                        <div class="component-desc">Interactive table with all activities</div>
                    </div>
                    <div class="component" draggable="true" data-component="map">
                        <div class="component-name">🗺️ Route Map</div>
                        <div class="component-desc">GPS route visualization</div>
                    </div>
                    <div class="component" draggable="true" data-component="chart">
                        <div class="component-name">📈 Lap Analysis</div>
                        <div class="component-desc">Variable width pace bars</div>
                    </div>
                    <div class="component" draggable="true" data-component="details">
                        <div class="component-name">🎯 Activity Details</div>
                        <div class="component-desc">Advanced metrics and analysis</div>
                    </div>
                    <div class="component" draggable="true" data-component="stats">
                        <div class="component-name">📋 Quick Stats</div>
                        <div class="component-desc">Essential metrics only</div>
                    </div>
                    <div class="component" draggable="true" data-component="search">
                        <div class="component-name">🔍 Search/Filter</div>
                        <div class="component-desc">Find activities quickly</div>
                    </div>
                    <div class="component" draggable="true" data-component="overview">
                        <div class="component-name">📊 Overview Stats</div>
                        <div class="component-desc">Monthly summary banner</div>
                    </div>
                    <div class="component" draggable="true" data-component="insights">
                        <div class="component-name">⚡ Performance Insights</div>
                        <div class="component-desc">AI-generated insights</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom1">
                        <div class="component-name">📋 Activity Summary</div>
                        <div class="component-desc">Name, date, sport type, workout type, description, distance, pace, time, avg HR</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom2">
                        <div class="component-name">📝 Custom Component 2</div>
                        <div class="component-desc">Empty box - write your idea here</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom3">
                        <div class="component-name">📝 Custom Component 3</div>
                        <div class="component-desc">Empty box - write your idea here</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom4">
                        <div class="component-name">💭 Idea Box 1</div>
                        <div class="component-desc">Blank space for your thoughts</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom5">
                        <div class="component-name">💭 Idea Box 2</div>
                        <div class="component-desc">Blank space for your thoughts</div>
                    </div>
                    <div class="component" draggable="true" data-component="custom6">
                        <div class="component-name">🎨 Design Element</div>
                        <div class="component-desc">Custom UI element placeholder</div>
                    </div>
                </div>
            </div>
            
            <!-- Layout Area -->
            <div class="layout-area">
                <!-- Left Column -->
                <div class="layout-left">
                    <div class="drop-zone" id="leftTop">
                        <h3>📍 Left Top (2/3 width)</h3>
                        <div class="zone-content"></div>
                    </div>
                    <div class="drop-zone" id="leftBottom">
                        <h3>📍 Left Bottom (2/3 width)</h3>
                        <div class="zone-content"></div>
                    </div>
                </div>
                
                <!-- Right Column -->
                <div class="layout-right">
                    <div class="drop-zone" id="rightTop">
                        <h3>📍 Right Top (1/3 width)</h3>
                        <div class="zone-content"></div>
                    </div>
                    <div class="drop-zone" id="rightMiddle">
                        <h3>📍 Right Middle (1/3 width)</h3>
                        <div class="zone-content"></div>
                    </div>
                    <div class="drop-zone" id="rightBottom">
                        <h3>📍 Right Bottom (1/3 width)</h3>
                        <div class="zone-content"></div>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            let draggedElement = null;
            
            // Add drag event listeners
            document.addEventListener('DOMContentLoaded', function() {{
                addDragListeners();
            }});
            
            function addDragListeners() {{
                // Library components
                document.querySelectorAll('.component').forEach(item => {{
                    item.addEventListener('dragstart', handleDragStart);
                    item.addEventListener('dragend', handleDragEnd);
                }});
                
                // Drop zones
                document.querySelectorAll('.drop-zone').forEach(zone => {{
                    zone.addEventListener('dragover', handleDragOver);
                    zone.addEventListener('drop', handleDrop);
                    zone.addEventListener('dragenter', handleDragEnter);
                    zone.addEventListener('dragleave', handleDragLeave);
                }});
            }}
            
            function handleDragStart(e) {{
                draggedElement = e.target.closest('.component, .dropped-component');
                draggedElement.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            }}
            
            function handleDragEnd(e) {{
                e.target.classList.remove('dragging');
            }}
            
            function handleDragOver(e) {{
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
            }}
            
            function handleDragEnter(e) {{
                e.target.closest('.drop-zone').classList.add('drag-over');
            }}
            
            function handleDragLeave(e) {{
                if (!e.target.closest('.drop-zone').contains(e.relatedTarget)) {{
                    e.target.closest('.drop-zone').classList.remove('drag-over');
                }}
            }}
            
            function handleDrop(e) {{
                e.preventDefault();
                const dropZone = e.target.closest('.drop-zone');
                dropZone.classList.remove('drag-over');
                
                if (draggedElement) {{
                    const componentData = draggedElement.dataset.component || 'unknown';
                    const componentName = draggedElement.querySelector('.component-name').textContent;
                    const componentDesc = draggedElement.querySelector('.component-desc').textContent;
                    
                    // Create dropped component
                    const droppedComponent = document.createElement('div');
                    droppedComponent.className = 'dropped-component';
                    droppedComponent.draggable = true;
                    droppedComponent.dataset.component = componentData;
                    droppedComponent.innerHTML = `
                        <div class="component-name">${{componentName}}</div>
                        <div class="component-desc">${{componentDesc}}</div>
                    `;
                    
                    // Add drag listeners to new component
                    droppedComponent.addEventListener('dragstart', handleDragStart);
                    droppedComponent.addEventListener('dragend', handleDragEnd);
                    
                    // Add to drop zone
                    dropZone.querySelector('.zone-content').appendChild(droppedComponent);
                    
                    // Remove from original location if it was already dropped
                    if (draggedElement.classList.contains('dropped-component')) {{
                        draggedElement.remove();
                    }}
                }}
                
                draggedElement = null;
            }}
            
            function resetLayout() {{
                document.querySelectorAll('.zone-content').forEach(zone => {{
                    zone.innerHTML = '';
                }});
            }}
        </script>
    </body>
    </html>
    """
    
    # Display the drag and drop interface
    components.html(html_content, height=800, scrolling=True)
    
    # Instructions for the user
    st.markdown("---")
    st.markdown("""
    ### 🎨 **Design Your Perfect Layout:**
    
    1. **Drag components** from the library above into your preferred positions
    2. **Experiment** with different arrangements 
    3. **Consider** what you want to see first when you open the dashboard
    4. **Think** about the workflow: Browse → Select → Analyze
    5. **Tell me** when you have a layout you like!
    
    **💡 Layout Tips:**
    - **Left side** typically for main content (bigger items)
    - **Right side** typically for details/secondary info  
    - **Top sections** for most important items
    - **Bottom sections** for supplementary information
    """)

if __name__ == "__main__":
    create_layout_designer() 