import streamlit as st
import pandas as pd
import pandas_datareader.data as web
import datetime
import plotly.graph_objects as go

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

# Create single chart visualization
def create_combined_chart(data):
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

# Create and display chart
chart = create_combined_chart(data)
st.plotly_chart(chart, use_container_width=True)

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

# Data controls
st.subheader("Data Exploration")
year_range = st.slider(
    "Select Year Range:",
    min_value=1970,
    max_value=datetime.datetime.now().year,
    value=(1970, datetime.datetime.now().year)
)

# Filter data based on selection
filtered_data = data[(data.index.year >= year_range[0]) & (data.index.year <= year_range[1])]

# Display metrics
st.metric("Current National Debt", f"${filtered_data['National Debt'].iloc[-1]:,.0f} Billion")
st.metric("Current Fed Rate", f"{filtered_data['Fed Funds Rate'].iloc[-1]:.2f}%")
st.metric("Current GDP", f"${filtered_data['GDP'].iloc[-1]:,.0f} Billion")
st.metric("Current Inflation", f"{filtered_data['Inflation'].iloc[-1]:.2f}%")

# Footer
st.markdown("---")
st.caption("""
**Data Source**: Federal Reserve Economic Data (FRED) | 
**National Debt**: GFDEBTN | **Fed Rate**: FEDFUNDS | 
**GDP**: GDP | **Inflation**: CPIAUCSL
""")
