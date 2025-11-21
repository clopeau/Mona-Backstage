import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Mona Backstage", layout="centered", page_icon="👗")
DATA_FILE = "mona_db_v3.json" # Nouvelle version DB pour nouvelle structure

# --- FONCTIONS DATE & DATA ---

def get_monday(date_obj):
    """Renvoie le lundi de la semaine correspondant à la date donnée"""
    return date_obj - timedelta(days=date_obj.weekday())

def date_to_str(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def str_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def load_data():
    # Structure: "weeks": { "2023-10-23": [slots...], "2023-10-30": [slots...] }
    default_data = {
        "weeks": {}, 
        "equipe": ["Julie", "Sarah", "Marie", "Sophie", "Laura"] 
    }
    if not os.path.exists(DATA_FILE):
        return default_data
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # Migration ou init
            if "weeks" not in data: data["weeks"] = {}
            if "equipe" not in data: data["equipe"] = default_data["equipe"]
            return data
    except:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

def generer_structure_vide(lundi_date):
    """Génère la structure par défaut (template) pour une semaine donnée"""
    slots = []
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    curr = lundi_date
    
    for i, jour in enumerate(jours):
        d_str = curr.strftime("%d/%m/%Y")
        
        # Logique métier : 2 lives sem, 1 live samedi
        # Matin
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
    # On ne prend que les slots ACTIFS
    slots_actifs = [s for s in slots if s.get('actif', True)]
    
    if not slots_actifs:
        return "https://wa.me/"
        
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

# --- AUTHENTIFICATION ---
st.sidebar.header("🔐 Connexion")
user_role = st.sidebar.selectbox("Qui êtes-vous ?", ["Visiteur", "Intervenante", "Admin"])
username = None

if user_role == "Intervenante":
    if data["equipe"]:
        username = st.sidebar.selectbox("Votre Prénom", data["equipe"])
    else:
        st.sidebar.error("Pas d'équipe.")

# --- LOGIQUE DE SÉLECTION DE SEMAINE ---
# On calcule le lundi de la semaine actuelle
today = datetime.now()
monday_current = get_monday(today)
monday_next = monday_current + timedelta(days=7)
monday_next_2 = monday_current + timedelta(days=14)

# Dictionnaire pour l'affichage convivial
choix_semaines = {
    f"Semaine en cours ({monday_current.strftime('%d/%m')})": date_to_str(monday_current),
    f"Semaine prochaine ({monday_next.strftime('%d/%m')})": date_to_str(monday_next),
    f"Dans 2 semaines ({monday_next_2.strftime('%d/%m')})": date_to_str(monday_next_2),
}

# --- VUE VISITEUR / INTERVENANTE ---
if user_role in ["Visiteur", "Intervenante"]:
    st.header("📅 Planning")
    
    # Sélecteur simple
    label_semaine = st.radio("Période :", list(choix_semaines.keys())[:2], horizontal=True, label_visibility="collapsed")
    key_week = choix_semaines[label_semaine]
    
    slots_week = data["weeks"].get(key_week, [])
    # On filtre pour ne montrer que les actifs
    slots_week_visibles = [s for s in slots_week if s.get('actif', True)]
    
    if not slots_week_visibles:
        st.info("⏳ Pas de planning publié pour cette semaine.")
    else:
        # MODE VISUALISATION
        if user_role == "Visiteur":
            for slot in slots_week_visibles:
                with st.container():
                    st.markdown(f"#### {slot['jour']} {slot['date']}")
                    st.caption(f"⏰ {slot['heure']}")
                    c1, c2 = st.columns(2)
                    c1.success(f"🎥 **{', '.join(slot['elu_cam']) if slot['elu_cam'] else '...'}**")
                    c2.warning(f"🎙️ **{slot['elu_voix'] if slot['elu_voix'] else '...'}**")
                    st.divider()
        
        # MODE INTERVENANTE (DISPOS)
        elif user_role == "Intervenante" and username:
            st.info(f"Saisie des dispos pour : {label_semaine}")
            with st.form("dispo"):
                for slot in slots_week_visibles:
                    st.markdown(f"**{slot['jour']} - {slot['heure']}**")
                    c1, c2 = st.columns(2)
                    
                    # Cam
                    is_c = username in slot['candidats_cam']
                    if c1.checkbox("Caméra", value=is_c, key=f"c_{slot['id']}"):
                        if username not in slot['candidats_cam']: slot['candidats_cam'].append(username)
                    else:
                        if username in slot['candidats_cam']: slot['candidats_cam'].remove(username)
                    
                    # Voix
                    is_v = username in slot['candidats_voix']
                    if c2.checkbox("Voix", value=is_v, key=f"v_{slot['id']}"):
                        if username not in slot['candidats_voix']: slot['candidats_voix'].append(username)
                    else:
                        if username in slot['candidats_voix']: slot['candidats_voix'].remove(username)
                    st.write("")
                    
                if st.form_submit_button("✅ Enregistrer mes dispos"):
                    # On met à jour la DB globale
                    # Note: slots_week est une référence à la liste dans data["weeks"], donc modif directe
                    save_data(data)
                    st.success("C'est enregistré !")


# --- VUE ADMIN ---
if user_role == "Admin":
    st.header("🔧 Backstage Admin")
    
    # 1. SÉLECTIONNER LA SEMAINE DE TRAVAIL
    st.markdown("### 1. Choisir la semaine à modifier")
    choix_admin = st.selectbox("Semaine cible :", list(choix_semaines.keys()))
    selected_week_key = choix_semaines[choix_admin]
    
    # Chargement ou Initialisation des données pour cette semaine
    if selected_week_key not in data["weeks"]:
        # On génère le template par défaut mais on ne sauvegarde pas encore (juste en mémoire)
        slots_current_work = generer_structure_vide(str_to_date(selected_week_key))
        is_new_week = True
    else:
        slots_current_work = data["weeks"][selected_week_key]
        is_new_week = False
        
    st.divider()
    
    t1, t2, t3, t4 = st.tabs(["🛠️ Structure (Horaires)", "🎬 Casting", "📢 Diffusion", "👥 Équipe"])
    
    # TAB 1: STRUCTURE (Création/Modif Persistante)
    with t1:
        st.caption("Cochez les lives actifs et modifiez les heures. Les modifications sont sauvegardées immédiatement.")
        
        with st.form("structure_form"):
            # On itère par jour (2 slots par jour dans notre structure)
            # On suppose que slots_current_work est trié (Matin/Soir)
            
            jours_vus = []
            for i in range(0, len(slots_current_work), 2): # Pas de 2
                slot_m = slots_current_work[i]   # Matin
                slot_s = slots_current_work[i+1] # Soir
                
                with st.expander(f"**{slot_m['jour']}** {slot_m['date']}", expanded=True):
                    
                    # LIGNE MATIN
                    c1, c2, c3 = st.columns([1, 2, 3])
                    act_m = c1.checkbox("Matin", value=slot_m.get('actif', True), key=f"act_{slot_m['id']}")
                    hr_m = c2.text_input("Heure", value=slot_m['heure'], key=f"hr_{slot_m['id']}", disabled=not act_m)
                    
                    # Mise à jour locale
                    slot_m['actif'] = act_m
                    slot_m['heure'] = hr_m
                    if not act_m: c3.caption("💤 Inactif")
                    else: c3.success(f"✅ Actif à {hr_m}")

                    # LIGNE SOIR
                    c1b, c2b, c3b = st.columns([1, 2, 3])
                    act_s = c1b.checkbox("Soir", value=slot_s.get('actif', True), key=f"act_{slot_s['id']}")
                    hr_s = c2b.text_input("Heure", value=slot_s['heure'], key=f"hr_{slot_s['id']}", disabled=not act_s)
                    
                    slot_s['actif'] = act_s
                    slot_s['heure'] = hr_s
                    if not act_s: c3b.caption("💤 Inactif")
                    else: c3b.success(f"✅ Actif à {hr_s}")

            if st.form_submit_button("💾 Enregistrer la structure"):
                # On écrase ou crée la semaine dans la DB
                data["weeks"][selected_week_key] = slots_current_work
                save_data(data)
                st.success("Structure mise à jour ! Allez dans l'onglet Casting.")
                st.rerun()

    # TAB 2: CASTING
    with t2:
        # On ne travaille que sur les slots actifs
        active_slots = [s for s in slots_current_work if s.get('actif', True)]
        
        if not active_slots:
            st.warning("Aucun live actif. Activez des créneaux dans l'onglet Structure.")
        else:
            # S'assurer que la semaine existe bien en base (au cas où on va direct dans casting sans sauver structure)
            if selected_week_key not in data["weeks"]:
                st.warning("⚠️ Cette semaine n'est pas encore créée. Validez d'abord l'onglet 'Structure'.")
            else:
                for i, s in enumerate(active_slots):
                    with st.expander(f"{s['jour']} {s['heure']} - ({len(s['candidats_cam'])+len(s['candidats_voix'])} candidatures)"):
                        c1, c2 = st.columns(2)
                        
                        # Cam
                        s['elu_cam'] = c1.multiselect("🎥 Caméra", data["equipe"], default=[p for p in s['elu_cam'] if p in data["equipe"]], key=f"cast_c_{s['id']}")
                        st.caption(f"Dispos: {', '.join(s['candidats_cam'])}")
                        
                        # Voix
                        idx = (["..."]+data["equipe"]).index(s['elu_voix']) if s['elu_voix'] in data["equipe"] else 0
                        sel = c2.selectbox("🎙️ Voix", ["..."]+data["equipe"], index=idx, key=f"cast_v_{s['id']}")
                        s['elu_voix'] = sel if sel != "..." else None
                        st.caption(f"Dispos: {', '.join(s['candidats_voix'])}")
                
                if st.button("💾 Sauvegarder le Casting"):
                    save_data(data)
                    st.success("Casting enregistré !")

    # TAB 3: DIFFUSION
    with t3:
        if selected_week_key in data["weeks"]:
            link = generer_lien_whatsapp(data["weeks"][selected_week_key])
            st.markdown(f"### [👉 Envoyer Planning WhatsApp]({link})")
            st.caption("Ce lien génère le message pour la semaine sélectionnée.")
        else:
            st.error("Sauvegardez d'abord la structure.")

    # TAB 4: ÉQUIPE
    with t4:
        c1, c2 = st.columns(2)
        new = c1.text_input("Ajout Membre")
        if c1.button("Ajouter") and new:
            data["equipe"].append(new)
            save_data(data)
            st.rerun()
        rem = c2.selectbox("Retrait Membre", ["..."] + data["equipe"])
        if c2.button("Supprimer") and rem != "...":
            data["equipe"].remove(rem)
            save_data(data)
            st.rerun()
