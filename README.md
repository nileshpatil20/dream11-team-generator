# Dream11 Fantasy Team Generator

This app generates a Dream11 fantasy team based on player roles and team constraints.

## 🔧 Features

- Probabilistic player selection.
- Team composition based on roles: BAT, BWL, AR, WK.
- Filters players by team combinations.
- Displays selected team and count of each role.

## How to Use

1. Upload or ensure `rosters.csv` is present.
2. The app selects players probabilistically and builds a team.
3. Roles and team constraints are respected.

## Deploy on Streamlit Cloud

You can deploy this app on [Streamlit Cloud](https://streamlit.io/cloud).

---

### Files:
- `streamlit_app.py`: Main Streamlit application.
- `rosters.csv`: CSV file containing player information.

---

### Sample Command (Locally):

```bash
streamlit run streamlit_app.py
