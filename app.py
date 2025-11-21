import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import urllib.parse

# --- CONFIGURATION ---
st.set_page_config(page_title="Mona Backstage", layout="centered", page_icon="👗")
DATA_FILE = "mona_planning_db.json"

# --- FONCTIONS ---

def load_data():
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
            if "equipe" not in data: data["equipe"] = default_data["equipe"]
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

# Nouvelle fonction : Génère un brouillon complet pour l'éditeur
def generer_brouillon_semaine(date_debut):
    structure = []
    jours = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
    current_date = date_debut

    for i, jour in enumerate(jours):
        date_str = current_date.strftime("%d/%m/%Y")
        
        # Configuration par défaut selon le jour
        slots_du_jour = []
        
        # Slot 1 (Matin)
        actif_matin = True if i < 6 else False # Actif Lundi-Samedi
        heure_matin = "10:00" if i == 5 else "12:00" # 10h le samedi, 12h sinon
        
        slots_du_jour.append({
            "type": "matin", "actif": actif_matin, "heure": heure_matin
        })

        # Slot 2 (Soir)
        actif_soir = True if i < 5 else False # Actif Lundi-Vendredi
        slots_du_jour.append({
            "type": "soir", "actif": actif_soir, "heure": "18:30"
        })

        structure.append({
            "jour": jour,
            "date": date_str,
            "slots": slots_du_jour
        })
        current_date += timedelta(days=1)
        
    return structure

def generer_lien_whatsapp(semaine_data):
    text = "*👗 LIVE PLANNER - MONA DRESS 👗*\n_Planning Semaine Prochaine_\n\n"
    for slot in semaine_data:
        cam = ", ".join(slot['elu_cam']) if slot['elu_cam'] else "❓"
        voix = slot['elu_voix'] if slot['elu_voix'] else "❓"
        text += f"🗓️ *{slot['jour']} {slot['date']} à {slot['heure']}*\n🎥 Cam: {cam}\n🎙️ Voix: {voix}\n\n"
    text += "Merci les filles ! ✨"
    return f"https://wa.me/?text={urllib.parse.quote(text)}"

# --- INTERFACE ---

data = load_data()

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

# --- VISUALISATION ---
if user_role in ["Visiteur", "Intervenante"]:
    st.header("📅 Planning")
    choix = st.radio("Période :", ["Semaine Courante", "Semaine Prochaine"], horizontal=True, label_visibility="collapsed")
    key = "semaine_courante" if choix == "Semaine Courante" else "semaine_prochaine"
    
    if not data.get(key):
        st.info("⏳ Planning non disponible.")
    else:
        for slot in data[key]:
            with st.container():
                st.markdown(f"#### {slot['jour']} {slot['date']}")
                st.caption(f"⏰ {slot['heure']}")
                c1, c2 = st.columns(2)
                c1.success(f"🎥 **{', '.join(slot['elu_cam']) if slot['elu_cam'] else '...'}**")
                c2.warning(f"🎙️ **{slot['elu_voix'] if slot['elu_voix'] else '...'}**")
                st.divider()

# --- DISPOS ---
if user_role == "Intervenante" and username:
    st.header(f"👋 Hello {username}")
    if not data.get("semaine_prochaine"):
        st.error("Planning fermé.")
    else:
        with st.form("dispo"):
            slots = data["semaine_prochaine"]
            for slot in slots:
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
            if st.form_submit_button("✅ Enregistrer"):
                data["semaine_prochaine"] = slots
                save_data(data)
                st.success("Dispos enregistrées !")

# --- ADMIN ---
if user_role == "Admin":
    st.header("🔧 Backstage Admin")
    t1, t2, t3, t4 = st.tabs(["👥 Équipe", "📅 Création (Éditeur)", "✅ Casting", "🚀 Publier"])
    
    # TAB 1 : ÉQUIPE
    with t1:
        st.write(f"Équipe : {', '.join(data['equipe'])}")
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

    # TAB 2 : CRÉATION AVEC ÉDITEUR
    with t2:
        st.subheader("Définir les créneaux")
        
        # Initialisation du brouillon dans la session
        if "draft_schedule" not in st.session_state:
            st.session_state["draft_schedule"] = None

        # Bouton pour lancer/reset le brouillon
        next_mon = get_next_monday()
        if st.button(f"🔄 Initialiser la semaine du {next_mon.strftime('%d/%m')}"):
            st.session_state["draft_schedule"] = generer_brouillon_semaine(next_mon)
            st.rerun()

        # Affichage de l'éditeur si le brouillon existe
        if st.session_state["draft_schedule"]:
            st.info("Cochez les lives actifs et modifiez les heures si besoin.")
            
            # On stocke les résultats finaux ici
            final_slots_to_create = []
            
            # Parcours du brouillon
            for day_idx, day_data in enumerate(st.session_state["draft_schedule"]):
                with st.expander(f"**{day_data['jour']}** {day_data['date']}", expanded=True):
                    
                    # Pour chaque slot du jour (Matin / Soir)
                    for slot_idx, slot in enumerate(day_data["slots"]):
                        col_check, col_time, col_label = st.columns([1, 2, 3])
                        
                        # Clé unique pour chaque widget
                        ukey = f"{day_idx}_{slot_idx}"
                        
                        # 1. Case à cocher (Activé/Désactivé)
                        is_active = col_check.checkbox("Actif", value=slot["actif"], key=f"chk_{ukey}")
                        
                        # 2. Champ Heure (affiché seulement si actif)
                        if is_active:
                            new_time = col_time.text_input("Heure", value=slot["heure"], key=f"time_{ukey}", label_visibility="collapsed")
                            col_label.success(f"✅ Live prévu à {new_time}")
                            
                            # On prépare l'objet final pour la sauvegarde
                            final_slots_to_create.append({
                                "id": f"{day_data['date']}-{new_time.replace(':','h')}",
                                "jour": day_data['jour'],
                                "date": day_data['date'],
                                "heure": new_time,
                                "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": None
                            })
                        else:
                            col_time.empty() # Vide
                            col_label.caption("💤 Pas de live")
                            
            st.divider()
            
            # Bouton de validation finale
            if st.button("💾 Valider et Créer le Planning Officiel", type="primary"):
                data["semaine_prochaine"] = final_slots_to_create
                save_data(data)
                # On nettoie la session
                st.session_state["draft_schedule"] = None
                st.success(f"{len(final_slots_to_create)} créneaux créés ! Allez dans l'onglet Casting.")
                st.rerun()

    # TAB 3 : CASTING
    with t3:
        if not data.get("semaine_prochaine"):
            st.warning("Aucun planning créé.")
        else:
            slots = data["semaine_prochaine"]
            for i, s in enumerate(slots):
                with st.expander(f"{s['jour']} {s['heure']} - ({len(s['candidats_cam'])+len(s['candidats_voix'])} candidatures)"):
                    # Edition heure de dernière minute
                    s['heure'] = st.text_input("Heure", s['heure'], key=f"edit_h_{i}")
                    
                    c1, c2 = st.columns(2)
                    # Cam (Multi)
                    s['elu_cam'] = c1.multiselect("🎥 Cam", data["equipe"], default=[p for p in s['elu_cam'] if p in data["equipe"]], key=f"ms_{i}")
                    st.caption(f"Dispos: {', '.join(s['candidats_cam'])}")
                    
                    # Voix (Single)
                    idx = (["..."]+data["equipe"]).index(s['elu_voix']) if s['elu_voix'] in data["equipe"] else 0
                    sel = c2.selectbox("🎙️ Voix", ["..."]+data["equipe"], index=idx, key=f"sb_{i}")
                    s['elu_voix'] = sel if sel != "..." else None
                    st.caption(f"Dispos: {', '.join(s['candidats_voix'])}")
            
            if st.button("Sauvegarder le Casting"):
                data["semaine_prochaine"] = slots
                save_data(data)
                st.success("Casting OK !")

    # TAB 4 : PUBLICATION
    with t4:
        if data.get("semaine_prochaine"):
            st.markdown(f"[👉 WhatsApp]({generer_lien_whatsapp(data['semaine_prochaine'])})")
            if st.button("🚀 Mettre en ligne (Semaine Courante)"):
                data["semaine_courante"] = data["semaine_prochaine"]
                data["semaine_prochaine"] = []
                save_data(data)
                st.balloons()
                st.rerun()
