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

# --- CSS SIMPLIFIÉ (Pour mobile) ---
st.markdown("""
    <style>
    /* Ajustement des boutons */
    div[data-testid="column"] button {
        width: 100% !important; /* Boutons pleine largeur sur mobile */
    }
    /* Espacement entre les éléments verticaux */
    .block-container {
        padding-top: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# --- FONCTIONS UTILITAIRES ---

def get_monday(date_obj):
    return date_obj - timedelta(days=date_obj.weekday())

def date_to_str(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def str_to_date(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d")

def format_titre_slot(slot):
    short_date = "/".join(slot['date'].split("/")[:2])
    return f"**{slot['jour']} {slot['heure']}** ({short_date})"

def load_data():
    default_data = {
        "weeks": {}, 
        "equipe": ["Julie", "Sarah", "Marie", "Sophie", "Laura"] 
    }
    if not os.path.exists(DATA_FILE):
        data = default_data
    else:
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                if "weeks" not in data: data["weeks"] = {}
                if "equipe" not in data: data["equipe"] = default_data["equipe"]
        except:
            data = default_data
    
    if data.get("equipe"):
        data["equipe"] = sorted(list(set(data["equipe"])))
    return data

def save_data(data):
    if data.get("equipe"):
        data["equipe"] = sorted(list(set(data["equipe"])))
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
        slots.append({"id": f"{d_str}-matin", "jour": jour, "date": d_str, "heure": heure_m, "actif": actif_m, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "matin"})
        actif_s = True if i < 5 else False
        slots.append({"id": f"{d_str}-soir", "jour": jour, "date": d_str, "heure": "18:30", "actif": actif_s, "candidats_cam": [], "candidats_voix": [], "elu_cam": [], "elu_voix": [], "type": "soir"})
        curr += timedelta(days=1)
    return slots

def generer_lien_whatsapp(slots):
    slots_actifs = [s for s in slots if s.get('actif', True)]
    if not slots_actifs: return "https://wa.me/"
    
    lines = []
    lines.append("*👗 LIVE PLANNER - MONA DRESS 👗*")
    lines.append("")
    
    for slot in slots_actifs:
        short_date = "/".join(slot['date'].split("/")[:2])
        header = f"🗓️ *{slot['jour']} {slot['heure']}* ({short_date})"
        
        list_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
        list_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []
        
        cam = ", ".join(list_cam) if list_cam else "❓"
        voix = ", ".join(list_voix) if list_voix else "❓"
        
        lines.append(header)
        lines.append(f"🎥 Cam: {cam}")
        lines.append(f"🎙️ Voix: {voix}")
        lines.append("")
    
    lines.append("Merci les filles ! ✨")
    
    # CORRECTION : On prépare le texte AVANT de le mettre dans l'URL
    full_text = "\n".join(lines)
    encoded = urllib.parse.quote(full_text)
    
    return f"https://wa.me/?text={encoded}"
    
# --- CHARGEMENT ---
data = load_data()
cookie_manager = stx.CookieManager()

# --- GESTION UTILISATEUR & COOKIES ---
# On récupère le cookie au démarrage
cookie_user = cookie_manager.get(cookie="mona_artiste_name")
current_artiste = None

# Barre latérale toujours visible pour navigation
st.sidebar.title("Mona Backstage")
mode_view = st.sidebar.radio("Navigation", ["Artiste", "Boss"])

# LOGIQUE DE DÉTECTION ARTISTE
# Si on est en mode artiste, on essaie de trouver qui c'est
if mode_view == "Artiste":
    # 1. Est-ce qu'on a déjà un cookie valide ?
    if cookie_user and cookie_user in data["equipe"]:
        current_artiste = cookie_user
    
    # 2. Si non (ou si on veut changer), on affiche le sélecteur dans la sidebar aussi
    # pour permettre de changer d'identité facilement
    idx = data["equipe"].index(current_artiste) if current_artiste else 0
    selected_sidebar = st.sidebar.selectbox("Identité actuelle :", data["equipe"], index=idx)
    
    # Si changement manuel dans la sidebar
    if selected_sidebar != current_artiste:
        current_artiste = selected_sidebar
        cookie_manager.set("mona_artiste_name", selected_sidebar, expires_at=datetime.now() + timedelta(days=30))
        # On force un petit reload pour être sûr
        time.sleep(0.5)
        st.rerun()

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
    
    # --- PAGE DE CONNEXION (SI PAS IDENTIFIÉ) ---
    if not current_artiste:
        st.title("👋 Bienvenue !")
        st.info("Pour commencer, dis-nous qui tu es :")
        
        # Grand sélecteur central (Plus ergonomique que sidebar au premier lancement)
        user_choice = st.selectbox("Je suis :", ["Choisir..."] + data["equipe"])
        
        if user_choice != "Choisir...":
            cookie_manager.set("mona_artiste_name", user_choice, expires_at=datetime.now() + timedelta(days=30))
            st.success(f"Enchanté {user_choice} ! Chargement...")
            time.sleep(1)
            st.rerun()
        
        st.stop() # On arrête l'affichage ici tant qu'on n'a pas choisi

    # --- PAGE PRINCIPALE ARTISTE ---
    st.title(f"👋 Hello {current_artiste}")
    
    tab_visu, tab_voeux = st.tabs(["📅 Planning", "✨ Mes Vœux"])
    
    # --- TAB 1 : PLANNING ---
    with tab_visu:
        key_week = date_to_str(monday_current)
        slots_week = data["weeks"].get(key_week, [])
        slots_visibles = [s for s in slots_week if s.get('actif', True)]
        
        if not slots_visibles:
            st.info("Planning non publié.")
        else:
            for slot in slots_visibles:
                with st.container(border=True):
                    # Layout vertical mobile
                    st.markdown(format_titre_slot(slot))
                    
                    l_cam = slot['elu_cam'] if isinstance(slot['elu_cam'], list) else []
                    l_voix = slot['elu_voix'] if isinstance(slot['elu_voix'], list) else [slot['elu_voix']] if slot['elu_voix'] else []
                    cam_txt = ", ".join(l_cam) if l_cam else "..."
                    voix_txt = ", ".join(l_voix) if l_voix else "..."
                    
                    st.write(f"🎥 **Cam:** {cam_txt}")
                    st.write(f"🎙️ **Voix:** {voix_txt}")

    # --- TAB 2 : VŒUX ---
    with tab_voeux:
        st.write("Disponibilités :")
        weeks_to_show = [(date_to_str(monday_next), f"Semaine Prochaine"), (date_to_str(monday_next_2), f"Dans 2 semaines")]
        if not any(wk[0] in data["weeks"] for wk in weeks_to_show):
            st.warning("⏳ Pas de créneaux ouverts.")
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
                            is_dispo = (current_artiste in slot['candidats_cam']) or (current_artiste in slot['candidats_voix'])
                            new_state = st.checkbox(label_case, value=is_dispo, key=f"d_{slot['id']}")
                            if new_state:
                                if current_artiste not in slot['candidats_cam']: slot['candidats_cam'].append(current_artiste)
                                if current_artiste not in slot['candidats_voix']: slot['candidats_voix'].append(current_artiste)
                            else:
                                if current_artiste in slot['candidats_cam']: slot['candidats_cam'].remove(current_artiste)
                                if current_artiste in slot['candidats_voix']: slot['candidats_voix'].remove(current_artiste)
                        st.divider()

                if st.form_submit_button("✅ Envoyer", use_container_width=True):
                    save_data(data)
                    st.balloons()
                    st.success("Envoyé !")

# ==========================================
#              VUE BOSS
# ==========================================
elif mode_view == "Boss":
    st.title("🕶️ Espace Boss")
    
    choix_admin = st.selectbox("Semaine cible :", list(choix_semaines.keys()))
    selected_week_key = choix_semaines[choix_admin]
    
    if selected_week_key not in data["weeks"]:
        slots_current_work = generer_structure_vide(str_to_date(selected_week_key))
    else:
        slots_current_work = data["weeks"][selected_week_key]
        
    t1, t2, t3, t4 = st.tabs(["🛠️ Structure", "🎬 Casting", "📢 Whatsapp", "👥 Équipe"])
    
    # --- STRUCTURE (Verticale) ---
    with t1:
        st.caption("Configurer les horaires")
        for i in range(0, len(slots_current_work), 2):
            slot_m = slots_current_work[i]
            slot_s = slots_current_work[i+1]
            short_date = "/".join(slot_m['date'].split("/")[:2])
            
            with st.container(border=True):
                st.markdown(f"**{slot_m['jour']}** ({short_date})")
                
                # MIDI
                st.markdown("---")
                is_active_m = st.toggle("Midi", value=slot_m.get('actif', True), key=f"tg_{slot_m['id']}")
                if is_active_m: 
                    st.text_input("Heure Midi", value=slot_m['heure'], key=f"hm_{slot_m['id']}")
                else: 
                    st.caption("💤 Off")
                
                # SOIR (En dessous)
                st.markdown("---")
                is_active_s = st.toggle("Soir", value=slot_s.get('actif', True), key=f"tg_{slot_s['id']}")
                if is_active_s: 
                    st.text_input("Heure Soir", value=slot_s['heure'], key=f"hs_{slot_s['id']}")
                else: 
                    st.caption("💤 Off")

        if st.button("💾 Enregistrer Structure", type="primary", use_container_width=True):
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
            st.success("Sauvegardé !")

    # --- CASTING (Vertical) ---
    with t2:
        active_slots = [s for s in slots_current_work if s.get('actif', True)]
        if not active_slots: st.warning("Activer d'abord des créneaux.")
        elif selected_week_key not in data["weeks"]: st.warning("Sauvegarder la structure.")
        else:
            for s in active_slots:
                with st.expander(format_titre_slot(s) + f" - ({len(s['candidats_cam'])})", expanded=True):
                    
                    # SECTION CAMERA
                    curr_cam = s['elu_cam'] if isinstance(s['elu_cam'], list) else []
                    s['elu_cam'] = st.multiselect("🎥 Caméra", data["equipe"], default=[p for p in curr_cam if p in data["equipe"]], key=f"mc_{s['id']}")
                    if s['candidats_cam']:
                        st.caption(f"✋ Dispos: {', '.join(s['candidats_cam'])}")
                    
                    st.write("") # Espace
                    
                    # SECTION VOIX (En dessous)
                    curr_voix = s['elu_voix'] if isinstance(s['elu_voix'], list) else [s['elu_voix']] if s['elu_voix'] else []
                    s['elu_voix'] = st.multiselect("🎙️ Voix", data["equipe"], default=[p for p in curr_voix if p in data["equipe"]], key=f"mv_{s['id']}")
            
            if st.button("💾 Sauvegarder Casting", use_container_width=True):
                save_data(data)
                st.success("Casting OK !")

    # --- DIFFUSION ---
    with t3:
        if selected_week_key in data["weeks"]:
            link = generer_lien_whatsapp(data["weeks"][selected_week_key])
            st.markdown(f"### [👉 WhatsApp]({link})")
        else: st.error("Sauvegarder structure.")

    # --- ÉQUIPE (Vertical) ---
    with t4:
        st.subheader("Team")
        
        # 1. FORMULAIRE VERTICAL
        with st.form("add_member", clear_on_submit=True):
            new = st.text_input("Nouveau membre", placeholder="Prénom")
            if st.form_submit_button("Ajouter", use_container_width=True):
                if new:
                    data["equipe"].append(new)
                    save_data(data)
                    st.rerun()

        st.markdown("---")
        
        # 2. LISTE
        for i, member in enumerate(data["equipe"]):
            with st.container(border=True):
                col_txt, col_act = st.columns([4, 1])
                with col_txt:
                    st.markdown(f"**{member}**")
                with col_act:
                    if st.button("❌", key=f"pre_del_{i}"):
                        st.session_state[f"confirm_del_{i}"] = True
                
                if st.session_state.get(f"confirm_del_{i}", False):
                    st.write("Supprimer ?")
                    if st.button("Oui", key=f"y_{i}", type="primary", use_container_width=True):
                        data["equipe"].pop(i)
                        save_data(data)
                        st.rerun()
                    if st.button("Non", key=f"n_{i}", use_container_width=True):
                        st.session_state[f"confirm_del_{i}"] = False
                        st.rerun()
