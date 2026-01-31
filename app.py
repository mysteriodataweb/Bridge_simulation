import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# --- PAGE SETUP ---
st.set_page_config(page_title="Total Bridge MMC Simulator", layout="wide")
st.title("🏗️ Full Marine Bridge Mechanical Analysis")

# --- 1. PARAMETERS (Interface mise à jour avec les nouveaux paramètres) ---
st.sidebar.header("🌉 Bridge Geometry")
L_deck = st.sidebar.slider("Deck Length (m)", 50, 500, 200)
W_deck = st.sidebar.slider("Deck Width (m)", 10, 30, 15)
T_deck = st.sidebar.slider("Deck Thickness (m)", 1.0, 5.0, 2.5) # NOUVEAU
H_piers = st.sidebar.slider("Piers Height (m)", 10, 60, 30)
D_piers = st.sidebar.slider("Piers Diameter (m)", 2.0, 8.0, 4.0)

st.sidebar.header("🌪️ Environmental Hazards")
V_wind = st.sidebar.slider("Wind Velocity (m/s)", 0, 100, 40)
H_wave = st.sidebar.slider("Wave Height / Water Depth (m)", 0.0, 20.0, 5.0) # MIS À JOUR
A_seismic = st.sidebar.slider("Seismic Accel (g)", 0.0, 1.5, 0.3)

# --- 2. THE PHYSICS ENGINE (MMC) ---
E = 30e9        # Module de Young du Béton (Pa)
rho_c = 2500    # Masse volumique Béton (kg/m3)
rho_w = 1025    # Masse volumique Eau salée (kg/m3)
yield_limit = 25e6 # Limite élastique (25 MPa)

# Calculs Géométriques
Area_pier = np.pi * (D_piers/2)**2
I_pier = (np.pi * D_piers**4) / 64
Vol_deck = L_deck * W_deck * T_deck 
Vol_piers = Area_pier * H_piers * 2 

# Masse & Poids Effectif (Bilan Vertical : Poids - Archimède)
Mass_total = (Vol_deck + Vol_piers) * rho_c
# Archimède : Poids de l'eau déplacée par la partie immergée des piles
Vol_submerged = Area_pier * H_wave * 2 
F_buoyancy = Vol_submerged * rho_w * 9.81
Weight_effective = (Mass_total * 9.81) - F_buoyancy

# Forces de Surface (Bilan Horizontal)
# Vent : Frappe la face latérale du deck (L x T) et la partie émergée des piles
F_wind_deck = 0.5 * 1.2 * (V_wind**2) * (L_deck * T_deck)
F_wind_piers = 0.5 * 1.2 * (V_wind**2) * (D_piers * (H_piers - H_wave))
F_wind = F_wind_deck + F_wind_piers

# Eau : Traînée hydrodynamique sur les piles
F_water = 0.5 * rho_w * 1.5 * D_piers * (H_wave**2)

# Séisme : Force d'inertie de Volume (F = m*a)
F_seismic = Mass_total * (A_seismic * 9.81)

# Analyse des Contraintes à la Base (Point Critique)
# 1. Contrainte Normale (Compression axiale)
sigma_axial = (Weight_effective / 2) / Area_pier

# 2. Contrainte de Flexion (Moments cumulés)
# Le vent sur le deck a un bras de levier de H_piers
Total_Horizontal_F = (F_wind + F_water + F_seismic) / 2
Moment_base = (F_wind_deck * H_piers) + (F_wind_piers * H_piers/2) + (F_water * H_wave/2) + (F_seismic/2 * H_piers/2)
sigma_bending = (Moment_base * (D_piers/2)) / I_pier

# 3. Combinaison de Von Mises (Simplifiée pour flexion-compression)
sigma_max = np.sqrt(sigma_axial**2 + sigma_bending**2)
safety_ratio = sigma_max / yield_limit

# --- 3. DASHBOARD DISPLAY ---
col1, col2, col3 = st.columns(3)
col1.metric("Effective Weight (Net)", f"{Weight_effective/1e6:.1f} MN")
col2.metric("Total Wind Force", f"{F_wind/1e3:.1f} kN")
col3.metric("Seismic Force", f"{F_seismic/1e6:.1f} MN")

# --- 4. VISUALIZATION ---
st.write("### 🌍 Force & Stress Distribution")
fig, ax = plt.subplots(figsize=(12, 6))

# Dessin du niveau de l'eau
ax.axhspan(0, H_wave, color='cyan', alpha=0.1, label="Submerged Zone")

# Dessin de la structure originale (en pointillé)
ax.plot([L_deck/4, L_deck/4], [0, H_piers], 'k--', alpha=0.3)
ax.plot([3*L_deck/4, 3*L_deck/4], [0, H_piers], 'k--', alpha=0.3)
ax.plot([0, L_deck], [H_piers, H_piers], 'k--', alpha=0.3)

# Calcul de la déformée (Réponse élastique)
deflection = (Total_Horizontal_F * H_piers**3) / (3 * E * I_pier)
d_x = deflection * 40 # Échelle d'exagération visuelle

# Dessin des Piles déformées
z = np.linspace(0, H_piers, 50)
x_p1 = (d_x) * (z/H_piers)**2 + L_deck/4
x_p2 = (d_x) * (z/H_piers)**2 + 3*L_deck/4
ax.plot(x_p1, z, color='blue', lw=D_piers, label="Piers (Stressed)")
ax.plot(x_p2, z, color='blue', lw=D_piers)

# Dessin du Tablier déformé (Épaisseur visuelle corrélée à T_deck)
ax.plot([x_p1[-1] - L_deck/4, x_p2[-1] + L_deck/4], [H_piers, H_piers], color='darkred', lw=T_deck*2, label="Deck")

# Flèches des forces
ax.arrow(L_deck/2, H_piers + 5, V_wind/2, 0, head_width=2, color='orange', label="Wind")
ax.arrow(-10, H_wave/2, 10, 0, head_width=2, color='teal', label="Waves")

ax.set_ylim(-5, H_piers + 20)
ax.legend(loc='upper right')
ax.set_title("Bridge Response Simulation (MMC Analysis)")
st.pyplot(fig)

# Rapport d'intégrité
if sigma_max > yield_limit:
    st.error(f"❌ COLLAPSE: Max Stress {sigma_max/1e6:.2f} MPa exceeds Material Strength (25 MPa)!")
else:
    st.success(f"✅ STABLE: Max Stress {sigma_max/1e6:.2f} MPa is within Elastic limits.")