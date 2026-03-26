import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_INPUT = os.path.join(BASE_DIR, "data", "json", "donnees_extraites.json")
REPORT_OUTPUT = os.path.join(BASE_DIR, "rapport", "rapport_final.html")
ENV_PATH = os.path.join(BASE_DIR, ".env")

# 1. Configuration
load_dotenv(ENV_PATH)
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def charger_donnees_extraites():
    """Charge le JSON généré par extractor.py"""
    if not os.path.exists(DATA_INPUT):
        raise FileNotFoundError(f"Le fichier '{DATA_INPUT}' n'existe pas. Lancez d'abord l'extraction.")
    with open(DATA_INPUT, "r", encoding="utf-8") as f:
        return json.load(f)

def valider_factures(data_factures):
    """L'agent analyse intelligemment les données extraites"""
    factures_text = json.dumps(data_factures, indent=2)
    
    prompt = f"""Tu es un agent comptable expert. Analyse ces données de factures :
    {factures_text}

    Règles strictes :
    1. Rejeter si total_ttc > 5000€ (Montant suspect)
    2. Rejeter si tva_taux n'est pas 20, 10, 5.5 ou 2.1 (Erreur fiscale)
    3. Rejeter si siret est null ou 'non renseigné' (Fournisseur inconnu)

    Réponds UNIQUEMENT en JSON avec cette structure :
    {{
        "factures_validees": [{{"fournisseur": "...", "montant": 0.0, "raison": "...", "description": "..."}}],
        "factures_rejetees": [{{"fournisseur": "...", "montant": 0.0, "raison": "...", "description": "..."}}],
        "resume": "..."
    }}"""

    response = client.chat.complete(
        model="mistral-small-latest",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)


def generer_html_rapport(data):
    """Génère le rapport visuel inspiré de Sentinel FEC"""
    approuvees = data.get("factures_validees", [])
    rejetees = data.get("factures_rejetees", [])
    resume = data.get("resume", "Analyse terminée.")
    total_traite = len(approuvees) + len(rejetees)

    def create_items_html(items, is_rejetee=False):
        html = ""
        for item in items:
            border_color = "#ee0979" if is_rejetee else "#11998e"
            bg_color = "#fff5f0" if is_rejetee else "#f8f9fa"
            label = "REJETÉ" if is_rejetee else "APPROUVÉ"
            status_color = "#721c24" if is_rejetee else "#155724"
            
            html += f"""
            <div class="facture-item" style="border-left: 5px solid {border_color}; background-color: {bg_color};">
                <div class="facture-details">
                    <h3 style="color: #333; font-size: 16px; margin-bottom: 5px;">{item.get('fournisseur', 'N/A')}</h3>
                    <p style="color: #666; font-size: 14px; margin-bottom: 4px;">{item.get('description', 'Sans description')}</p>
                    <p style="color: #888; font-size: 13px; font-style: italic;">{item.get('raison', '')}</p>
                </div>
                <div style="text-align: right;">
                    <div style="font-weight: bold; font-size: 18px; color: #2c3e50; margin-bottom: 5px;">{item.get('montant', 0):,.2f} €</div>
                    <span style="font-size: 11px; font-weight: bold; color: {status_color}; text-transform: uppercase; letter-spacing: 1px;">{label}</span>
                </div>
            </div>"""
        return html

    html_approuvees = create_items_html(approuvees, False)
    html_rejetees = create_items_html(rejetees, True)

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>Rapport Auditor - Sentinel Style</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8f9fa; color: #333; margin: 0; padding: 40px 20px; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); overflow: hidden; }}
        .header {{ background-color: #2b5797; color: white; padding: 30px; padding-bottom: 15px; text-align: left; }}
        .header h1 {{ font-size: 24px; margin: 0; font-weight: 600; }}
        .header p {{ font-size: 14px; opacity: 0.8; margin-top: 10px; }}
        .content {{ padding: 30px; }}
        .summary-banner {{ background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; border-radius: 4px; font-size: 14px; margin-bottom: 30px; line-height: 1.5; }}
        .stats-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 40px; }}
        .stat-card {{ background: #eef4fb; border: 1px solid #d1e3f8; padding: 8px; border-radius: 6px; text-align: center; }}
        .stat-card .label {{ font-size: 12px; text-transform: uppercase; color: #5b7da3; font-weight: bold; margin-bottom: 10px; display: block; }}
        .stat-card .value {{ font-size: 32px; font-weight: bold; color: #2b5797; }}
        .section-title {{ font-size: 18px; font-weight: 600; text-transform: uppercase; color: #2b5797; border-bottom: 2px solid #eef4fb; padding-bottom: 10px; margin: 40px 0 20px 0; }}
        .facture-item {{ display: flex; justify-content: space-between; align-items: center; padding-left: 20px; padding-right: 20px; margin-bottom: 15px; border-radius: 4px; }}
        .facture-item p, .facture-item h3 {{ margin: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Prototype Agent de Validation & Conformité Factures</h1>
            <p>Contrôle intelligent des flux Factur-X (XML) et PDF — Démo Prototype - Nathalie DEVOGELAERE</p>
        </div>
        <div class="content">
            <div class="summary-banner">
                <strong>Analyse en mode autonome :</strong> {resume}
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <span class="label">Total Traité</span>
                    <div class="value">{total_traite}</div>
                </div>
                <div class="stat-card">
                    <span class="label">Approuvées</span>
                    <div class="value">{len(approuvees)}</div>
                </div>
                <div class="stat-card">
                    <span class="label">Rejetées</span>
                    <div class="value">{len(rejetees)}</div>
                </div>
            </div>

            <div class="section-title">Contrôles validés</div>
            {html_approuvees}

            <div class="section-title">Anomalies détectées</div>
            {html_rejetees}
        </div>
        <div style="padding: 20px; text-align: center; color: #999; font-size: 12px; background: #fdfdfd; border-top: 1px solid #eee;">
            Rapport généré par Agent Auditor © 2026 | Technologie Mistral AI
        </div>
    </div>
</body>
</html>"""

if __name__ == "__main__":
    print("Lancement de l'Agent Auditor...")
    try:
        os.makedirs(os.path.dirname(REPORT_OUTPUT), exist_ok=True)
        data = charger_donnees_extraites()
        resultat = valider_factures(data)
        html = generer_html_rapport(resultat)
        
        with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
            f.write(html)
        
        print(f"Rapport généré avec succès : {REPORT_OUTPUT}")
    except Exception as e:
        print(f"Erreur : {e}")

# import os
# import json
# from mistralai.client import Mistral
# from dotenv import load_dotenv

# # --- CONFIGURATION DES CHEMINS ---
# # On définit la racine du projet par rapport à ce fichier (src/auditeur.py)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# DATA_INPUT = os.path.join(BASE_DIR, "data", "json", "donnees_extraites.json")
# REPORT_OUTPUT = os.path.join(BASE_DIR, "rapport", "rapport_final.html")
# ENV_PATH = os.path.join(BASE_DIR, ".env")


# # 1. Configuration
# load_dotenv(ENV_PATH)
# api_key = os.getenv("MISTRAL_API_KEY")
# client = Mistral(api_key=api_key)

# def charger_donnees_extraites():
#     """Charge le JSON généré par extractor.py"""
#     if not os.path.exists(DATA_INPUT):
#         raise FileNotFoundError(f"Le fichier '{DATA_INPUT}' n'existe pas. Lancez d'abord l'extraction.")
#     with open(DATA_INPUT, "r", encoding="utf-8") as f:
#         return json.load(f)

# def valider_factures(data_factures):
#     """L'agent analyse intelligemment les données extraites"""
#     factures_text = json.dumps(data_factures, indent=2)
    
#     prompt = f"""Tu es un agent comptable expert. Analyse ces données de factures :
#     {factures_text}

#     Règles strictes :
#     1. Rejeter si total_ttc > 5000€ (Montant suspect)
#     2. Rejeter si tva_taux n'est pas 20, 10, 5.5 ou 2.1 (Erreur fiscale)
#     3. Rejeter si siret est null ou 'non renseigné' (Fournisseur inconnu)

#     Réponds UNIQUEMENT en JSON avec cette structure :
#     {{
#         "factures_validees": [{{"fournisseur": "...", "montant": 0.0, "raison": "...", "description": "..."}}],
#         "factures_rejetees": [{{"fournisseur": "...", "montant": 0.0, "raison": "...", "description": "..."}}],
#         "resume": "..."
#     }}"""

#     response = client.chat.complete(
#         model="mistral-small-latest",
#         messages=[{"role": "user", "content": prompt}],
#         response_format={"type": "json_object"}
#     )
#     return json.loads(response.choices[0].message.content)

# def generer_html_rapport(data):
#     """Génère le rapport visuel avec tes styles CSS"""
#     approuvees = data.get("factures_validees", [])
#     rejetees = data.get("factures_rejetees", [])
#     resume = data.get("resume", "Analyse terminée.")

#     def create_items_html(items, is_rejetee=False):
#         html = ""
#         for item in items:
#             status_class = "rejetee" if is_rejetee else ""
#             badge_class = "rejetee" if is_rejetee else "approuvee"
#             icon = "❌" if is_rejetee else "✅"
#             label = "Rejetée" if is_rejetee else "Approuvée"
            
#             html += f"""
#             <div class="facture-item {status_class}">
#                 <div class="facture-icon">{icon}</div>
#                 <div class="facture-details">
#                     <h3>{item.get('fournisseur', 'Inconnu')}</h3>
#                     <p>{item.get('description', 'Facture traitée')}</p>
#                     <p class="raison">{item.get('raison', '')}</p>
#                 </div>
#                 <div style="text-align: right;">
#                     <div class="montant">{item.get('montant', 0):,.2f} €</div>
#                     <div class="badge {badge_class}">{label}</div>
#                 </div>
#             </div>"""
#         return html

#     html_approuvees = create_items_html(approuvees, False)
#     html_rejetees = create_items_html(rejetees, True)

#     # Ton template HTML (simplifié pour la lecture ici, mais garde tes styles complets !)
#     return f"""<!DOCTYPE html>
#     <html>
#     <head>
#         <meta charset="UTF-8">
#         <title>Rapport Agent Comptable</title>
#         <style>
#             body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
#             .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; shadow: 0 2px 10px rgba(0,0,0,0.1); }}
#             .header {{ background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
#             .facture-item {{ display: flex; justify-content: space-between; padding: 15px; border-bottom: 1px solid #eee; margin-bottom: 10px; background: #fafafa; border-left: 5px solid #2ecc71; }}
#             .facture-item.rejetee {{ border-left-color: #e74c3c; background: #fff5f5; }}
#             .montant {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; }}
#             .badge {{ padding: 5px 10px; border-radius: 20px; font-size: 0.8em; color: white; }}
#             .badge.approuvee {{ background: #2ecc71; }}
#             .badge.rejetee {{ background: #e74c3c; }}
#             .raison {{ color: #7f8c8d; font-style: italic; font-size: 0.9em; }}
#         </style>
#     </head>
#     <body>
#         <div class="container">
#             <div class="header"><h1>Audit Agentique Mistral</h1><p>{len(approuvees + rejetees)} factures analysées</p></div>
#             <div style="padding: 15px; background: #eef2f3; border-radius: 5px; margin-bottom: 20px;"><strong>Résumé :</strong> {resume}</div>
#             <h2 style="color: #27ae60;">✅ Approuvées ({len(approuvees)})</h2>
#             {html_approuvees}
#             <h2 style="color: #c0392b; margin-top: 30px;">❌ Rejetées ({len(rejetees)})</h2>
#             {html_rejetees}
#         </div>
#     </body>
#     </html>"""

# if __name__ == "__main__":
#     print("Lancement de l'Agent Comptable...")
#     try:
#         # On s'assure que le dossier reports existe
#         os.makedirs(os.path.dirname(REPORT_OUTPUT), exist_ok=True)

#         data = charger_donnees_extraites()
#         resultat_audit = valider_factures(data)
#         html_final = generer_html_rapport(resultat_audit)
        
#         with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
#             f.write(html_final)
        
#         print(f"Audit terminé ! Le rapport est ici : {REPORT_OUTPUT}")
#         print(f"{len(resultat_audit['factures_validees'])} validées, {len(resultat_audit['factures_rejetees'])} rejetées.")
#     except Exception as e:    
#         print(f"Erreur : {e}")



