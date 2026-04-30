"""
TerraIQ — Streamlit simulation dashboard.

Run with:
    streamlit run app.py
"""

import sys
sys.path.insert(0, ".")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="TerraIQ",
    page_icon="⛰️",
    layout="wide",
)

st.title("TerraIQ — Fuel Optimization Simulator")
st.caption("Baseline simulation: physics-based fuel consumption on real-world routes.")

# ── Sidebar ───────────────────────────────────────────────────────────────────

PRESETS = {
    "Donner Pass → Sacramento (I-80)": {
        "origin": (39.30, -120.14),
        "destination": (38.73, -121.38),
        "name": "Donner Pass → Sacramento",
    },
    "Provo → St. George (I-15)": {
        "origin": (40.23, -111.66),
        "destination": (37.10, -113.58),
        "name": "Provo → St. George",
    },
    "Denver → Grand Junction (I-70)": {
        "origin": (39.74, -104.98),
        "destination": (39.07, -108.55),
        "name": "Denver → Grand Junction",
    },
    "Nashville → Memphis (I-40)": {
        "origin": (36.17, -86.78),
        "destination": (35.15, -90.05),
        "name": "Nashville → Memphis",
    },
}

with st.sidebar:
    st.header("Route")
    preset = st.selectbox("Quick presets", options=["Custom"] + list(PRESETS.keys()))

    if preset != "Custom":
        p = PRESETS[preset]
        default_orig = p["origin"]
        default_dest = p["destination"]
        default_name = p["name"]
    else:
        default_orig = (39.30, -120.14)
        default_dest = (38.73, -121.38)
        default_name = "My Route"

    route_name = st.text_input("Route name", value=default_name)

    st.subheader("Origin")
    c1, c2 = st.columns(2)
    orig_lat = c1.number_input("Lat", value=default_orig[0], format="%.4f", key="olat")
    orig_lon = c2.number_input("Lon", value=default_orig[1], format="%.4f", key="olon")

    st.subheader("Destination")
    c3, c4 = st.columns(2)
    dest_lat = c3.number_input("Lat", value=default_dest[0], format="%.4f", key="dlat")
    dest_lon = c4.number_input("Lon", value=default_dest[1], format="%.4f", key="dlon")

    st.divider()
    st.header("Vehicle")
    vehicle_choice = st.selectbox("Vehicle", ["2022 Freightliner Cascadia DD15"])

    st.divider()
    st.header("Mode")
    mode = st.radio("Simulation mode", ["Baseline only", "Baseline + Optimizer"])
    spatial_step = st.slider(
        "Optimizer resolution (m)",
        min_value=50, max_value=300, value=100, step=50,
        help="Smaller = more accurate but slower. 100m recommended.",
        disabled=(mode == "Baseline only"),
    )

    st.divider()
    st.header("Speed")
    use_fixed = st.checkbox("Fixed speed (ignore limits)", disabled=(mode != "Baseline only"))
    fixed_kmh = st.slider("Speed (km/h)", 50, 120, 90, 5, disabled=not use_fixed)

    st.divider()
    st.header("Economics")
    diesel_price_gal = st.number_input(
        "Diesel price ($/gallon)",
        min_value=0.50, max_value=10.0, value=3.90, step=0.05, format="%.2f",
        help="Used to calculate cost savings. Default is US avg retail (EIA, 2026).",
    )
    diesel_price_liter = diesel_price_gal / 3.78541

    run = st.button("Run Simulation", type="primary", use_container_width=True)

# ── Idle state ────────────────────────────────────────────────────────────────

if not run:
    st.info(
        "Configure your route in the sidebar and click **Run Simulation**.\n\n"
        "The first run fetches live road network and elevation data — expect 30–90 seconds "
        "depending on route length."
    )
    st.stop()

# ── Run simulation ────────────────────────────────────────────────────────────

from simulation.runner import SimulationRunner
from data.vehicle_profiles.freightliner_2022 import Freightliner2022

vehicle_map = {"2022 Freightliner Cascadia DD15": Freightliner2022()}
vehicle = vehicle_map[vehicle_choice]
target_speed_ms = (fixed_kmh / 3.6) if use_fixed else None

runner = SimulationRunner(vehicle=vehicle)

with st.spinner("Fetching route and elevation data..."):
    try:
        baseline = runner.run(
            origin=(orig_lat, orig_lon),
            destination=(dest_lat, dest_lon),
            route_name=route_name,
            target_speed_ms=target_speed_ms,
        )
    except Exception as e:
        st.error(f"Simulation failed: {e}")
        st.stop()

optimized = None
if mode == "Baseline + Optimizer":
    with st.spinner(f"Optimizing speed trajectory ({spatial_step}m resolution)..."):
        try:
            optimized = runner.run_optimized(
                origin=(orig_lat, orig_lon),
                destination=(dest_lat, dest_lon),
                route_name=route_name,
                spatial_step_m=float(spatial_step),
            )
        except Exception as e:
            st.error(f"Optimizer failed: {e}")
            st.stop()

st.success(f"Done in {baseline.elapsed_seconds + (optimized.elapsed_seconds if optimized else 0):.1f}s")

# ── Metrics ───────────────────────────────────────────────────────────────────

result = baseline
if optimized:
    from simulation.evaluator import EvaluationReport
    report = EvaluationReport(baseline=baseline, optimized=optimized, diesel_price_per_liter=diesel_price_liter)
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    m1.metric("Distance", f"{baseline.total_distance_km:.1f} km")
    m2.metric("Baseline Fuel", f"{baseline.total_fuel_liters:.1f} L")
    m3.metric("Optimized Fuel", f"{optimized.total_fuel_liters:.1f} L")
    m4.metric("Fuel Saved", f"{report.fuel_saved_liters:.1f} L", delta=f"-{report.fuel_saved_pct:.1f}%")
    m5.metric("Cost Saved", f"${report.cost_saved_usd:.2f}", delta=f"-{report.fuel_saved_pct:.1f}%")
    m6.metric("CO₂ Saved", f"{report.co2_saved_kg:.1f} kg")
    m7.metric("Elev. Gain", f"+{baseline.elevation_gain_m:.0f} m")
else:
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Distance", f"{result.total_distance_km:.1f} km")
    m2.metric("Total Fuel", f"{result.total_fuel_liters:.1f} L")
    m3.metric("Efficiency", f"{result.fuel_per_100km:.1f} L/100km")
    m4.metric("Elevation Gain", f"+{result.elevation_gain_m:.0f} m")
    m5.metric("CO₂ (approx)", f"{result.total_fuel_liters * 2.68:.0f} kg")

st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

if optimized:
    from visualization.plotter import plot_comparison
    fig_compare = plot_comparison(report, show=False)
    st.subheader("Baseline vs Optimized")
    st.pyplot(fig_compare, use_container_width=True)
    plt.close(fig_compare)
    st.divider()
    st.subheader("Baseline Detail")

dist_km = result.distances_m / 1000.0
seg_dist_km = (result.distances_m[:-1] + result.distances_m[1:]) / 2000.0
speed_kmh = result.speed_profile_ms * 3.6
limit_kmh = result.speed_limits_ms * 3.6
grade_pct = result.grades * 100.0
cum_fuel = np.concatenate([[0.0], np.cumsum(result.segment_fuel_L)])

DARK_BG  = "#0e1117"
PLOT_BG  = "#1a1d23"
TEXT     = "#d0d0d0"
GRID     = "#2a2d35"

def _style(ax):
    ax.set_facecolor(PLOT_BG)
    ax.tick_params(colors=TEXT, labelsize=8)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for sp in ax.spines.values():
        sp.set_edgecolor(GRID)
    ax.grid(True, color=GRID, linewidth=0.6)
    ax.set_xlim(0, dist_km[-1])

fig = plt.figure(figsize=(13, 11), facecolor=DARK_BG)
gs = gridspec.GridSpec(4, 1, hspace=0.55)

# Elevation
ax = fig.add_subplot(gs[0])
ax.fill_between(dist_km, result.elevations_m, alpha=0.3, color="#a07040")
ax.plot(dist_km, result.elevations_m, color="#c89060", lw=1.8)
ax.set_ylabel("Elevation (m)", fontsize=9)
ax.set_title("Elevation Profile", fontsize=10)
_style(ax)
ax2t = ax.twinx()
ax2t.plot(dist_km, grade_pct, color="#e06060", lw=0.9, alpha=0.7, ls="--")
ax2t.set_ylabel("Grade (%)", color="#e06060", fontsize=8)
ax2t.tick_params(axis="y", labelcolor="#e06060", labelsize=8)
ax2t.set_facecolor(PLOT_BG)

# Speed
ax = fig.add_subplot(gs[1])
ax.plot(dist_km, limit_kmh, color="#666e82", lw=1.0, ls="--", label="Speed limit")
ax.plot(dist_km, speed_kmh, color="#4a9edd", lw=1.8, label="Baseline speed")
ax.set_ylabel("Speed (km/h)", fontsize=9)
ax.set_title("Speed Profile", fontsize=10)
ax.legend(fontsize=8, facecolor=PLOT_BG, labelcolor=TEXT, framealpha=0.8)
ax.set_ylim(bottom=0)
_style(ax)

# Power
ax = fig.add_subplot(gs[2])
ax.fill_between(seg_dist_km, result.segment_power_kw, alpha=0.4, color="#e0853a")
ax.plot(seg_dist_km, result.segment_power_kw, color="#e0853a", lw=1.2)
ax.axhline(0, color=TEXT, lw=0.4, alpha=0.3)
ax.set_ylabel("Power (kW)", fontsize=9)
ax.set_title("Engine Power Demand", fontsize=10)
_style(ax)

# Fuel
ax = fig.add_subplot(gs[3])
ax.plot(dist_km, cum_fuel, color="#4caf82", lw=2.2)
ax.fill_between(dist_km, cum_fuel, alpha=0.2, color="#4caf82")
ax.set_ylabel("Fuel (L)", fontsize=9)
ax.set_xlabel("Distance (km)", fontsize=9)
ax.set_title("Cumulative Fuel Consumed", fontsize=10)
_style(ax)

st.pyplot(fig, use_container_width=True)
plt.close(fig)

# ── Route map ─────────────────────────────────────────────────────────────────

st.divider()
st.subheader("Route Map")

# Downsample for performance — no more than 500 points on the map
step = max(1, len(result.lat) // 500)
map_df = pd.DataFrame({
    "lat": result.lat[::step],
    "lon": result.lon[::step],
})
st.map(map_df, zoom=8)
