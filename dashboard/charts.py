"""Chart components for the restaurant dashboard"""

import reflex as rx
from typing import List, Dict, Any, Optional
from dashboard.components import progress_ring
from dashboard.styles import COLORS


def revenue_line_chart(
    data: List[Dict[str, Any]],
    period: str = "7d",
    height: int = 300
) -> rx.Component:
    """Revenue line chart component with time period selection"""
    
    # Calculate chart dimensions and data points
    chart_width = 400
    chart_height = height - 60  # Account for padding
    
    if not data:
        return empty_chart_placeholder("No revenue data available", height)
    
    # Find min/max values for scaling
    revenues = [float(d.get("revenue", 0)) for d in data]
    min_revenue = min(revenues) if revenues else 0
    max_revenue = max(revenues) if revenues else 100
    
    # Avoid division by zero
    if max_revenue == min_revenue:
        max_revenue = min_revenue + 1
    
    # Create SVG path for line chart
    points = []
    for i, item in enumerate(data):
        x = (i / (len(data) - 1)) * chart_width if len(data) > 1 else chart_width / 2
        y = chart_height - ((float(item.get("revenue", 0)) - min_revenue) / (max_revenue - min_revenue)) * chart_height
        points.append(f"{x},{y}")
    
    path_data = f"M {' L '.join(points)}" if points else "M 0,0"
    
    # Define colors to avoid f-string issues
    grid_color = "#E5E7EB"
    text_color = "#6B7280"
    primary_color = COLORS['primary']
    
    return rx.box(
        rx.html(
            f"""
            <svg width="{chart_width}" height="{height}" viewBox="0 0 {chart_width} {height}">
                <!-- Grid lines -->
                <defs>
                    <pattern id="grid" width="40" height="30" patternUnits="userSpaceOnUse">
                        <path d="M 40 0 L 0 0 0 30" fill="none" stroke="{grid_color}" stroke-width="1" opacity="0.5"/>
                    </pattern>
                    <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:{primary_color};stop-opacity:0.3" />
                        <stop offset="100%" style="stop-color:{primary_color};stop-opacity:0.05" />
                    </linearGradient>
                </defs>
                
                <!-- Grid background -->
                <rect width="{chart_width}" height="{chart_height}" fill="url(#grid)" />
                
                <!-- Area under curve -->
                <path d="{path_data} L {chart_width},{chart_height} L 0,{chart_height} Z" 
                      fill="url(#gradient)" />
                
                <!-- Line -->
                <path d="{path_data}" 
                      stroke="{primary_color}" 
                      stroke-width="3" 
                      fill="none" 
                      stroke-linecap="round" 
                      stroke-linejoin="round" />
                
                <!-- Data points -->
                {' '.join([
                    f'<circle cx="{(i / (len(data) - 1)) * chart_width if len(data) > 1 else chart_width / 2}" '
                    f'cy="{chart_height - ((float(item.get("revenue", 0)) - min_revenue) / (max_revenue - min_revenue)) * chart_height}" '
                    f'r="4" fill="{primary_color}" stroke="white" stroke-width="2" />'
                    for i, item in enumerate(data)
                ])}
                
                <!-- Y-axis labels -->
                <text x="10" y="20" font-size="12" fill="{text_color}">${max_revenue:,.0f}</text>
                <text x="10" y="{chart_height - 10}" font-size="12" fill="{text_color}">${min_revenue:,.0f}</text>
                
                <!-- X-axis labels -->
                {' '.join([
                    f'<text x="{(i / (len(data) - 1)) * chart_width if len(data) > 1 else chart_width / 2}" '
                    f'y="{height - 10}" font-size="10" fill="{text_color}" text-anchor="middle">'
                    f'{item.get("date", "").split("-")[-1] if item.get("date") else ""}</text>'
                    for i, item in enumerate(data[::max(1, len(data)//7)])
                ])}
            </svg>
            """
        ),
        width="100%",
        height=f"{height}px",
        display="flex",
        justify_content="center",
        align_items="center"
    )


def order_status_donut_chart(
    status_data: Dict[str, int],
    size: int = 200
) -> rx.Component:
    """Donut chart showing order status distribution"""
    
    if not status_data or sum(status_data.values()) == 0:
        return empty_chart_placeholder("No order data available", size)
    
    total_orders = sum(status_data.values())
    
    # Define colors for each status
    status_colors = {
        "completed": COLORS["success"],
        "in_progress": COLORS["warning"],
        "pending": COLORS["error"],
        "ready": "#8B5CF6",
        "confirmed": COLORS["info"],
        "canceled": COLORS["gray_400"]
    }
    
    # Calculate angles for each segment
    segments = []
    current_angle = 0
    
    for status, count in status_data.items():
        if count > 0:
            percentage = (count / total_orders) * 100
            angle = (count / total_orders) * 360
            
            segments.append({
                "status": status,
                "count": count,
                "percentage": percentage,
                "start_angle": current_angle,
                "end_angle": current_angle + angle,
                "color": status_colors.get(status, COLORS["gray_400"])
            })
            current_angle += angle
    
    # Create SVG paths for donut segments
    center = size / 2
    outer_radius = (size - 40) / 2
    inner_radius = outer_radius * 0.6
    
    def create_arc_path(start_angle: float, end_angle: float, outer_r: float, inner_r: float) -> str:
        """Create SVG path for donut arc"""
        import math
        
        start_rad = math.radians(start_angle - 90)  # Start from top
        end_rad = math.radians(end_angle - 90)
        
        x1 = center + outer_r * math.cos(start_rad)
        y1 = center + outer_r * math.sin(start_rad)
        x2 = center + outer_r * math.cos(end_rad)
        y2 = center + outer_r * math.sin(end_rad)
        
        x3 = center + inner_r * math.cos(end_rad)
        y3 = center + inner_r * math.sin(end_rad)
        x4 = center + inner_r * math.cos(start_rad)
        y4 = center + inner_r * math.sin(start_rad)
        
        large_arc = 1 if (end_angle - start_angle) > 180 else 0
        
        return f"M {x1} {y1} A {outer_r} {outer_r} 0 {large_arc} 1 {x2} {y2} L {x3} {y3} A {inner_r} {inner_r} 0 {large_arc} 0 {x4} {y4} Z"
    
    # Generate SVG paths
    svg_paths = []
    for segment in segments:
        path = create_arc_path(
            segment["start_angle"],
            segment["end_angle"],
            outer_radius,
            inner_radius
        )
        svg_paths.append(f'<path d="{path}" fill="{segment["color"]}" stroke="white" stroke-width="2" />')
    
    # Calculate completion percentage for center text
    completed_count = status_data.get("completed", 0)
    completion_percentage = (completed_count / total_orders * 100) if total_orders > 0 else 0
    
    # Define colors to avoid f-string issues
    text_dark = "#1A202C"
    text_light = "#6B7280"
    
    return rx.box(
        rx.html(
            f"""
            <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <!-- Donut segments -->
                {' '.join(svg_paths)}
                
                <!-- Center text -->
                <text x="{center}" y="{center - 10}" text-anchor="middle" font-size="24" font-weight="bold" fill="{text_dark}">
                    {completion_percentage:.0f}%
                </text>
                <text x="{center}" y="{center + 15}" text-anchor="middle" font-size="14" fill="{text_light}">
                    Complete
                </text>
            </svg>
            """
        ),
        width=f"{size}px",
        height=f"{size}px",
        display="flex",
        justify_content="center",
        align_items="center"
    )


def bar_chart(
    data: List[Dict[str, Any]],
    x_key: str,
    y_key: str,
    title: Optional[str] = None,
    height: int = 300,
    color: str = None
) -> rx.Component:
    """Generic bar chart component"""
    
    if not data:
        return empty_chart_placeholder("No data available", height)
    
    chart_color = color or COLORS["primary"]
    chart_width = 400
    chart_height = height - 80  # Account for padding and labels
    
    # Find max value for scaling
    values = [float(item.get(y_key, 0)) for item in data]
    max_value = max(values) if values else 100
    
    bar_width = chart_width / len(data) * 0.8
    bar_spacing = chart_width / len(data) * 0.2
    
    # Define colors to avoid f-string issues
    grid_color = "#E5E7EB"
    text_color = "#6B7280"
    
    return rx.box(
        rx.cond(
            title,
            rx.text(title, font_size="lg", font_weight="semibold", color="gray.900", margin_bottom="4")
        ),
        rx.html(
            f"""
            <svg width="{chart_width}" height="{height}" viewBox="0 0 {chart_width} {height}">
                <!-- Grid lines -->
                <defs>
                    <pattern id="bar-grid" width="{chart_width}" height="25" patternUnits="userSpaceOnUse">
                        <path d="M 0 25 L {chart_width} 25" stroke="{grid_color}" stroke-width="1" opacity="0.5"/>
                    </pattern>
                </defs>
                
                <!-- Grid background -->
                <rect width="{chart_width}" height="{chart_height}" fill="url(#bar-grid)" />
                
                <!-- Bars -->
                {' '.join([
                    f'<rect x="{i * (bar_width + bar_spacing) + bar_spacing/2}" '
                    f'y="{chart_height - (float(item.get(y_key, 0)) / max_value) * chart_height}" '
                    f'width="{bar_width}" '
                    f'height="{(float(item.get(y_key, 0)) / max_value) * chart_height}" '
                    f'fill="{chart_color}" '
                    f'rx="4" />'
                    for i, item in enumerate(data)
                ])}
                
                <!-- X-axis labels -->
                {' '.join([
                    f'<text x="{i * (bar_width + bar_spacing) + bar_spacing/2 + bar_width/2}" '
                    f'y="{height - 10}" font-size="10" fill="{text_color}" text-anchor="middle">'
                    f'{str(item.get(x_key, ""))[:8]}</text>'
                    for i, item in enumerate(data)
                ])}
                
                <!-- Y-axis labels -->
                <text x="10" y="20" font-size="12" fill="{text_color}">{max_value:,.0f}</text>
                <text x="10" y="{chart_height - 10}" font-size="12" fill="{text_color}">0</text>
            </svg>
            """
        ),
        width="100%",
        height=f"{height}px",
        display="flex",
        flex_direction="column",
        align_items="center"
    )


def empty_chart_placeholder(message: str, height: int) -> rx.Component:
    """Empty state placeholder for charts"""
    return rx.box(
        rx.vstack(
            rx.icon(tag="bar_chart_3", size=48, color="gray.300"),
            rx.text(message, color="gray.500", font_size="sm"),
            spacing="3",
            align="center"
        ),
        height=f"{height}px",
        width="100%",
        display="flex",
        align_items="center",
        justify_content="center",
        background="gray.50",
        border="2px dashed",
        border_color="#D1D5DB",
        border_radius="md"
    )


def metric_sparkline(
    data: List[float],
    width: int = 100,
    height: int = 30,
    color: str = None
) -> rx.Component:
    """Small sparkline chart for metric trends"""
    
    if not data or len(data) < 2:
        return rx.box(width=f"{width}px", height=f"{height}px")
    
    line_color = color or COLORS["primary"]
    
    # Normalize data points
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val if max_val != min_val else 1
    
    points = []
    for i, value in enumerate(data):
        x = (i / (len(data) - 1)) * width
        y = height - ((value - min_val) / range_val) * height
        points.append(f"{x},{y}")
    
    path_data = f"M {' L '.join(points)}"
    
    return rx.html(
        f"""
        <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}">
            <path d="{path_data}" 
                  stroke="{line_color}" 
                  stroke-width="2" 
                  fill="none" 
                  stroke-linecap="round" 
                  stroke-linejoin="round" />
        </svg>
        """
    )


def gauge_chart(
    value: float,
    max_value: float = 100,
    size: int = 120,
    color: str = None
) -> rx.Component:
    """Gauge chart component for displaying single metrics"""
    
    gauge_color = color or COLORS["primary"]
    percentage = min((value / max_value) * 100, 100) if max_value > 0 else 0
    
    # Calculate arc parameters
    center = size / 2
    radius = (size - 20) / 2
    start_angle = 135  # Start from bottom left
    end_angle = 45     # End at bottom right
    total_angle = 270  # Total arc span
    
    current_angle = start_angle + (percentage / 100) * total_angle
    
    import math
    
    def polar_to_cartesian(angle_deg: float, r: float) -> tuple:
        angle_rad = math.radians(angle_deg)
        x = center + r * math.cos(angle_rad)
        y = center + r * math.sin(angle_rad)
        return x, y
    
    # Arc path for background
    start_x, start_y = polar_to_cartesian(start_angle, radius)
    end_x, end_y = polar_to_cartesian(end_angle, radius)
    
    # Arc path for value
    value_x, value_y = polar_to_cartesian(current_angle, radius)
    
    # Define colors to avoid f-string issues
    bg_color = "#E5E7EB"
    text_dark = "#1A202C"
    text_light = "#6B7280"
    
    return rx.box(
        rx.html(
            f"""
            <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}">
                <!-- Background arc -->
                <path d="M {start_x} {start_y} A {radius} {radius} 0 1 1 {end_x} {end_y}"
                      stroke="{bg_color}" 
                      stroke-width="8" 
                      fill="none" 
                      stroke-linecap="round" />
                
                <!-- Value arc -->
                <path d="M {start_x} {start_y} A {radius} {radius} 0 {1 if percentage > 50 else 0} 1 {value_x} {value_y}"
                      stroke="{gauge_color}" 
                      stroke-width="8" 
                      fill="none" 
                      stroke-linecap="round" />
                
                <!-- Center text -->
                <text x="{center}" y="{center - 5}" text-anchor="middle" font-size="18" font-weight="bold" fill="{text_dark}">
                    {value:.1f}
                </text>
                <text x="{center}" y="{center + 15}" text-anchor="middle" font-size="12" fill="{text_light}">
                    / {max_value:.0f}
                </text>
            </svg>
            """
        ),
        width=f"{size}px",
        height=f"{size}px",
        display="flex",
        justify_content="center",
        align_items="center"
    )