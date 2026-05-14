"""Stable job error codes and human-readable explanations (API + UI)."""

ERROR_CODE_HELP: dict[str, str] = {
    "GEOCODE_FAILED": "Could not turn the origin or destination into map coordinates. Check spelling and use city, region format.",
    "SOLVER_FAILED": "The route optimizer could not find a feasible solution for this route or vehicle settings.",
    "ROUTE_FETCH_FAILED": "Could not download street routing data for this corridor.",
    "SIMULATION_FAILED": "The simulation stopped with an unexpected error.",
    "TRANSPORT_EXHAUSTED": "Temporary infrastructure issue — the job exceeded automatic retries.",
}


def describe_error_code(code: str | None) -> str | None:
    if not code:
        return None
    return ERROR_CODE_HELP.get(code, f"Error code: {code}")
