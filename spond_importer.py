"""
Spond importer (starter stub).

Spond does not currently offer an open API. You can export CSV or (optionally) use the unofficial 'spond' Python package.
"""
import pandas as pd
from pathlib import Path

def parse_players_from_spond_csv(path: Path) -> pd.DataFrame:
    """
    Accept a CSV export from Spond and map to players schema.
    """
    df = pd.read_csv(path)
    out = pd.DataFrame()
    # Try to infer common columns
    first = next((c for c in df.columns if c.lower() in ("first name","first_name","firstname","given name")), None)
    last = next((c for c in df.columns if c.lower() in ("last name","last_name","lastname","surname","family name")), None)
    out["first_name"] = df[first] if first else ""
    out["last_name"] = df[last] if last else ""
    out["rfu_id"] = None
    out["front_row_trained"] = "No"
    out["suspected_concussions"] = 0
    out["status"] = "available"
    out["injury_notes"] = ""
    out.insert(0,"player_id", range(1, len(out)+1))
    return out
