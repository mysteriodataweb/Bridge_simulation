import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE SETUP ---
st.set_page_config(page_title="Total Bridge MMC Simulator", layout="wide")
st.title("🏗️ Full Marine Bridge Mechanical Analysis")

# --- 1. PARAMETERS ---
st.sidebar.header("🌉 Bridge Geometry")
L_deck = st.sidebar.slider("Deck Length (m)", 50, 500, 200)
W_deck = st.sidebar.slider("Deck Width (m)", 10, 30, 15)
H_piers = st.sidebar.slider("Piers Height (m)", 10, 60, 30)
D_piers = st.sidebar.slider("Piers Diameter (m)", 2.0, 8.0, 4.0)

st.sidebar.header("🌪️ Environmental Hazards")
V_wind = st.sidebar.slider("Wind Velocity (m/s)", 0, 100, 40)
H_wave = st.sidebar.slider("Wave Height (m)", 0.0, 20.0, 5.0)
A_seismic = st.sidebar.slider("Seismic Accel (g)", 0.0, 1.5, 0.3)

# --- 2. THE PHYSICS ENGINE (MMC) ---
E = 30e9        # Concrete Young's Modulus
rho_c = 2500    # Concrete Density
yield_limit = 25e6 # 25 MPa

# Geometry Calculations
Area_pier = np.pi * (D_piers/2)**2
I_pier = (np.pi * D_piers**4) / 64
Vol_deck = L_deck * W_deck * 2 # Assuming 2m thickness
Vol_piers = Area_pier * H_piers * 2 # 2 Piers system

# Mass & Weight (Volume Forces)
Mass_total = (Vol_deck + Vol_piers) * rho_c
Weight_total = Mass_total * 9.81

# Surface Forces
# Wind on Deck + Piers
F_wind = 0.5 * 1.2 * (V_wind**2) * (L_deck * 2 + H_piers * D_piers)
# Water on Piers
F_water = 0.5 * 1025 * 1.5 * D_piers * (H_wave**2)
# Seismic Inertia (F = m*a)
F_seismic = Mass_total * (A_seismic * 9.81)

# Resultant Stress Analysis at Pier Base
# 1. Normal Stress (Compression from weight)
sigma_axial = (Weight_total / 2) / Area_pier
# 2. Bending Stress (From horizontal loads)
Total_Horizontal_F = (F_wind + F_water + F_seismic) / 2 # Per pier
Moment_base = Total_Horizontal_F * H_piers
sigma_bending = (Moment_base * (D_piers/2)) / I_pier

# 3. Von Mises Combination
# sigma_VM = sqrt( (sigma_axial + sigma_bending)^2 + 3*tau^2 ) 
# Simplified: Focus on max normal stress sum
sigma_max = sigma_axial + sigma_bending
safety_ratio = sigma_max / yield_limit

# --- 3. DASHBOARD DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Total Weight", f"{Weight_total/1e6:.1f} MN")
col2.metric("Total Wind Force", f"{F_wind/1e3:.1f} kN")
col3.metric("Seismic Force", f"{F_seismic/1e6:.1f} MN")

# --- 4. VISUALIZATION ---
st.write("### 🌍 Force & Stress Distribution")
fig, ax = plt.subplots(figsize=(12, 6))

# Draw Water Level
ax.axhspan(0, H_wave, color='cyan', alpha=0.1, label="Submerged Zone")

# Draw Bridge Structure (Original)
# Piers
ax.plot([L_deck/4, L_deck/4], [0, H_piers], 'k--', alpha=0.3)
ax.plot([3*L_deck/4, 3*L_deck/4], [0, H_piers], 'k--', alpha=0.3)
# Deck
ax.plot([0, L_deck], [H_piers, H_piers], 'k--', alpha=0.3)

# Draw Deflected Structure (Scaled for visibility)
scale = 5.0 / (max(sigma_max/1e6, 1))
deflection = (Total_Horizontal_F * H_piers**3) / (3 * E * I_pier)
d_x = deflection * 20 # exaggerated for view

# Deformed Piers
z = np.linspace(0, H_piers, 50)
x_p1 = (d_x) * (z/H_piers)**2 + L_deck/4
x_p2 = (d_x) * (z/H_piers)**2 + 3*L_deck/4
ax.plot(x_p1, z, color='blue', lw=D_piers, label="Piers (Stressed)")
ax.plot(x_p2, z, color='blue', lw=D_piers)

# Deformed Deck
ax.plot([x_p1[-1] - L_deck/4, x_p2[-1] + L_deck/4], [H_piers, H_piers], color='darkred', lw=5, label="Deck")

# Force Arrows
ax.arrow(L_deck/2, H_piers + 5, V_wind, 0, head_width=2, color='orange', label="Wind")
ax.arrow(-10, H_wave/2, 10, 0, head_width=2, color='teal', label="Waves")

ax.set_ylim(-5, H_piers + 20)
ax.legend(loc='upper right')
ax.set_title("Bridge Response Simulation")
st.pyplot(fig)

# Final Integrity Check
if sigma_max > yield_limit:
    st.error(f"❌ COLLAPSE: Max Stress {sigma_max/1e6:.2f} MPa exceeds Material Strength!")
else:
    st.success(f"✅ STABLE: Max Stress {sigma_max/1e6:.2f} MPa is within limits.")