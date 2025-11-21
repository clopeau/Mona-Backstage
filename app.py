import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse

# --- CONFIGURATION DU BRANDING ---
st.set_page_config(page_title="Mona Backstage", layout="centered", page_icon="👗")
DATA_FILE = "mona_planning_db.json" # J'ai renommé le fichier de sauvegarde pour faire propre

# --- FONCTIONS UTILITAIRES ---

def load_data():
    # Données par défaut avec une équipe fictive pour commencer
    default_data = {
        "semaine_prochaine": [], 
        "semaine_courante": [],
        "equipe": ["Julie", "Sarah", "Marie", "Sophie", "Laura"] 
    }
    
    if not os.path.exists(DATA_FILE):
        return default_data
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            if "equipe" not in data:
                data["equipe"] = default_data["equipe"]
            return data
    except:
        return default_data

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, default=str)

def get_next_monday():
    today = datetime.now()
    next_monday = today + timedelta(days=(7 - today.weekday()))
    return next_monday

def generer_slots_par_defaut(date_debut):
    slots = []
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    current_date = date_debut

    for i, jour in enumerate(jours):
        date_str = current_date.strftime("%d/%m/%Y")
        
        base_slot = {
            "jour": jour, 
            "date": date_str, 
            "candidats_cam": [], 
            "candidats_voix": [], 
            "elu_cam": [], 
            "elu_voix": None 
        }

        if i < 5: # Lundi à Vendredi (12h et 18h30)
            s1 = base_slot.copy()
            s1.update({"id": f"{date_str}-12h", "heure": "12:00"})
            slots.append(s1)
            
            s2 = base_slot.copy()
            s2.update({"id": f"{date_str}-18h30", "heure": "18:30", "elu_cam": [], "candidats_cam": [], "candidats_voix": []})
            slots.append(s2)
            
        elif i == 5: # Samedi (10h)
            s3 = base_slot.copy()
            s3.update({"id": f"{date_str}-10h", "heure": "10:00", "elu_cam": [], "candidats_cam": [], "candidats_voix": []})
            slots.append(s3)
        
        current_date += timedelta(days=1)
    return slots

def generer_lien_whatsapp(semaine_data):
    # En-tête personnalisé Mona Dress
    text = "*👗 LIVE PLANNER - MONA DRESS 👗*\n"
    text += "_Le planning de la semaine prochaine est prêt !_\n\n"
    
    for slot in semaine_data:
        if slot['elu_cam']:
            cam_names = ", ".join(slot['elu_cam'])
        else:
            cam_names = "❓"
            
        voix = slot['elu_voix'] if slot['elu_voix'] else "❓"
        
        text += f"🗓️ *{slot['jour']} {slot['date']} à {slot['heure']}*\n"
        text += f"🎥 Cam: {cam_names}\n🎙️ Voix: {voix}\n\n"
    
    text += "Merci les filles ! ✨"
    encoded_text = urllib.parse.quote(text)
    return f"https://wa.me/?text={encoded_text}"

# --- INTERFACE ---

data = load_data()

# Titre Principal
st.title("👗 Mona Backstage")
st.caption("Gestion du planning des Lives")

# MENU LATÉRAL
st.sidebar.header("🔐 Connexion")
user_role = st.sidebar.selectbox("Qui êtes-vous ?", ["Visiteur", "Intervenante", "Admin"])

username = None
if user_role == "Intervenante":
    if data["equipe"]:
        username = st.sidebar.selectbox("Votre Prénom", data["equipe"])
    else:
        st.sidebar.error("Aucune équipe définie.")

# --- ONGLET 1: VISUALISATION (Tout le monde) ---
if user_role == "Visiteur" or user_role == "Intervenante":
    st.header("📅 Planning")
    
    choix_semaine = st.radio("Période :", ["Semaine Courante", "Semaine Prochaine"], horizontal=True, label_visibility="collapsed")
    key_data = "semaine_courante" if choix_semaine == "Semaine Courante" else "semaine_prochaine"
    
    if not data.get(key_data):
        st.info("⏳ Le planning n'est pas encore disponible.")
    else:
        for slot in data[key_data]:
            with st.container():
                st.markdown(f"#### {slot['jour']} {slot['date']}")
                st.caption(f"⏰ {slot['heure']}")
                
                c_cam = ", ".join(slot['elu_cam']) if slot['elu_cam'] else "À définir"
                c_voix = slot['elu_voix'] if slot['elu_voix'] else "À définir"
                
                col1, col2 = st.columns(2)
                col1.success(f"🎥 **{c_cam}**")
                col2.warning(f"🎙️ **{c_voix}**")
                st.divider()

# --- ONGLET 2: DISPONIBILITÉS (Intervenantes) ---
if user_role == "Intervenante" and username:
    st.header(f"👋 Hello {username}")
    st.write("Tes dispos pour la **Semaine Prochaine** :")
    
    if not data.get("semaine_prochaine"):
        st.error("L'admin n'a pas encore ouvert les inscriptions.")
    else:
        with st.form("dispo_form"):
            slots_updated = data["semaine_prochaine"]
            for slot in slots_updated:
                st.markdown(f"**{slot['jour']} - {slot['heure']}**")
                c1, c2 = st.columns(2)
                
                # Checkbox Caméra
                is_in_cam = username in slot['candidats_cam']
                new_cam = c1.checkbox("Dispo Caméra", value=is_in_cam, key=f"c_{slot['id']}")
                
                # Checkbox Voix
                is_in_voix = username in slot['candidats_voix']
                new_voix = c2.checkbox("Dispo Voix", value=is_in_voix, key=f"v_{slot['id']}")
                
                # Logique
                if new_cam and username not in slot['candidats_cam']:
                    slot['candidats_cam'].append(username)
                elif not new_cam and username in slot['candidats_cam']:
                    slot['candidats_cam'].remove(username)
                    
                if new_voix and username not in slot['candidats_voix']:
                    slot['candidats_voix'].append(username)
                elif not new_voix and username in slot['candidats_voix']:
                    slot['candidats_voix'].remove(username)
                
                st.write("") 

            submitted = st.form_submit_button("✅ Enregistrer mes dispos", use_container_width=True)
            if submitted:
                data["semaine_prochaine"] = slots_updated
                save_data(data)
                st.success("C'est noté !")

# --- ONGLET 3: ADMIN ---
if user_role == "Admin":
    st.header("🔧 Backstage Admin")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Équipe", "📅 Création", "✅ Validation", "🚀 Publier"])
    
    # 1. GESTION ÉQUIPE
    with tab1:
        st.subheader("Gérer la Team Mona")
        st.write("Membres actuels :")
        st.info(", ".join(data["equipe"]))
        
        col_add, col_del = st.columns(2)
        with col_add:
            new_member = st.text_input("Ajouter un prénom")
            if st.button("Ajouter"):
                if new_member and new_member not in data["equipe"]:
                    data["equipe"].append(new_member)
                    save_data(data)
                    st.rerun()
        
        with col_del:
            del_member = st.selectbox("Retirer quelqu'un", ["Choisir..."] + data["equipe"])
            if st.button("Supprimer"):
                if del_member != "Choisir...":
                    data["equipe"].remove(del_member)
                    save_data(data)
                    st.rerun()

    # 2. CRÉATION PLANNING
    with tab2:
        st.subheader("Préparer semaine prochaine")
        next_monday = get_next_monday()
        st.write(f"Semaine du Lundi {next_monday.strftime('%d/%m/%Y')}")
        
        if st.button("✨ Générer les créneaux (Midi & Soir)"):
            data["semaine_prochaine"] = generer_slots_par_defaut(next_monday)
            save_data(data)
            st.success("Créneaux générés !")
            st.rerun()
            
        if data.get("semaine_prochaine"):
            if st.button("🗑️ Effacer le brouillon"):
                data["semaine_prochaine"] = []
                save_data(data)
                st.rerun()

    # 3. VALIDATION
    with tab3:
        st.subheader("Casting des Lives")
        if data.get("semaine_prochaine"):
            slots_to_edit = data["semaine_prochaine"]
            equipe_complete = data["equipe"]
            
            for i, slot in enumerate(slots_to_edit):
                nb_cand = len(slot['candidats_cam']) + len(slot['candidats_voix'])
                color_status = "🟢" if nb_cand > 0 else "🔴"
                
                with st.expander(f"{color_status} {slot['jour']} - {slot['heure']} ({nb_cand} candidatures)"):
                    
                    col_h, col_x = st.columns([1, 3])
                    new_time = col_h.text_input("Heure", value=slot['heure'], key=f"t_{i}")
                    slot['heure'] = new_time
                    
                    if slot['candidats_cam']:
                        st.caption(f"✋ Dispos Cam : {', '.join(slot['candidats_cam'])}")
                    else:
                        st.caption("✋ Dispos Cam : Personne")
                        
                    if slot['candidats_voix']:
                        st.caption(f"✋ Dispos Voix : {', '.join(slot['candidats_voix'])}")
                    
                    c1, c2 = st.columns(2)
                    
                    default_cam = [p for p in slot['elu_cam'] if p in equipe_complete]
                    selected_cam = c1.multiselect(
                        "🎥 Qui en Caméra ?", 
                        options=equipe_complete, 
                        default=default_cam,
                        key=f"ms_c_{i}"
                    )
                    slot['elu_cam'] = selected_cam
                    
                    opts_voix = ["Personne"] + equipe_complete
                    idx_voix = opts_voix.index(slot['elu_voix']) if slot['elu_voix'] in opts_voix else 0
                    selected_voix = c2.selectbox(
                        "🎙️ Qui à la Voix ?", 
                        options=opts_voix, 
                        index=idx_voix,
                        key=f"sb_v_{i}"
                    )
                    slot['elu_voix'] = None if selected_voix == "Personne" else selected_voix

            if st.button("💾 Sauvegarder le Casting"):
                data["semaine_prochaine"] = slots_to_edit
                save_data(data)
                st.success("Planning enregistré !")
        else:
            st.warning("Générez d'abord les créneaux.")

    # 4. DIFFUSION
    with tab4:
        st.subheader("📢 Communication")
        
        st.markdown("#### 1. WhatsApp")
        if data.get("semaine_prochaine"):
            link = generer_lien_whatsapp(data["semaine_prochaine"])
            st.info("Cliquez ci-dessous pour envoyer le récap au groupe 'Les filles' :")
            st.markdown(f"### 👉 [Envoyer sur WhatsApp]({link})")
        else:
            st.write("Pas de planning prêt.")
            
        st.divider()
        
        st.markdown("#### 2. Publication App")
        st.write("Rendre le planning visible pour tout le monde sur l'accueil.")
        if st.button("🚀 Publier Officiellement"):
            data["semaine_courante"] = data["semaine_prochaine"]
            data["semaine_prochaine"] = [] 
            save_data(data)
            st.balloons()
            st.success("Le planning est en ligne !")
