import random
import numpy as np
import streamlit as st
import pandas as pd
from io import BytesIO

# --- App Config ---

st.set_page_config(page_title="Dream11 Team Generator", layout="wide")

# --- Footer ---

st.markdown(
    """ <style>
    .footer { position: fixed; bottom: 10px; left: 20px; font-size: 14px; color: #888;
    background-color: rgba(255,255,255,0.85); padding: 8px 14px; border-radius: 12px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    animation: fadeIn 2s ease-in; display: flex; align-items: center; gap: 10px;
    }
    .footer img { width: 20px; height: 20px; animation: pulse 2s infinite; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity:1; transform:translateY(0); } }
    @keyframes pulse { 0%,100% { transform:scale(1); } 50% { transform:scale(1.2); } } </style> <div class="footer"> <img src="https://img.icons8.com/color/48/controller.png" alt="dev-logo"/> <span>Created by <b>Nilesh Patil</b></span> </div>
    """, unsafe_allow_html=True)

# --- Title ---

st.markdown(
    "<h1 style='text-align:center;'>🏏 Dream11 Team Generator</h1>",
    unsafe_allow_html=True
)

# --- Roster Upload / Edit ---

st.sidebar.header("📁 Roster Management")
uploaded = st.sidebar.file_uploader("Upload roster CSV", type="csv")
if uploaded:
    roster_df = pd.read_csv(uploaded)
else:
    try:
        roster_df = pd.read_csv("rosters.csv")
    except FileNotFoundError:
        roster_df = pd.DataFrame(columns=["team","role","player"])
        st.sidebar.warning("No roster CSV found. Please upload one.")

# Add 'active' flag if missing

target_cols = ["team","role","player","active"]
if "active" not in roster_df.columns:
    roster_df["active"] = True

# --- Team Selection ---

teams = roster_df[roster_df["active"]]["team"].unique().tolist()
if not teams:
    st.sidebar.info("Upload or load a roster first.")
    st.stop()
colA, colB = st.sidebar.columns(2)
with colA:
    team1 = st.selectbox("Team 1", teams)
with colB:
    other_teams = [t for t in teams if t != team1]
    team2 = st.selectbox("Team 2", other_teams)
st.sidebar.markdown("---")

# Inline editor for active toggles (capture active flags)

team_dfs = []
for team in (team1, team2):
    st.sidebar.markdown(f"**{team}**")
    df_team = roster_df[roster_df["team"]==team].reset_index(drop=True)
    edited = st.sidebar.data_editor(
        df_team, key=f"edit_{team}", num_rows="dynamic"
    )
    team_dfs.append(edited)

# rebuild roster_df only from edited teams with active==True

roster_df = pd.concat(team_dfs, ignore_index=True)
roster_df = roster_df[roster_df["active"]]

# --- Build categories & mapping ---

roles = ["WK","BAT","ALL","BOWL"]
categories = {}
player_to_team = {}
filtered = roster_df[roster_df["team"].isin([team1, team2])]
for role in roles:
    lst = filtered[filtered["role"]==role]["player"].unique().tolist()
    categories[role] = lst
    for p in lst:
        player_to_team[p] = filtered[filtered["player"]==p]["team"].iloc[0]
players = list(player_to_team.keys())

# --- Player Metrics Input ---

with st.expander("🎯 Player Metrics for Probability Calculation", expanded=True):
    prob_mode = st.selectbox(
        "Choose metric for selection probability",
        ["Fantasy Points","Dream Team % Inclusion","Average Points"]
    )
    metric_values = []
    idx = 0
    for role in roles:
        vals = categories.get(role, [])
        if vals:
            st.markdown(f"#### {role}")
            cols = st.columns(len(vals))
            for i, player in enumerate(vals):
                with cols[i]:
                    default = 30 if prob_mode!="Dream Team % Inclusion" else 50
                    max_val = 100 if prob_mode=="Dream Team % Inclusion" else None
                    key = f"met_{role}_{idx}"
                    val = st.number_input(
                        player, min_value=0, value=default,
                        step=1, max_value=max_val, key=key
                    )
                    metric_values.append(val)
                idx += 1
        else:
            st.warning(f"No active players for role: {role}")
    metric_values = np.array(metric_values)
    try:
        prob = metric_values / metric_values.sum()
    except ZeroDivisionError:
        st.error("Total metric values must be greater than zero.")
        st.stop()

# --- Settings & Key Players ---

with st.sidebar:
    st.header("⚙️ Settings")
    no_of_teams = st.slider("Number of Teams",1,40,20)
    max_per_real_team = st.selectbox("Max players per team",[6,7,8],index=1)
    use_key = st.checkbox("Use key players for C/VC", value=True)
    export_option = st.selectbox("Export Format",["None","CSV"])
default_keys = players[:min(5,len(players))]
key_players = st.multiselect("Key players (C/VC)", players, default=default_keys)

# --- Generate Teams ---

teams_output=[]
if st.button("🚀 Generate Teams"):
    for t in range(1,no_of_teams+1):
        while True:
            source = key_players if use_key and key_players else players
            sidx = [players.index(p) for p in source]
            sp = np.array([prob[i] for i in sidx]); sp /= sp.sum() if sp.sum()>0 else 1
            cap,vc = (np.random.choice(source,2,replace=False,p=sp)
                        if len(source)>2 else (source[0],source[1]))
            team_sel={cap,vc}
            count={team1:0,team2:0}
            for p in team_sel: count[player_to_team[p]]+=1
            # ensure each role
            for role in roles:
                if not any(p in categories[role] for p in team_sel):
                    avail=[p for p in categories[role]
                            if p not in team_sel and count[player_to_team[p]]<max_per_real_team]
                    ridx=[players.index(p) for p in avail]
                    rp=np.array([prob[i] for i in ridx]); rp/=rp.sum() if rp.sum()>0 else 1
                    sel=np.random.choice(avail,p=rp)
                    team_sel.add(sel); count[player_to_team[sel]]+=1
            # fill
            pool=[p for p in players if p not in team_sel and count[player_to_team[p]]<max_per_real_team]
            pidx=[players.index(p) for p in pool]
            pp=np.array([prob[i] for i in pidx]); pp/=pp.sum() if pp.sum()>0 else 1
            while len(team_sel)<11 and pool:
                sel=np.random.choice(pool,p=pp); team_sel.add(sel)
                count[player_to_team[sel]]+=1
                i=pool.index(sel); pool.pop(i); pp=np.delete(pp,i)
                if pp.sum()>0: pp/=pp.sum()
            if len(team_sel)==11 and all(v<=max_per_real_team for v in count.values()):
                break
        # order by role₹
        final = []
        for role in roles:
            for p in categories[role]:
                if p in team_sel:
                    final.append(p)
        real_counts=[f"{count[team1]}",f"{count[team2]}"]
        formation=[sum(p in categories[r] for p in final) for r in roles]
        disp=[f"{i+1}. {p}{' 🧢' if p==cap else ' 🥈' if p==vc else ''}" 
              for i,p in enumerate(final)]
        st.markdown(f"### 🏏 TEAM {t}")
        st.markdown(f"**🧢 Captain:** {cap} | **🥈 Vice:** {vc}")
        st.code("\n".join(disp))
        st.markdown(f"🗂️ Counts: {'-'.join(real_counts)} ({team1}-{team2})")
        st.markdown(f"📊 Formation: {'-'.join(map(str,formation))} (WK-BAT-ALL-BOWL)")
        st.divider()
        teams_output.append({**{f"P{i+1}":p for i,p in enumerate(final)},'Captain':cap,'Vice':vc,
                            'Formation':'-'.join(map(str,formation)),team1:count[team1],team2:count[team2]})
    if export_option=='CSV':
        df=pd.DataFrame(teams_output); buf=BytesIO(); df.to_csv(buf,index=False); buf.seek(0)
        st.download_button("📥 Download CSV",buf.getvalue(),"dream11.csv","text/csv")
