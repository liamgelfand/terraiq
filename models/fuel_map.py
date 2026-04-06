"""
BSFCMap: Brake Specific Fuel Consumption lookup table.

Wraps a 2D grid of (RPM, load) -> BSFC values (g/kWh) and provides
bilinear interpolation for arbitrary operating points.

BSFC maps are vehicle-specific and stored in each vehicle profile.
This module provides the interpolation engine only — it knows nothing
about which vehicle it belongs to.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import RegularGridInterpolator


class BSFCMap:
    """
    2D BSFC lookup table with bilinear interpolation.

    Args:
        rpm_points: 1D array of RPM values (must be monotonically increasing)
        load_points: 1D array of load fractions 0.0–1.0 (monotonically increasing)
        bsfc_data: 2D array shaped (len(rpm_points), len(load_points))
                   Values in g/kWh

    Usage:
        bsfc_map = BSFCMap(rpm_points, load_points, bsfc_data)
        fuel_rate_g_per_kwh = bsfc_map.lookup(rpm=1200, load=0.75)
    """

    def __init__(
        self,
        rpm_points: np.ndarray,
        load_points: np.ndarray,
        bsfc_data: np.ndarray,
    ):
        self.rpm_points = np.asarray(rpm_points, dtype=float)
        self.load_points = np.asarray(load_points, dtype=float)
        self.bsfc_data = np.asarray(bsfc_data, dtype=float)

        if self.bsfc_data.shape != (len(self.rpm_points), len(self.load_points)):
            raise ValueError(
                f"bsfc_data shape {self.bsfc_data.shape} must be "
                f"({len(self.rpm_points)}, {len(self.load_points)})"
            )

        self._interpolator = RegularGridInterpolator(
            (self.rpm_points, self.load_points),
            self.bsfc_data,
            method="linear",
            bounds_error=False,
            fill_value=None,  # extrapolate at edges rather than returning NaN
        )

    def lookup(self, rpm: float, load: float) -> float:
        """
        Return BSFC in g/kWh for a given engine operating point.

        Args:
            rpm: engine speed in RPM
            load: engine load as fraction of peak torque (0.0–1.0)

        Returns:
            BSFC in g/kWh (grams of fuel per kilowatt-hour of output)
        """
        rpm_clamped = np.clip(rpm, self.rpm_points[0], self.rpm_points[-1])
        load_clamped = np.clip(load, 0.0, 1.0)
        return float(self._interpolator([[rpm_clamped, load_clamped]])[0])

    def lookup_array(self, rpm: np.ndarray, load: np.ndarray) -> np.ndarray:
        """Vectorized version of lookup for arrays of operating points."""
        rpm_clamped = np.clip(rpm, self.rpm_points[0], self.rpm_points[-1])
        load_clamped = np.clip(load, 0.0, 1.0)
        points = np.column_stack([rpm_clamped.ravel(), load_clamped.ravel()])
        return self._interpolator(points).reshape(rpm.shape)

    @property
    def min_bsfc(self) -> float:
        """Minimum BSFC on the map — the engine's most efficient operating point."""
        return float(np.min(self.bsfc_data))

    @property
    def sweet_spot(self) -> tuple[float, float]:
        """(RPM, load) at the minimum BSFC point."""
        idx = np.unravel_index(np.argmin(self.bsfc_data), self.bsfc_data.shape)
        return float(self.rpm_points[idx[0]]), float(self.load_points[idx[1]])
