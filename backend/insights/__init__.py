"""Per-insight analysis modules.

Each module exposes one or two pure functions that take a player-view
DataFrame (from `build_player_view`) plus optional move-level errors data,
and return a DataFrame ready to render in the dashboard or write to CSV.
"""
