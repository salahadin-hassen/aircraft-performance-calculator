import streamlit as st
import numpy as np
import plotly.graph_objects as go
from PIL import Image

# STANDARD ATMOSPHERE MODEL (1976 US Standard)
def standard_atmosphere(altitude_ft):
    """
    US Standard Atmosphere 1976
    Returns density (kg/m³) at given altitude
    """
    h = altitude_ft * 0.3048  # Convert feet to meters
    
    # Troposphere (0-11,000m)
    if h <= 11000:
        temp = 288.15 - (0.0065 * h)
        pressure = 101325 * (temp / 288.15) ** 5.2561
    
    # Lower Stratosphere (11,000-20,000m)
    elif h <= 20000:
        temp = 216.65
        pressure = 22632.1 * np.exp(-0.0001577 * (h - 11000))
    
    # Upper Stratosphere (20,000-32,000m)
    else:
        temp = 216.65 + 0.001 * (h - 20000)
        pressure = 5474.89 * (216.65 / temp) ** 34.1632
    
    # Density
    R = 287.05
    rho = pressure / (R * temp)
    
    return rho

def calculate_lift(cl, velocity, wing_area, rho):
    if wing_area == 0 or cl == 0:
        return 0  # Helicopters or aircraft with no wing data
    return 0.5 * cl * rho * velocity**2 * wing_area

def calculate_drag(cd, velocity, wing_area, rho):
    if wing_area == 0:
        # For helicopters, use a reasonable reference area (rotor disc)
        ref_area = 50  # m², approximate rotor disc area
        return 0.5 * cd * rho * velocity**2 * ref_area
    return 0.5 * cd * rho * velocity**2 * wing_area

AIRCRAFT_CATEGORIES = {
    "🚁 Helicopters": {
        "Robinson R22": {"weight_kg": 417, "wing_area_m2": 0, "cl": 0, "cd": 0.08, "type": "helicopter"},
        "Boeing CH-47": {"weight_kg": 10800, "wing_area_m2": 0, "cl": 0, "cd": 0.09, "type": "helicopter"},
    },
    
    "🛩️ Light Aircraft": {
        "Cessna 152": {"weight_kg": 785, "wing_area_m2": 14.5, "cl": 0.48, "cd": 0.032, "type": "fixed"},
        "Cessna 172": {"weight_kg": 1111, "wing_area_m2": 16.2, "cl": 0.5, "cd": 0.03, "type": "fixed"},
        "Piper PA-28": {"weight_kg": 950, "wing_area_m2": 15.8, "cl": 0.52, "cd": 0.028, "type": "fixed"},
        "Diamond DA40": {"weight_kg": 1150, "wing_area_m2": 13.5, "cl": 0.51, "cd": 0.026, "type": "fixed"},
    },
    
    "💼 General Aviation": {
        "Cirrus SR22": {"weight_kg": 1542, "wing_area_m2": 13.5, "cl": 0.55, "cd": 0.025, "type": "fixed"},
        "Beechcraft Bonanza": {"weight_kg": 1520, "wing_area_m2": 16.8, "cl": 0.53, "cd": 0.027, "type": "fixed"},
    },
    
    "🛫 Turboprops": {
        "Pilatus PC-12 NG": {"weight_kg": 2800, "wing_area_m2": 30.0, "cl": 0.55, "cd": 0.026, "type": "fixed"},
        "C-12F Huron": {"weight_kg": 6750, "wing_area_m2": 28.2, "cl": 0.52, "cd": 0.027, "type": "fixed"},
    },
    
    "🛬 Regional Jets": {
        "Embraer E175": {"weight_kg": 37400, "wing_area_m2": 72.7, "cl": 0.58, "cd": 0.021, "type": "fixed"},
        "Bombardier CRJ900": {"weight_kg": 41500, "wing_area_m2": 70.3, "cl": 0.59, "cd": 0.02, "type": "fixed"},
    },
    
    "✈️ Business Jets": {
        "Cessna Citation X": {"weight_kg": 22600, "wing_area_m2": 55.6, "cl": 0.6, "cd": 0.02, "type": "fixed"},
        "Gulfstream G650": {"weight_kg": 34800, "wing_area_m2": 105.6, "cl": 0.61, "cd": 0.019, "type": "fixed"},
        "Bombardier Global 7500": {"weight_kg": 52600, "wing_area_m2": 127.2, "cl": 0.63, "cd": 0.018, "type": "fixed"},
    },
    
    "🌍 Commercial Narrow-Body": {
        "Boeing 737": {"weight_kg": 79000, "wing_area_m2": 125, "cl": 0.6, "cd": 0.02, "type": "fixed"},
        "Airbus A320": {"weight_kg": 73500, "wing_area_m2": 122.6, "cl": 0.62, "cd": 0.018, "type": "fixed"},
    },
    
    "🌎 Commercial Wide-Body": {
        "Boeing 747": {"weight_kg": 333400, "wing_area_m2": 541, "cl": 0.65, "cd": 0.016, "type": "fixed"},
        "Boeing 787": {"weight_kg": 254000, "wing_area_m2": 377, "cl": 0.64, "cd": 0.017, "type": "fixed"},
        "Airbus A380": {"weight_kg": 560000, "wing_area_m2": 845, "cl": 0.68, "cd": 0.015, "type": "fixed"},
    },
    
    "⚡ Supersonic": {
        "Concorde": {"weight_kg": 185000, "wing_area_m2": 358.3, "cl": 0.55, "cd": 0.024, "type": "fixed"},
        "Convair B-58 Hustler": {"weight_kg": 25200, "wing_area_m2": 143.5, "cl": 0.35, "cd": 0.024, "type": "fixed"},
        "English Electric Lightning": {"weight_kg": 13400, "wing_area_m2": 44.5, "cl": 0.40, "cd": 0.028, "type": "fixed"},
    },
    
    "⚔️ Military Fighters": {
        "F-104 Starfighter": {"weight_kg": 6350, "wing_area_m2": 18.5, "cl": 0.30, "cd": 0.022, "type": "fixed"},
        "Eurofighter Typhoon": {"weight_kg": 11000, "wing_area_m2": 51.2, "cl": 0.45, "cd": 0.024, "type": "fixed"},
        "Republic XP-69": {"weight_kg": 8165, "wing_area_m2": 46.9, "cl": 0.48, "cd": 0.032, "type": "fixed"},
    },
    
    "🛡️ Military Transport": {
        "C-47 Skytrain": {"weight_kg": 8103, "wing_area_m2": 91.69, "cl": 0.64, "cd": 0.035, "type": "fixed"},
    },
    
    "🕰️ WWII Classics": {
        "Supermarine Spitfire": {"weight_kg": 3000, "wing_area_m2": 22.5, "cl": 0.58, "cd": 0.028, "type": "fixed"},
        "Messerschmitt Bf 109": {"weight_kg": 3100, "wing_area_m2": 16.1, "cl": 0.54, "cd": 0.029, "type": "fixed"},
    }
}

AIRPLANES = {}
for category, aircraft_dict in AIRCRAFT_CATEGORIES.items():
    for name, data in aircraft_dict.items():
        AIRPLANES[name] = data


image_map = {
    "Cessna 172": "images/cessna172.jpg",
    "Boeing 737": "images/boeing737.jpg",
    "Piper PA-28": "images/Piper PA-28.jpg",
    "Cirrus SR22": "images/Cirrus SR22.webp",
    "Beechcraft Bonanza": "images/Beechcraft Bonanza.jpg",
    "Diamond DA40": "images/Diamond DA40.jpg",
    "Airbus A320": "images/Airbus A320.webp",
    "Boeing 787": "images/Boeing 787.jpg",
    "Embraer E175": "images/Embraer E175.jpg",
    "Bombardier CRJ900": "images/Bombardier CRJ900.jpg",
    "Gulfstream G650": "images/Gulfstream G650.jpg",
    "Cessna Citation X": "images/Cessna Citation X.jpg",
    "Bombardier Global 7500": "images/Bombardier Global 7500.jpg", 
    "Airbus A380": "images/Airbus A380.jpg",
    "Concorde": "images/Concorde.jpg",
    "Cessna 152": "images/Cessna 152.jpg",
    "Robinson R22": "images/Robinson R22.jpg",
    "Boeing CH-47": "images/Boeing CH-47.jpg",
    "Republic XP-69": "images/Republic XP-69.jpg",
    "Convair B-58 Hustler": "images/Convair B-58 Hustler.jpg",
    "Pilatus PC-12 NG": "images/Pilatus PC-12 NG.jpg",
    "C-12F Huron": "images/C-12F Huron.jpg",
    "English Electric Lightning": "images/English Electric Lightning.jpg",
    "C-47 Skytrain": "images/C-47 Skytrain.jpg",
    "Supermarine Spitfire": "images/Supermarine Spitfire.jpg",
    "Messerschmitt Bf 109": "image/Messerschmitt Bf 109.jpg",
    "F-104 Starfighter": "images/F-104 Starfighter.jpg",
    "Eurofighter Typhoon": "images/Eurofighter Typhoon.jpg"
}

# APP STARTS HERE

st.set_page_config(page_title="Aircraft Performance Calculator", page_icon="✈️", layout="centered")
st.title("✈️ Aircraft Performance Calculator")
st.caption("US Standard Atmosphere 1976 | Variable Density Model | Categorized Library")

# Aircraft Category
st.header("1. Choose Aircraft")

# Create two-column layout for selection
col1, col2 = st.columns([1, 1])

with col1:
    # First select the category
    category = st.selectbox(
        "Select Aircraft Category",
        list(AIRCRAFT_CATEGORIES.keys())
    )

with col2:
    # Then select aircraft from that category
    aircraft_name = st.selectbox(
        "Select Aircraft",
        list(AIRCRAFT_CATEGORIES[category].keys())
    )

# Category descriptions
category_info = {
    "🚁 Helicopters": "Rotary-wing aircraft for vertical flight",
    "🛩️ Light Aircraft": "Small, single-engine piston aircraft for training and personal use",
    "💼 General Aviation": "High-performance piston aircraft for business and personal travel",
    "🛫 Turboprops": "Turbine-powered propeller aircraft for regional transport",
    "🛬 Regional Jets": "Small jet airliners for short-haul routes",
    "✈️ Business Jets": "Fast, long-range jets for corporate travel",
    "🌍 Commercial Narrow-Body": "Single-aisle airliners for medium-range routes",
    "🌎 Commercial Wide-Body": "Twin-aisle airliners for long-haul international routes",
    "⚡ Supersonic": "Aircraft capable of supersonic flight",
    "⚔️ Military Fighters": "Combat aircraft for air superiority and attack",
    "🛡️ Military Transport": "Cargo and troop transport aircraft",
    "🕰️ WWII Classics": "Historic piston-engine fighters from World War II"
}

if category in category_info:
    st.caption(f"📌 {category_info[category]}")

# Display aircraft image
if aircraft_name in image_map:
    try:
        img = Image.open(image_map[aircraft_name])
        st.image(img, caption=aircraft_name, use_column_width=True)
    except Exception as e:
        st.caption(f"📷 Image for {aircraft_name} not found")
else:
    st.caption(f"📷 No image available for {aircraft_name}")

# Get the selected aircraft data
plane = AIRPLANES[aircraft_name]

# Display aircraft specifications
with st.expander("📋 Aircraft Specifications"):
    col1, col2, col3 = st.columns(3)
    col1.metric("Weight", f"{plane['weight_kg']} kg")
    if plane['wing_area_m2'] > 0:
        col2.metric("Wing Area", f"{plane['wing_area_m2']} m²")
        col3.metric("CL / CD", f"{plane['cl']} / {plane['cd']}")
    else:
        col2.metric("Rotorcraft", "Rotary wing", "N/A")
        col3.metric("Drag Coeff", f"{plane['cd']}", "Profile drag")

# ============================================================================
# FLIGHT CONDITIONS
# ============================================================================
st.header("2. Enter Flight Conditions")

col1, col2 = st.columns(2)
with col1:
    velocity = st.slider("Speed (m/s)", 0, 300, 100, 5)
with col2:
    altitude = st.slider("Altitude (feet)", 0, 40000, 5000, 1000)

# Show atmospheric conditions
rho = standard_atmosphere(altitude)
rho0 = 1.225
density_ratio = rho / rho0

with st.expander("📊 Atmospheric Conditions"):
    col1, col2, col3 = st.columns(3)
    col1.metric("Air Density", f"{rho:.3f} kg/m³", f"{density_ratio:.1%} of SL")
    col2.metric("Density Altitude", f"{altitude} ft")
    col3.metric("Pressure Altitude", f"{altitude} ft")

# CALCULATIONS

if st.button("🚀 Calculate Performance", type="primary"):
    with st.spinner("Calculating..."):
        
        rho = standard_atmosphere(altitude)
        
        # Get aircraft type
        aircraft_type = plane.get("type", "fixed")
        
        # Calculate lift and drag based on aircraft type
        if aircraft_type == "helicopter" or plane["wing_area_m2"] == 0:
            lift = 0
            # Use rotor disc area for drag calculation
            if aircraft_name == "Robinson R22":
                drag = 0.5 * plane["cd"] * rho * velocity**2 * 45  # ~7.5m rotor diameter
            elif aircraft_name == "Boeing CH-47":
                drag = 0.5 * plane["cd"] * rho * velocity**2 * 120  # ~18m rotor diameter
            else:
                drag = calculate_drag(plane["cd"], velocity, 0, rho)
        else:
            lift = calculate_lift(plane["cl"], velocity, plane["wing_area_m2"], rho)
            drag = calculate_drag(plane["cd"], velocity, plane["wing_area_m2"], rho)
        
        weight = plane["weight_kg"] * 9.81
        
        # Display results
        st.subheader("📋 Performance Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if aircraft_type == "helicopter" or plane["wing_area_m2"] == 0:
                st.metric("Lift", "N/A", "Rotary wing")
            else:
                st.metric("Lift", f"{lift/1000:.1f} kN")
        with col2:
            st.metric("Drag", f"{drag/1000:.1f} kN")
        with col3:
            st.metric("Weight", f"{weight/1000:.1f} kN")
        
        # Status indicators
        col1, col2 = st.columns(2)
        with col1:
            if aircraft_type == "helicopter" or plane["wing_area_m2"] == 0:
                st.info("🚁 Helicopter - Lift generated by rotor system")
                st.caption("Performance estimates are approximate")
            else:
                if lift > weight:
                    st.success("✅ SUFFICIENT LIFT - Aircraft can fly")
                    lift_margin = ((lift - weight) / weight) * 100
                    st.caption(f"Lift margin: {lift_margin:.1f}%")
                else:
                    st.error("❌ INSUFFICIENT LIFT - Will not fly")
                    if lift > 0:
                        lift_deficit = ((weight - lift) / weight) * 100
                        st.caption(f"Lift deficit: {lift_deficit:.1f}%")
        
        with col2:
            if altitude > 0 and aircraft_type == "fixed" and plane["wing_area_m2"] > 0:
                sea_level_lift = calculate_lift(plane["cl"], velocity, plane["wing_area_m2"], 1.225)
                lift_loss = (1 - (lift / sea_level_lift)) * 100
                st.info(f"🏔️ Altitude effect: {lift_loss:.1f}% lift loss")
            elif aircraft_type == "helicopter":
                # Rough estimate of rotor efficiency loss with altitude
                rotor_efficiency = density_ratio * 100
                st.info(f"🏔️ Rotor efficiency: {rotor_efficiency:.0f}% of sea level")
        
        # Plot for fixed-wing aircraft only
        if aircraft_type == "fixed" and plane["wing_area_m2"] > 0:
            st.subheader("3. Lift vs Speed")
            speeds = np.linspace(30, 300, 50)
            lifts = [calculate_lift(plane["cl"], v, plane["wing_area_m2"], rho) for v in speeds]
            sea_level_lifts = [calculate_lift(plane["cl"], v, plane["wing_area_m2"], 1.225) for v in speeds]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=speeds, y=lifts, 
                                    name=f"Lift at {altitude:,} ft",
                                    line=dict(color="#4FC3F7", width=3)))
            fig.add_trace(go.Scatter(x=speeds, y=sea_level_lifts,
                                    name="Lift at Sea Level",
                                    line=dict(color="#9E9E9E", width=2, dash="dash")))
            fig.add_hline(y=weight, line_dash="dash", line_color="#EF5350",
                         annotation_text="Aircraft Weight")
            
            fig.update_layout(
                xaxis_title="Speed (m/s)",
                yaxis_title="Lift (N)",
                hovermode="x unified",
                legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
                height=500
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Stall speed calculation
            if lift > 0:
                stall_speed = np.sqrt((2 * weight) / (rho * plane["wing_area_m2"] * plane["cl"]))
                st.caption(f"⚠️ Estimated stall speed: {stall_speed:.1f} m/s at current density")
        
        elif aircraft_type == "helicopter":
            st.subheader("3. Helicopter Performance Note")
            st.info("""
            **Helicopter Aerodynamics:**
            - Lift generated by rotor blades, not fixed wings
            - Main rotor acts as rotating wing
            - Drag includes profile drag + induced drag
            - Hover performance strongly affected by density altitude
            """)

st.markdown("---")
url = "https://t.me/Voyager_557"
link_text = "Salahadin"
st.markdown(f"Built by [{link_text}]({url}) | Version 2.1 - Categorized Aircraft Library")












#=====================================================================================


# import streamlit as st
# import numpy as np
# import plotly.graph_objects as go
# from PIL import Image

# # aircraft data
# AIRPLANES = {
#     "Cessna 172": {"weight_kg": 1111, "wing_area_m2": 16.2, "cl": 0.5, "cd": 0.03},
#     "Boeing 737": {"weight_kg": 79000, "wing_area_m2": 125, "cl": 0.6, "cd": 0.02},
#     "Piper PA-28": {"weight_kg": 950, "wing_area_m2": 15.8, "cl": 0.52, "cd": 0.028},
#     "Cirrus SR22": {"weight_kg": 1542, "wing_area_m2": 13.5, "cl": 0.55, "cd": 0.025},
#     "Beechcraft Bonanza": {"weight_kg": 1520, "wing_area_m2": 16.8, "cl": 0.53, "cd": 0.027},
#     "Diamond DA40": {"weight_kg": 1150, "wing_area_m2": 13.5, "cl": 0.51, "cd": 0.026},
    
#     "Airbus A320": {"weight_kg": 73500, "wing_area_m2": 122.6, "cl": 0.62, "cd": 0.018},
#     "Boeing 747": {"weight_kg": 333400, "wing_area_m2": 541, "cl": 0.65, "cd": 0.016},
#     "Airbus A380": {"weight_kg": 560000, "wing_area_m2": 845, "cl": 0.68, "cd": 0.015},
#     "Boeing 787": {"weight_kg": 254000, "wing_area_m2": 377, "cl": 0.64, "cd": 0.017},
#     "Embraer E175": {"weight_kg": 37400, "wing_area_m2": 72.7, "cl": 0.58, "cd": 0.021},
#     "Bombardier CRJ900": {"weight_kg": 41500, "wing_area_m2": 70.3, "cl": 0.59, "cd": 0.02},
    
#     "Gulfstream G650": {"weight_kg": 34800, "wing_area_m2": 105.6, "cl": 0.61, "cd": 0.019},
#     "Cessna Citation X": {"weight_kg": 22600, "wing_area_m2": 55.6, "cl": 0.6, "cd": 0.02},
#     "Bombardier Global 7500": {"weight_kg": 52600, "wing_area_m2": 127.2, "cl": 0.63, "cd": 0.018},
    
#     "Concorde": {"weight_kg": 185000, "wing_area_m2": 358.3, "cl": 0.55, "cd": 0.024},
#     "Cessna 152": {"weight_kg": 785, "wing_area_m2": 14.5, "cl": 0.48, "cd": 0.032},
#     "Robinson R22": {"weight_kg": 417, "wing_area_m2": 0, "cl": 0, "cd": 0.08},  # Helicopter (rotor disc area)
#     "Boeing CH-47": {"weight_kg": 10800, "wing_area_m2": 0, "cl": 0, "cd": 0.09},  # Helicopter
#       # 1. WWII Fighter: Republic XP-69 (NACA test data, official)
#     # Source: NACA Full-Scale Tunnel Tests [citation:1]
#     "Republic XP-69": {
#         "weight_kg": 8165,        # 18,000 lb [citation:1]
#         "wing_area_m2": 46.9,     # 505 sq ft [citation:1]
#         "cl": 0.48,              # Calculated from section lift coefficient [citation:1]
#         "cd": 0.032,            # Typical for high-drag radial engine fighters
#         "notes": "Experimental fighter, NACA 66 series airfoil"
#     },
    
#     # 2. Supersonic Bomber: Convair B-58 Hustler
#     # Source: Official aircraft datasheet [citation:4]
#     "Convair B-58 Hustler": {
#         "weight_kg": 25200,       # Empty weight [citation:4]
#         "wing_area_m2": 143.5,    # Calculated from span (17.3m) and aspect ratio (2.09) [citation:4]
#         "cl": 0.35,              # Low CL for supersonic delta wing at cruise
#         "cd": 0.024,            # Supersonic drag coefficient, zerolift Cd0=0.0068 [citation:4]
#         "max_speed_mach": 2.0,   # [citation:4]
#         "lift_to_drag": 11.3     # Subsonic [citation:4]
#     },
    
#     # 3. Modern Utility Transport: Pilatus PC-12 NG (Finnish Air Force)
#     # Source: Finnish Defence Forces official specs [citation:7]
#     "Pilatus PC-12 NG": {
#         "weight_kg": 2800,        # Empty weight [citation:7]
#         "wing_area_m2": 30.0,     # Calculated: span 16.28m, typical aspect ratio ~8.8
#         "cl": 0.55,              # Efficient turboprop wing
#         "cd": 0.026,            # Clean turboprop
#         "mto_kg": 4760,         # Max takeoff [citation:7]
#         "ceiling_m": 9144,      # [citation:7]
#         "power_kw": 895         # PT6A-67P [citation:7]
#     },
    
#     # 4. Military Transport: C-12F Huron (Beechcraft Super King Air B200C)
#     # Source: JBER.mil official fact sheet [citation:9]
#     "C-12F Huron": {
#         "weight_kg": 6750,        # Max gross takeoff weight [citation:9]
#         "wing_area_m2": 28.2,     # Standard Super King Air wing area
#         "cl": 0.52,             # Typical high-lift turboprop
#         "cd": 0.027,           # [citation:9]
#         "span_m": 16.52,       # [citation:9]
#         "engine_shp": 850,     # PT6A-42 [citation:9]
#         "range_km": 3658       # [citation:9]
#     },
    
#     # 5. British Supersonic Fighter: English Electric Lightning
#     # Source: China Daily /新华网 technical specifications [citation:8]
#     "English Electric Lightning": {
#         "weight_kg": 13400,       # Empty weight [citation:8]
#         "wing_area_m2": 44.5,     # Calculated from wing loading: 494 kg/m² at 16600kg [citation:8]
#         "cl": 0.40,             # Supersonic fighter, moderate CL
#         "cd": 0.028,           # Supersonic clean configuration
#         "max_speed_mach": 2.2,  # [citation:8]
#         "wing_loading_kgm2": 494, # Max [citation:8]
#         "ceiling_m": 18300      # [citation:8]
#     },
    
#     # 6. WWII Transport: C-47 Skytrain (DC-3)
#     # Source: WW2DB verified specifications [citation:3]
#     "C-47 Skytrain": {
#         "weight_kg": 8103,        # Empty weight [citation:3]
#         "wing_area_m2": 91.69,    # Officially documented [citation:3]
#         "cl": 0.64,             # High-lift wing with Fowler flaps
#         "cd": 0.035,           # Higher drag due to radial engines, fixed gear
#         "mto_kg": 14061,       # Maximum [citation:3]
#         "span_m": 29.41,       # [citation:3]
#         "range_km": 2575       # [citation:3]
#     },
    
#     # 7. Classic Fighter Reference (from wing loading data)
#     # Source: Wikipedia Wing Loading archive [citation:5][citation:10]
#     # Note: CL calculated from stall speed estimates
#     "Supermarine Spitfire": {
#         "weight_kg": 3000,        # Approximate combat weight
#         "wing_area_m2": 22.5,     
#         "cl": 0.58,             # Elliptical wing, excellent lift
#         "cd": 0.028,
#         "wing_loading_kgm2": 158  # [citation:5]
#     },
    
#     "Messerschmitt Bf 109": {
#         "weight_kg": 3100,
#         "wing_area_m2": 16.1,    
#         "cl": 0.54,
#         "cd": 0.029,
#         "wing_loading_kgm2": 173  # [citation:5]
#     },
    
#     "F-104 Starfighter": {
#         "weight_kg": 6350,        # Empty weight approx
#         "wing_area_m2": 18.5,     # Very small wing
#         "cl": 0.30,             # Very low CL, tiny wing, high landing speed
#         "cd": 0.022,           # Very low drag for Mach 2
#         "wing_loading_kgm2": 514  # [citation:5] - Extremely high
#     },
    
#     "Eurofighter Typhoon": {
#         "weight_kg": 11000,       # Approx combat weight
#         "wing_area_m2": 51.2,     
#         "cl": 0.45,             # Delta-canard, high alpha capability
#         "cd": 0.024,
#         "wing_loading_kgm2": 311  # [citation:5]
#     }
# }
# def calculate_lift(cl, velocity, wing_area):
#     rho = 1.225
#     return 0.5 * cl * rho * velocity**2 * wing_area

# def calculate_drag(cd, velocity, wing_area):
#     rho = 1.225
#     return 0.5 * cd * rho * velocity**2 * wing_area

# # App starts here
# st.set_page_config(page_title="Aircraft Calculator", page_icon="✈️", layout="centered")
# st.title("✈️ Aircraft Performance Calculator")

# # 1. Select aircraft

# st.header("1. Choose Aircraft")

# aircraft_name = st.selectbox(
#     "Select Aircraft",
#     list(AIRPLANES.keys())
# )

# image_map = {
#     "Cessna 172": "images/cessna172.jpg",
#     "Boeing 737": "images/boeing737.jpg",
#     "Piper PA-28": "images/Piper PA-28.jpg",
#     "Cirrus SR22" : "images/Cirrus SR22.webp",
#      "Beechcraft Bonanza" : "images/Beechcraft Bonanza.jpg",
#      "Diamond DA40" : "images/Diamond DA40.jpg",
#      "Airbus A320" : "images/Airbus A320.webp",
#     "Boeing 787" : "images/Boeing 787.jpg",
#      "Embraer E175" : "images/Embraer E175.jpg",
#      "Bombardier CRJ900" : "images/Bombardier CRJ900.jpg",
#      "Gulfstream G650" : "images/Gulfstream G650.jpg",
#     "Cessna Citation X" : "images/Cessna Citation X.jpg",
#     "Bombardier Global 7500" : "images/Bombardier Global 7500.jpg", 
#      "Airbus A380" : "images/Airbus A380.jpg",
#       "Concorde"   : "images/Concorde.jpg",
#        "Cessna 152" : "images/Cessna 152.jpg",
#      "Robinson R22" : "images/Robinson R22.jpg",
#       "Boeing CH-47" : "images/Boeing CH-47.jpg",
#     # about to add the image
#     "Republic XP-69" : "images/Republic XP-69.jpg",
#          "Convair B-58 Hustler" : "images/Convair B-58 Hustler.jpg",
#        "Pilatus PC-12 NG" : "images/Pilatus PC-12 NG.jpg",
#        "C-12F Huron" : "images/C-12F Huron.jpg",
#      "English Electric Lightning" : "images/English Electric Lightning.jpg",
#     "C-47 Skytrain" : "images/C-47 Skytrain.jpg",
#     "Supermarine Spitfire" : "images/Supermarine Spitfire.jpg",
#     "Messerschmitt Bf 109" : "image/Messerschmitt Bf 109.jpg",
#     "F-104 Starfighter" : "images/F-104 Starfighter.jpg",
#      "Eurofighter Typhoon" : "images/Eurofighter Typhoon.jpg"
# }

# if aircraft_name in image_map:
#     img = Image.open(image_map[aircraft_name])
#     st.image(
#         img,
#         caption=aircraft_name,
#         use_column_width=True
#     )

    
    
# plane = AIRPLANES[aircraft_name]

# # 2. Flight conditions
# st.header("2. Enter Flight Conditions")
# velocity = st.slider("Speed (m/s)", 50, 300, 100)
# altitude = st.slider("Altitude (feet)", 0, 40000, 5000)
# # Add to flight conditions section
# # 3. Calculate
# if st.button("🚀 Calculate Performance", type="primary"):
#     with st.spinner("Calculating..."):
#         # Calculations
#         lift = calculate_lift(plane["cl"], velocity, plane["wing_area_m2"])
#         drag = calculate_drag(plane["cd"], velocity, plane["wing_area_m2"])
#         weight = plane["weight_kg"] * 9.81
        
#         # Display results
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("Lift", f"{lift/1000:.1f} kN")
#         with col2:
#             st.metric("Drag", f"{drag/1000:.1f} kN")
#         with col3:
#             st.metric("Weight", f"{weight/1000:.1f} kN")
        
#         # Status
#         if lift > weight:
#             st.success("✅ Enough lift to fly!")
#         else:
#             st.error("❌ Not enough lift!")
        
#         # Plot
#         st.header("3. Lift vs Speed")
#         speeds = np.linspace(50, 300, 50)
#         lifts = [calculate_lift(plane["cl"], v, plane["wing_area_m2"]) for v in speeds]
        
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(x=speeds, y=lifts, name="Lift"))
#         fig.add_hline(y=weight, line_dash="dash", line_color="red")
#         fig.update_layout(xaxis_title="Speed (m/s)", yaxis_title="Lift (N)")
#         st.plotly_chart(fig)

# st.markdown("---")
# url = "https://t.me/Voyager_557"
# link_text = "Salahadin"
# # st.markdown(f"Visit [{link_text}]({url})")
# st.markdown(f"Built by [{link_text}]({url}) | Version 1.0")













#-----------------------------------AI version-#----------------------------------------#
# import streamlit as st
# import numpy as np
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# from PIL import Image
# import pandas as pd
# from scipy.interpolate import interp1d
# import json
# from datetime import datetime
# import io

# # ================================
# # PROFESSIONAL AEROSPACE DATABASE
# # ================================

# AIRPLANES = {
#     "Cessna 172 Skyhawk": {
#         "type": "Light GA",
#         "manufacturer": "Cessna",
#         "weight_kg": 1111,
#         "wing_area_m2": 16.2,
#         "aspect_ratio": 7.32,
#         "wing_span_m": 11.0,
#         "cl_alpha": 5.73,  # per radian
#         "cl_max": 1.6,
#         "cd0": 0.027,
#         "k": 0.054,  # induced drag factor
#         "engine_hp": 180,
#         "fuel_capacity_kg": 172,
#         "v_ne": 163.0,  # never exceed speed (m/s)
#         "v_no": 138,  # normal operating
#         "v_fe": 40,   # flaps extended
#         "service_ceiling_m": 4115,
#         "color": "#1f77b4"
#     },
#     "Boeing 737-800": {
#         "type": "Narrow-body Airliner",
#         "manufacturer": "Boeing",
#         "weight_kg": 79000,
#         "wing_area_m2": 125,
#         "aspect_ratio": 9.44,
#         "wing_span_m": 34.3,
#         "cl_alpha": 6.28,
#         "cl_max": 1.8,
#         "cd0": 0.020,
#         "k": 0.042,
#         "engine_thrust_n": 117000,
#         "fuel_capacity_kg": 26000,
#         "v_ne": 270.0,
#         "v_no": 250,
#         "v_fe": 85,
#         "service_ceiling_m": 12500,
#         "color": "#ff7f0e"
#     },
#     "Airbus A320neo": {
#         "type": "Narrow-body Airliner",
#         "manufacturer": "Airbus",
#         "weight_kg": 78000,
#         "wing_area_m2": 122.6,
#         "aspect_ratio": 9.39,
#         "wing_span_m": 35.8,
#         "cl_alpha": 6.5,
#         "cl_max": 1.85,
#         "cd0": 0.019,
#         "k": 0.038,
#         "engine_thrust_n": 120000,
#         "fuel_capacity_kg": 25000,
#         "v_ne": 275.0,
#         "v_no": 255,
#         "v_fe": 90,
#         "service_ceiling_m": 11900,
#         "color": "#2ca02c"
#     },
#     "F-16 Fighting Falcon": {
#         "type": "Multirole Fighter",
#         "manufacturer": "Lockheed Martin",
#         "weight_kg": 12000,
#         "wing_area_m2": 27.87,
#         "aspect_ratio": 3.0,
#         "wing_span_m": 9.96,
#         "cl_alpha": 8.0,
#         "cl_max": 2.2,
#         "cd0": 0.015,
#         "k": 0.12,
#         "engine_thrust_n": 130000,
#         "fuel_capacity_kg": 3200,
#         "v_ne": 945.0,  # Mach 2.05
#         "v_no": 800,
#         "v_fe": 300,
#         "service_ceiling_m": 15240,
#         "color": "#d62728"
#     }
# }

# # ================================
# # PROFESSIONAL ATMOSPHERE MODEL
# # ================================

# class InternationalStandardAtmosphere:
#     """ICAO International Standard Atmosphere Model (ISA)"""
    
#     @staticmethod
#     def temperature(h):
#         """h in meters"""
#         if h <= 11000:
#             return 288.15 - 0.0065 * h  # Troposphere
#         elif h <= 20000:
#             return 216.65  # Tropopause
#         else:
#             return 216.65 + 0.001 * (h - 20000)  # Lower Stratosphere
    
#     @staticmethod
#     def pressure(h):
#         """h in meters"""
#         T0 = 288.15
#         p0 = 101325
#         g = 9.80665
#         R = 287.05
        
#         if h <= 11000:
#             T = 288.15 - 0.0065 * h
#             return p0 * (T / T0) ** (g / (0.0065 * R))
#         elif h <= 20000:
#             p11 = InternationalStandardAtmosphere.pressure(11000)
#             return p11 * np.exp(-g * (h - 11000) / (R * 216.65))
#         else:
#             p20 = InternationalStandardAtmosphere.pressure(20000)
#             T20 = 216.65
#             T = 216.65 + 0.001 * (h - 20000)
#             return p20 * (T / T20) ** (-g / (0.001 * R))
    
#     @staticmethod
#     def density(h):
#         """h in meters"""
#         R = 287.05
#         T = InternationalStandardAtmosphere.temperature(h)
#         p = InternationalStandardAtmosphere.pressure(h)
#         return p / (R * T)

# # ================================
# # ENGINEERING CALCULATIONS
# # ================================

# class AerospaceCalculator:
#     """Professional aerospace performance calculator"""
    
#     def __init__(self, aircraft_data):
#         self.aircraft = aircraft_data
        
#     def calculate_coefficients(self, alpha_deg):
#         """Calculate CL and CD for given angle of attack"""
#         alpha_rad = np.radians(alpha_deg)
        
#         # Linear CL-alpha up to stall
#         cl_linear = self.aircraft["cl_alpha"] * alpha_rad
        
#         # Simple stall model
#         if alpha_deg > 12:
#             cl = self.aircraft["cl_max"] * np.cos(alpha_rad - np.radians(12))
#         else:
#             cl = cl_linear
        
#         # Drag polar: CD = CD0 + k*CL²
#         cd = self.aircraft["cd0"] + self.aircraft["k"] * cl**2
        
#         return cl, cd
    
#     def calculate_lift(self, cl, velocity, altitude_m):
#         rho = InternationalStandardAtmosphere.density(altitude_m)
#         return 0.5 * rho * velocity**2 * self.aircraft["wing_area_m2"] * cl
    
#     def calculate_drag(self, cd, velocity, altitude_m):
#         rho = InternationalStandardAtmosphere.density(altitude_m)
#         return 0.5 * rho * velocity**2 * self.aircraft["wing_area_m2"] * cd
    
#     def stall_speed(self, altitude_m, load_factor=1.0):
#         """Calculate stall speed for given altitude and load factor"""
#         rho = InternationalStandardAtmosphere.density(altitude_m)
#         weight_n = self.aircraft["weight_kg"] * 9.80665 * load_factor
#         return np.sqrt((2 * weight_n) / (rho * self.aircraft["cl_max"] * self.aircraft["wing_area_m2"]))
    
#     def required_thrust(self, velocity, altitude_m, gamma_deg=0):
#         """Calculate required thrust for given flight condition"""
#         gamma_rad = np.radians(gamma_deg)
#         weight_n = self.aircraft["weight_kg"] * 9.80665
        
#         # Get CL for level flight
#         rho = InternationalStandardAtmosphere.density(altitude_m)
#         cl = (2 * weight_n * np.cos(gamma_rad)) / (rho * velocity**2 * self.aircraft["wing_area_m2"])
#         cd = self.aircraft["cd0"] + self.aircraft["k"] * cl**2
        
#         drag = 0.5 * rho * velocity**2 * self.aircraft["wing_area_m2"] * cd
#         return drag + weight_n * np.sin(gamma_rad)
    
#     def flight_envelope(self, altitude_m):
#         """Calculate V-n diagram points"""
#         vs = self.stall_speed(altitude_m)
#         v_ne = self.aircraft["v_ne"]
        
#         # Simplified V-n diagram
#         speeds = np.linspace(vs, v_ne, 50)
#         load_factors = []
        
#         for v in speeds:
#             rho = InternationalStandardAtmosphere.density(altitude_m)
#             cl_available = min(
#                 self.aircraft["cl_max"],
#                 (self.aircraft["weight_kg"] * 9.80665) / 
#                 (0.5 * rho * v**2 * self.aircraft["wing_area_m2"])
#             )
#             n = (0.5 * rho * v**2 * self.aircraft["wing_area_m2"] * cl_available) / \
#                 (self.aircraft["weight_kg"] * 9.80665)
#             load_factors.append(min(n, 3.8))  # Limit to +3.8g for transport
        
#         return speeds, load_factors

# # ================================
# # STREAMLIT APP - PROFESSIONAL UI
# # ================================

# st.set_page_config(
#     page_title="Aerospace Engineering Suite",
#     page_icon="✈️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Custom CSS for professional look
# st.markdown("""
# <style>
#     .main-header {
#         font-size: 3rem;
#         background: linear-gradient(90deg, #1a2980, #26d0ce);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         font-weight: 700;
#         text-align: center;
#         margin-bottom: 2rem;
#     }
#     .section-header {
#         font-size: 1.8rem;
#         color: #1a2980;
#         border-bottom: 3px solid #26d0ce;
#         padding-bottom: 0.5rem;
#         margin-top: 2rem;
#     }
#     .metric-card {
#         background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#         padding: 1.5rem;
#         border-radius: 15px;
#         color: white;
#         box-shadow: 0 10px 20px rgba(0,0,0,0.2);
#     }
#     .warning-box {
#         background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
#         padding: 1rem;
#         border-radius: 10px;
#         color: white;
#         font-weight: bold;
#     }
#     .info-box {
#         background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
#         padding: 1rem;
#         border-radius: 10px;
#         color: white;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ================================
# # SIDEBAR - PROFESSIONAL CONTROLS
# # ================================

# with st.sidebar:
#     st.markdown("## 🎛️ Mission Control")
    
#     # Aircraft Selection with images
#     st.markdown("### Aircraft Selection")
#     aircraft_name = st.selectbox(
#         "Select Aircraft",
#         list(AIRPLANES.keys()),
#         format_func=lambda x: f"{x} ({AIRPLANES[x]['type']})"
#     )
    
#     plane = AIRPLANES[aircraft_name]
#     calculator = AerospaceCalculator(plane)
    
#     # Flight Conditions
#     st.markdown("### Flight Conditions")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         velocity = st.number_input(
#             "True Airspeed (m/s)",
#             min_value=50.0,  # Make float
#             max_value=float(plane["v_ne"]),  # Convert to float
#             value=100.0,
#             step=10.0,
#             help="Must be below V_NE (Never Exceed Speed)"
#         )
#     with col2:
#         altitude_ft = st.number_input(
#             "Altitude (ft)",
#             min_value=0.0,  # Make float
#             max_value=50000.0,  # Make float
#             value=10000.0,
#             step=1000.0
#         )
    
#     altitude_m = altitude_ft * 0.3048
    
#     # Angle of Attack Control
#     alpha_deg = st.slider(
#         "Angle of Attack (°)",
#         min_value=-5.0,
#         max_value=20.0,
#         value=2.0,
#         step=0.5,
#         help="Warning: Values above 12° may cause stall"
#     )
    
#     # Flight Path Angle
#     gamma_deg = st.slider(
#         "Flight Path Angle (°)",
#         min_value=-15.0,
#         max_value=15.0,
#         value=0.0,
#         step=1.0,
#         help="Positive = Climbing, Negative = Descending"
#     )
    
#     # Calculate Button
#     calculate_btn = st.button(
#         "🚀 Run Engineering Analysis",
#         type="primary",
#         use_container_width=True
#     )

# # ================================
# # MAIN DASHBOARD
# # ================================

# st.markdown('<h1 class="main-header">✈️ Aerospace Engineering Suite</h1>', unsafe_allow_html=True)

# # Top Metrics Row
# col1, col2, col3, col4 = st.columns(4)
# with col1:
#     st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#     st.metric("Aircraft Type", plane["type"])
#     st.markdown('</div>', unsafe_allow_html=True)

# with col2:
#     st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#     st.metric("Manufacturer", plane["manufacturer"])
#     st.markdown('</div>', unsafe_allow_html=True)

# with col3:
#     wing_loading = plane["weight_kg"] * 9.80665 / plane["wing_area_m2"]
#     st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#     st.metric("Wing Loading", f"{wing_loading:.0f} N/m²")
#     st.markdown('</div>', unsafe_allow_html=True)

# with col4:
#     aspect_ratio = plane["aspect_ratio"]
#     st.markdown('<div class="metric-card">', unsafe_allow_html=True)
#     st.metric("Aspect Ratio", f"{aspect_ratio:.2f}")
#     st.markdown('</div>', unsafe_allow_html=True)

# # ================================
# # ENGINEERING ANALYSIS
# # ================================

# if calculate_btn:
#     st.markdown('<h2 class="section-header">Engineering Analysis Results</h2>', unsafe_allow_html=True)
    
#     # Calculate coefficients
#     cl, cd = calculator.calculate_coefficients(alpha_deg)
#     lift = calculator.calculate_lift(cl, velocity, altitude_m)
#     drag = calculator.calculate_drag(cd, velocity, altitude_m)
#     required_thrust = calculator.required_thrust(velocity, altitude_m, gamma_deg)
#     weight = plane["weight_kg"] * 9.80665
#     stall_speed = calculator.stall_speed(altitude_m)
    
#     # Safety Checks
#     safety_status = []
#     if velocity < stall_speed * 1.2:
#         safety_status.append("⚠️ Near stall speed - increase airspeed")
#     if alpha_deg > 12:
#         safety_status.append("⚠️ High angle of attack - risk of stall")
#     if velocity > plane["v_no"]:
#         safety_status.append("⚠️ Exceeding normal operating speed")
    
#     # Performance Metrics
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.markdown("#### Aerodynamic Coefficients")
#         st.metric("CL (Lift Coefficient)", f"{cl:.3f}")
#         st.metric("CD (Drag Coefficient)", f"{cd:.4f}")
#         st.metric("L/D Ratio", f"{(cl/cd):.1f}" if cd > 0 else "∞")
    
#     with col2:
#         st.markdown("#### Forces & Moments")
#         st.metric("Lift Force", f"{lift/1000:.1f} kN")
#         st.metric("Drag Force", f"{drag/1000:.1f} kN")
#         st.metric("Required Thrust", f"{required_thrust/1000:.1f} kN")
    
#     with col3:
#         st.markdown("#### Performance Envelope")
#         st.metric("Stall Speed", f"{stall_speed:.1f} m/s")
#         st.metric("Current Speed", f"{velocity:.1f} m/s")
#         st.metric("Mach Number", f"{(velocity/343):.2f} M")
    
#     with col4:
#         st.markdown("#### Safety Status")
#         if safety_status:
#             for status in safety_status:
#                 st.markdown(f'<div class="warning-box">{status}</div>', unsafe_allow_html=True)
#         else:
#             st.markdown('<div class="info-box">✅ All parameters within safe limits</div>', unsafe_allow_html=True)
    
#     # ================================
#     # PROFESSIONAL VISUALIZATIONS
#     # ================================
    
#     tab1, tab2, tab3, tab4 = st.tabs([
#         "📈 Aerodynamic Polar",
#         "🛫 Flight Envelope",
#         "⚡ Performance Curves",
#         "📊 Engineering Data"
#     ])
    
#     with tab1:
#         # Drag Polar Plot
#         alphas = np.linspace(-5, 20, 100)
#         cls = []
#         cds = []
        
#         for a in alphas:
#             cl_temp, cd_temp = calculator.calculate_coefficients(a)
#             cls.append(cl_temp)
#             cds.append(cd_temp)
        
#         fig1 = make_subplots(
#             rows=1, cols=2,
#             subplot_titles=("Drag Polar", "Lift vs Angle of Attack"),
#             specs=[[{"type": "scatter"}, {"type": "scatter"}]]
#         )
        
#         fig1.add_trace(
#             go.Scatter(x=cds, y=cls, mode='lines', line=dict(width=3, color=plane['color']),
#                       name="Drag Polar", hovertemplate="CD: %{x:.3f}<br>CL: %{y:.3f}"),
#             row=1, col=1
#         )
#         fig1.add_trace(
#             go.Scatter(x=[cd], y=[cl], mode='markers', marker=dict(size=15, color='red'),
#                       name="Current Point"),
#             row=1, col=1
#         )
        
#         fig1.add_trace(
#             go.Scatter(x=alphas, y=cls, mode='lines', line=dict(width=3, color=plane['color']),
#                       name="CL-α Curve"),
#             row=1, col=2
#         )
        
#         fig1.update_xaxes(title_text="Drag Coefficient (CD)", row=1, col=1)
#         fig1.update_yaxes(title_text="Lift Coefficient (CL)", row=1, col=1)
#         fig1.update_xaxes(title_text="Angle of Attack (°)", row=1, col=2)
#         fig1.update_yaxes(title_text="Lift Coefficient (CL)", row=1, col=2)
        
#         fig1.update_layout(
#             title=f"Aerodynamic Characteristics - {aircraft_name}",
#             height=500,
#             showlegend=True,
#             hovermode='closest'
#         )
        
#         st.plotly_chart(fig1, use_container_width=True)
    
#     with tab2:
#         # V-n Diagram
#         speeds_vn, load_factors = calculator.flight_envelope(altitude_m)
        
#         fig2 = go.Figure()
        
#         fig2.add_trace(go.Scatter(
#             x=speeds_vn, y=load_factors,
#             fill='tozeroy',
#             fillcolor='rgba(26, 150, 65, 0.3)',
#             line=dict(color=plane['color'], width=3),
#             name="Flight Envelope"
#         ))
        
#         fig2.add_vline(x=stall_speed, line_dash="dash", line_color="red",
#                       annotation_text=f"Stall Speed: {stall_speed:.1f} m/s")
#         fig2.add_vline(x=plane["v_no"], line_dash="dash", line_color="orange",
#                       annotation_text=f"V_NO: {plane['v_no']} m/s")
#         fig2.add_vline(x=plane["v_ne"], line_dash="dash", line_color="darkred",
#                       annotation_text=f"V_NE: {plane['v_ne']} m/s")
        
#         fig2.add_trace(go.Scatter(
#             x=[velocity], y=[lift/weight],
#             mode='markers',
#             marker=dict(size=20, color='yellow', symbol='star'),
#             name="Current Flight Point"
#         ))
        
#         fig2.update_layout(
#             title=f"Flight Envelope (V-n Diagram) at {altitude_ft:.0f} ft",
#             xaxis_title="Equivalent Airspeed (m/s)",
#             yaxis_title="Load Factor (n)",
#             height=500,
#             showlegend=True
#         )
        
#         st.plotly_chart(fig2, use_container_width=True)
    
#     with tab3:
#         # Performance Curves
#         speeds_range = np.linspace(stall_speed * 1.1, plane["v_no"], 50)
#         thrust_required = []
#         power_required = []
        
#         for v in speeds_range:
#             tr = calculator.required_thrust(v, altitude_m, 0)
#             thrust_required.append(tr)
#             power_required.append(tr * v / 1000)  # kW
        
#         fig3 = make_subplots(
#             rows=1, cols=2,
#             subplot_titles=("Thrust Required", "Power Required"),
#             specs=[[{"type": "scatter"}, {"type": "scatter"}]]
#         )
        
#         fig3.add_trace(
#             go.Scatter(x=speeds_range, y=thrust_required,
#                       mode='lines', line=dict(width=3, color='#00b4d8'),
#                       name="Thrust Required"),
#             row=1, col=1
#         )
        
#         fig3.add_trace(
#             go.Scatter(x=speeds_range, y=power_required,
#                       mode='lines', line=dict(width=3, color='#ff006e'),
#                       name="Power Required"),
#             row=1, col=2
#         )
        
#         fig3.add_vline(x=velocity, line_dash="dash", line_color="orange",
#                       row=1, col=1)
#         fig3.add_vline(x=velocity, line_dash="dash", line_color="orange",
#                       row=1, col=2)
        
#         fig3.update_xaxes(title_text="True Airspeed (m/s)", row=1, col=1)
#         fig3.update_yaxes(title_text="Thrust Required (N)", row=1, col=1)
#         fig3.update_xaxes(title_text="True Airspeed (m/s)", row=1, col=2)
#         fig3.update_yaxes(title_text="Power Required (kW)", row=1, col=2)
        
#         fig3.update_layout(
#             title=f"Performance Curves at {altitude_ft:.0f} ft",
#             height=500,
#             showlegend=True
#         )
        
#         st.plotly_chart(fig3, use_container_width=True)
    
#     with tab4:
#         # Engineering Data Table
#         st.markdown("#### Complete Engineering Analysis")
        
#         # Calculate at multiple conditions for comparison
#         altitudes_comparison = [0, 5000, 10000, 15000]
#         comparison_data = []
        
#         for alt_ft in altitudes_comparison:
#             alt_m = alt_ft * 0.3048
#             vs = calculator.stall_speed(alt_m)
#             rho = InternationalStandardAtmosphere.density(alt_m)
            
#             comparison_data.append({
#                 "Altitude (ft)": alt_ft,
#                 "Stall Speed (m/s)": f"{vs:.1f}",
#                 "Air Density (kg/m³)": f"{rho:.3f}",
#                 "Dynamic Pressure at 100 m/s (Pa)": f"{0.5 * rho * 100**2:.0f}",
#                 "L/D Max Speed (m/s)": f"{vs * 1.5:.1f}"  # Simplified
#             })
        
#         df = pd.DataFrame(comparison_data)
#         st.dataframe(df, use_container_width=True)
        
#         # Download Button for Results
#         csv = df.to_csv(index=False)
#         st.download_button(
#             label="📥 Download Engineering Data (CSV)",
#             data=csv,
#             file_name=f"aerospace_analysis_{aircraft_name.replace(' ', '_')}.csv",
#             mime="text/csv",
#             type="primary"
#         )
    
#     # ================================
#     # TECHNICAL DETAILS EXPANDER
#     # ================================
    
#     with st.expander("🔬 View Technical Calculations", expanded=False):
#         st.markdown("#### Detailed Engineering Formulas")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown("""
#             **Lift Equation:**
#             ```
#             L = ½ × ρ × V² × S × CL
#             Where:
#             ρ = Air Density (kg/m³)
#             V = True Airspeed (m/s)
#             S = Wing Area (m²)
#             CL = Lift Coefficient
#             ```
            
#             **Drag Polar:**
#             ```
#             CD = CD₀ + k × CL²
#             Where:
#             CD₀ = Zero-lift Drag Coefficient
#             k = Induced Drag Factor = 1/(π × AR × e)
#             AR = Aspect Ratio
#             e = Oswald Efficiency Factor
#             ```
#             """)
        
#         with col2:
#             st.markdown("""
#             **Stall Speed:**
#             ```
#             V_s = √[2 × W / (ρ × S × CL_max)]
#             Where:
#             W = Weight (N)
#             CL_max = Maximum Lift Coefficient
#             ```
            
#             **Load Factor:**
#             ```
#             n = L / W
#             Where:
#             L = Lift Force (N)
#             W = Weight (N)
#             ```
            
#             **International Standard Atmosphere:**
#             ```
#             Troposphere (0-11km): T = 288.15 - 0.0065 × h
#             Stratosphere (11-20km): T = 216.65 K
#             ```
#             """)
        
#         st.markdown("---")
#         st.markdown(f"**Current Atmosphere Conditions at {altitude_ft:.0f} ft:**")
        
#         atmos_col1, atmos_col2, atmos_col3, atmos_col4 = st.columns(4)
#         with atmos_col1:
#             temp_k = InternationalStandardAtmosphere.temperature(altitude_m)
#             st.metric("Temperature", f"{temp_k - 273.15:.1f} °C")
#         with atmos_col2:
#             pressure = InternationalStandardAtmosphere.pressure(altitude_m)
#             st.metric("Pressure", f"{pressure/1000:.1f} kPa")
#         with atmos_col3:
#             density = InternationalStandardAtmosphere.density(altitude_m)
#             st.metric("Density", f"{density:.3f} kg/m³")
#         with atmos_col4:
#             st.metric("Speed of Sound", f"{np.sqrt(1.4 * 287 * temp_k):.1f} m/s")

# # ================================
# # FOOTER & CREDITS
# # ================================

# st.markdown("---")
# footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
# with footer_col2:
#     st.markdown("""
#     <div style="text-align: center; color: #666;">
#         <h4>🚀 Aerospace Engineering Suite <span style="font-weight: normal;">v2.0</span></h4>
#         <p><strong>Professional Flight Mechanics & Performance Analysis Tool</strong></p>
#         <p style="font-size: 0.9em;">
#             Built with Streamlit · Uses International Standard Atmosphere (ISA)
#         </p>
#         <a href="https://t.me/Voyager_557" target="_blank" 
#            style="text-decoration: none; color: #1f77b4;">
#             VOYAGER #557
#         </a>
#     </div>
#     """, unsafe_allow_html=True)


# # ================================
# # SESSION STATE FOR PROFESSIONAL FEATURES
# # ================================

# if 'analysis_history' not in st.session_state:
#     st.session_state.analysis_history = []

# if calculate_btn:
#     # Save analysis to history
#     analysis_entry = {
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "aircraft": aircraft_name,
#         "velocity": velocity,
#         "altitude": altitude_ft,
#         "alpha": alpha_deg,
#         "cl": cl,
#         "cd": cd,
#         "lift_kn": lift/1000,
#         "drag_kn": drag/1000
#     }
#     st.session_state.analysis_history.append(analysis_entry)
    
#     # Show history in sidebar
#     with st.sidebar:
#         st.markdown("---")
#         st.markdown("### 📋 Analysis History")
#         if len(st.session_state.analysis_history) > 0:
#             for i, entry in enumerate(reversed(st.session_state.analysis_history[-5:])):
#                 st.caption(f"{entry['timestamp']}: {entry['aircraft']} @ ####{entry['velocity']} m/s")

#------------------------------------------2nd Ai version---------------------------------


# import streamlit as st
# import numpy as np
# import plotly.graph_objects as go
# import plotly.express as px
# from plotly.subplots import make_subplots
# from PIL import Image
# import pandas as pd
# import json
# from datetime import datetime
# from scipy import interpolate
# import math

# # ===============================================
# # INDUSTRY-STANDARD AIRCRAFT PERFORMANCE MODULE
# # ===============================================

# class FlightPhase:
#     """Industry standard flight phases"""
#     TAKEOFF = "Takeoff"
#     CLIMB = "Climb"
#     CRUISE = "Cruise"
#     DESCENT = "Descent"
#     APPROACH = "Approach"
#     LANDING = "Landing"

# class AircraftPerformanceModel:
#     """Realistic aircraft performance model used in industry"""
    
#     def __init__(self, aircraft_data):
#         self.aircraft = aircraft_data
#         self.g = 9.80665  # m/s²
#         self.R = 287.05   # J/(kg·K)
#         self.gamma = 1.4  # Ratio of specific heats for air
        
#     # ============ ATMOSPHERIC MODEL ============
#     def isa_atmosphere(self, altitude_m):
#         """ICAO International Standard Atmosphere (industry standard)"""
#         if altitude_m <= 11000:
#             # Troposphere
#             T0 = 288.15  # K
#             p0 = 101325  # Pa
#             lapse_rate = -0.0065  # K/m
#             T = T0 + lapse_rate * altitude_m
#             p = p0 * (T / T0) ** (-self.g / (lapse_rate * self.R))
#         elif altitude_m <= 20000:
#             # Tropopause
#             T = 216.65  # K
#             p11 = 22632.1  # Pa at 11km
#             p = p11 * math.exp(-self.g * (altitude_m - 11000) / (self.R * T))
#         else:
#             # Lower stratosphere
#             T20 = 216.65
#             p20 = 5474.89
#             lapse_rate = 0.001  # K/m
#             T = T20 + lapse_rate * (altitude_m - 20000)
#             p = p20 * (T / T20) ** (-self.g / (lapse_rate * self.R))
        
#         rho = p / (self.R * T)
#         a = math.sqrt(self.gamma * self.R * T)  # Speed of sound
        
#         return {
#             'temperature_K': T,
#             'pressure_Pa': p,
#             'density_kg_m3': rho,
#             'speed_of_sound_m_s': a
#         }
    
#     # ============ AERODYNAMIC MODEL ============
#     def calculate_coefficients(self, alpha_deg, mach, flap_setting=0, gear_down=False):
#         """Realistic CL/CD calculation with compressibility and configuration effects"""
#         alpha_rad = math.radians(alpha_deg)
        
#         # Base CL calculation
#         cl_alpha = self.aircraft.get('cl_alpha', 5.73)  # per radian
#         cl0 = self.aircraft.get('cl0', 0.2)
        
#         # Linear region
#         if abs(alpha_deg) <= 10:
#             cl = cl0 + cl_alpha * alpha_rad
#         # Near stall
#         elif alpha_deg <= self.aircraft.get('alpha_stall', 16):
#             # Non-linear lift curve
#             cl_max = self.aircraft.get('cl_max', 1.6)
#             alpha_stall_rad = math.radians(self.aircraft.get('alpha_stall', 16))
#             cl = cl_max * math.sin(alpha_rad) / math.sin(alpha_stall_rad)
#         else:
#             # Post-stall (simplified)
#             cl = self.aircraft.get('cl_max', 1.6) * 0.7
        
#         # Flap effects
#         if flap_setting > 0:
#             cl += flap_setting * 0.4  # Flap contribution
#             cl *= (1 + 0.05 * flap_setting)  # Lift curve slope increase
        
#         # Compressibility correction (Prandtl-Glauert)
#         if mach > 0.3:
#             beta = math.sqrt(1 - mach**2)
#             cl /= beta
        
#         # Drag calculation with realistic components
#         cd0 = self.aircraft.get('cd0', 0.02)
#         k = self.aircraft.get('k', 0.05)
#         e = self.aircraft.get('oswald_efficiency', 0.85)
#         AR = self.aircraft['wing_span_m']**2 / self.aircraft['wing_area_m2']
        
#         # Induced drag
#         cd_induced = cl**2 / (math.pi * AR * e)
        
#         # Configuration drag
#         cd_config = 0
#         if flap_setting == 1:
#             cd_config += 0.02
#         elif flap_setting == 2:
#             cd_config += 0.05
#         elif flap_setting == 3:
#             cd_config += 0.10
        
#         if gear_down:
#             cd_config += 0.025
        
#         # Compressibility drag rise (simplified)
#         cd_compress = 0
#         if mach > self.aircraft.get('mach_crit', 0.7):
#             cd_compress = 0.1 * (mach - 0.7)**2
        
#         cd = cd0 + cd_induced + cd_config + cd_compress
        
#         return cl, cd
    
#     # ============ PERFORMANCE CALCULATIONS ============
#     def takeoff_distance(self, weight_kg, altitude_m, temperature_C, headwind_m_s=0):
#         """FAR 25 Takeoff distance calculation"""
#         # Simplified takeoff model
#         atmos = self.isa_atmosphere(altitude_m)
#         rho = atmos['density_kg_m3']
        
#         # Stall speed
#         V_stall = math.sqrt(
#             (2 * weight_kg * self.g) / 
#             (rho * self.aircraft['wing_area_m2'] * self.aircraft.get('cl_max_to', 1.8))
#         )
        
#         # Takeoff speeds
#         V_r = 1.1 * V_stall  # Rotation speed
#         V_2 = 1.2 * V_stall  # Takeoff safety speed
        
#         # Ground roll (simplified)
#         mu = 0.02  # Rolling friction coefficient
#         thrust_weight_ratio = self.aircraft.get('thrust_weight_ratio', 0.3)
#         T_avg = thrust_weight_ratio * weight_kg * self.g
        
#         # Average acceleration
#         a_avg = (T_avg - mu * weight_kg * self.g) / weight_kg
        
#         # Ground roll distance
#         S_g = (V_r**2) / (2 * a_avg)
        
#         # Air distance (rotation to 35ft)
#         gamma_climb = math.radians(self.aircraft.get('climb_gradient', 15))
#         S_a = (35 * 0.3048) / math.tan(gamma_climb)  # Convert 35ft to meters
        
#         # Headwind correction
#         total_distance = (S_g + S_a) / (1 + headwind_m_s / V_r)
        
#         return {
#             'V_stall': V_stall,
#             'V_r': V_r,
#             'V_2': V_2,
#             'ground_roll_m': S_g,
#             'air_distance_m': S_a,
#             'total_distance_m': total_distance,
#             'total_distance_ft': total_distance / 0.3048
#         }
    
#     def landing_distance(self, weight_kg, altitude_m, temperature_C, tailwind_m_s=0):
#         """FAR 25 Landing distance calculation"""
#         atmos = self.isa_atmosphere(altitude_m)
#         rho = atmos['density_kg_m3']
        
#         # Approach speed
#         V_ref = 1.3 * math.sqrt(
#             (2 * weight_kg * self.g) / 
#             (rho * self.aircraft['wing_area_m2'] * self.aircraft.get('cl_max_ldg', 2.0))
#         )
        
#         # Touchdown speed
#         V_td = 1.15 * V_ref * 0.8
        
#         # Deceleration during flare and ground roll
#         deceleration = -3.0  # m/s² (typical for braking)
        
#         # Air distance (50ft to touchdown)
#         gamma_approach = math.radians(3)  # Standard 3° glide path
#         S_air = (50 * 0.3048) / math.tan(gamma_approach)
        
#         # Ground roll
#         S_ground = (V_td**2) / (2 * abs(deceleration))
        
#         total_distance = S_air + S_ground
        
#         # Tailwind correction
#         total_distance *= (1 + tailwind_m_s / V_ref)
        
#         return {
#             'V_ref': V_ref,
#             'V_td': V_td,
#             'air_distance_m': S_air,
#             'ground_roll_m': S_ground,
#             'total_distance_m': total_distance,
#             'total_distance_ft': total_distance / 0.3048
#         }
    
#     def climb_performance(self, weight_kg, altitude_m, velocity, configuration="clean"):
#         """Rate of climb and climb gradient calculation"""
#         atmos = self.isa_atmosphere(altitude_m)
#         rho = atmos['density_kg_m3']
#         mach = velocity / atmos['speed_of_sound_m_s']
        
#         # Get coefficients based on configuration
#         flap_setting = 0 if configuration == "clean" else 1
#         cl, cd = self.calculate_coefficients(2, mach, flap_setting)
        
#         # Available thrust (simplified)
#         if 'engine_thrust_n' in self.aircraft:
#             # Jet engine - thrust decreases with altitude
#             T_sl = self.aircraft['engine_thrust_n']
#             sigma = rho / 1.225
#             T = T_sl * sigma**0.7
#         else:
#             # Piston engine - power constant, thrust decreases with velocity
#             power_hp = self.aircraft.get('engine_hp', 180)
#             power_w = power_hp * 745.7
#             T = power_w / velocity  # Simplified
        
#         # Required thrust
#         D = 0.5 * rho * velocity**2 * self.aircraft['wing_area_m2'] * cd
        
#         # Excess power
#         excess_power = (T - D) * velocity
        
#         # Rate of climb
#         ROC = excess_power / (weight_kg * self.g)
        
#         # Climb gradient
#         climb_gradient = (T - D) / (weight_kg * self.g)
#         climb_angle = math.degrees(math.asin(climb_gradient))
        
#         return {
#             'rate_of_climb_m_s': ROC,
#             'rate_of_climb_ft_min': ROC * 196.85,
#             'climb_gradient': climb_gradient,
#             'climb_angle_deg': climb_angle,
#             'excess_power_w': excess_power
#         }
    
#     def cruise_performance(self, weight_kg, altitude_m, mach):
#         """Cruise performance - range, endurance, specific air range"""
#         atmos = self.isa_atmosphere(altitude_m)
#         rho = atmos['density_kg_m3']
#         T = atmos['temperature_K']
#         a = atmos['speed_of_sound_m_s']
        
#         velocity = mach * a
#         cl, cd = self.calculate_coefficients(2, mach)
        
#         # Lift required
#         L = weight_kg * self.g
        
#         # Check if lift equals weight at this CL
#         L_available = 0.5 * rho * velocity**2 * self.aircraft['wing_area_m2'] * cl
        
#         # Required CL for level flight
#         cl_req = (2 * L) / (rho * velocity**2 * self.aircraft['wing_area_m2'])
#         cd_req = self.calculate_coefficients(math.degrees(math.asin(cl_req/cl_alpha)), mach)[1]
        
#         # Drag
#         D = 0.5 * rho * velocity**2 * self.aircraft['wing_area_m2'] * cd_req
        
#         # L/D ratio
#         LD_ratio = L / D if D > 0 else 0
        
#         # Fuel flow (simplified)
#         if 'engine_thrust_n' in self.aircraft:
#             # Jet - TSFC typically 0.5-0.8 lb/(lbf·hr)
#             tsfc = 0.6 / 3600  # Convert to 1/s
#             fuel_flow_kg_s = tsfc * D / self.g
#         else:
#             # Piston - BSFC typically 0.4 lb/(hp·hr)
#             bsfc = 0.4 * 0.453592 / (745.7 * 3600)  # Convert to kg/(W·s)
#             power_required = D * velocity
#             fuel_flow_kg_s = bsfc * power_required
        
#         # Specific Air Range (SAR) - distance per unit fuel
#         SAR = velocity / fuel_flow_kg_s if fuel_flow_kg_s > 0 else 0
        
#         # Endurance
#         if 'fuel_capacity_kg' in self.aircraft:
#             endurance = self.aircraft['fuel_capacity_kg'] / fuel_flow_kg_s
#             range_km = SAR * self.aircraft['fuel_capacity_kg'] / 1000
#         else:
#             endurance = 0
#             range_km = 0
        
#         return {
#             'velocity_m_s': velocity,
#             'cl_req': cl_req,
#             'cd_req': cd_req,
#             'LD_ratio': LD_ratio,
#             'fuel_flow_kg_s': fuel_flow_kg_s,
#             'fuel_flow_kg_hr': fuel_flow_kg_s * 3600,
#             'SAR_m_kg': SAR,
#             'endurance_hr': endurance / 3600,
#             'range_km': range_km,
#             'drag_n': D
#         }

# # ===============================================
# # REALISTIC AIRCRAFT DATABASE
# # ===============================================

# AIRCRAFT_DATABASE = {
#     "Cessna 172S Skyhawk SP": {
#         "type": "Single Engine Piston",
#         "manufacturer": "Cessna",
#         "category": "Normal",
#         "weight_kg": 1111.0,
#         "wing_area_m2": 16.2,
#         "wing_span_m": 11.0,
#         "cl_alpha": 5.73,
#         "cl0": 0.2,
#         "cl_max": 1.6,
#         "cl_max_to": 1.8,
#         "cl_max_ldg": 2.0,
#         "alpha_stall": 16.0,
#         "cd0": 0.027,
#         "k": 0.054,
#         "oswald_efficiency": 0.85,
#         "engine_hp": 180.0,
#         "fuel_capacity_kg": 172.0,
#         "v_ne": 163.0,
#         "v_no": 138.0,
#         "v_fe": 40.0,
#         "service_ceiling_m": 4115.0,
#         "climb_gradient": 15.0,
#         "color": "#1E88E5",
#         "description": "Four-seat, single-engine, high-wing, fixed-wing aircraft. Primary trainer and personal aircraft.",
#         "flight_manual_ref": "POH Cessna 172S"
#     },
#     "Boeing 737-800": {
#         "type": "Twin Engine Jet",
#         "manufacturer": "Boeing",
#         "category": "Transport",
#         "weight_kg": 79000.0,
#         "wing_area_m2": 125.0,
#         "wing_span_m": 34.3,
#         "cl_alpha": 6.28,
#         "cl0": 0.25,
#         "cl_max": 1.8,
#         "cl_max_to": 2.0,
#         "cl_max_ldg": 2.2,
#         "alpha_stall": 18.0,
#         "cd0": 0.020,
#         "k": 0.042,
#         "oswald_efficiency": 0.90,
#         "engine_thrust_n": 117000.0,
#         "thrust_weight_ratio": 0.3,
#         "fuel_capacity_kg": 26000.0,
#         "v_ne": 270.0,
#         "v_no": 250.0,
#         "v_fe": 85.0,
#         "mach_mmo": 0.82,
#         "mach_crit": 0.75,
#         "service_ceiling_m": 12500.0,
#         "climb_gradient": 20.0,
#         "color": "#FF9800",
#         "description": "Narrow-body airliner, most popular jet airliner in history.",
#         "flight_manual_ref": "Boeing FCOM 737-800"
#     },
#     "Airbus A320neo": {
#         "type": "Twin Engine Jet",
#         "manufacturer": "Airbus",
#         "category": "Transport",
#         "weight_kg": 78000.0,
#         "wing_area_m2": 122.6,
#         "wing_span_m": 35.8,
#         "cl_alpha": 6.5,
#         "cl0": 0.22,
#         "cl_max": 1.85,
#         "cl_max_to": 2.1,
#         "cl_max_ldg": 2.3,
#         "alpha_stall": 18.5,
#         "cd0": 0.019,
#         "k": 0.038,
#         "oswald_efficiency": 0.92,
#         "engine_thrust_n": 120000.0,
#         "thrust_weight_ratio": 0.31,
#         "fuel_capacity_kg": 25000.0,
#         "v_ne": 275.0,
#         "v_no": 255.0,
#         "v_fe": 90.0,
#         "mach_mmo": 0.82,
#         "mach_crit": 0.76,
#         "service_ceiling_m": 11900.0,
#         "climb_gradient": 22.0,
#         "color": "#4CAF50",
#         "description": "Narrow-body airliner with new engine option for improved efficiency.",
#         "flight_manual_ref": "Airbus FCOM A320neo"
#     }
# }

# # ===============================================
# # STREAMLIT APP - INDUSTRY GRADE
# # ===============================================

# st.set_page_config(
#     page_title="AeroPerformance Pro",
#     page_icon="✈️",
#     layout="wide",
#     initial_sidebar_state="expanded"
# )

# # Professional CSS
# st.markdown("""
# <style>
#     .main-title {
#         font-size: 2.8rem;
#         background: linear-gradient(90deg, #0d47a1, #42a5f5);
#         -webkit-background-clip: text;
#         -webkit-text-fill-color: transparent;
#         font-weight: 700;
#         text-align: center;
#         margin-bottom: 1rem;
#         font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#     }
#     .section-title {
#         font-size: 1.6rem;
#         color: #1565c0;
#         border-bottom: 2px solid #42a5f5;
#         padding-bottom: 0.5rem;
#         margin-top: 2rem;
#         font-weight: 600;
#     }
#     .metric-box {
#         background: white;
#         border: 1px solid #e0e0e0;
#         border-radius: 8px;
#         padding: 1rem;
#         box-shadow: 0 2px 4px rgba(0,0,0,0.1);
#         margin-bottom: 1rem;
#     }
#     .warning {
#         background: linear-gradient(135deg, #ff5252, #ff867f);
#         color: white;
#         padding: 0.75rem;
#         border-radius: 6px;
#         font-weight: 500;
#         margin: 1rem 0;
#     }
#     .info {
#         background: linear-gradient(135deg, #2196f3, #64b5f6);
#         color: white;
#         padding: 0.75rem;
#         border-radius: 6px;
#         font-weight: 500;
#         margin: 1rem 0;
#     }
#     .success {
#         background: linear-gradient(135deg, #4caf50, #81c784);
#         color: white;
#         padding: 0.75rem;
#         border-radius: 6px;
#         font-weight: 500;
#         margin: 1rem 0;
#     }
#     .data-card {
#         background: #f8f9fa;
#         border-left: 4px solid #2196f3;
#         padding: 1rem;
#         border-radius: 4px;
#         margin: 0.5rem 0;
#     }
# </style>
# """, unsafe_allow_html=True)

# # ===============================================
# # SIDEBAR - FLIGHT PLANNER
# # ===============================================

# with st.sidebar:
#     st.markdown("## 🗺️ Flight Planning")
    
#     # Aircraft Selection
#     st.markdown("### 1. Aircraft Selection")
#     aircraft_name = st.selectbox(
#         "Select Aircraft",
#         list(AIRCRAFT_DATABASE.keys()),
#         index=0
#     )
    
#     aircraft = AIRCRAFT_DATABASE[aircraft_name]
#     performance_model = AircraftPerformanceModel(aircraft)
    
#     # Flight Phase Selection
#     st.markdown("### 2. Flight Phase")
#     flight_phase = st.selectbox(
#         "Select Phase",
#         [FlightPhase.TAKEOFF, FlightPhase.CLIMB, FlightPhase.CRUISE, 
#          FlightPhase.DESCENT, FlightPhase.APPROACH, FlightPhase.LANDING]
#     )
    
#     # Common Parameters
#     st.markdown("### 3. Flight Conditions")
    
#     col1, col2 = st.columns(2)
#     with col1:
#         weight_kg = st.number_input(
#             "Takeoff Weight (kg)",
#             min_value=aircraft["weight_kg"] * 0.5,
#             max_value=aircraft["weight_kg"] * 1.1,
#             value=aircraft["weight_kg"],
#             step=100.0
#         )
#     with col2:
#         altitude_m = st.number_input(
#             "Altitude (m)",
#             min_value=0.0,
#             max_value=aircraft["service_ceiling_m"],
#             value=2000.0 if flight_phase == FlightPhase.TAKEOFF else 10000.0,
#             step=500.0
#         )
    
#     # Phase-specific parameters
#     if flight_phase == FlightPhase.TAKEOFF:
#         col1, col2 = st.columns(2)
#         with col1:
#             temperature_C = st.number_input(
#                 "OAT (°C)",
#                 min_value=-50.0,
#                 max_value=50.0,
#                 value=15.0,
#                 step=5.0
#             )
#         with col2:
#             headwind_m_s = st.number_input(
#                 "Headwind (m/s)",
#                 min_value=0.0,
#                 max_value=30.0,
#                 value=5.0,
#                 step=1.0
#             )
    
#     elif flight_phase == FlightPhase.LANDING:
#         col1, col2 = st.columns(2)
#         with col1:
#             temperature_C = st.number_input(
#                 "OAT (°C)",
#                 min_value=-50.0,
#                 max_value=50.0,
#                 value=15.0,
#                 step=5.0
#             )
#         with col2:
#             tailwind_m_s = st.number_input(
#                 "Tailwind (m/s)",
#                 min_value=0.0,
#                 max_value=15.0,
#                 value=0.0,
#                 step=1.0
#             )
    
#     elif flight_phase in [FlightPhase.CLIMB, FlightPhase.CRUISE]:
#         velocity = st.number_input(
#             "Indicated Airspeed (m/s)",
#             min_value=50.0,
#             max_value=aircraft["v_no"],
#             value=100.0 if flight_phase == FlightPhase.CLIMB else 200.0,
#             step=10.0
#         )
        
#         if flight_phase == FlightPhase.CRUISE:
#             mach = st.slider(
#                 "Mach Number",
#                 min_value=0.1,
#                 max_value=aircraft.get("mach_mmo", 0.82),
#                 value=0.78,
#                 step=0.01
#             )
    
#     # Configuration
#     st.markdown("### 4. Configuration")
    
#     if flight_phase in [FlightPhase.TAKEOFF, FlightPhase.LANDING]:
#         flap_setting = st.select_slider(
#             "Flap Setting",
#             options=[0, 1, 2, 3],
#             value=1 if flight_phase == FlightPhase.TAKEOFF else 3
#         )
#         gear_down = st.checkbox("Gear Down", 
#                               value=flight_phase == FlightPhase.LANDING)
#     else:
#         flap_setting = 0
#         gear_down = False
    
#     # Calculate Button
#     calculate_btn = st.button(
#         "📊 Calculate Performance",
#         type="primary",
#         use_container_width=True
#     )

# # ===============================================
# # MAIN DASHBOARD
# # ===============================================

# st.markdown('<h1 class="main-title">✈️ AeroPerformance Pro</h1>', unsafe_allow_html=True)
# st.markdown('<p style="text-align: center; color: #666; font-size: 1.1rem;">Professional Aircraft Performance Analysis Tool</p>', unsafe_allow_html=True)

# # Aircraft Info Banner
# col1, col2, col3 = st.columns([2, 1, 1])
# with col1:
#     st.markdown(f"### {aircraft_name}")
#     st.markdown(f"**{aircraft['type']}** • {aircraft['manufacturer']}")
#     st.caption(aircraft["description"])

# with col2:
#     wing_loading = weight_kg * 9.80665 / aircraft["wing_area_m2"]
#     st.metric("Wing Loading", f"{wing_loading:.0f} N/m²")

# with col3:
#     aspect_ratio = aircraft["wing_span_m"]**2 / aircraft["wing_area_m2"]
#     st.metric("Aspect Ratio", f"{aspect_ratio:.2f}")

# st.markdown("---")

# # ===============================================
# # PERFORMANCE ANALYSIS
# # ===============================================

# if calculate_btn:
#     st.markdown(f'<h3 class="section-title">📈 {flight_phase} Performance Analysis</h3>', unsafe_allow_html=True)
    
#     # Atmosphere conditions
#     atmos = performance_model.isa_atmosphere(altitude_m)
    
#     with st.expander("🌡️ Atmosphere Conditions", expanded=True):
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("Temperature", f"{atmos['temperature_K'] - 273.15:.1f} °C")
#         with col2:
#             st.metric("Pressure", f"{atmos['pressure_Pa']/100:.0f} hPa")
#         with col3:
#             st.metric("Density", f"{atmos['density_kg_m3']:.3f} kg/m³")
#         with col4:
#             st.metric("Speed of Sound", f"{atmos['speed_of_sound_m_s']:.0f} m/s")
    
#     # Phase-specific calculations
#     if flight_phase == FlightPhase.TAKEOFF:
#         st.markdown('<div class="info">🚀 Takeoff Performance Calculation (FAR 25)</div>', unsafe_allow_html=True)
        
#         results = performance_model.takeoff_distance(
#             weight_kg, altitude_m, temperature_C, headwind_m_s
#         )
        
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("V₁ - Stall Speed", f"{results['V_stall']:.1f} m/s")
#             st.metric("Vᵣ - Rotation Speed", f"{results['V_r']:.1f} m/s")
#             st.metric("V₂ - Safety Speed", f"{results['V_2']:.1f} m/s")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         with col2:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("Ground Roll", f"{results['ground_roll_m']:.0f} m")
#             st.metric("Air Distance", f"{results['air_distance_m']:.0f} m")
#             st.metric("Total Distance", f"{results['total_distance_m']:.0f} m")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         with col3:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             # Field length requirements
#             field_length_required = results['total_distance_m'] * 1.15  # FAR 25 margin
#             available_runway = 2000.0  # Assume 2000m runway
            
#             st.metric("Required Field Length", f"{field_length_required:.0f} m")
#             st.metric("Runway Available", f"{available_runway:.0f} m")
            
#             if field_length_required <= available_runway:
#                 st.markdown('<div class="success">✅ Takeoff feasible</div>', unsafe_allow_html=True)
#             else:
#                 st.markdown('<div class="warning">⚠️ Insufficient runway</div>', unsafe_allow_html=True)
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         # Takeoff chart
#         fig = go.Figure()
        
#         # Ground roll phase
#         fig.add_trace(go.Scatter(
#             x=[0, results['ground_roll_m']],
#             y=[0, 0],
#             mode='lines',
#             line=dict(width=4, color='#4CAF50'),
#             name='Ground Roll'
#         ))
        
#         # Air phase
#         fig.add_trace(go.Scatter(
#             x=[results['ground_roll_m'], results['total_distance_m']],
#             y=[0, 15],  # 15m height
#             mode='lines',
#             line=dict(width=4, color='#2196F3'),
#             name='Air Phase'
#         ))
        
#         # Rotation point
#         fig.add_trace(go.Scatter(
#             x=[results['ground_roll_m']],
#             y=[0],
#             mode='markers',
#             marker=dict(size=12, color='#FF9800'),
#             name='Rotation'
#         ))
        
#         # 35ft point
#         fig.add_trace(go.Scatter(
#             x=[results['total_distance_m']],
#             y=[15],
#             mode='markers',
#             marker=dict(size=12, color='#E91E63'),
#             name='35ft Clearance'
#         ))
        
#         fig.update_layout(
#             title='Takeoff Profile',
#             xaxis_title='Distance (m)',
#             yaxis_title='Height (m)',
#             height=400,
#             showlegend=True
#         )
        
#         st.plotly_chart(fig, use_container_width=True)
    
#     elif flight_phase == FlightPhase.LANDING:
#         st.markdown('<div class="info">🛬 Landing Performance Calculation (FAR 25)</div>', unsafe_allow_html=True)
        
#         results = performance_model.landing_distance(
#             weight_kg, altitude_m, temperature_C, tailwind_m_s
#         )
        
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("Vʀᴇꜰ - Reference Speed", f"{results['V_ref']:.1f} m/s")
#             st.metric("Vᴛᴅ - Touchdown Speed", f"{results['V_td']:.1f} m/s")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         with col2:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("Air Distance", f"{results['air_distance_m']:.0f} m")
#             st.metric("Ground Roll", f"{results['ground_roll_m']:.0f} m")
#             st.metric("Total Distance", f"{results['total_distance_m']:.0f} m")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         with col3:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             field_length_required = results['total_distance_m'] * 1.67  # FAR 25 margin
#             available_runway = 2000.0
            
#             st.metric("Required Field Length", f"{field_length_required:.0f} m")
#             st.metric("Runway Available", f"{available_runway:.0f} m")
            
#             if field_length_required <= available_runway:
#                 st.markdown('<div class="success">✅ Landing feasible</div>', unsafe_allow_html=True)
#             else:
#                 st.markdown('<div class="warning">⚠️ Insufficient runway</div>', unsafe_allow_html=True)
#             st.markdown('</div>', unsafe_allow_html=True)
    
#     elif flight_phase == FlightPhase.CLIMB:
#         st.markdown('<div class="info">📈 Climb Performance</div>', unsafe_allow_html=True)
        
#         mach = velocity / atmos['speed_of_sound_m_s']
#         results = performance_model.climb_performance(
#             weight_kg, altitude_m, velocity, "clean"
#         )
        
#         col1, col2, col3, col4 = st.columns(4)
#         with col1:
#             st.metric("Rate of Climb", f"{results['rate_of_climb_m_s']:.1f} m/s")
#             st.metric("", f"{results['rate_of_climb_ft_min']:.0f} ft/min")
#         with col2:
#             st.metric("Climb Angle", f"{results['climb_angle_deg']:.1f}°")
#             st.metric("Climb Gradient", f"{results['climb_gradient']*100:.1f}%")
#         with col3:
#             st.metric("Excess Power", f"{results['excess_power_w']/1000:.1f} kW")
#         with col4:
#             st.metric("Mach Number", f"{mach:.2f}")
        
#         # Climb gradient chart
#         altitudes = np.linspace(0, aircraft['service_ceiling_m'], 20)
#         climb_rates = []
        
#         for alt in altitudes:
#             climb_results = performance_model.climb_performance(
#                 weight_kg, alt, velocity, "clean"
#             )
#             climb_rates.append(climb_results['rate_of_climb_ft_min'])
        
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(
#             x=climb_rates, y=altitudes,
#             mode='lines',
#             line=dict(width=3, color='#2196F3'),
#             name='Rate of Climb'
#         ))
        
#         fig.add_hline(y=altitude_m, line_dash="dash", line_color="red",
#                      annotation_text=f"Current: {altitude_m:.0f} m")
        
#         fig.update_layout(
#             title='Climb Performance vs Altitude',
#             xaxis_title='Rate of Climb (ft/min)',
#             yaxis_title='Altitude (m)',
#             height=400
#         )
        
#         st.plotly_chart(fig, use_container_width=True)
    
#     elif flight_phase == FlightPhase.CRUISE:
#         st.markdown('<div class="info">✈️ Cruise Performance</div>', unsafe_allow_html=True)
        
#         results = performance_model.cruise_performance(weight_kg, altitude_m, mach)
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("True Airspeed", f"{results['velocity_m_s']:.0f} m/s")
#             st.metric("Mach Number", f"{mach:.2f}")
#             st.metric("L/D Ratio", f"{results['LD_ratio']:.1f}")
#             st.metric("Drag", f"{results['drag_n']/1000:.1f} kN")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         with col2:
#             st.markdown('<div class="metric-box">', unsafe_allow_html=True)
#             st.metric("Fuel Flow", f"{results['fuel_flow_kg_hr']:.0f} kg/hr")
#             st.metric("Specific Air Range", f"{results['SAR_m_kg']/1000:.1f} km/kg")
            
#             if results['endurance_hr'] > 0:
#                 st.metric("Endurance", f"{results['endurance_hr']:.1f} hours")
#                 st.metric("Range", f"{results['range_km']:.0f} km")
#             st.markdown('</div>', unsafe_allow_html=True)
        
#         # Range-Payload Chart
#         payloads = np.linspace(0, aircraft['weight_kg'] * 0.4, 10)
#         ranges = []
        
#         for payload in payloads:
#             total_weight = aircraft['weight_kg'] * 0.6 + payload  # Assume 60% empty weight
#             cruise_results = performance_model.cruise_performance(
#                 total_weight, altitude_m, mach
#             )
#             ranges.append(cruise_results['range_km'])
        
#         fig = go.Figure()
#         fig.add_trace(go.Scatter(
#             x=payloads, y=ranges,
#             mode='lines+markers',
#             line=dict(width=3, color='#4CAF50'),
#             name='Range-Payload'
#         ))
        
#         fig.update_layout(
#             title='Range-Payload Diagram',
#             xaxis_title='Payload (kg)',
#             yaxis_title='Range (km)',
#             height=400
#         )
        
#         st.plotly_chart(fig, use_container_width=True)
    
#     # Performance Summary Card
#     st.markdown("---")
#     st.markdown("### 📋 Performance Summary")
    
#     summary_data = {
#         "Parameter": ["Flight Phase", "Altitude", "Aircraft", "Weight", "Status"],
#         "Value": [
#             flight_phase,
#             f"{altitude_m:.0f} m ({altitude_m/0.3048:.0f} ft)",
#             aircraft_name,
#             f"{weight_kg:.0f} kg",
#             "✅ Within Limits" if flight_phase != FlightPhase.TAKEOFF or field_length_required <= available_runway else "⚠️ Check Limits"
#         ]
#     }
    
#     st.table(pd.DataFrame(summary_data))
    
#     # Download Report
#     report = {
#         "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
#         "aircraft": aircraft_name,
#         "flight_phase": flight_phase,
#         "weight_kg": weight_kg,
#         "altitude_m": altitude_m,
#         "results": results if 'results' in locals() else {}
#     }
    
#     json_report = json.dumps(report, indent=2, default=str)
    
#     st.download_button(
#         label="📥 Download Performance Report (JSON)",
#         data=json_report,
#         file_name=f"performance_report_{aircraft_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
#         mime="application/json"
#     )

# # ===============================================
# # FOOTER
# # ===============================================

# st.markdown("---")
# footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])
# with footer_col2:
#     st.markdown("""
#     <div style="text-align: center; color: #666; font-size: 0.9rem;">
#         <p><strong>AeroPerformance Pro v2.1</strong> | Industry-Standard Flight Performance Analysis</p>
#         <p>© 2024 Aerospace Engineering Tools | Based on FAR 25/23 Regulations</p>
#         <p>For training and simulation purposes only</p>
#     </div>
#     """, unsafe_allow_html=True)

# # ===============================================
# # ADDITIONAL PROFESSIONAL FEATURES (Collapsible)
# # ===============================================

# with st.expander("🛠️ Engineering Tools"):
#     tab1, tab2, tab3 = st.tabs(["Unit Converter", "Performance Tables", "References"])
    
#     with tab1:
#         st.markdown("#### Aviation Unit Converter")
#         col1, col2 = st.columns(2)
#         with col1:
#             knots = st.number_input("Knots (KTAS)", value=100.0)
#             feet = st.number_input("Feet (ft)", value=1000.0)
#             lbs = st.number_input("Pounds (lbs)", value=1000.0)
#         with col2:
#             st.metric("→ m/s", f"{knots * 0.514444:.1f}")
#             st.metric("→ meters", f"{feet * 0.3048:.0f}")
#             st.metric("→ kg", f"{lbs * 0.453592:.1f}")
    
#     with tab2:
#         st.markdown("#### Standard Performance Tables")
#         # Could add Breguet range equation, climb tables, etc.
#         st.info("Performance tables would be loaded from aircraft flight manual data")
    
#     with tab3:
#         st.markdown("#### Industry References")
#         st.markdown("""
#         - **FAR Part 25**: Airworthiness Standards: Transport Category Airplanes
#         - **FAR Part 23**: Airworthiness Standards: Normal Category Airplanes
#         - **ICAO Doc 8168**: Procedures for Air Navigation Services - Aircraft Operations
#         - **AC 25-7**: Flight Test Guide for Certification of Transport Category Airplanes
#         - **ESDU Data Sheets**: Aerodynamic and performance data
#         """)
