import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import extra_streamlit_components as stx
import time

# --- CONFIGURATION ---
st.set_page_config(page_title="Mona Backstage", layout="centered", page_icon="👗")
DATA_FILE = "mona_db_v3.json"
GLOBAL_PASSWORD = "mona"
SHORT_URL = "https://m-drs.fr/1Tv"

# --- CSS / STYLE ---
st.markdown("""
    <style>
    /* Ajustement général Mobile */
    div[data-testid="column"] button { width: 100% !important; }
    .block-container { padding-top: 1rem; padding-bottom: 5rem; }
    .compact-hr { margin-top: 5px !important; margin-bottom: 5px !important; border: 0; border-top: 1px solid #e0e0e0; }
    
    /* 1. VIGNETTES SÉLECTIONNÉES (DANS LE MULTISELECT) -> VERT */
    span[data-baseweb="tag"] {
        background-color: #e8f5e9 !important; /* Vert très clair */
        border: 1px solid #c8e6c9 !important;
    }
    span[data-baseweb="tag"] span {
        color: #2e7d32 !important; /* Texte Vert foncé */
        font-weight: bold;
    }

    /* 2. VIGNETTES DISPONIBLES (BOUTONS) -> ORANGE */
    div[data-testid="column"] button[kind="secondary"] {
        background-color: #fff3e0 !important; /* Orange très clair */
        border: 1px solid #ffcc80 !important;
        color: #ef6c00 !important; /* Texte Orange foncé */
        font-weight: 500;
    }
    div[data-testid="column"] button[kind="secondary"]:hover {
        border-color: #ef6c00 !important;
        background-color: #ffe0b2 !important;
    }

    /* Bouton WhatsApp */
    .wa-btn {
        text-decoration: none; background-color: #25D366; color: white !important;
        padding: 10px 20px; border-radius: 8px; display: block;
        text-align: center; font-weight: bold; margin-top: 20px; font-family: sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---
def get_monday(date_obj): return date_obj - timedelta(days=date_obj.weekday())
def date_to_str(date_obj): return date_obj.strftime("%Y-%m-%d")
def str_to_date(date_str): return datetime.strptime(date_str, "%Y-%m-%d")

def get_time_options():
    times = []
    for h in range(8, 23):
        times.append(f"{h:02d}:00")
        times.append(f"{h:02d}:30")
    return times

def format_titre_slot(slot):
    short_date = "/".join(slot['date'].split("/")[:2])
    return f"**{slot['jour']} {slot['heure']}** ({short_date})"

def is_future(slot):
    try:
        slot_dt = datetime.strptime(f"{slot['date']} {slot['heure']}", "%d/%m/%Y %H:%M")
        return slot_dt > datetime.now()
    except: return True

def load_data():
    default_data = {"weeks": {}, "equipe": ["Julie", "Sarah", "Marie", "Sophie", "Laura"]}
    if not os.path.exists(DATA_FILE): data = default_data
    else:
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "weeks" not in data: data["weeks"] = {}
                if "equipe" not in data: data["equipe"] = default_data["equipe"]
        except: data = default_data
    if data.get("equipe"): data["equipe"] = sorted(list(set(data["equipe"])))
    return data

def save_data(data):
    if data.get("equipe"): data["equipe"] = sorted(list(set(data["equipe"])))
    with open(DATA_FILE, "w") as f: json.dump(data, f, default=str)

def generer_structure_vide(lundi_date):
    slots = []
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    curr = lundi_date
    for i, jour in enumerate(jours):
        d_str = curr.strftime("%d/%m/%Y")
        actif_m = True if i < 6 else False
        heure_m = "10:00" if i == 5 else "12:00"
        slots.append({"id": f"{d_str}-matin", "jour": jour, "date": d_str, "heure": heure_m, "actif": actif_m, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "matin"})
        actif_s = True if i < 5 else False
        slots.append({"id": f"{d_str}-soir", "jour": jour, "date": d_str, "heure": "18:30", "actif": actif_s, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "soir"})
        curr += timedelta(days=1)
    return slots

def generer_wa_structure(slots):
    slots_actifs = [s for s in slots if s.get('actif', True)]
    if not slots_actifs: return "https://wa.me/"
    lines = ["✨ *HELLO LA TEAM !* ✨", "", "📅 La grille des Lives est ouverte !", f"👉 Mettez vos dispos ici : {SHORT_URL}", "", "*Au programme cette semaine :*"]
    current_day = ""
    for slot in slots_actifs:
        short_date = "/".join(slot['date'].split("/")[:2])
        if slot['jour'] != current_day:
            lines.append(f"🔹 *{slot['jour']} ({short_date})*")
            current_day = slot['jour']
        lines.append(f"   ⏰ {slot['heure']}")
    lines.append("")
    lines.append("A vos agendas ! 🚀")
    full_text = "\n".join(lines)
    encoded = urllib.parse.quote(full_text)
    return f"https://wa.me/?text={encoded}"

def generer_wa_casting(slots):
    slots_actifs = [s for s in slots if s.get('actif', True)]
    if not slots_actifs: return "https://wa.me/"
    lines = ["🎬 *PLANNING OFFICIEL MONA DRESS* 🎬", "", "Le casting est validé ! 🔥", f"👀 Voir sur l'app : {SHORT_URL}", ""]
    for slot in slots_actifs:
        short_date = "/".join(slot['date'].split("/")[:2])
        l_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
        l_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []
        lines.append(f"🗓️ *{slot['jour']} {slot['heure']}* ({short_date})")
        lines.append(f"🎥 {', '.join(l_cam) if l_cam else '❓'}")
        lines.append(f"🎙️ {', '.join(l_voix) if l_voix else '❓'}")
        lines.append("")
    lines.append("Bon live à toutes ! 💪")
    full_text = "\n".join(lines)
    encoded = urllib.parse.quote(full_text)
    return f"https://wa.me/?text={encoded}"

# --- CHARGEMENT ---
data = load_data()
cookie_manager = stx.CookieManager(key="mona_mgr")
long_expire = datetime.now() + timedelta(days=3650)
TIME_OPTIONS = get_time_options()

# 1. LOGIN
if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
auth_cookie = cookie_manager.get(cookie="mona_access")
if auth_cookie == "granted": st.session_state["authenticated"] = True

if not st.session_state["authenticated"]:
    st.title("🔒 Accès Privé")
    pwd_input = st.text_input("Mot de passe", type="password")
    if st.button("Entrer", type="primary"):
        if pwd_input == GLOBAL_PASSWORD:
            cookie_manager.set("mona_access", "granted", expires_at=long_expire)
            st.session_state["authenticated"] = True
            st.success("Accès autorisé")
            time.sleep(1)
            st.rerun()
        else: st.error("Non.")
    st.stop()

# 2. IDENTITÉ
if "current_user" not in st.session_state: st.session_state["current_user"] = None
identity_cookie = cookie_manager.get(cookie="mona_whoami")
if identity_cookie and identity_cookie in data["equipe"]: st.session_state["current_user"] = identity_cookie

if not st.session_state["current_user"]:
    st.title("👋 Qui es-tu ?")
    user_choice = st.selectbox("Je suis :", ["Choisir..."] + data["equipe"])
    if user_choice != "Choisir...":
        cookie_manager.set("mona_whoami", user_choice, expires_at=long_expire)
        st.session_state["current_user"] = user_choice
        st.rerun()
    st.stop()

current_user = st.session_state["current_user"]

# --- APP ---
st.sidebar.title("Mona Backstage")
st.sidebar.success(f"👤 **{current_user}**")
with st.sidebar.expander("Changer d'utilisateur"):
    change_user = st.selectbox("Identité", data["equipe"], index=data["equipe"].index(current_user))
    if change_user != current_user:
        cookie_manager.set("mona_whoami", change_user, expires_at=long_expire)
        st.session_state["current_user"] = change_user
        time.sleep(0.5)
        st.rerun()
st.sidebar.markdown("---")
mode_view = st.sidebar.radio("Navigation", ["Artiste", "Boss"])

# DATES
today = datetime.now()
monday_current = get_monday(today)
monday_next = monday_current + timedelta(days=7)
monday_next_2 = monday_current + timedelta(days=14)

choix_semaines = {
    f"Semaine en cours ({monday_current.strftime('%d/%m')})": date_to_str(monday_current),
    f"Semaine prochaine ({monday_next.strftime('%d/%m')})": date_to_str(monday_next),
    f"Dans 2 semaines ({monday_next_2.strftime('%d/%m')})": date_to_str(monday_next_2),
}

# ==========================================
#              VUE ARTISTE
# ==========================================
if mode_view == "Artiste":
    st.title(f"✨ Espace Artiste")
    tab_visu, tab_voeux = st.tabs(["📅 Timeline", "✍️ Mes Dispos"])
    
    with tab_visu:
        all_future_slots = []
        weeks_to_check = [date_to_str(monday_current), date_to_str(monday_next), date_to_str(monday_next_2)]
        for w_key in weeks_to_check:
            if w_key in data["weeks"]:
                for s in data["weeks"][w_key]:
                    if s.get('actif', True) and is_future(s):
                        all_future_slots.append(s)
        
        if not all_future_slots: st.info("Aucun live à venir pour le moment.")
        else:
            for slot in all_future_slots:
                with st.container(border=True):
                    st.markdown(format_titre_slot(slot))
                    l_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
                    l_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []
                    st.write(f"🎥 **Cam:** {', '.join(l_cam) if l_cam else '...'}")
                    st.write(f"🎙️ **Voix:** {', '.join(l_voix) if l_voix else '...'}")

    with tab_voeux:
        st.write(f"Coche les créneaux pour **{current_user}** :")
        weeks_to_show = [(date_to_str(monday_next), f"Semaine Prochaine"), (date_to_str(monday_next_2), f"Dans 2 semaines")]
        if not any(wk[0] in data["weeks"] for wk in weeks_to_show): st.warning("⏳ Pas encore de créneaux ouverts.")
        else:
            with st.form("dispo_form"):
                for wk_key, wk_label in weeks_to_show:
                    if wk_key in data["weeks"]:
                        st.markdown(f"##### 🗓️ {wk_label}")
                        slots_target = data["weeks"][wk_key]
                        slots_vis = [s for s in slots_target if s.get('actif', True)]
                        if not slots_vis: st.caption("Rien de prévu.")
                        for slot in slots_vis:
                            label_case = format_titre_slot(slot).replace("**", "")
                            is_dispo = (current_user in slot['candidats_cam']) or (current_user in slot['candidats_voix'])
                            new_state = st.checkbox(label_case, value=is_dispo, key=f"d_{slot['id']}")
                            if new_state:
                                if current_user not in slot['candidats_cam']: slot['candidats_cam'].append(current_user)
                                if current_user not in slot['candidats_voix']: slot['candidats_voix'].append(current_user)
                            else:
                                if current_user in slot['candidats_cam']: slot['candidats_cam'].remove(current_user)
                                if current_user in slot['candidats_voix']: slot['candidats_voix'].remove(current_user)
                        st.divider()
                if st.form_submit_button("✅ Envoyer mes dispos", use_container_width=True):
                    save_data(data)
                    st.balloons()
                    st.success("C'est envoyé !")

# ==========================================
#              VUE BOSS
# ==========================================
elif mode_view == "Boss":
    st.title("🕶️ Espace Boss")
    choix_admin = st.selectbox("Semaine cible :", list(choix_semaines.keys()))
    selected_week_key = choix_semaines[choix_admin]
    
    if selected_week_key not in data["weeks"]: slots_current_work = generer_structure_vide(str_to_date(selected_week_key))
    else: slots_current_work = data["weeks"][selected_week_key]
    
    t1, t2, t3 = st.tabs(["🛠️ Structure", "🎬 Casting", "👥 Équipe"])
    
    # --- TAB 1 : STRUCTURE ---
    with t1:
        st.caption("Configurer les horaires (Sauvegarde auto)")
        changes_detected = False
        
        for i in range(0, len(slots_current_work), 2):
            slot_m = slots_current_work[i]
            slot_s = slots_current_work[i+1]
            short_date = "/".join(slot_m['date'].split("/")[:2])
            
            with st.container(border=True):
                st.markdown(f"<h4 style='margin:0; padding:0;'>{slot_m['jour']} ({short_date})</h4>", unsafe_allow_html=True)
                
                # MIDI
                st.markdown("<hr class='compact-hr'>", unsafe_allow_html=True)
                m_active = st.toggle("Midi", value=slot_m.get('actif', True), key=f"tg_{slot_m['id']}")
                if m_active != slot_m.get('actif', True):
                    slot_m['actif'] = m_active
                    changes_detected = True
                
                if m_active:
                    idx_m = TIME_OPTIONS.index(slot_m['heure']) if slot_m['heure'] in TIME_OPTIONS else TIME_OPTIONS.index("12:00")
                    m_heure = st.selectbox("Heure M", TIME_OPTIONS, index=idx_m, key=f"hm_{slot_m['id']}", label_visibility="collapsed")
                    if m_heure != slot_m['heure']:
                        slot_m['heure'] = m_heure
                        changes_detected = True
                else: st.caption("💤 Off")
                
                # SOIR
                st.markdown("<hr class='compact-hr'>", unsafe_allow_html=True)
                s_active = st.toggle("Soir", value=slot_s.get('actif', True), key=f"tg_{slot_s['id']}")
                if s_active != slot_s.get('actif', True):
                    slot_s['actif'] = s_active
                    changes_detected = True
                
                if s_active:
                    idx_s = TIME_OPTIONS.index(slot_s['heure']) if slot_s['heure'] in TIME_OPTIONS else TIME_OPTIONS.index("18:30")
                    s_heure = st.selectbox("Heure S", TIME_OPTIONS, index=idx_s, key=f"hs_{slot_s['id']}", label_visibility="collapsed")
                    if s_heure != slot_s['heure']:
                        slot_s['heure'] = s_heure
                        changes_detected = True
                else: st.caption("💤 Off")

        if changes_detected:
            data["weeks"][selected_week_key] = slots_current_work
            save_data(data)

        st.markdown("---")
        link_struct = generer_wa_structure(slots_current_work)
        st.markdown(f"""<a href="{link_struct}" target="_blank" class="wa-btn">📢 Envoyer ouverture (WhatsApp)</a>""", unsafe_allow_html=True)


    # --- TAB 2 : CASTING ---
    with t2:
        active_slots = [s for s in slots_current_work if s.get('actif', True)]
        if not active_slots: st.warning("Pas de créneaux actifs.")
        else:
            changes_casting = False
            for s in active_slots:
                with st.expander(format_titre_slot(s) + f" - ({len(s['candidats_cam'])})", expanded=True):
                    
                    # --- CAMÉRA ---
                    st.write("🎥 **Caméra**")
                    curr_cam = s['elu_cam'] if isinstance(s['elu_cam'], list) else []
                    new_cam = st.multiselect("Select Cam", data["equipe"], default=[p for p in curr_cam if p in data["equipe"]], key=f"mc_{s['id']}", label_visibility="collapsed")
                    if new_cam != curr_cam:
                        s['elu_cam'] = new_cam
                        changes_casting = True
                        curr_cam = new_cam
                    
                    # BOUTONS CANDIDATS ORANGE
                    cand_cam = [c for c in s['candidats_cam'] if c not in curr_cam]
                    if cand_cam:
                        st.write("**Dispo :**")
                        cols_c = st.columns(min(len(cand_cam), 4))
                        for i, cand in enumerate(cand_cam):
                            # On passe l'objet complet à save_data pour être sûr
                            if cols_c[i % 4].button(f"{cand}", key=f"btn_c_{s['id']}_{cand}", type="secondary"):
                                s['elu_cam'].append(cand)
                                # Sauvegarde immédiate
                                data["weeks"][selected_week_key] = slots_current_work
                                save_data(data)
                                st.rerun()

                    st.markdown("<hr class='compact-hr'>", unsafe_allow_html=True)
                    
                    # --- VOIX ---
                    st.write("🎙️ **Voix**")
                    curr_voix = s['elu_voix'] if isinstance(s['elu_voix'], list) else [s['elu_voix']] if s['elu_voix'] else []
                    new_voix = st.multiselect("Select Voix", data["equipe"], default=[p for p in curr_voix if p in data["equipe"]], key=f"mv_{s['id']}", label_visibility="collapsed")
                    if new_voix != curr_voix:
                        s['elu_voix'] = new_voix
                        changes_casting = True
                        curr_voix = new_voix
                    
                    cand_voix = [c for c in s['candidats_voix'] if c not in curr_voix]
                    if cand_voix:
                        st.write("**Dispo :**")
                        cols_v = st.columns(min(len(cand_voix), 4))
                        for i, cand in enumerate(cand_voix):
                            if cols_v[i % 4].button(f"{cand}", key=f"btn_v_{s['id']}_{cand}", type="secondary"):
                                s['elu_voix'].append(cand)
                                data["weeks"][selected_week_key] = slots_current_work
                                save_data(data)
                                st.rerun()
            
            if changes_casting:
                data["weeks"][selected_week_key] = slots_current_work
                save_data(data)

            st.markdown("---")
            link_cast = generer_wa_casting(slots_current_work)
            st.markdown(f"""<a href="{link_cast}" target="_blank" class="wa-btn">🎬 Envoyer planning final (WhatsApp)</a>""", unsafe_allow_html=True)


    # --- TAB 3 : EQUIPE ---
    with t3:
        st.subheader("Team")
        with st.form("add_member", clear_on_submit=True):
            new = st.text_input("Nouveau membre", placeholder="Prénom")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new:
                    data["equipe"].append(new)
                    save_data(data)
                    st.rerun()
        st.markdown("---")
        for i, member in enumerate(data["equipe"]):
            with st.container(border=True):
                col_txt, col_act = st.columns([4, 1])
                with col_txt: st.markdown(f"**{member}**")
                with col_act:
                    if st.button("❌", key=f"pre_del_{i}"): st.session_state[f"confirm_del_{i}"] = True
                if st.session_state.get(f"confirm_del_{i}", False):
                    st.write("Supprimer ?")
                    c1, c2 = st.columns(2)
                    if c1.button("Oui", key=f"y_{i}", type="primary", use_container_width=True):
                        data["equipe"].pop(i)
                        save_data(data)
                        st.rerun()
                    if c2.button("Non", key=f"n_{i}", use_container_width=True):
                        st.session_state[f"confirm_del_{i}"] = False
                        st.rerun()
