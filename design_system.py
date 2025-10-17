"""
Design System for Load Forecaster Dashboard
ThingsBoard-inspired color palette, typography, and CSS utilities
"""

# ============================================================
# COLOR PALETTE - Deep Blue Theme (ThingsBoard-inspired)
# ============================================================

class Colors:
    """Modern color system with deep blue/purple gradient"""
    
    # Primary Colors
    PRIMARY_DARK = "#3d4c7a"      # Deep navy blue (main brand)
    PRIMARY = "#5b6fa8"           # Soft blue-purple
    PRIMARY_LIGHT = "#7c8db5"     # Light blue-gray
    
    # Background Colors
    BG_APP = "#f5f7fa"            # Subtle blue-gray background
    BG_CARD = "#ffffff"           # Pure white cards
    BG_HOVER = "#f8f9fb"          # Hover state
    
    # Status Colors (Enhanced from original)
    SUCCESS = "#10b981"           # Emerald green (safe)
    WARNING = "#f59e0b"           # Amber (warning)
    DANGER = "#ef4444"            # Red (danger)
    INFO = "#3b82f6"              # Blue (info)
    
    # Text Colors
    TEXT_PRIMARY = "#1f2937"      # Almost black
    TEXT_SECONDARY = "#6b7280"    # Gray
    TEXT_MUTED = "#9ca3af"        # Light gray
    
    # Border & Divider
    BORDER = "#e5e7eb"            # Light border
    DIVIDER = "#f3f4f6"           # Divider line
    
    # Chart Colors
    CHART_BLUE = "#5b6fa8"        # Primary chart color
    CHART_GREEN = "#10b981"       # Success chart
    CHART_ORANGE = "#f59e0b"      # Warning chart
    CHART_PURPLE = "#8b5cf6"      # Alternative chart


# ============================================================
# TYPOGRAPHY SYSTEM
# ============================================================

class Typography:
    """Font family, sizes, and weights"""
    
    FONT_FAMILY = "'Roboto', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif"
    
    # Font Sizes
    SIZE_HERO = "2.5rem"          # 40px
    SIZE_H1 = "1.875rem"          # 30px
    SIZE_H2 = "1.5rem"            # 24px
    SIZE_H3 = "1.25rem"           # 20px
    SIZE_H4 = "1.125rem"          # 18px
    SIZE_BODY = "0.9rem"          # 14.4px
    SIZE_SMALL = "0.8rem"         # 12.8px
    SIZE_TINY = "0.7rem"          # 11.2px
    
    # Font Weights
    WEIGHT_LIGHT = 300
    WEIGHT_REGULAR = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


# ============================================================
# SPACING SYSTEM (8px Grid)
# ============================================================

class Spacing:
    """Consistent spacing based on 8px grid"""
    
    XS = "0.25rem"   # 4px
    SM = "0.5rem"    # 8px
    MD = "1rem"      # 16px
    LG = "1.5rem"    # 24px
    XL = "2rem"      # 32px
    XXL = "3rem"     # 48px


# ============================================================
# SHADOW SYSTEM
# ============================================================

class Shadows:
    """Box shadow utilities for depth"""
    
    NONE = "none"
    SM = "0 1px 3px rgba(61, 76, 122, 0.08)"
    MD = "0 4px 6px rgba(61, 76, 122, 0.1)"
    LG = "0 10px 25px rgba(61, 76, 122, 0.12)"
    XL = "0 20px 40px rgba(61, 76, 122, 0.15)"
    
    # Hover shadows
    HOVER = "0 12px 24px rgba(61, 76, 122, 0.15)"


# ============================================================
# CSS GENERATOR FUNCTIONS
# ============================================================

def generate_modern_css(logo_base64: str = "") -> str:
    """
    Generate complete CSS with modern ThingsBoard-inspired styling
    
    Args:
        logo_base64: Base64 encoded logo image
        
    Returns:
        Complete CSS string for Streamlit markdown
    """
    
    css = f"""
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.1.3/dist/css/bootstrap.min.css" integrity="sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO" crossorigin="anonymous">
<link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap" rel="stylesheet">

<style>
/* ============================================================
   GLOBAL STYLES
   ============================================================ */
* {{
    font-family: {Typography.FONT_FAMILY};
}}

.stApp {{
    background-color: {Colors.BG_APP} !important;
}}

/* ============================================================
   HEADER SECTION
   ============================================================ */
.main-header {{
    background: linear-gradient(135deg, {Colors.PRIMARY_DARK} 0%, {Colors.PRIMARY} 100%);
    margin: -50px -80px 0 -80px;
    padding: 1.2rem 2rem;
    box-shadow: {Shadows.MD};
    position: sticky;
    top: 0;
    z-index: 999;
}}

.logo-section {{
    display: flex;
    align-items: center;
    gap: 1rem;
}}

.logo-section img {{
    height: 100px;
    width: auto;
    filter: brightness(0) invert(1);  /* Make logo white */
}}

.dashboard-title {{
    font-size: 1.8rem; 
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    color: white;
    margin: 0;
    letter-spacing: -0.5px;
}}

/* ============================================================
   FILTER CONTAINER
   ============================================================ */
.filter-container {{
    background: {Colors.BG_CARD};
    border-radius: 12px;
    box-shadow: {Shadows.SM};
    
    margin-bottom: 1.5rem;
}}

/* ============================================================
   MODERN CARD SYSTEM
   ============================================================ */
.card-modern {{
    background: {Colors.BG_CARD};
    border: none;
    border-radius: 12px;
    box-shadow: {Shadows.MD};
    margin-bottom: 1.5rem;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.card-modern:hover {{
    box-shadow: {Shadows.HOVER};
    transform: translateY(-2px);
}}

.card-header-modern {{
    background: linear-gradient(135deg, {Colors.PRIMARY_DARK} 0%, {Colors.PRIMARY} 100%);
    color: white;
    font-size: {Typography.SIZE_SMALL};
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 1rem 1.5rem;
    border: none;
    border-radius: 12px;
}}

.card-body-modern {{
    padding: 0.5rem 1rem 1rem 1rem;
    background-color: transparent;
    border-radius: 0 0 1rem 1rem;
}}

/* ============================================================
   RECOMMENDATION BAR CHART CONTAINER
   ============================================================ */
.recommendation-container {{
    background: {Colors.BG_CARD};
    border-radius: 12px;
    box-shadow: {Shadows.MD};
    padding: 0;
    margin-bottom: 1.5rem;
}}

.recommendation-header {{
    background: linear-gradient(135deg, {Colors.PRIMARY_DARK} 0%, {Colors.PRIMARY} 100%);
    color: white;
    font-size: {Typography.SIZE_SMALL};
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 1rem 1.5rem;
    border: none;
    border-radius: 12px;
}}

# .recommendation-body {{
#     padding: 1rem 5rem;
# }}

/* ============================================================
   STATUS BADGES
   ============================================================ */
.status-badge {{
    display: inline-block;
    padding: 0.35rem 0.8rem;
    border-radius: 20px;
    font-size: {Typography.SIZE_TINY};
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}

.badge-safe {{
    background-color: rgba(16, 185, 129, 0.15);
    color: {Colors.SUCCESS};
    border: 1px solid {Colors.SUCCESS};
}}

.badge-warning {{
    background-color: rgba(245, 158, 11, 0.15);
    color: {Colors.WARNING};
    border: 1px solid {Colors.WARNING};
}}

.badge-danger {{
    background-color: rgba(239, 68, 68, 0.15);
    color: {Colors.DANGER};
    border: 1px solid {Colors.DANGER};
}}

/* ============================================================
   DATA TABLE (Enhanced)
   ============================================================ */

.data-table {{
    font-size: {Typography.SIZE_SMALL};
    max-height: 320px;
    overflow-y: auto;
    border-radius: 8px;
}}

.data-table::-webkit-scrollbar {{
    width: 6px;
}}

.data-table::-webkit-scrollbar-track {{
    background: {Colors.DIVIDER};
    border-radius: 10px;
}}

.data-table::-webkit-scrollbar-thumb {{
    background: {Colors.PRIMARY};
    border-radius: 10px;
}}

.data-table table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
}}

.data-table th {{
    background: linear-gradient(135deg, {Colors.PRIMARY_DARK} 0%, {Colors.PRIMARY} 100%);
    color: white;
    font-weight: {Typography.WEIGHT_SEMIBOLD};
    padding: 0.75rem 1rem;
    text-align: left;
    position: sticky;
    top: 0;
    font-size: {Typography.SIZE_SMALL};
    z-index: 10;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

.data-table th:first-child {{
    border-top-left-radius: 8px;
}}

.data-table th:last-child {{
    border-top-right-radius: 8px;
}}

.data-table td {{
    padding: 0.65rem 1rem;
    border-bottom: 1px solid {Colors.DIVIDER};
    color: {Colors.TEXT_PRIMARY};
}}

.data-table tbody tr {{
    transition: background-color 0.2s ease;
}}

.data-table tbody tr:nth-child(even) {{
    background-color: {Colors.BG_HOVER};
}}

.data-table tbody tr:hover {{
    background-color: rgba(91, 111, 168, 0.08);
}}

/* ============================================================
   LOAD INDICATORS
   ============================================================ */
.high-load {{
    color: {Colors.DANGER};
    font-weight: {Typography.WEIGHT_BOLD};
}}

.medium-load {{
    color: {Colors.WARNING};
    font-weight: {Typography.WEIGHT_SEMIBOLD};
}}

.low-load {{
    color: {Colors.SUCCESS};
    font-weight: {Typography.WEIGHT_MEDIUM};
}}

/* ============================================================
   PLOTLY CHART CONTAINER
   ============================================================ */
.stPlotlyChart {{
    background: {Colors.BG_CARD};
    border-radius: 8px;
}}

/* ============================================================
   HIDE STREAMLIT BRANDING
   ============================================================ */
#MainMenu {{visibility: hidden;}}
footer {{visibility: hidden;}}
header {{visibility: hidden;}}

/* ============================================================
   RESPONSIVE ADJUSTMENTS
   ============================================================ */
@media (max-width: 768px) {{
    .main-header {{
        margin: -30px -20px 0 -20px;
        padding: 1rem;
    }}
    
    .logo-section img {{
        height: 50px;
    }}
    
    .dashboard-title {{
        font-size: {Typography.SIZE_H3};
    }}
}}
</style>

<div class="main-header">
    <div class="logo-section">
        {'<img src="data:image/png;base64,' + logo_base64 + '" alt="LoadStar Logo">' if logo_base64 else ''}
        <div class="dashboard-title">Load Forecaster Dashboard</div>
    </div>
</div>
"""
    
    return css


# ============================================================
# GRADIENT HELPER FUNCTIONS
# ============================================================

def get_chart_gradient(color_hex: str, intensity: str = 'medium') -> dict:
    """
    Create multi-layer gradient configuration for Plotly charts
    
    Args:
        color_hex: Hex color code (e.g., '#5b6fa8')
        intensity: 'light', 'medium', or 'strong'
        
    Returns:
        Plotly fillgradient dictionary
    """
    # Convert hex to RGB
    rgb = tuple(int(color_hex.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    intensity_map = {
        'light': (0, 0.3),
        'medium': (0, 0.5),
        'strong': (0, 0.7)
    }
    
    start_alpha, end_alpha = intensity_map.get(intensity, (0, 0.5))
    
    return dict(
        type="vertical",
        colorscale=[
            [0, f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{start_alpha})"],
            [0.5, f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{end_alpha * 0.7})"],
            [1, f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{end_alpha})"]
        ]
    )


def get_status_color(max_load: float, warning_threshold: float = 320.0, max_capacity: float = 400.0) -> tuple:
    """
    Determine status color based on load value
    
    Args:
        max_load: Maximum load value
        warning_threshold: Warning threshold (default 320A)
        max_capacity: Maximum capacity (default 400A)
        
    Returns:
        Tuple of (status_code, color_hex, label)
    """
    if max_load < warning_threshold:
        return ('safe', Colors.SUCCESS, 'Aman')
    elif warning_threshold <= max_load < max_capacity:
        return ('warning', Colors.WARNING, 'Mendekati Batas')
    else:
        return ('danger', Colors.DANGER, 'Tidak Aman')