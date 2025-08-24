
# KLRUFC Coaching Hub — Streamlit Starter Pack

A lightweight starter app for squad selection, availability, fixtures, and GAME player analysis.

## Quickstart

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data

CSV files live in `data/`. Start by committing the generated ones, or import your own GMS/Spond exports via the app.

- `players.csv` — player_id, rfu_id, first_name, last_name, front_row_trained, suspected_concussions, status, injury_notes
- `fixtures.csv` — fixture_id, date, team, opposition, venue, ground_address, kickoff, selected_player_ids
- `availability.csv` — fixture_id, player_id, available, reason
- `analysis_scores.csv` — fixture_id, player_id, go_forward, attitude, mighty_defence, energy, notes

## Branding

Edit `.streamlit/config.toml` to set club colours and add `assets/logo.png` for your crest.

## Auth (10 users)

For a small group, add [streamlit-authenticator](https://streamlit-authenticator.readthedocs.io/) or use Streamlit's OIDC (Microsoft Entra) if you prefer SSO.

## Integrations

- **RFU GMS**: No public API; use Reports → Export to Excel/CSV and import here.
- **Spond**: No open API; you can export CSV or (optionally) use the *unofficial* `spond` Python package if you accept the risks.


## Video + Tracking

- Paste a **Veo** share link or upload MP4s right in **Video & Tracking**.
- Tag timeline events (carry, tackle, offload, etc.) and save to `data/events.csv`.
- Use the **Pitch view** canvas to drop markers and map to players; positions save to `data/tracking.csv` (x/y as pitch percentages).

> Veo supports sharing recordings via link. Some links require login to view/embeds — use a public share link for in-app playback. There is no general open analytics export for rugby at present; use this pack's tagging/tracking to build your own analysis tables.

### Data files
- `tracking.csv` — fixture_id, time_s, player_id, x_pct, y_pct, team
- `events.csv` — fixture_id, time_s, event, player_id, notes


### Visual overlays
- **KLR players:** red fill (#C8102E), black outline, gold numbers (#FFCC33)
- **Bench:** white fill, gold outline (no fill highlight)
- **Opposition:** grey fill (#777777), black outline, white numbers
- **Arrows:** passes (black), linebreaks (gold) for events within ±2s of selected time


### Timeline player
- Use the slider scrubber to jump through seconds of saved tracking.
- Enable **Play / Auto-step** to auto-advance with a short delay (0.5s per step).
- Adjust **step size** for faster or slower playback.
