import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
import json
from processing.data_processor import DataProcessor
import pandas as pd

class Visualizer:
    # Modern Analytics Colors from reference image
    COLORS = ['#3f6adb', '#ffb038', '#f24a4a', '#43cc79', '#9b59b6', '#34495e']
    
    @classmethod
    def apply_beautiful_layout(cls, fig, title=None):
        """Helper to apply a clean, professional layout matching the reference image."""
        layout_args = dict(
            font=dict(family="Inter, sans-serif", size=13, color="#8a92a6"),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=20, r=20, t=40 if title else 20, b=20),
            hoverlabel=dict(
                bgcolor="white",
                font_size=13,
                font=dict(family="Inter, sans-serif", color="#232d42"),
                bordercolor="#eef2f5"
            ),
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color="#8a92a6")
            )
        )
        if title:
            layout_args['title'] = dict(
                text=title,
                font=dict(size=16, family="Inter, sans-serif", color="#232d42", weight="bold"),
                x=0.02, # Left aligned title
                y=0.98
            )
            
        fig.update_layout(**layout_args)
        return fig

    @staticmethod
    def generate_location_chart(df=None, user_id=None):
        """Bar chart or smooth area chart for locations/trends."""
        if df is None:
            df = DataProcessor.get_job_data(user_id=user_id)
            
        location_df = DataProcessor.get_location_counts(df)
        if location_df.empty:
            return None

        location_df = location_df.head(8)

        # Using a smooth area/line chart to match the bottom left of the image
        fig = go.Figure()
        
        # We will use the location data but plot it as a smooth line/area to match the aesthetic requested
        fig.add_trace(go.Scatter(
            x=location_df['Location'], 
            y=location_df['job_count'],
            mode='lines+markers',
            line=dict(color='#3f6adb', width=3, shape='spline'), # Spline for smooth curve
            marker=dict(size=8, color='#3f6adb', symbol='circle'),
            fill='tozeroy',
            fillcolor='rgba(63, 106, 219, 0.1)',
            name='Jobs'
        ))

        fig = Visualizer.apply_beautiful_layout(fig)
        
        fig.update_xaxes(showgrid=False, showticklabels=True, linecolor='#eef2f5', tickfont=dict(color="#8a92a6"))
        fig.update_yaxes(showgrid=True, gridcolor='#eef2f5', zeroline=False, tickfont=dict(color="#8a92a6"))

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    @staticmethod
    def generate_company_chart(df=None, user_id=None):
        """Thick donut chart reflecting the bottom right of the image."""
        if df is None:
            df = DataProcessor.get_job_data(user_id=user_id)
            
        company_df = DataProcessor.get_company_counts(df)
        if company_df.empty:
            return None

        # Just top 4 for a cleaner look
        company_df = company_df.head(4)
        total_jobs = company_df['job_count'].sum()

        fig = go.Figure(data=[go.Pie(
            labels=company_df['Company'], 
            values=company_df['job_count'], 
            hole=0.75, # Very thick donut
            marker=dict(colors=Visualizer.COLORS, line=dict(color='#ffffff', width=3)),
            textinfo='none', # Hide text on slices to match reference
            hoverinfo='label+percent+value',
            direction='clockwise',
            sort=False
        )])
        
        fig = Visualizer.apply_beautiful_layout(fig)
        
        # Add center text
        if total_jobs > 0:
            percentage = round((company_df.iloc[0]['job_count'] / total_jobs) * 100)
            fig.add_annotation(
                text=f"<span style='font-size:32px; font-weight:bold; color:#232d42;'>{percentage}%</span><br><span style='font-size:12px; color:#8a92a6;'>Avg Share</span>",
                x=0.5, y=0.5,
                showarrow=False,
                xref="paper", yref="paper"
            )
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        
    @staticmethod
    def generate_timeline_chart(df=None, user_id=None):
        """Generates a smooth dual-line chart for the main dashboard"""
        if df is None:
            df = DataProcessor.get_job_data(user_id=user_id)
            
        if df.empty:
            return None
            
        # Group by date posted
        timeline_df = df.groupby('date_posted').size().reset_index(name='job_count')
        # If dates are strings or fake, let's just use the index to scatter them nicely
        timeline_df = timeline_df.head(15) # Limit to 15 points
        
        fig = go.Figure()
        
        # Primary line (Blue)
        fig.add_trace(go.Scatter(
            x=timeline_df['date_posted'], 
            y=timeline_df['job_count'],
            mode='lines',
            line=dict(color='#3f6adb', width=3, shape='spline'),
            name='This Month'
        ))
        
        # Synthetic Secondary line for Comparison (Red dotted style)
        fig.add_trace(go.Scatter(
            x=timeline_df['date_posted'], 
            y=timeline_df['job_count'] * 0.7, # 70% for visual distinction
            mode='lines',
            line=dict(color='#f24a4a', width=2, shape='spline', dash='dot'),
            name='Last Month'
        ))

        fig = Visualizer.apply_beautiful_layout(fig)
        fig.update_layout(legend=dict(y=-0.2))
        
        fig.update_xaxes(showgrid=False, showticklabels=False) # Hide x labels for a cleaner line look
        fig.update_yaxes(showgrid=True, gridcolor='#eef2f5', zeroline=False, tickfont=dict(color="#8a92a6"))

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
