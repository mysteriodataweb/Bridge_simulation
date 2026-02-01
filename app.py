import streamlit as st
import numpy as np
import plotly.graph_objects as go

# --- PAGE SETUP ---
st.set_page_config(page_title="3D Marine Bridge MMC", layout="wide")
st.title("🌉 3D Marine Bridge Structural Analysis")

# --- 1. PARAMETERS (Sidebar) ---
st.sidebar.header("🌉 Bridge Geometry")
L_deck = st.sidebar.slider("Deck Length (m)", 50, 500, 200)
W_deck = st.sidebar.slider("Deck Width (m)", 10, 30, 15)
T_deck = st.sidebar.slider("Deck Thickness (m)", 1.0, 5.0, 2.5)
H_piers = st.sidebar.slider("Piers Height (m)", 10, 60, 30)
D_piers = st.sidebar.slider("Piers Diameter (m)", 2.0, 8.0, 4.0)

st.sidebar.header("🌪️ Environmental Hazards")
V_wind = st.sidebar.slider("Wind Velocity (m/s)", 0, 100, 40)
H_wave = st.sidebar.slider("Water Depth (m)", 0.0, 20.0, 5.0)
A_seismic = st.sidebar.slider("Seismic Accel (g)", 0.0, 1.5, 0.3)

# --- 2. PHYSICS ENGINE (MMC) ---
E = 30e9        # Young's Modulus (Pa)
rho_c = 2500    # Concrete Density
rho_w = 1025    # Water Density
yield_limit = 25e6 

Area_pier = np.pi * (D_piers/2)**2
I_pier = (np.pi * D_piers**4) / 64
Vol_deck = L_deck * W_deck * T_deck 
Vol_piers = Area_pier * H_piers * 2 
Mass_total = (Vol_deck + Vol_piers) * rho_c

# Forces
F_wind = 0.5 * 1.2 * (V_wind**2) * (L_deck * T_deck + D_piers * (H_piers - H_wave))
F_water = 0.5 * rho_w * 1.5 * D_piers * (H_wave**2)
F_seismic = Mass_total * (A_seismic * 9.81)
Total_F_h = (F_wind + F_water + F_seismic) / 2 # Per pier

# Stress & Deflection
Moment_base = (F_wind * H_piers) + (F_water * H_wave/2) + (F_seismic * H_piers/2)
sigma_axial = (Mass_total * 9.81 / 2) / Area_pier
sigma_bending = (Moment_base/2 * (D_piers/2)) / I_pier
sigma_max = np.sqrt(sigma_axial**2 + sigma_bending**2)

# Elastic Deflection (The curve)
max_d = (Total_F_h * H_piers**3) / (3 * E * I_pier)
z = np.linspace(0, H_piers, 20)
deflection_curve = max_d * (z/H_piers)**2

# --- 3. 3D VISUALIZATION (PLOTLY) ---
st.write("### 🧊 Interactive 3D Structural Response & Force Vectors")
fig = go.Figure()

# --- DRAWING PIERS ---
def draw_pier(x_offset, color):
    x_coords = x_offset + deflection_curve
    y_coords = np.zeros_like(z)
    fig.add_trace(go.Scatter3d(
        x=x_coords, y=y_coords, z=z,
        mode='lines',
        line=dict(color=color, width=D_piers*5),
        name="Bridge Pier"
    ))

draw_pier(-L_deck/4, 'blue')
draw_pier(L_deck/4, 'blue')

# --- DRAWING DECK ---
d_top = deflection_curve[-1]
fig.add_trace(go.Mesh3d(
    x=[d_top-L_deck/2, d_top+L_deck/2, d_top+L_deck/2, d_top-L_deck/2, d_top-L_deck/2, d_top+L_deck/2, d_top+L_deck/2, d_top-L_deck/2],
    y=[-W_deck/2, -W_deck/2, W_deck/2, W_deck/2, -W_deck/2, -W_deck/2, W_deck/2, W_deck/2],
    z=[H_piers, H_piers, H_piers, H_piers, H_piers+T_deck, H_piers+T_deck, H_piers+T_deck, H_piers+T_deck],
    i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2], j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3], k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
    color='brown', opacity=0.8, name="Deck"
))

# --- DRAWING WATER SURFACE ---
fig.add_trace(go.Mesh3d(
    x=[-L_deck, L_deck, L_deck, -L_deck], y=[-L_deck/2, -L_deck/2, L_deck/2, L_deck/2],
    z=[H_wave, H_wave, H_wave, H_wave],
    color='cyan', opacity=0.2, name="Water Level"
))

# --- ADDING FORCE VECTORS (CONES) ---
# Normalizing vector size for visibility
scale_f = L_deck / 5

def add_force(x, y, z, val, name, col):
    if val > 0:
        fig.add_trace(go.Cone(
            x=[x], y=[y], z=[z], u=[val], v=[0], w=[0],
            sizemode="scaled", sizeref=0.5, showscale=False,
            colorscale=[[0, col], [1, col]], name=name
        ))

# Wind Force (Applied to Deck)
add_force(d_top, 0, H_piers + T_deck/2, scale_f, "Wind Force", "orange")
# Wave Force (Applied to Piers at water level)
add_force(deflection_curve[int(len(z)/2)], 0, H_wave/2, scale_f*0.7, "Wave Force", "teal")
# Seismic Force (Applied to middle of structure)
add_force(d_top/2, 0, H_piers/2, scale_f*0.5, "Seismic Force", "green")

# Scene Configuration
fig.update_layout(
    scene=dict(
        aspectmode='data',
        xaxis=dict(title="Lateral (m)", range=[-L_deck, L_deck]),
        yaxis=dict(title="Width (m)", range=[-L_deck/2, L_deck/2]),
        zaxis=dict(title="Height (m)", range=[0, H_piers + 15]),
    ),
    margin=dict(l=0, r=0, b=0, t=0), height=700
)

st.plotly_chart(fig, use_container_width=True)

# --- RESULTS ---
if sigma_max > yield_limit:
    st.error(f"❌ COLLAPSE: Von Mises Stress ({sigma_max/1e6:.2f} MPa) exceeds 25 MPa!")
else:
    st.success(f"✅ STABLE: Von Mises Stress ({sigma_max/1e6:.2f} MPa) is safe.")