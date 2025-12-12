# 👗 Mona Backstage - Application de Planning

Application de gestion de planning d'équipe (Lives, Casting, Dispos) développée avec **Streamlit**.

## 📋 Prérequis

*   **Python 3.8** ou supérieur installé sur la machine.
*   Un système d'exploitation Linux, Mac ou Windows.

## 🚀 Installation pas à pas

### 1. Préparer le dossier
Crée un dossier pour l'application et place ton fichier principal (ex: `app.py`) à l'intérieur.

Ouvre un terminal dans ce dossier.

### 2. Créer l'environnement virtuel (venv)
Cela permet d'isoler les bibliothèques du projet pour ne pas perturber ton système.

**Sous Linux / Mac :**
```bash
python3 -m venv venv
```

**Sous Windows :**
```cmd
python -m venv venv
```

### 3. Activer l'environnement virtuel
Une fois activé, le nom `(venv)` devrait apparaître au début de la ligne de commande.

**Sous Linux / Mac :**
```bash
source venv/bin/activate
```

**Sous Windows :**
```cmd
venv\Scripts\activate
```

### 4. Installer les dépendances
Tu as deux options.

**Option A (Recommandée) : Créer un fichier requirements.txt**
Crée un fichier nommé `requirements.txt` et colle ceci dedans :
```text
streamlit
pandas
extra-streamlit-components
```
Puis lance la commande :
```bash
pip install -r requirements.txt
```

**Option B (Manuelle) :**
Tape directement dans le terminal :
```bash
pip install streamlit pandas extra-streamlit-components
```

---

## ▶️ Lancer l'application

Toujours avec l'environnement virtuel activé (`source venv/bin/activate`), lance la commande :

```bash
streamlit run app.py
```
*(Remplace `app.py` par le nom réel de ton fichier python si différent)*

L'application s'ouvrira automatiquement dans ton navigateur à l'adresse : `http://localhost:8501`.

---

## 📂 Structure des fichiers

*   `app.py` : Le code source de l'application.
*   `mona_db_v3.json` : La base de données (créée automatiquement au premier lancement). **Ne pas supprimer**.
*   `venv/` : Dossier contenant les bibliothèques Python (ne pas toucher).
*   `requirements.txt` : Liste des dépendances.

## ⚠️ Notes importantes

1.  **Sauvegarde :** Toutes les données (équipe, plannings) sont stockées dans `mona_db_v3.json`. Pense à faire une copie de ce fichier de temps en temps par sécurité.
2.  **Mise à jour du code :** Si tu modifies le code, il suffit de rafraîchir la page web (F5) pour voir les changements (si tu as laissé le mode "Run on save" actif).
3.  **Arrêter l'app :** Dans le terminal, fais `Ctrl + C`.

## 🛠️ Dépannage rapide

*   **Erreur `ModuleNotFoundError`** : Tu as oublié d'activer le venv ou d'installer les dépendances (`pip install...`).
*   **Problème de Cookies** : Si l'identification ne tient pas, vérifie que tu n'es pas en navigation privée stricte qui bloque les cookies tiers.
