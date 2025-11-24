import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse
import extra_streamlit_components as stx

# --- CONFIGURATION ---
st.set_page_config(page_title="Mona Backstage", layout="centered", page_icon="👗")
DATA_FILE = "mona_db_v3.json"

# --- FONCTIONS UTILITAIRES ---

def get_monday(date_obj):
    return date_obj - timedelta(days=date_obj.weekday())

def date_to_str(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def str_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def load_data():
    default_data = {
        "weeks": {}, 
        "equipe": ["Julie", "Sarah", "Marie", "Sophie", "Laura"] 
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "weeks" not in data: data["weeks"] = {}
            if "equipe" not in data: data["equipe"] = default_data["equipe"]
            return data
    except:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

def generer_structure_vide(lundi_date):
    slots = []
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    curr = lundi_date
    for i, jour in enumerate(jours):
        d_str = curr.strftime("%d/%m/%Y")
        actif_m = True if i < 6 else False
        heure_m = "10:00" if i == 5 else "12:00"
        # Note : elu_voix est maintenant initialisé comme une liste []
        slots.append({"id": f"{d_str}-matin", "jour": jour, "date": d_str, "heure": heure_m, "actif": actif_m, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "matin"})
        actif_s = True if i < 5 else False
        slots.append({"id": f"{d_str}-soir", "jour": jour, "date": d_str, "heure": "18:30", "actif": actif_s, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "soir"})
        curr += timedelta(days=1)
    return slots

def generer_lien_whatsapp(slots):
    slots_actifs = [s for s in slots if s.get('actif', True)]
    if not slots_actifs: return "https://wa.me/"
    text = "*👗 LIVE PLANNER - MONA DRESS 👗*\n\n"
    for slot in slots_actifs:
        # Gestion multi-voix pour l'affichage
        # On s'assure que c'est une liste (compatibilité anciens fichiers)
        list_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
        list_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []

        cam = ", ".join(list_cam) if list_cam else "❓"
        voix = ", ".join(list_voix) if list_voix else "❓"
        
        text += f"🗓️ *{slot['jour']} {slot['date']} à {slot['heure']}*\n🎥 Cam: {cam}\n🎙️ Voix: {voix}\n\n"
    text += "Merci les filles ! ✨"
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- INTERFACE ---

data = load_data()
st.title("👗 Mona Backstage")

# --- COOKIES ---
cookie_manager = stx.CookieManager()
cookie_user = cookie_manager.get(cookie="mona_artiste_name")

st.sidebar.header("Loges")
mode_view = st.sidebar.selectbox("Mode", ["Artiste", "Boss"])
current_artiste = None

if mode_view == "Artiste":
    st.sidebar.markdown("---")
    st.sidebar.write("👤 **Identification**")
    team_list = ["Choisir..."] + data["equipe"]
    default_index = team_list.index(cookie_user) if cookie_user in data["equipe"] else 0
    selected_user = st.sidebar.selectbox("Je suis :", team_list, index=default_index)
    if selected_user != "Choisir...":
        current_artiste = selected_user
        if selected_user != cookie_user:
            cookie_manager.set("mona_artiste_name", selected_user, expires_at=datetime.now() + timedelta(days=30))
    elif cookie_user and cookie_user in data["equipe"]:
        current_artiste = cookie_user

# --- DATES ---
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
    
    if not current_artiste:
        st.info("👈 Veuillez sélectionner votre prénom dans le menu de gauche.")
        st.stop()
    
    st.header(f"👋 Hello {current_artiste}")
    
    tab_visu, tab_voeux = st.tabs(["📅 Planning", "✨ Mes Vœux"])
    
    # --- TAB 1 : PLANNING COMPACT ---
    with tab_visu:
        key_week = date_to_str(monday_current)
        slots_week = data["weeks"].get(key_week, [])
        slots_visibles = [s for s in slots_week if s.get('actif', True)]
        
        if not slots_visibles:
            st.info("Planning non publié.")
        else:
            for slot in slots_visibles:
                with st.container(border=True):
                    c_time, c_info = st.columns([1, 3])
                    with c_time:
                        st.markdown(f"### {slot['heure']}")
                    with c_info:
                        st.markdown(f"**{slot['jour']} {slot['date']}**")
                        
                        # Sécurisation types listes pour affichage
                        l_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
                        l_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []
                        
                        cam_txt = ", ".join(l_cam) if l_cam else "..."
                        voix_txt = ", ".join(l_voix) if l_voix else "..."
                        
                        st.caption(f"🎥 {cam_txt} | 🎙️ {voix_txt}")

    # --- TAB 2 : VŒUX SIMPLIFIÉS ---
    with tab_voeux:
        st.write("Cochez les créneaux où vous êtes disponible :")
        
        weeks_to_show = [
            (date_to_str(monday_next), f"Semaine Prochaine"),
            (date_to_str(monday_next_2), f"Dans 2 semaines")
        ]
        
        if not any(wk[0] in data["weeks"] for wk in weeks_to_show):
            st.warning("⏳ Pas de créneaux ouverts pour l'instant.")
        else:
            with st.form("dispo_form"):
                for wk_key, wk_label in weeks_to_show:
                    if wk_key in data["weeks"]:
                        st.markdown(f"##### 🗓️ {wk_label}")
                        slots_target = data["weeks"][wk_key]
                        slots_vis = [s for s in slots_target if s.get('actif', True)]
                        
                        if not slots_vis:
                            st.caption("Rien de prévu.")
                        
                        for slot in slots_vis:
                            short_date = "/".join(slot['date'].split("/")[:2])
                            label_case = f"**{slot['heure']}** - {slot['jour']} {short_date}"
                            
                            is_dispo = (current_artiste in slot['candidats_cam']) or (current_artiste in slot['candidats_voix'])
                            
                            new_state = st.checkbox(label_case, value=is_dispo, key=f"d_{slot['id']}")
                            
                            if new_state:
                                if current_artiste not in slot['candidats_cam']: slot['candidats_cam'].append(current_artiste)
                                if current_artiste not in slot['candidats_voix']: slot['candidats_voix'].append(current_artiste)
                            else:
                                if current_artiste in slot['candidats_cam']: slot['candidats_cam'].remove(current_artiste)
                                if current_artiste in slot['candidats_voix']: slot['candidats_voix'].remove(current_artiste)
                        
                        st.divider()

                if st.form_submit_button("✅ Envoyer mes disponibilités", use_container_width=True):
                    save_data(data)
                    st.balloons()
                    st.success("Disponibilités envoyées au Boss !")

# ==========================================
#              VUE BOSS
# ==========================================
elif mode_view == "Boss":
    st.header("🕶️ Espace Boss")
    
    choix_admin = st.selectbox("Semaine cible :", list(choix_semaines.keys()))
    selected_week_key = choix_semaines[choix_admin]
    
    if selected_week_key not in data["weeks"]:
        slots_current_work = generer_structure_vide(str_to_date(selected_week_key))
    else:
        slots_current_work = data["weeks"][selected_week_key]
        
    st.divider()
    t1, t2, t3, t4 = st.tabs(["🛠️ Structure", "🎬 Casting", "📢 Diffusion", "👥 Équipe"])
    
    # --- STRUCTURE ---
    with t1:
        st.caption("Activez les Switchs pour afficher/masquer l'heure.")
        for i in range(0, len(slots_current_work), 2):
            slot_m = slots_current_work[i]
            slot_s = slots_current_work[i+1]
            with st.container(border=True):
                st.markdown(f"**{slot_m['jour']}** {slot_m['date']}")
                col_matin, col_soir = st.columns(2)
                with col_matin:
                    is_active_m = st.toggle("Midi", value=slot_m.get('actif', True), key=f"tg_{slot_m['id']}")
                    if is_active_m: st.text_input("Heure M", value=slot_m['heure'], key=f"hm_{slot_m['id']}", label_visibility="collapsed")
                    else: st.caption("💤 Off")
                with col_soir:
                    is_active_s = st.toggle("Soir", value=slot_s.get('actif', True), key=f"tg_{slot_s['id']}")
                    if is_active_s: st.text_input("Heure S", value=slot_s['heure'], key=f"hs_{slot_s['id']}", label_visibility="collapsed")
                    else: st.caption("💤 Off")

        if st.button("💾 Enregistrer la Structure", type="primary", use_container_width=True):
            for slot in slots_current_work:
                k_act = f"tg_{slot['id']}"
                if k_act in st.session_state:
                    slot['actif'] = st.session_state[k_act]
                    if slot['actif']:
                        prefix = "hm" if "matin" in slot['id'] else "hs"
                        k_hr = f"{prefix}_{slot['id']}"
                        if k_hr in st.session_state: slot['heure'] = st.session_state[k_hr]
            data["weeks"][selected_week_key] = slots_current_work
            save_data(data)
            st.success("Structure sauvegardée !")

    # --- CASTING (Multi-Selection pour les deux) ---
    with t2:
        active_slots = [s for s in slots_current_work if s.get('actif', True)]
        if not active_slots: st.warning("Aucun live actif.")
        elif selected_week_key not in data["weeks"]: st.warning("Sauvegardez la structure d'abord.")
        else:
            for s in active_slots:
                with st.expander(f"{s['jour']} {s['heure']} ({len(s['candidats_cam'])})"):
                    c1, c2 = st.columns(2)
                    
                    # --- CAMÉRA ---
                    # Vérification compatibilité type list
                    curr_cam = s['elu_cam'] if isinstance(s['elu_cam'], list) else []
                    s['elu_cam'] = c1.multiselect(
                        "🎥 Cam", 
                        data["equipe"], 
                        default=[p for p in curr_cam if p in data["equipe"]], 
                        key=f"mc_{s['id']}"
                    )
                    st.caption(f"Dispos : {', '.join(s['candidats_cam'])}")
                    
                    # --- VOIX (NOUVEAU : Multiselect) ---
                    # Vérification compatibilité type list (si ancienne version string)
                    curr_voix = s['elu_voix'] if isinstance(s['elu_voix'], list) else [s['elu_voix']] if s['elu_voix'] else []
                    
                    s['elu_voix'] = c2.multiselect(
                        "🎙️ Voix", 
                        data["equipe"], 
                        default=[p for p in curr_voix if p in data["equipe"]], 
                        key=f"mv_{s['id']}"
                    )
            
            if st.button("💾 Sauvegarder Casting", use_container_width=True):
                save_data(data)
                st.success("Casting OK !")

    # --- DIFFUSION ---
    with t3:
        if selected_week_key in data["weeks"]:
            link = generer_lien_whatsapp(data["weeks"][selected_week_key])
            st.markdown(f"### [👉 WhatsApp]({link})")
        else: st.error("Structure non sauvegardée.")

    # --- ÉQUIPE ---
    with t4:
        c1, c2 = st.columns(2)
        new = c1.text_input("Ajout")
        if c1.button("Ajouter") and new:
            data["equipe"].append(new)
            save_data(data)
            st.rerun()
        rem = c2.selectbox("Retrait", ["..."] + data["equipe"])
        if c2.button("Supprimer") and rem != "...":
            data["equipe"].remove(rem)
            save_data(data)
            st.rerun()
