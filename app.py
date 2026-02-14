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
