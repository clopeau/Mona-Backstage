import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse

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
        
        # Midi
        actif_m = True if i < 6 else False
        heure_m = "10:00" if i == 5 else "12:00"
        slots.append({
            "id": f"{d_str}-matin", "jour": jour, "date": d_str, "heure": heure_m, "actif": actif_m,
            "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": None, "type": "matin"
        })
        
        # Soir
        actif_s = True if i < 5 else False
        slots.append({
            "id": f"{d_str}-soir", "jour": jour, "date": d_str, "heure": "18:30", "actif": actif_s,
            "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": None, "type": "soir"
        })
        curr += timedelta(days=1)
    return slots

def generer_lien_whatsapp(slots):
    slots_actifs = [s for s in slots if s.get('actif', True)]
    if not slots_actifs: return "https://wa.me/"
        
    text = "*👗 LIVE PLANNER - MONA DRESS 👗*\n\n"
    for slot in slots_actifs:
        cam = ", ".join(slot['elu_cam']) if slot['elu_cam'] else "❓"
        voix = slot['elu_voix'] if slot['elu_voix'] else "❓"
        text += f"🗓️ *{slot['jour']} {slot['date']} à {slot['heure']}*\n🎥 Cam: {cam}\n🎙️ Voix: {voix}\n\n"
    text += "Merci les filles ! ✨"
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- INTERFACE ---

data = load_data()
st.title("👗 Mona Backstage")

# --- LOGIN ---
st.sidebar.header("🔐 Connexion")
user_role = st.sidebar.selectbox("Qui êtes-vous ?", ["Visiteur", "Intervenante", "Admin"])
username = None
if user_role == "Intervenante":
    if data["equipe"]:
        username = st.sidebar.selectbox("Votre Prénom", data["equipe"])
    else:
        st.sidebar.error("Pas d'équipe.")

# --- SÉLECTION SEMAINE ---
today = datetime.now()
monday_current = get_monday(today)
monday_next = monday_current + timedelta(days=7)
monday_next_2 = monday_current + timedelta(days=14)

choix_semaines = {
    f"Semaine en cours ({monday_current.strftime('%d/%m')})": date_to_str(monday_current),
    f"Semaine prochaine ({monday_next.strftime('%d/%m')})": date_to_str(monday_next),
    f"Dans 2 semaines ({monday_next_2.strftime('%d/%m')})": date_to_str(monday_next_2),
}

# --- LOGIQUE VISITEUR / INTERVENANTE ---
if user_role in ["Visiteur", "Intervenante"]:
    st.header("📅 Planning")
    label_semaine = st.radio("Période :", list(choix_semaines.keys())[:2], horizontal=True, label_visibility="collapsed")
    key_week = choix_semaines[label_semaine]
    slots_week = data["weeks"].get(key_week, [])
    slots_visibles = [s for s in slots_week if s.get('actif', True)]
    
    if not slots_visibles:
        st.info("⏳ Planning non disponible.")
    else:
        if user_role == "Visiteur":
            for slot in slots_visibles:
                with st.container():
                    st.markdown(f"#### {slot['jour']} {slot['date']}")
                    st.caption(f"⏰ {slot['heure']}")
                    c1, c2 = st.columns(2)
                    c1.success(f"🎥 {', '.join(slot['elu_cam']) if slot['elu_cam'] else '...'}")
                    c2.warning(f"🎙️ {slot['elu_voix'] if slot['elu_voix'] else '...'}")
                    st.divider()
        elif user_role == "Intervenante" and username:
            with st.form("dispo"):
                for slot in slots_visibles:
                    st.markdown(f"**{slot['jour']} - {slot['heure']}**")
                    c1, c2 = st.columns(2)
                    is_c = username in slot['candidats_cam']
                    if c1.checkbox("Caméra", value=is_c, key=f"c_{slot['id']}"):
                        if username not in slot['candidats_cam']: slot['candidats_cam'].append(username)
                    else:
                        if username in slot['candidats_cam']: slot['candidats_cam'].remove(username)
                    
                    is_v = username in slot['candidats_voix']
                    if c2.checkbox("Voix", value=is_v, key=f"v_{slot['id']}"):
                        if username not in slot['candidats_voix']: slot['candidats_voix'].append(username)
                    else:
                        if username in slot['candidats_voix']: slot['candidats_voix'].remove(username)
                    st.write("")
                if st.form_submit_button("✅ Enregistrer"):
                    save_data(data)
                    st.success("C'est noté !")

# --- LOGIQUE ADMIN ---
if user_role == "Admin":
    st.header("🔧 Backstage Admin")
    
    choix_admin = st.selectbox("Semaine cible :", list(choix_semaines.keys()))
    selected_week_key = choix_semaines[choix_admin]
    
    if selected_week_key not in data["weeks"]:
        slots_current_work = generer_structure_vide(str_to_date(selected_week_key))
    else:
        slots_current_work = data["weeks"][selected_week_key]
        
    st.divider()
    t1, t2, t3, t4 = st.tabs(["🛠️ Structure", "🎬 Casting", "📢 Diffusion", "👥 Équipe"])
    
    # TAB 1: STRUCTURE OPTIMISÉE MOBILE
    with t1:
        st.caption("Activez les créneaux (Switch) et réglez l'heure.")
        
        with st.form("structure_form"):
            # On boucle par paire (Matin + Soir)
            for i in range(0, len(slots_current_work), 2):
                slot_m = slots_current_work[i]   # Matin
                slot_s = slots_current_work[i+1] # Soir
                
                # CARTE DU JOUR (Cadre)
                with st.container(border=True):
                    st.markdown(f"**{slot_m['jour']}** {slot_m['date']}")
                    
                    # Colonnes compactes
                    col_matin, col_soir = st.columns(2)
                    
                    # COLONNE MATIN
                    with col_matin:
                        # Switch (Toggle)
                        act_m = st.toggle("Midi", value=slot_m.get('actif', True), key=f"tg_{slot_m['id']}")
                        slot_m['actif'] = act_m
                        if act_m:
                            # Si actif : champ texte visible
                            slot_m['heure'] = st.text_input("Heure M", value=slot_m['heure'], key=f"hm_{slot_m['id']}", label_visibility="collapsed")
                        else:
                            # Si inactif : texte gris
                            st.caption("💤 Off")

                    # COLONNE SOIR
                    with col_soir:
                        act_s = st.toggle("Soir", value=slot_s.get('actif', True), key=f"tg_{slot_s['id']}")
                        slot_s['actif'] = act_s
                        if act_s:
                            slot_s['heure'] = st.text_input("Heure S", value=slot_s['heure'], key=f"hs_{slot_s['id']}", label_visibility="collapsed")
                        else:
                            st.caption("💤 Off")
            
            # Bouton de validation large
            if st.form_submit_button("💾 Enregistrer la Structure", type="primary", use_container_width=True):
                data["weeks"][selected_week_key] = slots_current_work
                save_data(data)
                st.success("Mise à jour effectuée !")
                st.rerun()

    # TAB 2: CASTING
    with t2:
        active_slots = [s for s in slots_current_work if s.get('actif', True)]
        if not active_slots:
            st.warning("Aucun live actif.")
        elif selected_week_key not in data["weeks"]:
             st.warning("Enregistrez d'abord la structure.")
        else:
            for s in active_slots:
                with st.expander(f"{s['jour']} {s['heure']} ({len(s['candidats_cam'])+len(s['candidats_voix'])})"):
                    c1, c2 = st.columns(2)
                    s['elu_cam'] = c1.multiselect("🎥 Cam", data["equipe"], default=[p for p in s['elu_cam'] if p in data["equipe"]], key=f"mc_{s['id']}")
                    st.caption(f"Dispos: {', '.join(s['candidats_cam'])}")
                    
                    idx = (["..."]+data["equipe"]).index(s['elu_voix']) if s['elu_voix'] in data["equipe"] else 0
                    sel = c2.selectbox("🎙️ Voix", ["..."]+data["equipe"], index=idx, key=f"mv_{s['id']}")
                    s['elu_voix'] = sel if sel != "..." else None
                    st.caption(f"Dispos: {', '.join(s['candidats_voix'])}")
            
            if st.button("💾 Sauvegarder Casting", use_container_width=True):
                save_data(data)
                st.success("OK !")

    # TAB 3: DIFFUSION
    with t3:
        if selected_week_key in data["weeks"]:
            link = generer_lien_whatsapp(data["weeks"][selected_week_key])
            st.markdown(f"### [👉 WhatsApp]({link})")
        else:
            st.error("Sauvegardez structure.")

    # TAB 4: ÉQUIPE
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
