import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Live Planner", layout="centered", page_icon="📅")
DATA_FILE = "planning_db_v2.json"

# --- FONCTIONS UTILITAIRES ---

def load_data():
    # Structure par défaut avec une liste d'équipe initiale
    default_data = {
        "semaine_prochaine": [], 
        "semaine_courante": [],
        "equipe": ["Julie", "Sarah", "Marie", "Sophie"] # Liste par défaut
    }
    
    if not os.path.exists(DATA_FILE):
        return default_data
    
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            # S'assurer que la clé équipe existe (si mise à jour depuis v1)
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
        
        # Structure : elu_cam est maintenant une LISTE pour en mettre plusieurs
        base_slot = {
            "jour": jour, 
            "date": date_str, 
            "candidats_cam": [], 
            "candidats_voix": [], 
            "elu_cam": [], # Liste vide pour plusieurs personnes
            "elu_voix": None # Une seule personne (ou None)
        }

        if i < 5: # Lundi à Vendredi
            s1 = base_slot.copy()
            s1.update({"id": f"{date_str}-12h", "heure": "12:00"})
            slots.append(s1)
            
            s2 = base_slot.copy()
            s2.update({"id": f"{date_str}-18h30", "heure": "18:30", "elu_cam": [], "candidats_cam": [], "candidats_voix": []}) # Reset lists for copy safety
            slots.append(s2)
            
        elif i == 5: # Samedi
            s3 = base_slot.copy()
            s3.update({"id": f"{date_str}-10h", "heure": "10:00", "elu_cam": [], "candidats_cam": [], "candidats_voix": []})
            slots.append(s3)
        
        current_date += timedelta(days=1)
    return slots

def generer_lien_whatsapp(semaine_data):
    text = "*📅 PLANNING LIVES SEMAINE PROCHAINE 📅*\n\n"
    for slot in semaine_data:
        # Gestion affichage multiple pour Caméra
        if slot['elu_cam']:
            cam_names = ", ".join(slot['elu_cam'])
        else:
            cam_names = "❓"
            
        voix = slot['elu_voix'] if slot['elu_voix'] else "❓"
        
        text += f"🔴 *{slot['jour']} {slot['date']} à {slot['heure']}*\n"
        text += f"🎥 Cam: {cam_names}\n🎙️ Voix: {voix}\n\n"
    
    text += "Merci la team ! 💪"
    encoded_text = urllib.parse.quote(text)
    return f"https://wa.me/?text={encoded_text}"

# --- INTERFACE ---

data = load_data()
st.title("📱 Gestion Planning Live")

# MENU LATÉRAL
st.sidebar.header("Connexion")
user_role = st.sidebar.selectbox("Qui êtes-vous ?", ["Visiteur", "Intervenante", "Admin"])

username = None
if user_role == "Intervenante":
    # Choix parmi la liste gérée par l'admin
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
        st.info("Planning non disponible pour le moment.")
    else:
        for slot in data[key_data]:
            with st.container():
                # Card style
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
    st.write("Cochez vos dispos pour la **Semaine Prochaine** :")
    
    if not data.get("semaine_prochaine"):
        st.error("L'admin n'a pas encore ouvert le planning.")
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
                
                # Logique de mise à jour des listes candidates
                if new_cam and username not in slot['candidats_cam']:
                    slot['candidats_cam'].append(username)
                elif not new_cam and username in slot['candidats_cam']:
                    slot['candidats_cam'].remove(username)
                    
                if new_voix and username not in slot['candidats_voix']:
                    slot['candidats_voix'].append(username)
                elif not new_voix and username in slot['candidats_voix']:
                    slot['candidats_voix'].remove(username)
                
                st.write("") # Spacer

            submitted = st.form_submit_button("✅ Enregistrer mes disponibilités", use_container_width=True)
            if submitted:
                data["semaine_prochaine"] = slots_updated
                save_data(data)
                st.success("C'est enregistré !")

# --- ONGLET 3: ADMIN ---
if user_role == "Admin":
    st.header("🔧 Espace Admin")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Équipe", "📅 Création", "✅ Validation", "🚀 Publier"])
    
    # 1. GESTION ÉQUIPE
    with tab1:
        st.subheader("Gérer les intervenantes")
        
        # Afficher l'équipe actuelle
        st.write("Membres actuels :")
        st.write(", ".join(data["equipe"]))
        
        col_add, col_del = st.columns(2)
        
        with col_add:
            new_member = st.text_input("Ajouter un prénom")
            if st.button("Ajouter"):
                if new_member and new_member not in data["equipe"]:
                    data["equipe"].append(new_member)
                    save_data(data)
                    st.rerun()
        
        with col_del:
            del_member = st.selectbox("Supprimer quelqu'un", ["Choisir..."] + data["equipe"])
            if st.button("Supprimer"):
                if del_member != "Choisir...":
                    data["equipe"].remove(del_member)
                    save_data(data)
                    st.rerun()

    # 2. CRÉATION PLANNING
    with tab2:
        st.subheader("Préparer semaine prochaine")
        next_monday = get_next_monday()
        st.info(f"Semaine du Lundi {next_monday.strftime('%d/%m/%Y')}")
        
        if st.button("1. Générer les créneaux standards"):
            data["semaine_prochaine"] = generer_slots_par_defaut(next_monday)
            save_data(data)
            st.success("Créneaux générés !")
            st.rerun()
            
        if data.get("semaine_prochaine"):
            if st.button("🗑️ Effacer le brouillon"):
                data["semaine_prochaine"] = []
                save_data(data)
                st.rerun()

    # 3. VALIDATION (ATTRIBUTION)
    with tab3:
        st.subheader("Attribuer les rôles")
        if data.get("semaine_prochaine"):
            slots_to_edit = data["semaine_prochaine"]
            equipe_complete = data["equipe"]
            
            for i, slot in enumerate(slots_to_edit):
                # On compte les candidats pour l'affichage du header
                nb_cand = len(slot['candidats_cam']) + len(slot['candidats_voix'])
                color_status = "🟢" if nb_cand > 0 else "🔴"
                
                with st.expander(f"{color_status} {slot['jour']} - {slot['heure']} ({nb_cand} dispos)"):
                    
                    # MODIFICATION HEURE
                    col_h, col_x = st.columns([1, 3])
                    new_time = col_h.text_input("Horaire", value=slot['heure'], key=f"t_{i}")
                    slot['heure'] = new_time
                    
                    # Affichage des disponibilités déclarées
                    if slot['candidats_cam']:
                        st.caption(f"✋ Dispos Caméra : {', '.join(slot['candidats_cam'])}")
                    else:
                        st.caption("✋ Dispos Caméra : Personne")
                        
                    if slot['candidats_voix']:
                        st.caption(f"✋ Dispos Voix : {', '.join(slot['candidats_voix'])}")
                    
                    c1, c2 = st.columns(2)
                    
                    # SÉLECTION CAMÉRA (MULTI-SELECT)
                    # On pré-remplit avec ce qui est sauvegardé (elu_cam est une liste)
                    default_cam = [p for p in slot['elu_cam'] if p in equipe_complete]
                    selected_cam = c1.multiselect(
                        "🎥 Qui en Caméra ?", 
                        options=equipe_complete, 
                        default=default_cam,
                        key=f"ms_c_{i}"
                    )
                    slot['elu_cam'] = selected_cam
                    
                    # SÉLECTION VOIX (SINGLE SELECT)
                    opts_voix = ["Personne"] + equipe_complete
                    # On trouve l'index de l'élu actuel
                    idx_voix = opts_voix.index(slot['elu_voix']) if slot['elu_voix'] in opts_voix else 0
                    
                    selected_voix = c2.selectbox(
                        "🎙️ Qui à la Voix ?", 
                        options=opts_voix, 
                        index=idx_voix,
                        key=f"sb_v_{i}"
                    )
                    slot['elu_voix'] = None if selected_voix == "Personne" else selected_voix

            if st.button("💾 Sauvegarder le Planning Final"):
                data["semaine_prochaine"] = slots_to_edit
                save_data(data)
                st.success("Planning mis à jour !")
        else:
            st.warning("Rien à valider. Générez d'abord les créneaux.")

    # 4. ACTIONS & WHATSAPP
    with tab4:
        st.subheader("Diffusion")
        
        st.markdown("#### 1. WhatsApp")
        if data.get("semaine_prochaine"):
            link = generer_lien_whatsapp(data["semaine_prochaine"])
            st.info("Cliquez ci-dessous pour envoyer le récap dans le groupe :")
            st.markdown(f"### 👉 [Ouvrir WhatsApp]({link})")
        else:
            st.write("Pas de planning futur à envoyer.")
            
        st.divider()
        
        st.markdown("#### 2. Publication Officielle")
        st.write("Une fois envoyé sur WhatsApp, publiez le planning sur l'app pour que tout le monde voie la semaine en cours.")
        if st.button("🚀 Rendre public (Passer en semaine courante)"):
            data["semaine_courante"] = data["semaine_prochaine"]
            data["semaine_prochaine"] = [] 
            save_data(data)
            st.balloons()
            st.success("C'est en ligne !")
