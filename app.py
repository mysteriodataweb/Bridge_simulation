import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="Simulateur MMC 3D - Pont Marin", layout="wide")
st.title("🏗️ Analyse Mécanique Avancée (MMC) : Pont en Milieu Marin")

# --- 1. PARAMÈTRES (Barre latérale) ---
st.sidebar.header("🌉 Géométrie du Pont")
L_deck = st.sidebar.slider("Longueur du Tablier (m)", 50, 500, 200)
W_deck = st.sidebar.slider("Largeur du Tablier (m)", 10, 30, 15)
T_deck = st.sidebar.slider("Épaisseur du Tablier (m)", 1.0, 5.0, 2.5)
H_piers = st.sidebar.slider("Hauteur des Piles (m)", 10, 60, 30)
D_piers = st.sidebar.slider("Diamètre des Piles (m)", 2.0, 8.0, 4.0)

st.sidebar.header("🌪️ Risques Environnementaux")
V_wind = st.sidebar.slider("Vitesse du Vent (m/s)", 0, 100, 40)
H_wave = st.sidebar.slider("Profondeur d'Eau (m)", 0.0, 20.0, 5.0)
A_seismic = st.sidebar.slider("Accélération Sismique (g)", 0.0, 1.5, 0.3)

# --- 2. MOTEUR PHYSIQUE (MMC) ---
E = 30e9        # Module de Young (Pa)
rho_c = 2500    # Densité Béton (kg/m3)
rho_w = 1025    # Densité Eau (kg/m3)
yield_limit = 25e6 

Area_pier = np.pi * (D_piers/2)**2
I_pier = (np.pi * D_piers**4) / 64
Vol_deck = L_deck * W_deck * T_deck 
Vol_piers = Area_pier * H_piers * 2 
Mass_total = (Vol_deck + Vol_piers) * rho_c

# Calcul des Forces
F_wind = 0.5 * 1.2 * (V_wind**2) * (L_deck * T_deck + D_piers * (H_piers - H_wave))
F_water = 0.5 * rho_w * 1.5 * D_piers * (H_wave**2)
F_seismic = Mass_total * (A_seismic * 9.81)
Total_F_h = (F_wind + F_water + F_seismic) / 2 # Par pile

# Calcul d'Archimède (Poussée ascendante)
F_buoyancy = (Area_pier * H_wave * 2) * rho_w * 9.81
Weight_net = (Mass_total * 9.81) - F_buoyancy

# Analyse des Contraintes (Von Mises)
Moment_base = (F_wind * H_piers) + (F_water * H_wave/2) + (F_seismic * H_piers/2)
sigma_axial = (Weight_net / 2) / Area_pier
sigma_bending = (Moment_base/2 * (D_piers/2)) / I_pier
sigma_max = np.sqrt(sigma_axial**2 + sigma_bending**2)

# Déformation élastique (Courbe)
max_d = (Total_F_h * H_piers**3) / (3 * E * I_pier)
z = np.linspace(0, H_piers, 20)
deflection_curve = max_d * (z/H_piers)**2

# --- 3. AFFICHAGE DES VALEURS CLÉS (METRICS) ---
st.write("### 📊 Données Techniques de la Simulation")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Poids Net (MN)", f"{Weight_net/1e6:.2f}", help="Poids total incluant la poussée d'Archimède")
m2.metric("Force Vent (kN)", f"{F_wind/1e3:.1f}")
m3.metric("Inertie Séisme (MN)", f"{F_seismic/1e6:.2f}")
m4.metric("Stress Max (MPa)", f"{sigma_max/1e6:.2f}", delta=f"{(sigma_max/yield_limit)*100:.1f}% de limite", delta_color="inverse")

# --- 4. VISUALISATION 3D ---
st.write("### 🧊 Modélisation 3D et Vecteurs de Charge")
fig = go.Figure()

# Dessin des Piles
def draw_pier(x_offset, color):
    x_coords = x_offset + deflection_curve
    fig.add_trace(go.Scatter3d(x=x_coords, y=np.zeros_like(z), z=z, mode='lines',
                               line=dict(color=color, width=D_piers*5), name="Pile"))

draw_pier(-L_deck/4, 'blue')
draw_pier(L_deck/4, 'blue')

# Dessin du Tablier (Mesh3D)
d_top = deflection_curve[-1]
fig.add_trace(go.Mesh3d(
    x=[d_top-L_deck/2, d_top+L_deck/2, d_top+L_deck/2, d_top-L_deck/2, d_top-L_deck/2, d_top+L_deck/2, d_top+L_deck/2, d_top-L_deck/2],
    y=[-W_deck/2, -W_deck/2, W_deck/2, W_deck/2, -W_deck/2, -W_deck/2, W_deck/2, W_deck/2],
    z=[H_piers, H_piers, H_piers, H_piers, H_piers+T_deck, H_piers+T_deck, H_piers+T_deck, H_piers+T_deck],
    i=[7,0,0,0,4,4,6,6,4,0,3,2], j=[3,4,1,2,5,6,5,2,0,1,6,3], k=[0,7,2,3,6,7,1,1,5,5,7,6],
    color='brown', opacity=0.8, name="Tablier"
))

# Surface de l'eau
fig.add_trace(go.Mesh3d(x=[-L_deck, L_deck, L_deck, -L_deck], y=[-L_deck/2, -L_deck/2, L_deck/2, L_deck/2],
                        z=[H_wave, H_wave, H_wave, H_wave], color='cyan', opacity=0.2, name="Niveau d'eau"))

# --- AJOUT DES VECTEURS DE FORCE (CÔNES) ---
scale_f = L_deck / 5
def add_force(x, y, z, val, name, col):
    if val > 0:
        fig.add_trace(go.Cone(x=[x], y=[y], z=[z], u=[val], v=[0], w=[0],
                              sizemode="scaled", sizeref=0.5, showscale=False,
                              colorscale=[[0, col], [1, col]], name=name))

add_force(d_top, 0, H_piers + T_deck/2, scale_f, "Force Vent", "orange")
add_force(deflection_curve[10], 0, H_wave/2, scale_f*0.7, "Force Vagues", "teal")
add_force(d_top/2, 0, H_piers/2, scale_f*0.5, "Inertie Séisme", "green")

fig.update_layout(scene=dict(aspectmode='data', xaxis=dict(range=[-L_deck, L_deck]), 
                  zaxis=dict(range=[0, H_piers+20])), height=700, margin=dict(l=0, r=0, b=0, t=0))

st.plotly_chart(fig, use_container_width=True)

# --- BILAN D'INTÉGRITÉ ---
if sigma_max > yield_limit:
    st.error(f"❌ RUPTURE : La contrainte de Von Mises ({sigma_max/1e6:.2f} MPa) dépasse la limite élastique (25 MPa) !")
else:
    st.success(f"✅ STABLE : La contrainte ({sigma_max/1e6:.2f} MPa) est inférieure au seuil de rupture.")