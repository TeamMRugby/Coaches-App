"""
RFU GMS importer (starter stub).

The RFU GMS currently exposes exports via the Reports module; there is no public API.
Use: Help Centre → Reports → Run Export (Excel), then import here.
"""
import pandas as pd
from pathlib import Path

def parse_players_from_gms_export(path: Path) -> pd.DataFrame:
    """
    Accept a GMS Excel/CSV export and map to the starter schema:
    player_id (generated), rfu_id, first_name, last_name, front_row_trained, suspected_concussions, status, injury_notes
    """
    df = pd.read_excel(path) if str(path).lower().endswith(".xlsx") else pd.read_csv(path)
    cols = {c.lower(): c for c in df.columns}
    out = pd.DataFrame()
    out["rfu_id"] = df[cols.get("rfu id")] if cols.get("rfu id") in df.columns else None
    out["first_name"] = df[cols.get("first name")] if cols.get("first name") in df.columns else None
    out["last_name"] = df[cols.get("last name")] if cols.get("last name") in df.columns else None
    out["front_row_trained"] = df[cols.get("front row trained")] if cols.get("front row trained") in df.columns else "No"
    out["suspected_concussions"] = df[cols.get("suspected concussions")] if cols.get("suspected concussions") in df.columns else 0
    out["status"] = "available"
    out["injury_notes"] = ""
    out.insert(0,"player_id", range(1, len(out)+1))
    return out
