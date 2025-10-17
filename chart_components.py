"""
Chart Components for Load Forecaster Dashboard
Modern Plotly chart creation with ThingsBoard-inspired styling
"""

import plotly.graph_objects as go
import pandas as pd
from typing import Optional, Tuple, List
from design_system import Colors, Typography, get_chart_gradient, get_status_color
from constants import WARNING_THRESHOLD, MAX_CAPACITY


# ============================================================
# RECOMMENDATION BAR CHART (Horizontal Stacked)
# ============================================================

def create_recommendation_bar_chart(partner_results: List[Tuple]) -> go.Figure:
    """
    Create horizontal bar chart for maneuver recommendations
    Similar to ThingsBoard's 'Electricity usage by device' visualization
    
    Args:
        partner_results: List of tuples (partner_name, max_load, status, label, dataframe)
        
    Returns:
        Plotly Figure object
    """
    if not partner_results:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="Tidak ada rekomendasi yang tersedia",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=Colors.TEXT_MUTED)
        )
        fig.update_layout(
            height=280,
            plot_bgcolor='white',
            paper_bgcolor='white',
            xaxis=dict(visible=False),
            yaxis=dict(visible=False)
        )
        return fig
    
    # Sort by max_load descending
    sorted_results = sorted(partner_results, key=lambda x: x[1], reverse=True)
    
    # Prepare data
    feeders = []
    loads = []
    colors = []
    texts = []
    hovertemplates = []
    
    color_map = {
        'safe': Colors.SUCCESS,
        'warning': Colors.WARNING,
        'danger': Colors.DANGER
    }
    
    for partner, max_load, status, label, _ in sorted_results:
        feeders.append(partner.upper())
        loads.append(max_load)
        colors.append(color_map.get(status, Colors.INFO))
        texts.append(f"{max_load:.1f} A")
        hovertemplates.append(
            f"<b>{partner.upper()}</b><br>"
            f"Beban Maksimal: {max_load:.1f} A<br>"
            f"Status: {label}"
            "<extra></extra>"
        )
    
    # Create figure
    fig = go.Figure()
    
    # Add bars
    fig.add_trace(go.Bar(
        y=feeders,
        x=loads,
        orientation='h',
        marker=dict(
            color=colors,
            line=dict(color='white', width=2)
        ),
        text=texts,
        textposition='inside',
        textfont=dict(
            color='white',
            size=11,
            family=Typography.FONT_FAMILY,
            weight=600
        ),
        hovertemplate=hovertemplates,
        showlegend=False
    ))
    
    # Add reference line at warning threshold
    fig.add_vline(
        x=WARNING_THRESHOLD,
        line_dash="dash",
        line_color=Colors.WARNING,
        line_width=2,
        annotation_text=f"Batas Warning ({WARNING_THRESHOLD:.0f}A)",
        annotation_position="top",
        annotation=dict(
            font=dict(size=9, color=Colors.WARNING, family=Typography.FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
            borderpad=4
        )
    )
    
    # Add reference line at max capacity
    fig.add_vline(
        x=MAX_CAPACITY,
        line_dash="dot",
        line_color=Colors.DANGER,
        line_width=2,
        annotation_text=f"Kapasitas Max ({MAX_CAPACITY:.0f}A)",
        annotation_position="bottom",
        annotation=dict(
            font=dict(size=9, color=Colors.DANGER, family=Typography.FONT_FAMILY),
            bgcolor="rgba(255,255,255,0.9)",
            borderpad=4
        )
    )
    
    fig.update_traces(
        width=0.5,  
        marker=dict(
            line=dict(width=0)
        )
    )

    fig.update_layout(
        height=len(feeders) * 80 + 120,  # Dynamic height: 80px per bar + 120px for margins
        plot_bgcolor='rgba(255,255,255,0.5)',
        paper_bgcolor='white',
        margin=dict(l=140, r=80, t=20, b=60),
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            title=dict(
                text="Beban Maksimal (A)",
                font=dict(
                    size=12,
                    color=Colors.TEXT_SECONDARY,
                    family=Typography.FONT_FAMILY
                )
            ),
            range=[0, max(MAX_CAPACITY * 1.1, max(loads) * 1.1) if loads else MAX_CAPACITY * 1.1],
            tickfont=dict(size=11, color=Colors.TEXT_SECONDARY)
        ),
        yaxis=dict(
            showgrid=False,
            title="",
            tickfont=dict(
                size=12,
                color=Colors.TEXT_PRIMARY,
                family=Typography.FONT_FAMILY,
                weight=500
            ),
            categoryorder='total ascending'
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family=Typography.FONT_FAMILY,
            bordercolor=Colors.BORDER
        ),
        bargap=0.3,
        bargroupgap=0.1
    )

    return fig

# ============================================================
# PARTNER FORECAST CHART (Small Multi-Chart)
# ============================================================

def create_partner_forecast_chart(
    partner_name: str,
    df_main: pd.DataFrame,
    df_partner: pd.DataFrame,
    status: str,
    max_load: float
) -> go.Figure:
    """
    Create individual forecast chart for partner feeder
    Used in 2x2 grid layout
    
    Args:
        partner_name: Name of partner feeder
        df_main: Main feeder forecast dataframe
        df_partner: Partner feeder forecast dataframe
        status: Status code ('safe', 'warning', 'danger')
        max_load: Maximum total load value
        
    Returns:
        Plotly Figure object
    """
    # Merge dataframes
    merged = pd.merge(
        df_main,
        df_partner,
        on="timestamp",
        suffixes=("_main", "_partner")
    )
    merged["total_transfer"] = merged["forecast_main"] + merged["forecast_partner"]
    
    # Determine colors based on status
    color_map = {
        'safe': Colors.SUCCESS,
        'warning': Colors.WARNING,
        'danger': Colors.DANGER
    }
    
    color_partner = Colors.CHART_PURPLE
    color_total = color_map.get(status, Colors.INFO)
    
    # Find peak
    peak_idx = merged["total_transfer"].idxmax()
    peak_value = merged.loc[peak_idx, "total_transfer"]
    peak_time = merged.loc[peak_idx, "timestamp"]
    
    # Create figure
    fig = go.Figure()
    
    # Trace 1: Partner feeder (with gradient fill)
    fig.add_trace(go.Scatter(
        x=df_partner["timestamp"],
        y=df_partner["forecast"].round(2),
        mode="lines",
        name=partner_name.upper(),
        line=dict(
            color=color_partner,
            width=2.5,
            shape="spline"
        ),
        fill="tozeroy",
        fillgradient=get_chart_gradient(color_partner, 'light'),
        hovertemplate=(
            f"<b>{partner_name.upper()}</b><br>"
            "Waktu: %{x|%d %b %H:%M}<br>"
            "Arus: %{y:.1f} A"
            "<extra></extra>"
        )
    ))
    
    # Trace 2: Total combined (with gradient fill)
    fig.add_trace(go.Scatter(
        x=merged["timestamp"],
        y=merged["total_transfer"].round(2),
        mode="lines+markers",
        name="Total Gabungan",
        line=dict(
            color=color_total,
            width=3.5,
            shape="spline"
        ),
        marker=dict(
            size=6,
            color=color_total,
            symbol="circle",
            line=dict(width=2, color="white")
        ),
        fill="tonexty",
        fillgradient=get_chart_gradient(color_total, 'medium'),
        hovertemplate=(
            "<b>Total Gabungan</b><br>"
            "Waktu: %{x|%d %b %H:%M}<br>"
            "Arus: %{y:.1f} A"
            "<extra></extra>"
        )
    ))
    
    # Add warning threshold line
    fig.add_hline(
        y=WARNING_THRESHOLD,
        line=dict(color=Colors.DANGER, dash="dash", width=2),
        annotation_text=f"Batas ({WARNING_THRESHOLD:.0f}A)",
        annotation_position="top right",
        annotation=dict(
            font=dict(size=8, color=Colors.DANGER, family=Typography.FONT_FAMILY, weight=600),
            bgcolor="rgba(255, 255, 255, 0.95)",
            borderpad=2,
            xshift=-5,
            yshift=-5
        )
    )
    
    # Add peak annotation
    fig.add_annotation(
        x=peak_time,
        y=peak_value,
        text=f"Peak: {peak_value:.1f} A",
        showarrow=True,
        arrowhead=2,
        arrowsize=1.2,
        arrowwidth=2.5,
        arrowcolor=color_total,
        ax=0,
        ay=-40,
        bgcolor="rgba(255, 255, 255, 0.98)",
        bordercolor=color_total,
        borderwidth=2.5,
        borderpad=6,
        font=dict(
            size=10,
            color=color_total,
            family=Typography.FONT_FAMILY,
            weight=700
        )
    )
    
    # Update layout
    fig.update_layout(
        height=300,
        title=dict(
            text=f"<b>{partner_name.upper()}</b>",
            font=dict(
                size=13,
                color=Colors.TEXT_PRIMARY,
                family=Typography.FONT_FAMILY,
                weight=600
            ),
            x=0.5,
            xanchor="center",
            y=0.97,
            yanchor="top"
        ),
        template="plotly_white",
        margin=dict(l=50, r=50, t=45, b=80),
        xaxis_title="",
        yaxis_title="Arus (A)",
        xaxis=dict(
            showgrid=True,
            gridcolor='#f3f4f6',
            tickformat="%d %b\n%H:%M",
            tickfont=dict(size=8, color=Colors.TEXT_SECONDARY, family=Typography.FONT_FAMILY),
            tickangle=0,
            automargin=True
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f3f4f6',
            tickfont=dict(size=9, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY),
            zeroline=True,
            zerolinecolor='#e5e7eb',
            zerolinewidth=1,
            range=[0, max(merged["total_transfer"].max() * 1.2, 360)],
            automargin=True
        ),
        plot_bgcolor='#fafbfc',
        paper_bgcolor='white',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=8, family=Typography.FONT_FAMILY),
            bgcolor="rgba(255, 255, 255, 0.9)",
            bordercolor=Colors.BORDER,
            borderwidth=1
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family=Typography.FONT_FAMILY,
            bordercolor=Colors.BORDER
        )
    )
    
    return fig


# ============================================================
# MAIN FORECAST CHART (72 Hours)
# ============================================================

def create_main_forecast_chart(df: pd.DataFrame, feeder_name: str) -> go.Figure:
    """
    Create main 72-hour forecast chart
    
    Args:
        df: Forecast dataframe with 'timestamp' and 'forecast' columns
        feeder_name: Name of the feeder
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    # Main forecast line with gradient
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["forecast"].round(2),
        mode="lines+markers",
        name=feeder_name.upper(),
        line=dict(
            color=Colors.SUCCESS,
            width=3,
            shape="spline"
        ),
        marker=dict(
            size=5,
            color=Colors.SUCCESS,
            line=dict(width=1.5, color="white")
        ),
        fill="tozeroy",
        fillgradient=get_chart_gradient(Colors.SUCCESS, 'medium'),
        hovertemplate=(
            f"<b>{feeder_name.upper()}</b><br>"
            "Waktu: %{x|%d %b %H:%M}<br>"
            "Prediksi: %{y:.1f} A"
            "<extra></extra>"
        )
    ))
    
    # Add warning threshold
    fig.add_hline(
        y=WARNING_THRESHOLD,
        line=dict(color=Colors.DANGER, dash="dash", width=2.5),
        annotation_text=f"Batas Aman ({WARNING_THRESHOLD:.0f} A)",
        annotation_position="top right",
        annotation=dict(
            font=dict(size=10, color=Colors.DANGER, family=Typography.FONT_FAMILY, weight=600),
            bgcolor="rgba(255, 255, 255, 0.95)",
            borderpad=4
        )
    )
    
    # Find and annotate peak if above warning
    if df["forecast"].max() > WARNING_THRESHOLD:
        peak_idx = df["forecast"].idxmax()
        peak_value = df.loc[peak_idx, "forecast"]
        peak_time = df.loc[peak_idx, "timestamp"]
        
        fig.add_annotation(
            x=peak_time,
            y=peak_value,
            text=f"Peak: {peak_value:.1f} A",
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=3,
            arrowcolor=Colors.DANGER,
            ax=0,
            ay=-50,
            bgcolor="rgba(255, 255, 255, 0.98)",
            bordercolor=Colors.DANGER,
            borderwidth=2.5,
            borderpad=8,
            font=dict(
                size=11,
                color=Colors.DANGER,
                family=Typography.FONT_FAMILY,
                weight=700
            )
        )
    
    # Update layout
    fig.update_layout(
        height=320,
        title=dict(
            text=f"<b>{feeder_name.upper()}</b>",
            font=dict(
                size=14,
                color=Colors.SUCCESS,
                family=Typography.FONT_FAMILY,
                weight=600
            ),
            x=0.02,
            y=0.98,
            xanchor="left",
            yanchor="top"
        ),
        template="plotly_white",
        margin=dict(l=60, r=40, t=50, b=60),
        xaxis_title="Waktu",
        yaxis_title="Arus (A)",
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickformat="%d %b\n%H:%M",
            tickfont=dict(size=10, color=Colors.TEXT_SECONDARY, family=Typography.FONT_FAMILY),
            title_font=dict(size=11, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=10, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY),
            title_font=dict(size=11, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY),
            range=[0, max(df["forecast"].max() * 1.15, WARNING_THRESHOLD * 1.1)]
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=11,
            font_family=Typography.FONT_FAMILY,
            bordercolor=Colors.BORDER
        )
    )
    
    return fig


# ============================================================
# REALTIME DATA CHART
# ============================================================

def create_realtime_chart(df: pd.DataFrame, feeder_name: str) -> go.Figure:
    """
    Create real-time historical data chart
    
    Args:
        df: Historical dataframe with 'timestamp' and 'arus' columns
        feeder_name: Name of the feeder
        
    Returns:
        Plotly Figure object
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df["timestamp"],
        y=df["arus"].round(2),
        mode="lines",
        name=feeder_name.upper(),
        line=dict(
            color=Colors.CHART_BLUE,
            width=2.5,
            shape="spline"
        ),
        fill='tozeroy',
        fillgradient=get_chart_gradient(Colors.CHART_BLUE, 'medium'),
        hovertemplate=(
            f"<b>{feeder_name.upper()}</b><br>"
            "Waktu: %{x|%d %b %H:%M}<br>"
            "Arus: %{y:.1f} A"
            "<extra></extra>"
        )
    ))
    
    fig.update_layout(
        height=280,
        title=dict(
            text=f"<b>{feeder_name.upper()}</b>",
            font=dict(
                size=13,
                color=Colors.CHART_BLUE,
                family=Typography.FONT_FAMILY,
                weight=600
            ),
            x=0.02,
            y=0.98,
            xanchor='left',
            yanchor='top'
        ),
        template="plotly_white",
        margin=dict(l=60, r=40, t=45, b=60),
        xaxis_title="Waktu",
        yaxis_title="Arus (A)",
        xaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickformat="%d %b\n%H:%M",
            tickfont=dict(size=9, color=Colors.TEXT_SECONDARY, family=Typography.FONT_FAMILY),
            title_font=dict(size=10, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY)
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#f0f0f0',
            tickfont=dict(size=9, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY),
            title_font=dict(size=10, color=Colors.TEXT_PRIMARY, family=Typography.FONT_FAMILY)
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        hoverlabel=dict(
            bgcolor="white",
            font_size=10,
            font_family=Typography.FONT_FAMILY,
            bordercolor=Colors.BORDER
        )
    )
    
    return fig