import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE SETUP ---
st.set_page_config(page_title="Total Bridge MMC Simulator", layout="wide")
st.title("🏗️ Full Marine Bridge Mechanical Analysis")

# --- 1. PARAMETERS (Interface kept identical) ---
st.sidebar.header("🌉 Bridge Geometry")
L_deck = st.sidebar.slider("Deck Length (m)", 50, 500, 200)
W_deck = st.sidebar.slider("Deck Width (m)", 10, 30, 15)
H_piers = st.sidebar.slider("Piers Height (m)", 10, 60, 30)
D_piers = st.sidebar.slider("Piers Diameter (m)", 2.0, 8.0, 4.0)

st.sidebar.header("🌪️ Environmental Hazards")
V_wind = st.sidebar.slider("Wind Velocity (m/s)", 0, 100, 40)
H_wave = st.sidebar.slider("Wave Height (m)", 0.0, 20.0, 5.0)
A_seismic = st.sidebar.slider("Seismic Accel (g)", 0.0, 1.5, 0.3)

# --- 2. UPDATED PHYSICS ENGINE (MMC) ---
E = 30e9        # Concrete Young's Modulus
rho_c = 2500    # Concrete Density
rho_w = 1025    # Saltwater Density
yield_limit = 25e6 # 25 MPa
T_deck = 2.0    # Defined thickness for calculation

# Geometry Calculations
Area_pier = np.pi * (D_piers/2)**2
I_pier = (np.pi * D_piers**4) / 64
Vol_deck = L_deck * W_deck * T_deck # Updated with T_deck variable
Vol_piers = Area_pier * H_piers * 2 

# Mass & Weight with Buoyancy (Archimède)
Mass_total = (Vol_deck + Vol_piers) * rho_c
# Buoyancy: weight of displaced water by the submerged pier part (assume wave height = water depth for simplicity)
Vol_submerged = Area_pier * H_wave * 2 
F_buoyancy = Vol_submerged * rho_w * 9.81
Weight_effective = (Mass_total * 9.81) - F_buoyancy

# Surface Forces
# Updated Wind: Wind acts on the lateral surface of the Deck (Length * Thickness)
F_wind_deck = 0.5 * 1.2 * (V_wind**2) * (L_deck * T_deck)
F_wind_piers = 0.5 * 1.2 * (V_wind**2) * (D_piers * (H_piers - H_wave))
F_wind = F_wind_deck + F_wind_piers

# Water Forces (Drag on submerged piers)
F_water = 0.5 * rho_w * 1.5 * D_piers * (H_wave**2)

# Seismic Inertia
F_seismic = Mass_total * (A_seismic * 9.81)

# Resultant Stress Analysis (Von Mises logic)
# 1. Normal Stress (Compression from effective weight)
sigma_axial = (Weight_effective / 2) / Area_pier

# 2. Bending Stress
# The Deck wind force has a leverage of H_piers
Total_Horizontal_F = (F_wind + F_water + F_seismic) / 2
Moment_base = (F_wind_deck * H_piers) + (F_wind_piers * H_piers/2) + (F_water * H_wave/2) + (F_seismic/2 * H_piers/2)
sigma_bending = (Moment_base * (D_piers/2)) / I_pier

# 3. Combined Stress (Simplified Von Mises)
sigma_max = np.sqrt(sigma_axial**2 + sigma_bending**2)
safety_ratio = sigma_max / yield_limit

# --- 3. DASHBOARD DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Effective Weight (Net)", f"{Weight_effective/1e6:.1f} MN")
col2.metric("Total Wind Force", f"{F_wind/1e3:.1f} kN")
col3.metric("Seismic Force", f"{F_seismic/1e6:.1f} MN")

# --- 4. VISUALIZATION (Logic kept, scaled for new forces) ---
st.write("### 🌍 Force & Stress Distribution")
fig, ax = plt.subplots(figsize=(12, 6))
ax.axhspan(0, H_wave, color='cyan', alpha=0.1, label="Submerged Zone")

# Draw Bridge Original Axis
ax.plot([L_deck/4, L_deck/4], [0, H_piers], 'k--', alpha=0.3)
ax.plot([3*L_deck/4, 3*L_deck/4], [0, H_piers], 'k--', alpha=0.3)
ax.plot([0, L_deck], [H_piers, H_piers], 'k--', alpha=0.3)

# Deflection calculation
deflection = (Total_Horizontal_F * H_piers**3) / (3 * E * I_pier)
d_x = deflection * 50 # Scale for visibility

# Deformed Structure
z = np.linspace(0, H_piers, 50)
x_p1 = (d_x) * (z/H_piers)**2 + L_deck/4
x_p2 = (d_x) * (z/H_piers)**2 + 3*L_deck/4
ax.plot(x_p1, z, color='blue', lw=D_piers, label="Piers (Stressed)")
ax.plot(x_p2, z, color='blue', lw=D_piers)
ax.plot([x_p1[-1] - L_deck/4, x_p2[-1] + L_deck/4], [H_piers, H_piers], color='darkred', lw=T_deck*2, label="Deck")

# Force Arrows
ax.arrow(L_deck/2, H_piers + 5, V_wind/2, 0, head_width=2, color='orange', label="Wind Vector")
ax.arrow(-10, H_wave/2, 10, 0, head_width=2, color='teal', label="Wave Vector")

ax.set_ylim(-5, H_piers + 20)
ax.legend(loc='upper right')
ax.set_title("Bridge Response Simulation")
st.pyplot(fig)

if sigma_max > yield_limit:
    st.error(f"❌ COLLAPSE: Max Stress {sigma_max/1e6:.2f} MPa exceeds Material Strength!")
else:
    st.success(f"✅ STABLE: Max Stress {sigma_max/1e6:.2f} MPa is within limits.")