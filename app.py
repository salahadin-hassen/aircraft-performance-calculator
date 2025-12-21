import streamlit as st
import numpy as np
import plotly.graph_objects as go
from PIL import Image

# aircraft data
AIRPLANES = {
    "Cessna 172": {"weight_kg": 1111, "wing_area_m2": 16.2, "cl": 0.5, "cd": 0.03},
    "Boeing 737": {"weight_kg": 79000, "wing_area_m2": 125, "cl": 0.6, "cd": 0.02}
}

def calculate_lift(cl, velocity, wing_area):
    rho = 1.225
    return 0.5 * cl * rho * velocity**2 * wing_area

def calculate_drag(cd, velocity, wing_area):
    rho = 1.225
    return 0.5 * cd * rho * velocity**2 * wing_area

# App starts here
st.set_page_config(page_title="Aircraft Calculator", page_icon="✈️", layout="centered")
st.title("✈️ Aircraft Performance Calculator")

# 1. Select aircraft

st.header("1. Choose Aircraft")

aircraft_name = st.selectbox(
    "Select Aircraft",
    list(AIRPLANES.keys())
)

image_map = {
    "Cessna 172": "images/cessna172.jpg",
    "Boeing 737": "images/boeing737.jpg"
}

if aircraft_name in image_map:
    img = Image.open(image_map[aircraft_name])
    st.image(
        img,
        caption=aircraft_name,
        use_column_width=True
    )

    
    
plane = AIRPLANES[aircraft_name]

# 2. Flight conditions
st.header("2. Enter Flight Conditions")
velocity = st.slider("Speed (m/s)", 50, 300, 100)
altitude = st.slider("Altitude (feet)", 0, 40000, 5000)
# Add to flight conditions section
# 3. Calculate
if st.button("🚀 Calculate Performance", type="primary"):
    with st.spinner("Calculating..."):
        # Calculations
        lift = calculate_lift(plane["cl"], velocity, plane["wing_area_m2"])
        drag = calculate_drag(plane["cd"], velocity, plane["wing_area_m2"])
        weight = plane["weight_kg"] * 9.81
        
        # Display results
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Lift", f"{lift/1000:.1f} kN")
        with col2:
            st.metric("Drag", f"{drag/1000:.1f} kN")
        with col3:
            st.metric("Weight", f"{weight/1000:.1f} kN")
        
        # Status
        if lift > weight:
            st.success("✅ Enough lift to fly!")
        else:
            st.error("❌ Not enough lift!")
        
        # Plot
        st.header("3. Lift vs Speed")
        speeds = np.linspace(50, 300, 50)
        lifts = [calculate_lift(plane["cl"], v, plane["wing_area_m2"]) for v in speeds]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=speeds, y=lifts, name="Lift"))
        fig.add_hline(y=weight, line_dash="dash", line_color="red")
        fig.update_layout(xaxis_title="Speed (m/s)", yaxis_title="Lift (N)")
        st.plotly_chart(fig)

st.markdown("---")
url = "https://t.me/Voyager_557"
link_text = "Salahadin"
# st.markdown(f"Visit [{link_text}]({url})")
st.markdown(f"Built by [{link_text}]({url}) | Version 1.0")