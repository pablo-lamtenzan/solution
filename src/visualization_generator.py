"""
Visualization Generator for Paint Quality Analysis
Creates stakeholder-friendly visualizations for business communication.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

class VisualizationGenerator:
    """Generate business-focused visualizations for paint quality analysis."""
    
    def __init__(self, analyzer):
        """Initialize with analyzer instance."""
        self.analyzer = analyzer
        self.df = analyzer.df
        self.batch_df = analyzer.batch_df
        
    def create_executive_dashboard(self):
        """Create executive summary dashboard."""
        print("Creating Executive Dashboard...")
        
        # Create subplot figure
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=[
                'Failure Rate by Recipe Complexity',
                'Temperature Impact on Quality',
                'Station Performance Comparison',
                'Monthly Failure Trends'
            ],
            specs=[[{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Recipe Complexity Impact
        complexity_data = self.batch_df.groupby('Num_Ingredients_first')['Failed'].agg(['count', 'mean']).reset_index()
        complexity_data = complexity_data[complexity_data['count'] >= 10]  # Filter for statistical significance
        
        fig.add_trace(
            go.Scatter(
                x=complexity_data['Num_Ingredients_first'],
                y=complexity_data['mean'] * 100,
                mode='lines+markers',
                name='Failure Rate',
                line=dict(color='red', width=3),
                marker=dict(size=8)
            ),
            row=1, col=1
        )
        
        # Add complexity threshold line
        fig.add_vline(x=15, line_dash="dash", line_color="orange", 
                     annotation_text="Complexity Threshold", row=1, col=1)
        
        # 2. Temperature Impact
        temp_bins = pd.cut(self.batch_df['Facility_Temperature_mean'], bins=8)
        temp_data = self.batch_df.groupby(temp_bins)['Failed'].agg(['count', 'mean']).reset_index()
        temp_data['temp_midpoint'] = temp_data['Facility_Temperature_mean'].apply(lambda x: x.mid)
        
        fig.add_trace(
            go.Bar(
                x=temp_data['temp_midpoint'],
                y=temp_data['mean'] * 100,
                name='Failure Rate by Temp',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=1, col=2
        )
        
        # 3. Station Performance
        station_data = self.analyzer.analysis_results['systems_interactions']['station_analysis']
        
        fig.add_trace(
            go.Bar(
                x=station_data['Dosing_Station'],
                y=station_data['Failure_Rate'] * 100,
                name='Station Failure Rate',
                marker_color=['red' if x > 0.37 else 'green' for x in station_data['Failure_Rate']],
                text=[f"{x:.1%}" for x in station_data['Failure_Rate']],
                textposition='auto'
            ),
            row=2, col=1
        )
        
        # 4. Monthly Trends
        monthly_data = self.analyzer.analysis_results['systems_interactions']['temporal_analysis']
        
        fig.add_trace(
            go.Scatter(
                x=monthly_data.index,
                y=monthly_data['Failure_Rate'] * 100,
                mode='lines+markers',
                name='Monthly Failure Rate',
                line=dict(color='purple', width=3),
                marker=dict(size=8)
            ),
            row=2, col=2
        )
        
        # Update layout
        fig.update_layout(
            title_text="Paint Manufacturing Quality Crisis - Executive Dashboard",
            title_x=0.5,
            height=800,
            showlegend=False,
            font=dict(size=12)
        )
        
        # Update axes labels
        fig.update_xaxes(title_text="Number of Ingredients", row=1, col=1)
        fig.update_yaxes(title_text="Failure Rate (%)", row=1, col=1)
        
        fig.update_xaxes(title_text="Temperature (°C)", row=1, col=2)
        fig.update_yaxes(title_text="Failure Rate (%)", row=1, col=2)
        
        fig.update_xaxes(title_text="Dosing Station", row=2, col=1)
        fig.update_yaxes(title_text="Failure Rate (%)", row=2, col=1)
        
        fig.update_xaxes(title_text="Month", row=2, col=2)
        fig.update_yaxes(title_text="Failure Rate (%)", row=2, col=2)
        
        # Save dashboard
        fig.write_html("visualizations/executive_dashboard.html")
        print("Executive dashboard saved to visualizations/executive_dashboard.html")
        
        return fig
    
    def create_action_priority_chart(self):
        """Create action priority matrix."""
        print("Creating Action Priority Chart...")
        
        # Define recommendations with impact and effort
        recommendations = [
            {'Action': 'Recipe Complexity\nLimits', 'Impact': 12.7, 'Effort': 1, 'Type': 'Policy'},
            {'Action': 'Temperature\nControl', 'Impact': 10.6, 'Effort': 3, 'Type': 'Infrastructure'},
            {'Action': 'Station D03\nMaintenance', 'Impact': 5.0, 'Effort': 2, 'Type': 'Maintenance'},
            {'Action': 'Station D07\nCalibration', 'Impact': 4.5, 'Effort': 2, 'Type': 'Maintenance'},
            {'Action': 'Dosing Error\nReduction', 'Impact': 8.0, 'Effort': 4, 'Type': 'Process'}
        ]
        
        df_rec = pd.DataFrame(recommendations)
        
        # Create priority matrix
        fig = px.scatter(
            df_rec, 
            x='Effort', 
            y='Impact',
            color='Type',
            size='Impact',
            hover_name='Action',
            title='Action Priority Matrix: Impact vs Implementation Effort',
            labels={
                'Effort': 'Implementation Effort (1=Easy, 5=Hard)',
                'Impact': 'Expected Failure Rate Reduction (%)'
            }
        )
        
        # Add quadrant lines
        fig.add_hline(y=7.5, line_dash="dash", line_color="gray", opacity=0.5)
        fig.add_vline(x=2.5, line_dash="dash", line_color="gray", opacity=0.5)
        
        # Add quadrant labels
        fig.add_annotation(x=1.5, y=11, text="Quick Wins", showarrow=False, font=dict(size=14, color="green"))
        fig.add_annotation(x=4, y=11, text="Major Projects", showarrow=False, font=dict(size=14, color="orange"))
        fig.add_annotation(x=1.5, y=4, text="Fill-ins", showarrow=False, font=dict(size=14, color="gray"))
        fig.add_annotation(x=4, y=4, text="Questionable", showarrow=False, font=dict(size=14, color="red"))
        
        # Update layout
        fig.update_layout(
            width=800,
            height=600,
            font=dict(size=12)
        )
        
        # Save chart
        fig.write_html("visualizations/action_priority_matrix.html")
        print("Action priority matrix saved to visualizations/action_priority_matrix.html")
        
        return fig
    
    def create_station_analysis_chart(self):
        """Create detailed station analysis."""
        print("Creating Station Analysis Chart...")
        
        # Station performance data
        station_data = self.analyzer.analysis_results['systems_interactions']['station_analysis']
        station_bias = self.analyzer.analysis_results['systems_interactions']['station_bias']
        
        # Create subplot
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['Station Failure Rates', 'Station Dosing Bias'],
            specs=[[{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # Failure rates
        colors = ['red' if x > 0.37 else 'orange' if x > 0.35 else 'green' 
                 for x in station_data['Failure_Rate']]
        
        fig.add_trace(
            go.Bar(
                x=station_data['Dosing_Station'],
                y=station_data['Failure_Rate'] * 100,
                name='Failure Rate',
                marker_color=colors,
                text=[f"{x:.1%}" for x in station_data['Failure_Rate']],
                textposition='auto'
            ),
            row=1, col=1
        )
        
        # Dosing bias
        bias_colors = ['red' if abs(x) > 0.6 else 'orange' if abs(x) > 0.4 else 'green' 
                      for x in station_bias.values]
        
        fig.add_trace(
            go.Bar(
                x=station_bias.index,
                y=station_bias.values,
                name='Dosing Bias',
                marker_color=bias_colors,
                text=[f"{x:+.3f}" for x in station_bias.values],
                textposition='auto'
            ),
            row=1, col=2
        )
        
        # Add reference lines
        fig.add_hline(y=33, line_dash="dash", line_color="red", 
                     annotation_text="Overall Failure Rate", row=1, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="black", row=1, col=2)
        
        # Update layout
        fig.update_layout(
            title_text="Dosing Station Performance Analysis",
            title_x=0.5,
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(title_text="Dosing Station", row=1, col=1)
        fig.update_yaxes(title_text="Failure Rate (%)", row=1, col=1)
        
        fig.update_xaxes(title_text="Dosing Station", row=1, col=2)
        fig.update_yaxes(title_text="Dosing Bias (Actual - Target)", row=1, col=2)
        
        # Save chart
        fig.write_html("visualizations/station_analysis.html")
        print("Station analysis saved to visualizations/station_analysis.html")
        
        return fig

if __name__ == "__main__":
    # Import analyzer and run visualizations
    import os
    os.makedirs("visualizations", exist_ok=True)
    
    from paint_analysis import PaintQualityAnalyzer
    
    # Initialize and run analysis
    analyzer = PaintQualityAnalyzer("data/paint_production_data.csv")
    analyzer.load_and_validate_data()
    analyzer.analyze_fundamental_components()
    analyzer.analyze_systems_interactions()
    
    # Generate visualizations
    viz_gen = VisualizationGenerator(analyzer)
    viz_gen.create_executive_dashboard()
    viz_gen.create_action_priority_chart()
    viz_gen.create_station_analysis_chart()
    
    print("\nAll visualizations created successfully!")
