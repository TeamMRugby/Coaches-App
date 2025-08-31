import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from math import pi
from streamlit_drawable_canvas import st_canvas
import sqlite3

# --- Club palette constants ---
KLR_RED = "#C8102E"
KLR_GOLD = "#FFCC33"
KLR_BLACK = "#000000"
KLR_WHITE = "#FFFFFF"
OPP_GREY = "#777777"
PITCH_LENGTH = 100
PITCH_WIDTH = 70

st.set_page_config(page_title="KLRUFC Coaching Hub", page_icon="🏉", layout="wide")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "club.db"
ASSETS_DIR = Path("assets")

# --- Data Layer using SQLite ---
def get_connection():
    DATA_DIR.mkdir(exist_ok=True)
    return sqlite3.connect(DB_PATH)

def initialize_db():
    with get_connection() as conn:
        c = conn.cursor()
        # Players
        c.execute('''
            CREATE TABLE IF NOT EXISTS players (
                player_id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT,
                last_name TEXT,
                status TEXT,
                injury_notes TEXT,
                shirt_number INTEGER
            )
        ''')
        # Fixtures
        c.execute('''
            CREATE TABLE IF NOT EXISTS fixtures (
                fixture_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team TEXT,
                opposition TEXT,
                venue TEXT,
                ground_address TEXT,
                date TEXT,
                kickoff TEXT,
                selected_player_ids TEXT
            )
        ''')
        # Availability
        c.execute('''
            CREATE TABLE IF NOT EXISTS availability (
                player_id INTEGER,
                available INTEGER,
                reason TEXT
            )
        ''')
        # Analysis
        c.execute('''
            CREATE TABLE IF NOT EXISTS analysis_scores (
                fixture_id INTEGER,
                player_id INTEGER,
                go_forward INTEGER,
                attitude INTEGER,
                mighty_defence INTEGER,
                energy INTEGER,
                notes TEXT
            )
        ''')
        # Tracking
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracking (
                fixture_id INTEGER,
                time_s INTEGER,
                player_id INTEGER,
                x_pct REAL,
                y_pct REAL,
                team TEXT,
                bench INTEGER
            )
        ''')
        # Events
        c.execute('''
            CREATE TABLE IF NOT EXISTS events (
                fixture_id INTEGER,
                time_s INTEGER,
                event TEXT,
                player_id INTEGER,
                notes TEXT
            )
        ''')
        conn.commit()

initialize_db()

# --- Helper Functions ---

def fetch_df(query, params=()):
    with get_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
    return df

def execute_write(query, params=()):
    with get_connection() as conn:
        conn.execute(query, params)
        conn.commit()

def df_to_sql(df, table, if_exists='replace'):
    with get_connection() as conn:
        df.to_sql(table, conn, index=False, if_exists=if_exists)

def show_player_table(df, sort_by="name"):
    st.dataframe(df.sort_values(sort_by), use_container_width=True)

@st.cache_data
def get_players():
    return fetch_df("SELECT * FROM players")

@st.cache_data
def get_fixtures():
    return fetch_df("SELECT * FROM fixtures")

@st.cache_data
def get_availability():
    return fetch_df("SELECT * FROM availability")

@st.cache_data
def get_analysis():
    return fetch_df("SELECT * FROM analysis_scores")

@st.cache_data
def get_tracking():
    return fetch_df("SELECT * FROM tracking")

@st.cache_data
def get_events():
    return fetch_df("SELECT * FROM events")

def name(row):
    return f"{row.get('first_name','')} {row.get('last_name','')}".strip()

def plot_rugby_pitch(ax, length=PITCH_LENGTH, width=PITCH_WIDTH, line=KLR_BLACK, turf=KLR_WHITE, accent=KLR_GOLD):
    # Background turf
    ax.set_facecolor(turf)
    ax.set_xlim(0, length)
    ax.set_ylim(0, width)

    # Touchlines & goal lines (black)
    ax.plot([0, length], [0, 0], lw=2.5, color=KLR_BLACK)
    ax.plot([0, length], [width, width], lw=2.5, color=KLR_BLACK)
    ax.plot([0, 0], [0, width], lw=2.5, color=KLR_BLACK)
    ax.plot([length, length], [0, width], lw=2.5, color=KLR_BLACK)

    # 22m, halfway and dashed 5/15m in gold accents
    for x in [22, 78, 50]:
        ax.plot([x, x], [0, width], lw=2, color=accent, alpha=0.9)
    for x in [5, 15, 85, 95]:
        ax.plot([x, x], [0, width], lw=1.2, ls="--", color=accent, alpha=0.7)

    # In-goal markers/posts (red squares)
    ax.scatter([0, length], [width / 2, width / 2], s=160, marker="s", color=KLR_RED, edgecolors=KLR_BLACK, linewidths=1.2)

    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_aspect('equal', adjustable='box')

# --- Sidebar/logo ---
logo_path = ASSETS_DIR / "logo.png"
st.sidebar.image(str(logo_path) if logo_path.exists() else None, caption="KLRUFC", use_column_width=True)
st.sidebar.title("KLRUFC Coaching Hub")
page = st.sidebar.radio("Navigate", [
    "Dashboard",
    "Selection & Availability",
    "Player Analysis (GAME)",
    "Video & Tracking",
    "Data Sync",
    "Settings"
])

# --- Main UI Section Routing ---
players = get_players()
fixtures = get_fixtures()
availability = get_availability()
analysis = get_analysis()
tracking = get_tracking()
events = get_events()

# --- Dashboard ---
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

# --- Selection & Availability ---
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
            show_player_table(avail_df[['player_id','shirt_number','name','available','reason']], "name")
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
            execute_write("UPDATE fixtures SET selected_player_ids=? WHERE fixture_id=?", (",".join(map(str, chosen_ids)), fixture['fixture_id']))
            st.success("Selection saved.")
            st.cache_data.clear()
            st.experimental_rerun()
        # Unavailable & Injured views
        st.subheader("Unavailable & Injured")
        status_df = players.copy()
        show_player_table(status_df[['first_name','last_name','status','injury_notes']], ["status","last_name"])

# --- Player Analysis (GAME) ---
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
        execute_write(
            "INSERT INTO analysis_scores (fixture_id, player_id, go_forward, attitude, mighty_defence, energy, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (fixture_id, player_id, gf, att, defn, eng, notes)
        )
        st.success("Saved!")
        st.cache_data.clear()
    st.subheader("Player chart (latest)")
    df = get_analysis()
    dfp = df[df['player_id']==player_id].tail(1)
    if not dfp.empty:
        labels = ["Go Forward","Attitude","Mighty Defence","Energy"]
        values = [int(dfp['go_forward']), int(dfp['attitude']), int(dfp['mighty_defence']), int(dfp['energy'])]
        angles = [n/float(len(labels)) * 2*pi for n in range(len(labels))]
        values += values[:1]
        angles += angles[:1]
        fig = plt.figure(figsize=(4,4))
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, values, linewidth=2)
        ax.fill(angles, values, alpha=0.25)
        ax.set_thetagrids([a*180/pi for a in angles[:-1]], labels)
        ax.set_ylim(0,9)
        st.pyplot(fig, use_container_width=False)

# --- Video & Tracking ---
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
                execute_write(
                    "INSERT INTO events (fixture_id, time_s, event, player_id, notes) VALUES (?, ?, ?, ?, ?)",
                    (1, t, event, pid, notes)
                )
                st.success("Event saved.")
                st.cache_data.clear()
    st.divider()
    st.subheader("Pitch view (graphical)")
    view_mode = st.radio("View", ["List","Pitch"], horizontal=True)
    if view_mode == "List":
        # Show events list and tracking snapshot table
        colL, colR = st.columns(2)
        with colL:
            st.write("**Events**")
            ev = get_events()
            if not ev.empty:
                ev = ev.merge(players[['player_id','first_name','last_name']], how='left', on='player_id')
            st.dataframe(ev, use_container_width=True, height=300)
        with colR:
            st.write("**Tracking (latest 100 pts)**")
            tr = get_tracking().tail(100)
            if not tr.empty:
                tr = tr.merge(players[['player_id','first_name','last_name','shirt_number']], on='player_id', how='left')
            st.dataframe(tr, use_container_width=True, height=300)
    else:
        # --- Timeline player controls ---
        st.subheader("Timeline Controls")
        tracking_df = get_tracking()
        t_min, t_max = 0, 0
        if not tracking_df.empty:
            t_min = int(tracking_df['time_s'].min())
            t_max = int(tracking_df['time_s'].max())
        events_df = get_events()
        if not events_df.empty:
            t_min = min(t_min, int(events_df['time_s'].min()))
            t_max = max(t_max, int(events_df['time_s'].max()))
        if "time_s" not in st.session_state: st.session_state.time_s = 0
        if "playing" not in st.session_state: st.session_state.playing = False
        if "play_speed" not in st.session_state: st.session_state.play_speed = "1x"

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
        tr = get_tracking()
        snap = tr[(tr['time_s']==time_s) & (tr['fixture_id']==1)]
        if not snap.empty:
            snap = snap.merge(players[['player_id','first_name','last_name','shirt_number']], on='player_id', how='left')
            fig2, ax2 = plt.subplots(figsize=(8,5))
            plot_rugby_pitch(ax2)
            for _, r in snap.iterrows():
                ax2.scatter(r['x_pct'], r['y_pct'], s=800, marker='o', color=KLR_RED, edgecolors=KLR_BLACK, linewidth=2, zorder=2)
                num = str(r.get('shirt_number') or "")
                label = num if num else (str(r['first_name'])[0] + str(r['last_name'])[0])
                ax2.text(r['x_pct'], r['y_pct'], label, color=KLR_WHITE, weight="bold",
                         fontsize=12, ha="center", va="center", zorder=3)
            # Overlay arrows for events near this time
            ev = get_events()
            evw = ev[(ev['fixture_id']==1) & (ev['time_s'].between(time_s-2, time_s+2))]
            if not evw.empty:
                coords = {int(r['player_id']): (float(r['x_pct']), float(r['y_pct'])) for _, r in snap.dropna(subset=['player_id']).iterrows()}
                for _, e in evw.iterrows():
                    if str(e['event']).lower() == 'pass':
                        src = int(e['player_id']) if not pd.isna(e['player_id']) else None
                        if src in coords:
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
            st.pyplot(fig2, use_container_width=True)

        canvas_res = st_canvas(
            fill_color="rgba(0, 84, 60, 0.3)",
            stroke_width=2,
            background_color="#e8f1ed",
            height=350,
            drawing_mode="circle",
            key="pitch_canvas"
        )
        colB = st.columns([1])[0]
        with colB:
            st.write("Map drawn markers to players")
            # Show events at current time window
            evw = get_events()
            _win = evw[(evw['fixture_id']==1) & (evw['time_s'].between(time_s-2, time_s+2))]
            if not _win.empty:
                _win = _win.merge(players[['player_id','first_name','last_name']], on='player_id', how='left')
                st.caption("Events near this time (±2s):")
                st.dataframe(_win, use_container_width=True, height=160)
            if canvas_res and canvas_res.json_data is not None and 'objects' in canvas_res.json_data:
                objs = canvas_res.json_data['objects']
                st.write(f"Detected markers: {len(objs)}")
                entries = []
                for i, o in enumerate(objs):
                    if all(k in o for k in ("left","top","radius")):
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
                        for e in entries:
                            chosen = mapping.get(e['idx'])
                            if chosen and chosen != "(skip)":
                                pid = int(players.loc[players.apply(name, axis=1)==chosen, 'player_id'].iloc[0])
                                execute_write(
                                    "INSERT INTO tracking (fixture_id, time_s, player_id, x_pct, y_pct, team, bench) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                    (1, time_s, pid, round(e['x_pct'],2), round(e['y_pct'],2), team_choice, int(bench_flag))
                                )
                        st.success(f"Saved {len([m for m in mapping.values() if m != '(skip)'])} tracking points.")
                        st.cache_data.clear()
            else:
                st.info("Draw a few circles on the canvas to start mapping.")

# --- Data Sync ---
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
            # User mapping/validation step could be added here.
            if st.button("Save import"):
                df_to_sql(df, mapping.lower())
                st.success(f"{mapping} imported.")
                st.cache_data.clear()
        except Exception as e:
            st.error(f"Could not read file: {e}")

# --- Settings ---
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
            execute_write('''
                INSERT OR REPLACE INTO fixtures (fixture_id, team, opposition, venue, ground_address, date, kickoff, selected_player_ids)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                1, team, opposition, venue, ground, str(date), ko.strftime("%H:%M"), ""
            ))
            st.success("Fixture saved.")
            st.cache_data.clear()
    st.subheader("Player Management")
    if not players.empty:
        editable = players.copy()
        edited = st.data_editor(editable, num_rows="dynamic", use_container_width=True)
        if st.button("Save players"):
            df_to_sql(edited, "players")
            st.success("Players saved.")
            st.cache_data.clear()
