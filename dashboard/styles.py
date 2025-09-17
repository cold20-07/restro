"""Design system styles and theme configuration for the dashboard"""

import reflex as rx

# Color palette based on design requirements
COLORS = {
    # Primary brand colors
    "primary": "#FF6B35",
    "primary_hover": "#E55A2B",
    "primary_light": "#FFF5F5",
    
    # Status colors
    "success": "#10B981",
    "warning": "#F59E0B",
    "error": "#EF4444",
    "info": "#3B82F6",
    
    # Neutral colors
    "gray_50": "#F9FAFB",
    "gray_100": "#F3F4F6",
    "gray_200": "#E5E7EB",
    "gray_300": "#D1D5DB",
    "gray_400": "#9CA3AF",
    "gray_500": "#6B7280",
    "gray_600": "#4B5563",
    "gray_700": "#374151",
    "gray_800": "#1F2937",
    "gray_900": "#111827",
    
    # Background colors
    "bg_primary": "#FFFFFF",
    "bg_secondary": "#F9FAFB",
    "bg_tertiary": "#F3F4F6",
    
    # Sidebar colors
    "sidebar_bg": "linear-gradient(180deg, #2D3748 0%, #1A202C 100%)",
    "sidebar_text": "#FFFFFF",
    "sidebar_text_muted": "#A0AEC0",
    "sidebar_active": "#FF6B35",
}

# Typography scale
TYPOGRAPHY = {
    "font_family": "Inter, system-ui, sans-serif",
    "font_sizes": {
        "xs": "0.75rem",
        "sm": "0.875rem",
        "base": "1rem",
        "lg": "1.125rem",
        "xl": "1.25rem",
        "2xl": "1.5rem",
        "3xl": "1.875rem",
        "4xl": "2.25rem",
    },
    "font_weights": {
        "normal": "400",
        "medium": "500",
        "semibold": "600",
        "bold": "700",
    },
    "line_heights": {
        "tight": "1.25",
        "normal": "1.5",
        "relaxed": "1.625",
    }
}

# Spacing scale
SPACING = {
    "xs": "0.25rem",
    "sm": "0.5rem",
    "md": "1rem",
    "lg": "1.5rem",
    "xl": "2rem",
    "2xl": "3rem",
    "3xl": "4rem",
}

# Border radius
BORDER_RADIUS = {
    "sm": "0.25rem",
    "md": "0.375rem",
    "lg": "0.5rem",
    "xl": "0.75rem",
    "2xl": "1rem",
    "full": "9999px",
}

# Box shadows
SHADOWS = {
    "sm": "0 1px 2px 0 rgba(0, 0, 0, 0.05)",
    "md": "0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)",
    "lg": "0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)",
    "xl": "0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)",
}

# Component styles
COMPONENT_STYLES = {
    "card": {
        "background": COLORS["bg_primary"],
        "border": f"1px solid {COLORS['gray_200']}",
        "border_radius": BORDER_RADIUS["lg"],
        "box_shadow": SHADOWS["sm"],
        "padding": SPACING["lg"],
    },
    
    "button_primary": {
        "background": COLORS["primary"],
        "color": "white",
        "border": "none",
        "border_radius": BORDER_RADIUS["md"],
        "font_weight": TYPOGRAPHY["font_weights"]["medium"],
        "_hover": {
            "background": COLORS["primary_hover"],
            "transform": "translateY(-1px)",
            "box_shadow": SHADOWS["md"],
        }
    },
    
    "button_secondary": {
        "background": "transparent",
        "color": COLORS["gray_700"],
        "border": f"1px solid {COLORS['gray_300']}",
        "border_radius": BORDER_RADIUS["md"],
        "font_weight": TYPOGRAPHY["font_weights"]["medium"],
        "_hover": {
            "background": COLORS["gray_50"],
            "border_color": COLORS["gray_400"],
        }
    },
    
    "input": {
        "border": f"1px solid {COLORS['gray_300']}",
        "border_radius": BORDER_RADIUS["md"],
        "padding": f"{SPACING['sm']} {SPACING['md']}",
        "font_size": TYPOGRAPHY["font_sizes"]["sm"],
        "_focus": {
            "border_color": COLORS["primary"],
            "box_shadow": f"0 0 0 3px {COLORS['primary']}33",
            "outline": "none",
        }
    },
    
    "sidebar_nav_item": {
        "padding": SPACING["md"],
        "border_radius": BORDER_RADIUS["md"],
        "color": COLORS["sidebar_text_muted"],
        "transition": "all 0.2s ease",
        "_hover": {
            "background": COLORS["sidebar_active"],
            "color": COLORS["sidebar_text"],
            "cursor": "pointer",
        }
    },
    
    "sidebar_nav_item_active": {
        "padding": SPACING["md"],
        "border_radius": BORDER_RADIUS["md"],
        "background": COLORS["sidebar_active"],
        "color": COLORS["sidebar_text"],
    },
    
    "metric_card": {
        "background": COLORS["bg_primary"],
        "border": f"1px solid {COLORS['gray_200']}",
        "border_radius": BORDER_RADIUS["lg"],
        "box_shadow": SHADOWS["sm"],
        "padding": SPACING["xl"],
        "transition": "all 0.2s ease",
        "_hover": {
            "box_shadow": SHADOWS["md"],
            "transform": "translateY(-2px)",
        }
    },
    
    "status_badge": {
        "padding": f"{SPACING['xs']} {SPACING['sm']}",
        "border_radius": BORDER_RADIUS["full"],
        "font_size": TYPOGRAPHY["font_sizes"]["xs"],
        "font_weight": TYPOGRAPHY["font_weights"]["medium"],
        "text_transform": "uppercase",
        "letter_spacing": "0.05em",
    }
}

# Status-specific styles
STATUS_STYLES = {
    "pending": {
        "color": "#92400E",
        "background": "#FEF3C7",
        "border": "1px solid #F59E0B",
    },
    "confirmed": {
        "color": "#1E40AF",
        "background": "#DBEAFE",
        "border": "1px solid #3B82F6",
    },
    "in_progress": {
        "color": "#C2410C",
        "background": "#FED7AA",
        "border": "1px solid #F97316",
    },
    "ready": {
        "color": "#7C2D12",
        "background": "#E0E7FF",
        "border": "1px solid #8B5CF6",
    },
    "completed": {
        "color": "#065F46",
        "background": "#D1FAE5",
        "border": "1px solid #10B981",
    },
    "canceled": {
        "color": "#991B1B",
        "background": "#FEE2E2",
        "border": "1px solid #EF4444",
    }
}

# Layout constants
LAYOUT = {
    "sidebar_width": "250px",
    "header_height": "64px",
    "content_padding": SPACING["xl"],
    "max_content_width": "1200px",
    "grid_gap": SPACING["xl"],
}

# Animation constants
ANIMATIONS = {
    "transition_fast": "all 0.15s ease",
    "transition_normal": "all 0.2s ease",
    "transition_slow": "all 0.3s ease",
    "bounce": "transform 0.2s cubic-bezier(0.68, -0.55, 0.265, 1.55)",
}

# Responsive breakpoints
BREAKPOINTS = {
    "sm": "640px",
    "md": "768px",
    "lg": "1024px",
    "xl": "1280px",
    "2xl": "1536px",
}

def get_theme():
    """Get the complete theme configuration for the dashboard"""
    return rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="orange",
        gray_color="slate",
        panel_background="solid",
        scaling="100%"
    )

def apply_component_style(component_type: str) -> dict:
    """Apply predefined styles to a component"""
    return COMPONENT_STYLES.get(component_type, {})

def get_status_style(status: str) -> dict:
    """Get status-specific styling"""
    return STATUS_STYLES.get(status.lower(), STATUS_STYLES["pending"])

# CSS custom properties for advanced styling
CUSTOM_CSS = """
:root {
    --primary-color: #FF6B35;
    --primary-hover: #E55A2B;
    --success-color: #10B981;
    --warning-color: #F59E0B;
    --error-color: #EF4444;
    --info-color: #3B82F6;
    
    --sidebar-bg: linear-gradient(180deg, #2D3748 0%, #1A202C 100%);
    --content-bg: #F9FAFB;
    
    --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    
    --transition-fast: all 0.15s ease;
    --transition-normal: all 0.2s ease;
    --transition-slow: all 0.3s ease;
}

/* Custom scrollbar styles */
::-webkit-scrollbar {
    width: 6px;
}

::-webkit-scrollbar-track {
    background: #F3F4F6;
}

::-webkit-scrollbar-thumb {
    background: #D1D5DB;
    border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
    background: #9CA3AF;
}

/* Animation keyframes */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes slideIn {
    from { transform: translateX(-100%); }
    to { transform: translateX(0); }
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.5; }
}

/* Utility classes */
.fade-in {
    animation: fadeIn 0.3s ease-out;
}

.slide-in {
    animation: slideIn 0.3s ease-out;
}

.pulse {
    animation: pulse 2s infinite;
}

/* Responsive utilities */
@media (max-width: 768px) {
    .hide-mobile {
        display: none !important;
    }
}

@media (min-width: 769px) {
    .show-mobile {
        display: none !important;
    }
}
"""