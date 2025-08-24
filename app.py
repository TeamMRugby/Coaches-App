
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from math import pi
from streamlit_drawable_canvas import st_canvas

# --- Club palette constants ---
KLR_RED = "#C8102E"
KLR_GOLD = "#FFCC33"
KLR_BLACK = "#000000"
KLR_WHITE = "#FFFFFF"
OPP_GREY = "#777777"

st.set_page_config(page_title="KLRUFC Coaching Hub", page_icon="🏉", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
PLAYERS_CSV = DATA_DIR / "players.csv"
FIXTURES_CSV = DATA_DIR / "fixtures.csv"
AVAIL_CSV = DATA_DIR / "availability.csv"
ANALYSIS_CSV = DATA_DIR / "analysis_scores.csv"
TRACKING_CSV = DATA_DIR / "tracking.csv"
EVENTS_CSV = DATA_DIR / "events.csv"

def load_csv(path, dtype=None):
    if path.exists():
        return pd.read_csv(path, dtype=dtype)
    else:
        return pd.DataFrame()

@st.cache_data
def load_all():
    return (
        load_csv(PLAYERS_CSV),
        load_csv(FIXTURES_CSV),
        load_csv(AVAIL_CSV),
        load_csv(ANALYSIS_CSV),
        load_csv(TRACKING_CSV),
        load_csv(EVENTS_CSV)
    )

players, fixtures, availability, analysis, tracking, events = load_all()

st.sidebar.image(str(Path("assets/logo.png")) if Path("assets/logo.png").exists() else None, caption="KLRUFC", use_column_width=True)
st.sidebar.title("KLRUFC Coaching Hub")
page = st.sidebar.radio("Navigate", ["Dashboard","Selection & Availability","Player Analysis (GAME)","Video & Tracking","Data Sync","Settings"])

def name(row):
    return f"{row.get('first_name','')} {row.get('last_name','')}".strip()



def plot_rugby_pitch(ax, length=100, width=70, line="#000000", turf="#FFFFFF", accent="#FFCC33"):
    # Club palette
    RED = KLR_RED
    BLACK = KLR_BLACK
    GOLD = KLR_GOLD
    GREEN = "#0B5D42"  # optional accent if needed

    # Background turf
    ax.set_facecolor(turf)
    ax.set_xlim(0,100); ax.set_ylim(0,70)

    # Touchlines & goal lines (black)
    ax.plot([0,100],[0,0], lw=2.5, color=BLACK)
    ax.plot([0,100],[70,70], lw=2.5, color=BLACK)
    ax.plot([0,0],[0,70], lw=2.5, color=BLACK)
    ax.plot([100,100],[0,70], lw=2.5, color=BLACK)

    # 22m, halfway and dashed 5/15m in gold accents
    for x in [22, 78, 50]:
        ax.plot([x,x],[0,70], lw=2, color=GOLD, alpha=0.9)
    for x in [5,15,85,95]:
        ax.plot([x,x],[0,70], lw=1.2, ls="--", color=GOLD, alpha=0.7)

    # In-goal markers/posts (red squares)
    ax.scatter([0,100],[35,35], s=160, marker="s", color=RED, edgecolors=BLACK, linewidths=1.2)

    ax.set_xticks([]); ax.set_yticks([])
    ax.set_aspect('equal', adjustable='box')


if page == "Dashboard":
    st.header("🏉 KLRUFC Coaching Hub")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Players", len(players))
    col2.metric("Fixtures", len(fixtures))
    col3.metric("Available (next)", int(availability['available'].sum()) if not availability.empty else 0)
    selected_count = 0
    if not fixtures.empty and 'selected_player_ids' in fixtures.columns:
        try:
            selected_ids = [int(x) for x in str(fixtures.iloc[0]['selected_player_ids']).split(',') if str(x).strip().isdigit()]
            selected_count = len(selected_ids)
        except Exception:
            selected_count = 0
    col4.metric("Selected (next)", selected_count)
    st.write("Use the sidebar to manage selection, availability, GAME analysis, and video & tracking.")

elif page == "Selection & Availability":
    st.header("✅ Selection & Availability")
    if fixtures.empty:
        st.info("No fixtures yet. Add one in Settings → Fixtures.")
    else:
        fixture = fixtures.iloc[0]
        st.subheader(f"{fixture['team']} vs {fixture['opposition']} — {fixture['venue']} — {fixture['date']} {fixture['kickoff']}")
        # Availability editor
        if availability.empty:
            st.warning("No availability data yet.")
        else:
            avail_df = availability.merge(players[['player_id','first_name','last_name','status','injury_notes','shirt_number']], on='player_id', how='left')
            avail_df['name'] = avail_df.apply(name, axis=1)
            st.dataframe(avail_df[['player_id','shirt_number','name','available','reason']].sort_values('name'), use_container_width=True)
        # Selection list editor
        st.subheader("Selected Squad")
        current_sel = []
        if 'selected_player_ids' in fixture and isinstance(fixture['selected_player_ids'], str):
            current_sel = [int(x) for x in str(fixture['selected_player_ids']).split(',') if str(x).strip().isdigit()]
        options = players.assign(name=players.apply(name,axis=1)).sort_values('last_name')
        chosen = st.multiselect("Pick players", options=options['name'].tolist(),
                                default=[options.loc[options['player_id'].isin(current_sel),'name']].pop() if len(current_sel) else [])
        chosen_ids = options.loc[options['name'].isin(chosen),'player_id'].tolist()
        if st.button("Save selection"):
            fixtures.at[0,'selected_player_ids'] = ",".join([str(i) for i in chosen_ids])
            fixtures.to_csv(FIXTURES_CSV, index=False)
            st.success("Selection saved.")
            st.experimental_rerun()
        # Unavailable & Injured views
        st.subheader("Unavailable & Injured")
        status_df = players.copy()
        st.dataframe(status_df[['first_name','last_name','status','injury_notes']].sort_values(['status','last_name']), use_container_width=True)

elif page == "Player Analysis (GAME)":
    st.header("📊 GAME Analysis (1–9)")
    st.markdown("""
- **Go Forward**: with purpose; go for space; min 3 support points; offload each phase.
- **Attitude**: Positive and never give up.
- **Mighty Defence**: dominant, patient, focused on winning the ball back.
- **Energy**: pace, ferocity, aggression, calm under pressure.
""")
    if players.empty: st.stop()
    player = st.selectbox("Player", players.apply(name, axis=1))
    player_id = int(players.loc[players.apply(name, axis=1)==player, 'player_id'].iloc[0])
    fixture_id = st.number_input("Fixture ID", value=1, min_value=1, step=1)
    cols = st.columns(4)
    gf = cols[0].slider("Go Forward", 1, 9, 5)
    att = cols[1].slider("Attitude", 1, 9, 5)
    defn = cols[2].slider("Mighty Defence", 1, 9, 5)
    eng = cols[3].slider("Energy", 1, 9, 5)
    notes = st.text_input("Notes (optional)")
    if st.button("Save rating"):
        new = pd.DataFrame([{
            "fixture_id": fixture_id,
            "player_id": player_id,
            "go_forward": gf,
            "attitude": att,
            "mighty_defence": defn,
            "energy": eng,
            "notes": notes
        }])
        old = pd.read_csv(ANALYSIS_CSV) if ANALYSIS_CSV.exists() else pd.DataFrame()
        combined = pd.concat([old, new], ignore_index=True)
        combined.to_csv(ANALYSIS_CSV, index=False)
        st.success("Saved!")
    st.subheader("Player chart (latest)")
    if ANALYSIS_CSV.exists():
        df = pd.read_csv(ANALYSIS_CSV)
        dfp = df[df['player_id']==player_id].tail(1)
        if not dfp.empty:
            labels = ["Go Forward","Attitude","Mighty Defence","Energy"]
            values = [int(dfp['go_forward']), int(dfp['attitude']), int(dfp['mighty_defence']), int(dfp['energy'])]
            angles = [n/float(len(labels)) * 2*3.14159 for n in range(len(labels))]
            values += values[:1]
            angles += angles[:1]
            fig = plt.figure(figsize=(4,4))
            ax = plt.subplot(111, polar=True)
            ax.plot(angles, values, linewidth=2)
            ax.fill(angles, values, alpha=0.25)
            ax.set_thetagrids([a*180/3.14159 for a in angles[:-1]], labels)
            ax.set_ylim(0,9)
            st.pyplot(fig, use_container_width=False)

elif page == "Video & Tracking":
    st.header("🎥 Video & Player Tracking")
    c1, c2 = st.columns([2,1])
    with c1:
        st.subheader("Video")
        video_url = st.text_input("Paste a Veo share link or any video URL (mp4, YouTube, etc.)")
        up = st.file_uploader("...or upload a local MP4", type=["mp4","mov","m4v","webm"])
        if video_url:
            st.video(video_url)
        elif up:
            st.video(up)
        st.caption("Tip: Veo supports sharing via public link. If a link requires login, embed may not play in-app.")
    with c2:
        st.subheader("Event tagging")
        if players.empty:
            st.info("Add players first.")
        else:
            player = st.selectbox("Player", ["(team)"] + players.apply(name, axis=1).tolist())
            event = st.selectbox("Event", ["Carry","Tackle","Ruck Clean","Jackal","Offload","Linebreak","Kick","Pass","Turnover Won","Try","Penalty Won"])
            t = st.number_input("Time (seconds)", min_value=0, value=0, step=1)
            notes = st.text_input("Notes", "")
            if st.button("Save event"):
                pid = None if player=="(team)" else int(players.loc[players.apply(name, axis=1)==player, 'player_id'].iloc[0])
                row = pd.DataFrame([{"fixture_id": 1, "time_s": t, "event": event, "player_id": pid, "notes": notes}])
                old = pd.read_csv(EVENTS_CSV) if EVENTS_CSV.exists() else pd.DataFrame()
                pd.concat([old,row], ignore_index=True).to_csv(EVENTS_CSV, index=False)
                st.success("Event saved.")
    st.divider()
    st.subheader("Pitch view (graphical)")
    view_mode = st.radio("View", ["List","Pitch"], horizontal=True)
    if view_mode == "List":
        # Show events list and tracking snapshot table
        colL, colR = st.columns(2)
        with colL:
            st.write("**Events**")
            ev = load_csv(EVENTS_CSV)
            if not ev.empty:
                ev = ev.merge(players[['player_id','first_name','last_name']], how='left', on='player_id')
            st.dataframe(ev, use_container_width=True, height=300)
        with colR:
            st.write("**Tracking (latest 100 pts)**")
            tr = load_csv(TRACKING_CSV).tail(100)
            if not tr.empty:
                tr = tr.merge(players[['player_id','first_name','last_name','shirt_number']], on='player_id', how='left')
            st.dataframe(tr, use_container_width=True, height=300)
    
else:
        # --- Timeline player controls ---
        st.subheader("Timeline Controls")
        max_time = int(tracking['time_s'].max()) if not tracking.empty else 120
        current_t = st.slider("Time scrubber (s)", 0, max_time, 0, 1)
        play = st.checkbox("Play / Auto-step", value=False)
        step = st.number_input("Step size (s)", 1, 10, 1)
        if play:
            import time as _time
            for t in range(current_t, max_time+1, step):
                st.experimental_set_query_params(time=t)
                _time.sleep(0.5)
        time_s = current_t

        colA, colB = st.columns([3,2])

        with colA:
            st.write("Draw or click to place players on the pitch at a given time.")
            
# --- Timeline controls ---
if "time_s" not in st.session_state: st.session_state.time_s = 0
if "playing" not in st.session_state: st.session_state.playing = False
if "play_speed" not in st.session_state: st.session_state.play_speed = 1.0

# Determine timeline bounds from tracking/events
t_min, t_max = 0, 0
if TRACKING_CSV.exists():
    _tr_all = pd.read_csv(TRACKING_CSV)
    if not _tr_all.empty:
        t_min = int(_tr_all['time_s'].min())
        t_max = int(_tr_all['time_s'].max())
if EVENTS_CSV.exists():
    _ev_all = pd.read_csv(EVENTS_CSV)
    if not _ev_all.empty:
        t_min = min(t_min, int(_ev_all['time_s'].min()))
        t_max = max(t_max, int(_ev_all['time_s'].max()))

c_ctrl1, c_ctrl2, c_ctrl3, c_ctrl4, c_ctrl5 = st.columns([1,1,1,2,6])
with c_ctrl1:
    if st.button("⏮️ -1s"):
        st.session_state.time_s = max(t_min, st.session_state.time_s - 1)
with c_ctrl2:
    if st.button("⏭️ +1s"):
        st.session_state.time_s = min(t_max, st.session_state.time_s + 1)
with c_ctrl3:
    if st.session_state.playing:
        if st.button("⏸️ Pause"):
            st.session_state.playing = False
    else:
        if st.button("▶️ Play"):
            st.session_state.playing = True
with c_ctrl4:
    st.session_state.play_speed = st.selectbox("Speed", ["0.5x","1x","2x"], index=1, label_visibility="collapsed")
with c_ctrl5:
    st.session_state.time_s = st.slider("Time (s)", min_value=int(t_min), max_value=int(max(t_max, t_min+1)), value=int(st.session_state.time_s), step=1)

# Auto-advance while playing
if st.session_state.playing:
    import time
    speed = {"0.5x":2.0,"1x":1.0,"2x":0.5}[st.session_state.play_speed]
    time.sleep(0.4 * speed)
    st.session_state.time_s = int(min(t_max, st.session_state.time_s + 1))
    st.experimental_rerun()

time_s = int(st.session_state.time_s)

            fig, ax = plt.subplots(figsize=(8,5))
            plot_rugby_pitch(ax)
            st.pyplot(fig, use_container_width=True)
            st.caption("Below: use the canvas to drop circles at player locations, then map them to names and save to tracking.")
            # Overlay saved positions at this time
            if TRACKING_CSV.exists():
                tr = pd.read_csv(TRACKING_CSV)
                snap = tr[(tr['time_s']==time_s) & (tr['fixture_id']==1)]
                if not snap.empty:
                    snap = snap.merge(players[['player_id','first_name','last_name','shirt_number']], on='player_id', how='left')
                    fig2, ax2 = plt.subplots(figsize=(8,5))
                    plot_rugby_pitch(ax2)
                    
                    for _, r in snap.iterrows():
                        ax2.scatter(r['x_pct'], r['y_pct'], s=800, marker='o', color="#C8102E", edgecolors="#000000", linewidth=2, zorder=2)
                        num = str(r.get('shirt_number') or "")
                        label = num if num else (str(r['first_name'])[0] + str(r['last_name'])[0])
                        ax2.text(r['x_pct'], r['y_pct'], label, color="#FFFFFF", weight="bold",
                                 fontsize=12, ha="center", va="center", zorder=3)

                                        # Overlay arrows for events near this time
                    if EVENTS_CSV.exists():
                        try:
                            ev = pd.read_csv(EVENTS_CSV)
                            # consider events within +/- 2s of selected time
                            evw = ev[(ev['fixture_id']==1) & (ev['time_s'].between(time_s-2, time_s+2))]
                            if not evw.empty:
                                # Need coordinates for involved players from 'snap'
                                coords = {int(r['player_id']): (float(r['x_pct']), float(r['y_pct'])) for _, r in snap.dropna(subset=['player_id']).iterrows()}
                                for _, e in evw.iterrows():
                                    if str(e['event']).lower() == 'pass':
                                        # Find a 'target' by next row with same time (very simple heuristic)
                                        # or nearest teammate in snapshot
                                        src = int(e['player_id']) if not pd.isna(e['player_id']) else None
                                        if src in coords:
                                            # nearest other point
                                            sx, sy = coords[src]
                                            tx, ty, bestd = None, None, 1e9
                                            for pid,(x,y) in coords.items():
                                                if pid == src: continue
                                                d = (x-sx)**2 + (y-sy)**2
                                                if d < bestd:
                                                    bestd, (tx,ty) = d, (x,y)
                                            if tx is not None:
                                                ax2.arrow(sx, sy, tx-sx, ty-sy, width=0.1, head_width=2.5, head_length=2.5, length_includes_head=True, color=KLR_BLACK, alpha=0.8, zorder=2)
                                    elif str(e['event']).lower() == 'linebreak':
                                        src = int(e['player_id']) if not pd.isna(e['player_id']) else None
                                        if src in coords:
                                            sx, sy = coords[src]
                                            ax2.arrow(sx, sy, 8, 0, width=0.1, head_width=2.5, head_length=2.5, length_includes_head=True, color=KLR_GOLD, alpha=0.9, zorder=2)
                        except Exception as _:
                            pass
                    st.pyplot(fig2, use_container_width=True)

            canvas_res = st_canvas(
                fill_color="rgba(0, 84, 60, 0.3)",
                stroke_width=2,
                background_color="#e8f1ed",
                height=350,
                drawing_mode="circle",
                key="pitch_canvas"
            )
        with colB:
            st.write("Map drawn markers to players")
            # Show events at current time window
            if EVENTS_CSV.exists():
                _evw = pd.read_csv(EVENTS_CSV)
                _win = _evw[(_evw['fixture_id']==1) & (_evw['time_s'].between(time_s-2, time_s+2))]
                if not _win.empty:
                    _win = _win.merge(players[['player_id','first_name','last_name']], on='player_id', how='left')
                    st.caption("Events near this time (±2s):")
                    st.dataframe(_win, use_container_width=True, height=160)
            if canvas_res and canvas_res.json_data is not None and 'objects' in canvas_res.json_data:
                objs = canvas_res.json_data['objects']
                st.write(f"Detected markers: {len(objs)}")
                # Convert canvas coords to pitch percents (approx by canvas size)
                entries = []
                for i, o in enumerate(objs):
                    if all(k in o for k in ("left","top","radius")):
                        # canvas size ~ width=700, height=350 by default; normalize:
                        x_pct = min(max((o['left']) / 700 * 100, 0), 100)
                        y_pct = min(max((o['top']) / 350 * 70, 0), 70)
                        entries.append({"idx": i, "x_pct": x_pct, "y_pct": y_pct})
                if entries:
                    mapping = {}
                    names = players.assign(name=players.apply(name, axis=1))['name'].tolist()
                    team_choice = st.selectbox("Team for these markers", ["KLR","OPP"], index=0)
                    bench_flag = st.checkbox("Mark as bench (outline only)", value=False)
                    for e in entries:
                        mapping[e['idx']] = st.selectbox(f"Marker {e['idx']+1}", ["(skip)"]+names, key=f"map_{e['idx']}")
                    if st.button("Save tracking points"):
                        rows = []
                        for e in entries:
                            chosen = mapping.get(e['idx'])
                            if chosen and chosen != "(skip)":
                                pid = int(players.loc[players.apply(name, axis=1)==chosen, 'player_id'].iloc[0])
                                rows.append({"fixture_id": 1, "time_s": time_s, "player_id": pid, "x_pct": round(e['x_pct'],2), "y_pct": round(e['y_pct'],2), "team": team_choice, "bench": bench_flag})
                        if rows:
                            old = pd.read_csv(TRACKING_CSV) if TRACKING_CSV.exists() else pd.DataFrame()
                            pd.concat([old, pd.DataFrame(rows)], ignore_index=True).to_csv(TRACKING_CSV, index=False)
                            st.success(f"Saved {len(rows)} tracking points.")
            else:
                st.info("Draw a few circles on the canvas to start mapping.")

elif page == "Data Sync":
    st.header("🔄 Data Sync")
    st.write("Import latest exports from RFU GMS or Spond (CSV/XLSX). For Veo, paste share links on the Video page.")
    up = st.file_uploader("Upload a CSV or Excel export", type=["csv","xlsx"])
    mapping = st.selectbox("Import Type", ["Players","Availability","Fixtures","Tracking","Events"])
    if st.button("Import") and up:
        try:
            if up.name.endswith(".csv"):
                df = pd.read_csv(up)
            else:
                df = pd.read_excel(up)
            st.dataframe(df.head())
            st.info("Map your columns to the starter pack schema then save.")
        except Exception as e:
            st.error(f"Could not read file: {e}")

elif page == "Settings":
    st.header("⚙️ Settings")
    st.subheader("Fixture")
    with st.form("fixture_form"):
        team = st.text_input("Team", "KLRUFC U17 Colts")
        opposition = st.text_input("Opposition", "TBC")
        venue = st.selectbox("Venue", ["Home","Away","Neutral"], index=0)
        ground = st.text_input("Ground address", "Underley Park, Kirkby Lonsdale")
        date = st.date_input("Date")
        ko = st.time_input("Kickoff")
        submitted = st.form_submit_button("Save fixture")
        if submitted:
            fixtures_new = pd.DataFrame([{
                "fixture_id": 1, "team": team, "opposition": opposition, "venue": venue,
                "ground_address": ground, "date": str(date), "kickoff": ko.strftime("%H:%M"),
                "selected_player_ids": ""
            }])
            fixtures_new.to_csv(FIXTURES_CSV, index=False)
            st.success("Fixture saved.")
    st.subheader("Player Management")
    if not players.empty:
        editable = players.copy()
        edited = st.data_editor(editable, num_rows="dynamic", use_container_width=True)
        if st.button("Save players"):
            edited.to_csv(PLAYERS_CSV, index=False)
            st.success("Players saved.")
