import streamlit as st
import numpy as np
import plotly.graph_objects as go
from PIL import Image

# aircraft data
AIRPLANES = {
    "Cessna 172": {"weight_kg": 1111, "wing_area_m2": 16.2, "cl": 0.5, "cd": 0.03},
    "Boeing 737": {"weight_kg": 79000, "wing_area_m2": 125, "cl": 0.6, "cd": 0.02},
    "Piper PA-28": {"weight_kg": 950, "wing_area_m2": 15.8, "cl": 0.52, "cd": 0.028},
    "Cirrus SR22": {"weight_kg": 1542, "wing_area_m2": 13.5, "cl": 0.55, "cd": 0.025},
    "Beechcraft Bonanza": {"weight_kg": 1520, "wing_area_m2": 16.8, "cl": 0.53, "cd": 0.027},
    "Diamond DA40": {"weight_kg": 1150, "wing_area_m2": 13.5, "cl": 0.51, "cd": 0.026},
    
    "Airbus A320": {"weight_kg": 73500, "wing_area_m2": 122.6, "cl": 0.62, "cd": 0.018},
    "Boeing 747": {"weight_kg": 333400, "wing_area_m2": 541, "cl": 0.65, "cd": 0.016},
    "Airbus A380": {"weight_kg": 560000, "wing_area_m2": 845, "cl": 0.68, "cd": 0.015},
    "Boeing 787": {"weight_kg": 254000, "wing_area_m2": 377, "cl": 0.64, "cd": 0.017},
    "Embraer E175": {"weight_kg": 37400, "wing_area_m2": 72.7, "cl": 0.58, "cd": 0.021},
    "Bombardier CRJ900": {"weight_kg": 41500, "wing_area_m2": 70.3, "cl": 0.59, "cd": 0.02},
    
    "Gulfstream G650": {"weight_kg": 34800, "wing_area_m2": 105.6, "cl": 0.61, "cd": 0.019},
    "Cessna Citation X": {"weight_kg": 22600, "wing_area_m2": 55.6, "cl": 0.6, "cd": 0.02},
    "Bombardier Global 7500": {"weight_kg": 52600, "wing_area_m2": 127.2, "cl": 0.63, "cd": 0.018},
    
    "Concorde": {"weight_kg": 185000, "wing_area_m2": 358.3, "cl": 0.55, "cd": 0.024},
    "Cessna 152": {"weight_kg": 785, "wing_area_m2": 14.5, "cl": 0.48, "cd": 0.032},
    "Robinson R22": {"weight_kg": 417, "wing_area_m2": 0, "cl": 0, "cd": 0.08},  # Helicopter (rotor disc area)
    "Boeing CH-47": {"weight_kg": 10800, "wing_area_m2": 0, "cl": 0, "cd": 0.09},  # Helicopter
      # 1. WWII Fighter: Republic XP-69 (NACA test data, official)
    # Source: NACA Full-Scale Tunnel Tests [citation:1]
    "Republic XP-69": {
        "weight_kg": 8165,        # 18,000 lb [citation:1]
        "wing_area_m2": 46.9,     # 505 sq ft [citation:1]
        "cl": 0.48,              # Calculated from section lift coefficient [citation:1]
        "cd": 0.032,            # Typical for high-drag radial engine fighters
        "notes": "Experimental fighter, NACA 66 series airfoil"
    },
    
    # 2. Supersonic Bomber: Convair B-58 Hustler
    # Source: Official aircraft datasheet [citation:4]
    "Convair B-58 Hustler": {
        "weight_kg": 25200,       # Empty weight [citation:4]
        "wing_area_m2": 143.5,    # Calculated from span (17.3m) and aspect ratio (2.09) [citation:4]
        "cl": 0.35,              # Low CL for supersonic delta wing at cruise
        "cd": 0.024,            # Supersonic drag coefficient, zerolift Cd0=0.0068 [citation:4]
        "max_speed_mach": 2.0,   # [citation:4]
        "lift_to_drag": 11.3     # Subsonic [citation:4]
    },
    
    # 3. Modern Utility Transport: Pilatus PC-12 NG (Finnish Air Force)
    # Source: Finnish Defence Forces official specs [citation:7]
    "Pilatus PC-12 NG": {
        "weight_kg": 2800,        # Empty weight [citation:7]
        "wing_area_m2": 30.0,     # Calculated: span 16.28m, typical aspect ratio ~8.8
        "cl": 0.55,              # Efficient turboprop wing
        "cd": 0.026,            # Clean turboprop
        "mto_kg": 4760,         # Max takeoff [citation:7]
        "ceiling_m": 9144,      # [citation:7]
        "power_kw": 895         # PT6A-67P [citation:7]
    },
    
    # 4. Military Transport: C-12F Huron (Beechcraft Super King Air B200C)
    # Source: JBER.mil official fact sheet [citation:9]
    "C-12F Huron": {
        "weight_kg": 6750,        # Max gross takeoff weight [citation:9]
        "wing_area_m2": 28.2,     # Standard Super King Air wing area
        "cl": 0.52,             # Typical high-lift turboprop
        "cd": 0.027,           # [citation:9]
        "span_m": 16.52,       # [citation:9]
        "engine_shp": 850,     # PT6A-42 [citation:9]
        "range_km": 3658       # [citation:9]
    },
    
    # 5. British Supersonic Fighter: English Electric Lightning
    # Source: China Daily /新华网 technical specifications [citation:8]
    "English Electric Lightning": {
        "weight_kg": 13400,       # Empty weight [citation:8]
        "wing_area_m2": 44.5,     # Calculated from wing loading: 494 kg/m² at 16600kg [citation:8]
        "cl": 0.40,             # Supersonic fighter, moderate CL
        "cd": 0.028,           # Supersonic clean configuration
        "max_speed_mach": 2.2,  # [citation:8]
        "wing_loading_kgm2": 494, # Max [citation:8]
        "ceiling_m": 18300      # [citation:8]
    },
    
    # 6. WWII Transport: C-47 Skytrain (DC-3)
    # Source: WW2DB verified specifications [citation:3]
    "C-47 Skytrain": {
        "weight_kg": 8103,        # Empty weight [citation:3]
        "wing_area_m2": 91.69,    # Officially documented [citation:3]
        "cl": 0.64,             # High-lift wing with Fowler flaps
        "cd": 0.035,           # Higher drag due to radial engines, fixed gear
        "mto_kg": 14061,       # Maximum [citation:3]
        "span_m": 29.41,       # [citation:3]
        "range_km": 2575       # [citation:3]
    },
    
    # 7. Classic Fighter Reference (from wing loading data)
    # Source: Wikipedia Wing Loading archive [citation:5][citation:10]
    # Note: CL calculated from stall speed estimates
    "Supermarine Spitfire": {
        "weight_kg": 3000,        # Approximate combat weight
        "wing_area_m2": 22.5,     
        "cl": 0.58,             # Elliptical wing, excellent lift
        "cd": 0.028,
        "wing_loading_kgm2": 158  # [citation:5]
    },
    
    "Messerschmitt Bf 109": {
        "weight_kg": 3100,
        "wing_area_m2": 16.1,    
        "cl": 0.54,
        "cd": 0.029,
        "wing_loading_kgm2": 173  # [citation:5]
    },
    
    "F-104 Starfighter": {
        "weight_kg": 6350,        # Empty weight approx
        "wing_area_m2": 18.5,     # Very small wing
        "cl": 0.30,             # Very low CL, tiny wing, high landing speed
        "cd": 0.022,           # Very low drag for Mach 2
        "wing_loading_kgm2": 514  # [citation:5] - Extremely high
    },
    
    "Eurofighter Typhoon": {
        "weight_kg": 11000,       # Approx combat weight
        "wing_area_m2": 51.2,     
        "cl": 0.45,             # Delta-canard, high alpha capability
        "cd": 0.024,
        "wing_loading_kgm2": 311  # [citation:5]
    }
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
    "Boeing 737": "images/boeing737.jpg",
    "Piper PA-28": "images/Piper PA-28.jpg",
    "Cirrus SR22" : "images/Cirrus SR22.webp",
     "Beechcraft Bonanza" : "images/Beechcraft Bonanza.jpg",
     "Diamond DA40" : "images/Diamond DA40.jpg",
     "Airbus A320" : "images/Airbus A320.webp",
    "Boeing 787" : "images/Boeing 787.jpg",
     "Embraer E175" : "images/Embraer E175.jpg",
     "Bombardier CRJ900" : "images/Bombardier CRJ900.jpg",
     "Gulfstream G650" : "images/Gulfstream G650.jpg",
    "Cessna Citation X" : "images/Cessna Citation X.jpg",
    "Bombardier Global 7500" : "images/Bombardier Global 7500.jpg", 
     "Airbus A380" : "images/Airbus A380.jpg",
      "Concorde"   : "images/Concorde.jpg",
       "Cessna 152" : "images/Cessna 152.jpg",
     "Robinson R22" : "images/Robinson R22.jpg",
      "Boeing CH-47" : "images/Boeing CH-47.jpg",
    # about to add the image
    "Republic XP-69" : "images/Republic XP-69.jpg",
         "Convair B-58 Hustler" : "images/Convair B-58 Hustler.jpg",
       "Pilatus PC-12 NG" : "images/Pilatus PC-12 NG.jpg",
       "C-12F Huron" : "images/C-12F Huron.jpg",
     "English Electric Lightning" : "images/English Electric Lightning.jpg",
    "C-47 Skytrain" : "images/C-47 Skytrain.jpg",
    "Supermarine Spitfire" : "images/Supermarine Spitfire.jpg",
    "Messerschmitt Bf 109" : "image/Messerschmitt Bf 109.jpg",
    "F-104 Starfighter" : "images/F-104 Starfighter.jpg",
     "Eurofighter Typhoon" : "images/Eurofighter Typhoon.jpg"
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
