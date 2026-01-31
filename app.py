import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Marine Bridge MMC Simulator", layout="wide")
st.title("🌉 Marine Bridge Structural Analysis (MMC)")
st.markdown("""
This simulator evaluates the mechanical behavior of a bridge pier under combined external hazards.
It uses **Euler-Bernoulli beam theory** and the **Von Mises yield criterion**.
""")

# --- 1. USER INTERFACE (SIDEBAR) ---
st.sidebar.header("Design Parameters & Hazards")

# Structural Parameters
st.sidebar.subheader("🏗️ Structure")
D = st.sidebar.slider("Pier Diameter (m)", 2.0, 10.0, 5.0)
H = st.sidebar.slider("Pier Height (m)", 20.0, 100.0, 50.0)
material = st.sidebar.selectbox("Material", ["Concrete", "Steel"])

# Environmental Hazards
st.sidebar.subheader("🌪️ External Hazards")
V_wind = st.sidebar.slider("Wind Speed (m/s)", 0, 80, 35)
H_wave = st.sidebar.slider("Wave Height (m)", 0.0, 15.0, 4.0)
A_seismic = st.sidebar.slider("Seismic Intensity (g)", 0.0, 1.0, 0.15)

# --- 2. PHYSICS ENGINE (MMC LOGIC) ---
# Material properties
if material == "Concrete":
    E = 30e9        # Young's Modulus (Pa)
    yield_limit = 25e6 # Yield strength (25 MPa)
    rho_mat = 2500  # Density (kg/m3)
else:
    E = 210e9       # Steel Young's Modulus
    yield_limit = 250e6 # Yield strength (250 MPa)
    rho_mat = 7850

I = (np.pi * D**4) / 64  # Moment of Inertia (m4)

# Force Calculations
# Wind Surface Force (Drag)
F_wind = 0.5 * 1.225 * 1.2 * D * (V_wind**2) * (H/2) 

# Hydrodynamic Surface Force (Morison simplified)
F_water = 0.5 * 1025 * 1.5 * D * (H_wave**2) 

# Seismic Volume Force (Inertia: F = m * a)
mass = rho_mat * np.pi * (D/2)**2 * H
F_seismic = mass * (A_seismic * 9.81)

# Resultant Force and Moment
F_total = F_wind + F_water + F_seismic
M_base = F_total * (H/2) # Bending moment at the fixed base

# --- 3. MECHANICAL RESPONSE ---
# Elastic Deflection (Hooke's Law application)
# Max deflection formula for a cantilever beam
max_deflection = (F_total * H**3) / (3 * E * I)

# Stress Analysis (Von Mises)
# We calculate bending stress (sigma) and check against the yield limit
sigma_bending = (M_base * (D/2)) / I
von_mises = np.sqrt(sigma_bending**2) # Simplified for 1D bending
safety_ratio = von_mises / yield_limit

# --- 4. DATA VISUALIZATION ---
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📊 Structural Integrity (Von Mises)")
    
    if safety_ratio > 1:
        st.error(f"🔴 STRUCTURAL FAILURE! Stress: {von_mises/1e6:.2f} MPa exceeds Limit")
    elif safety_ratio > 0.8:
        st.warning(f"🟡 CRITICAL: Stress: {von_mises/1e6:.2f} MPa near Yield Limit")
    else:
        st.success(f"🟢 SAFE: Stress: {von_mises/1e6:.2f} MPa within Elastic Range")
    
    # Visual gauge
    st.progress(min(safety_ratio, 1.0))
    st.write(f"Utilization: **{safety_ratio*100:.1f}%**")

with col2:
    st.subheader("🎨 Elastic Displacement Visualization")
    fig, ax = plt.subplots(figsize=(5, 8))
    
    # Calculating the deflected shape (y = height, x = displacement)
    z = np.linspace(0, H, 100)
    # Cantilever deflection curve equation
    x_disp = (max_deflection) * ( (z**2 * (3*H - z)) / (2 * H**3) )
    
    ax.plot(x_disp * 100, z, lw=5, color='royalblue', label="Deflected Pier")
    ax.axvline(0, color='black', linestyle='--', alpha=0.5, label="Original Axis")
    ax.set_xlim(-150, 150) # Range in centimeters
    ax.set_ylim(0, H + 5)
    ax.set_xlabel("Horizontal Displacement (cm)")
    ax.set_ylabel("Height (m)")
    ax.legend()
    ax.grid(True, linestyle=':')
    st.pyplot(fig)

st.write("---")
st.caption("Developed for MMC Analysis. This model assumes a linear elastic material and a fixed-base cantilever pier.")