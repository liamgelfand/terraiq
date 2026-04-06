"""
Plotter: visualization of route, speed profiles, and fuel consumption.

Two modes:
- plot_baseline(result)     — single run: elevation, speed, power, fuel
- plot_comparison(report)   — side-by-side baseline vs optimized

All plots use matplotlib for static output and can optionally export to PNG.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

from simulation.runner import SimulationResult
from simulation.evaluator import EvaluationReport


def plot_baseline(
    result: SimulationResult,
    save_path: str | Path | None = None,
    show: bool = True,
) -> plt.Figure:
    """
    Four-panel plot for a single baseline simulation run:
      1. Elevation profile
      2. Speed profile vs speed limits
      3. Engine power demand
      4. Cumulative fuel consumed

    Args:
        result: SimulationResult from SimulationRunner.run()
        save_path: if provided, save figure to this path (PNG)
        show: if True, call plt.show()

    Returns:
        matplotlib Figure object
    """
    dist_km = result.distances_m / 1000.0
    seg_dist_km = (result.distances_m[:-1] + result.distances_m[1:]) / 2000.0
    speed_kmh = result.speed_profile_ms * 3.6
    limit_kmh = result.speed_limits_ms * 3.6
    grade_pct = result.grades * 100.0
    cumulative_fuel = np.concatenate([[0.0], np.cumsum(result.segment_fuel_L)])

    fig = plt.figure(figsize=(14, 10))
    fig.suptitle(
        f"{result.route_name}  |  {result.vehicle_name}\n"
        f"{result.total_distance_km:.1f} km  |  "
        f"{result.total_fuel_liters:.1f} L  |  "
        f"{result.fuel_per_100km:.1f} L/100km",
        fontsize=13,
        fontweight="bold",
    )
    gs = gridspec.GridSpec(4, 1, hspace=0.45)

    # Panel 1: Elevation + grade shading
    ax1 = fig.add_subplot(gs[0])
    ax1.fill_between(dist_km, result.elevations_m, alpha=0.3, color="saddlebrown")
    ax1.plot(dist_km, result.elevations_m, color="saddlebrown", linewidth=1.5)
    ax1.set_ylabel("Elevation (m)")
    ax1.set_title("Elevation Profile")
    ax1_twin = ax1.twinx()
    ax1_twin.plot(dist_km, grade_pct, color="firebrick", linewidth=0.8, alpha=0.6, linestyle="--")
    ax1_twin.set_ylabel("Grade (%)", color="firebrick")
    ax1_twin.tick_params(axis="y", labelcolor="firebrick")
    ax1_twin.axhline(0, color="firebrick", linewidth=0.4, alpha=0.4)

    # Panel 2: Speed profile vs limit
    ax2 = fig.add_subplot(gs[1])
    ax2.plot(dist_km, limit_kmh, color="gray", linewidth=1.0, linestyle="--", label="Speed limit")
    ax2.plot(dist_km, speed_kmh, color="steelblue", linewidth=1.5, label="Baseline speed")
    ax2.set_ylabel("Speed (km/h)")
    ax2.set_title("Speed Profile")
    ax2.legend(loc="upper right", fontsize=9)
    ax2.set_ylim(bottom=0)

    # Panel 3: Engine power demand
    ax3 = fig.add_subplot(gs[2])
    ax3.fill_between(seg_dist_km, result.segment_power_kw, alpha=0.4, color="darkorange")
    ax3.plot(seg_dist_km, result.segment_power_kw, color="darkorange", linewidth=1.2)
    ax3.axhline(0, color="black", linewidth=0.5)
    ax3.set_ylabel("Power (kW)")
    ax3.set_title("Engine Power Demand")

    # Panel 4: Cumulative fuel
    ax4 = fig.add_subplot(gs[3])
    ax4.plot(dist_km, cumulative_fuel, color="green", linewidth=2.0)
    ax4.fill_between(dist_km, cumulative_fuel, alpha=0.2, color="green")
    ax4.set_ylabel("Fuel (L)")
    ax4.set_xlabel("Distance (km)")
    ax4.set_title("Cumulative Fuel Consumed")

    for ax in [ax1, ax2, ax3, ax4]:
        ax.set_xlim(0, dist_km[-1])
        ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig


def plot_comparison(
    report: EvaluationReport,
    save_path: str | Path | None = None,
    show: bool = True,
) -> plt.Figure:
    """
    Three-panel comparison plot: baseline vs optimized.
      1. Elevation profile (shared)
      2. Speed profiles overlaid
      3. Cumulative fuel: baseline vs optimized

    Args:
        report: EvaluationReport from evaluator
        save_path: optional PNG export path
        show: if True, call plt.show()

    Returns:
        matplotlib Figure object
    """
    b = report.baseline
    o = report.optimized

    dist_km = b.distances_m / 1000.0
    cum_fuel_base = np.concatenate([[0.0], np.cumsum(b.segment_fuel_L)])
    cum_fuel_opt = np.concatenate([[0.0], np.cumsum(o.segment_fuel_L)])

    fig, axes = plt.subplots(3, 1, figsize=(14, 9), gridspec_kw={"hspace": 0.45})

    fig.suptitle(
        f"{b.route_name}  —  Baseline vs Optimized\n"
        f"Fuel saved: {report.fuel_saved_liters:.1f} L  ({report.fuel_saved_pct:.1f}%)  |  "
        f"CO₂ saved: {report.co2_saved_kg:.1f} kg",
        fontsize=13,
        fontweight="bold",
    )

    # Panel 1: Elevation
    ax = axes[0]
    ax.fill_between(dist_km, b.elevations_m, alpha=0.25, color="saddlebrown")
    ax.plot(dist_km, b.elevations_m, color="saddlebrown", linewidth=1.5)
    ax.set_ylabel("Elevation (m)")
    ax.set_title("Elevation Profile")

    # Panel 2: Speed profiles
    ax = axes[1]
    ax.plot(dist_km, b.speed_limits_ms * 3.6, color="gray", linewidth=1.0,
            linestyle="--", label="Speed limit")
    ax.plot(dist_km, b.speed_profile_ms * 3.6, color="steelblue", linewidth=1.5,
            label="Baseline", alpha=0.8)
    ax.plot(dist_km, o.speed_profile_ms * 3.6, color="darkorange", linewidth=1.5,
            label="Optimized", alpha=0.8)
    ax.set_ylabel("Speed (km/h)")
    ax.set_title("Speed Profiles")
    ax.legend(loc="upper right", fontsize=9)
    ax.set_ylim(bottom=0)

    # Panel 3: Cumulative fuel
    ax = axes[2]
    ax.plot(dist_km, cum_fuel_base, color="steelblue", linewidth=2.0,
            label=f"Baseline ({b.total_fuel_liters:.1f} L)")
    ax.plot(dist_km, cum_fuel_opt, color="darkorange", linewidth=2.0,
            label=f"Optimized ({o.total_fuel_liters:.1f} L)")
    ax.fill_between(dist_km, cum_fuel_base, cum_fuel_opt,
                    alpha=0.15, color="green", label=f"Saved ({report.fuel_saved_liters:.1f} L)")
    ax.set_ylabel("Fuel (L)")
    ax.set_xlabel("Distance (km)")
    ax.set_title("Cumulative Fuel")
    ax.legend(loc="upper left", fontsize=9)

    for ax in axes:
        ax.set_xlim(0, dist_km[-1])
        ax.grid(True, alpha=0.3)

    if save_path:
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"Saved plot to {save_path}")

    if show:
        plt.show()

    return fig
