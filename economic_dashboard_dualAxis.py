import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import datetime
import plotly.graph_objects as go
import time

# Configure Streamlit page
st.set_page_config(
    page_title="US Economic Dashboard",
    page_icon="📊",
    layout="wide"
)

# Title and description
st.title("US Economic Indicators (1970-Present)")
st.markdown("""
This interactive visualization shows four key US economic metrics in a single chart:
- **National Debt** (Left axis, Billions $)
- **Federal Funds Rate** (Right axis, %)
- **GDP** (Left axis, Billions $)
- **Inflation** (Right axis, YoY %)
""")

# Cache data loading
@st.cache_data(ttl=24*3600)
def load_economic_data():
    start = datetime.datetime(1970, 1, 1)
    end = datetime.datetime.now()
    
    indicators = {
        'National Debt': 'GFDEBTN',
        'Fed Funds Rate': 'FEDFUNDS',
        'GDP': 'GDP',
        'Inflation': 'CPIAUCSL'
    }
    
    data = web.DataReader(list(indicators.values()), 'fred', start, end)
    data = data.ffill().dropna()
    data.columns = list(indicators.keys())
    data['Inflation'] = data['Inflation'].pct_change(periods=12) * 100
    return data

# Load data
with st.spinner('Loading economic data from FRED...'):
    data = load_economic_data()
st.success(f"Data loaded through {data.index[-1].strftime('%B %Y')}")

# Create animation visualization
def create_animated_chart(data, end_date=None):
    if end_date is None:
        end_date = data.index[-1]
    
    fig = go.Figure()
    

    # Add traces with dual axes
    fig.add_trace(go.Scatter(
        x=data.index, y=data['National Debt'],
        name="National Debt",
        line=dict(color='royalblue', width=2),
        yaxis="y1"
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['GDP'],
        name="GDP",
        line=dict(color='forestgreen', width=2, dash='dot'),
        yaxis="y1"
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Fed Funds Rate'],
        name="Fed Funds Rate",
        line=dict(color='crimson', width=2),
        yaxis="y2"
    ))
    
    fig.add_trace(go.Scatter(
        x=data.index, y=data['Inflation'],
        name="Inflation",
        line=dict(color='darkorange', width=2),
        yaxis="y2"
    ))

    # Add recession bands
    recessions = [
        (datetime.datetime(1973, 11, 1), datetime.datetime(1975, 3, 1)),
        (datetime.datetime(1980, 1, 1), datetime.datetime(1980, 7, 1)),
        (datetime.datetime(1981, 7, 1), datetime.datetime(1982, 11, 1)),
        (datetime.datetime(1990, 7, 1), datetime.datetime(1991, 3, 1)),
        (datetime.datetime(2001, 3, 1), datetime.datetime(2001, 11, 1)),
        (datetime.datetime(2007, 12, 1), datetime.datetime(2009, 6, 1)),
        (datetime.datetime(2020, 2, 1), datetime.datetime(2020, 4, 1))
    ]
    
    for rec in recessions:
        fig.add_vrect(
            x0=rec[0], x1=rec[1],
            fillcolor="gray", opacity=0.2,
            line_width=0
        )

    # Layout configuration
    fig.update_layout(
        title="US Economic Indicators (1970-Present)",
        xaxis_title="Year",
        yaxis=dict(
            title=dict(text="Debt & GDP (Billions $)", font=dict(color="royalblue")),
            tickfont=dict(color="royalblue"),
            side="left"
        ),
        yaxis2=dict(
            title=dict(text="Interest & Inflation (%)", font=dict(color="crimson")),
            tickfont=dict(color="crimson"),
            overlaying="y",
            side="right"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig


# Create animation controls
st.subheader("Time Animation Controls")
col1, col2, col3 = st.columns([1, 1, 3])
animation_frame = "Year",

with col1:
    if st.button("▶️ Play Animation"):
        play_animation = True
    else:
        play_animation = False

with col2:
    animation_speed = st.slider("Speed", 1, 10, 5, key="speed")

# Create placeholder for the chart
chart_placeholder = st.empty()

# Create and display initial chart
current_date = data.index[0] + datetime.timedelta(days=365*5)  # Start at 5 years in
chart = create_animated_chart(data, current_date)
chart_placeholder.plotly_chart(chart, use_container_width=True, key="main_chart")

# Create metrics placeholders
metric_cols = st.columns(4)
metric_placeholders = [col.empty() for col in metric_cols]

# Animation logic
if play_animation:
    # Get date range for animation
    start_date = data.index[0]
    end_date = data.index[-1]
    
    # Create date sequence (one point per quarter)
    dates = pd.date_range(start=start_date, end=end_date, freq='QS')
    
    # Calculate steps based on animation speed
    step = max(1, len(dates) // (50 * animation_speed))
    
    # Progress bar
    progress_bar = st.progress(0)
    
    # Animation loop
    for i, date in enumerate(dates[::step]):
        # Update chart
        chart = create_animated_chart(data, date)
        chart_placeholder.plotly_chart(chart, use_container_width=True, key=f"main_chart_{i}")
        
        # Update metrics
        current_data = data[data.index <= date].iloc[-1]
        metric_placeholders[0].metric("National Debt", 
                                     f"${current_data['National Debt']:,.0f}B",
                                     delta=None)
        metric_placeholders[1].metric("Fed Rate", 
                                     f"{current_data['Fed Funds Rate']:.2f}%",
                                     delta=None)
        metric_placeholders[2].metric("GDP", 
                                     f"${current_data['GDP']:,.0f}B",
                                     delta=None)
        metric_placeholders[3].metric("Inflation", 
                                     f"{current_data['Inflation']:.2f}%",
                                     delta=None)
        
        # Update progress
        progress = min(100, int((i * step) / len(dates) * 100))
        progress_bar.progress(progress)
        
        # Pause between frames
        time.sleep(0.5/ animation_speed)

    # Show final state
    chart = create_animated_chart(data)
    chart_placeholder.plotly_chart(chart, use_container_width=True)
    
    # Update metrics to current values
    current_data = data.iloc[-1]
    metric_placeholders[0].metric("National Debt", 
                                 f"${current_data['National Debt']:,.0f}B",
                                 delta=None)
    metric_placeholders[1].metric("Fed Rate", 
                                 f"{current_data['Fed Funds Rate']:.2f}%",
                                 delta=None)
    metric_placeholders[2].metric("GDP", 
                                 f"${current_data['GDP']:,.0f}B",
                                 delta=None)
    metric_placeholders[3].metric("Inflation", 
                                 f"{current_data['Inflation']:.2f}%",
                                 delta=None)
    
    # Complete progress bar
    progress_bar.progress(100)
    st.success("Animation complete!")

# Add analysis insights
st.subheader("Key Observations")
col1, col2 = st.columns(2)
with col1:
    st.markdown("""
    **Debt & GDP Relationship:**
    - Notice how debt growth accelerated after 2008 financial crisis
    - Debt-to-GDP ratio changes visible through relative positions
    """)
    
with col2:
    st.markdown("""
    **Interest & Inflation Correlation:**
    - Fed typically raises rates to combat high inflation
    - Periods where inflation exceeds rates indicate loose policy
    """)

# Footer
st.markdown("---")
st.caption("""
**Data Source**: Federal Reserve Economic Data (FRED) | 
**National Debt**: GFDEBTN | **Fed Rate**: FEDFUNDS | 
**GDP**: GDP | **Inflation**: CPIAUCSL
""")
