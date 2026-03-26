import os
import json
from mistralai.client import Mistral
from dotenv import load_dotenv

# --- CONFIGURATION DES CHEMINS ---
# On définit la racine du projet par rapport à ce fichier (src/auditeur.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_INPUT = os.path.join(BASE_DIR, "data", "json", "donnees_extraites.json")
REPORT_OUTPUT = os.path.join(BASE_DIR, "rapport", "rapport_final.html")
ENV_PATH = os.path.join(BASE_DIR, ".env")


# 1. Configuration
load_dotenv(ENV_PATH)
api_key = os.getenv("MISTRAL_API_KEY")
client = Mistral(api_key=api_key)

def charger_donnees_extraites():
    """Charge le JSON généré par extract_invoices.py"""
    if not os.path.exists("DATA_INPUT"):
        raise FileNotFoundError("Le fichier '{DATA_INPUT}' n'existe pas. Lancez d'abord l'extraction.")
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
    """Génère le rapport visuel avec tes styles CSS"""
    approuvees = data.get("factures_validees", [])
    rejetees = data.get("factures_rejetees", [])
    resume = data.get("resume", "Analyse terminée.")

    def create_items_html(items, is_rejetee=False):
        html = ""
        for item in items:
            status_class = "rejetee" if is_rejetee else ""
            badge_class = "rejetee" if is_rejetee else "approuvee"
            icon = "❌" if is_rejetee else "✅"
            label = "Rejetée" if is_rejetee else "Approuvée"
            
            html += f"""
            <div class="facture-item {status_class}">
                <div class="facture-icon">{icon}</div>
                <div class="facture-details">
                    <h3>{item.get('fournisseur', 'Inconnu')}</h3>
                    <p>{item.get('description', 'Facture traitée')}</p>
                    <p class="raison">{item.get('raison', '')}</p>
                </div>
                <div style="text-align: right;">
                    <div class="montant">{item.get('montant', 0):,.2f} €</div>
                    <div class="badge {badge_class}">{label}</div>
                </div>
            </div>"""
        return html

    html_approuvees = create_items_html(approuvees, False)
    html_rejetees = create_items_html(rejetees, True)

    # Ton template HTML (simplifié pour la lecture ici, mais garde tes styles complets !)
    return f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Rapport Agent Comptable</title>
        <style>
            body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; }}
            .container {{ max-width: 800px; margin: auto; background: white; padding: 20px; border-radius: 10px; shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: #667eea; color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }}
            .facture-item {{ display: flex; justify-content: space-between; padding: 15px; border-bottom: 1px solid #eee; margin-bottom: 10px; background: #fafafa; border-left: 5px solid #2ecc71; }}
            .facture-item.rejetee {{ border-left-color: #e74c3c; background: #fff5f5; }}
            .montant {{ font-weight: bold; font-size: 1.2em; color: #2c3e50; }}
            .badge {{ padding: 5px 10px; border-radius: 20px; font-size: 0.8em; color: white; }}
            .badge.approuvee {{ background: #2ecc71; }}
            .badge.rejetee {{ background: #e74c3c; }}
            .raison {{ color: #7f8c8d; font-style: italic; font-size: 0.9em; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header"><h1>Audit Agentique Mistral</h1><p>{len(approuvees + rejetees)} factures analysées</p></div>
            <div style="padding: 15px; background: #eef2f3; border-radius: 5px; margin-bottom: 20px;"><strong>Résumé :</strong> {resume}</div>
            <h2 style="color: #27ae60;">✅ Approuvées ({len(approuvees)})</h2>
            {html_approuvees}
            <h2 style="color: #c0392b; margin-top: 30px;">❌ Rejetées ({len(rejetees)})</h2>
            {html_rejetees}
        </div>
    </body>
    </html>"""

if __name__ == "__main__":
    print("🚀 Lancement de l'Agent Comptable...")
    try:
        # On s'assure que le dossier reports existe
        os.makedirs(os.path.dirname(REPORT_OUTPUT), exist_ok=True)

        data = charger_donnees_extraites()
        resultat_audit = valider_factures(data)
        html_final = generer_html_rapport(resultat_audit)
        
        with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
            f.write(html_final)
        
        print(f"✨ Audit terminé ! Le rapport est ici : {REPORT_OUTPUT}")
        print(f"📊 {len(resultat_audit['factures_validees'])} validées, {len(resultat_audit['factures_rejetees'])} rejetées.")
    except Exception as e:    
        print(f"💥 Erreur : {e}")




# import os
# import json
# import pandas as pd
# from mistralai.client import Mistral
# from dotenv import load_dotenv

# # Charger les variables d'environnement
# load_dotenv()

# # Initialiser le client Mistral
# api_key = os.getenv("MISTRAL_API_KEY")
# client = Mistral(api_key=api_key)

# # Charger les données
# df_factures = pd.read_csv("factures.csv")

# def valider_factures():
#     """L'agent valide autonomiquement les factures"""
    
#     # Préparer les données
#     factures_text = df_factures.to_string()
    
#     # Prompt pour l'agent
#     prompt = f"""Tu es un agent comptable expert et autonome.

# Voici les factures à valider:
# {factures_text}

# Pour CHAQUE facture, tu dois autonomiquement:
# 1. Valider le montant (alerte si > 5000€)
# 2. Vérifier le fournisseur (alerte si inconnu)
# 3. DÉCIDER d'approuver ou rejeter
# 4. Justifier ta décision

# Sois strict. Rejette les anomalies.

# Réponds au format JSON VALIDE avec cette structure exacte:
# {{
#     "factures_validees": [
#         {{"id": 1, "fournisseur": "nom", "description": "...", "montant": 450.50, "raison": "..."}},
#         ...
#     ],
#     "factures_rejetees": [
#         {{"id": 5, "fournisseur": "nom", "description": "...", "montant": 150.00, "raison": "..."}}
#     ],
#     "resume": "Résumé général..."
# }}
# """
    
#     # Appeler l'API Mistral
#     message = client.chat.complete(
#         model="mistral-small-latest",
#         messages=[
#             {"role": "user", "content": prompt}
#         ]
#     )
    
#     # Récupérer le résultat
#     resultat_text = message.choices[0].message.content
    
#     # Extraire le JSON
#     try:
#         # Chercher le JSON dans la réponse
#         start_idx = resultat_text.find('{')
#         end_idx = resultat_text.rfind('}') + 1
#         json_str = resultat_text[start_idx:end_idx]
#         resultat_json = json.loads(json_str)
#     except:
#         print("⚠️ Erreur lors du parsing JSON")
#         return None
    
#     return resultat_json

# def generer_html_rapport(data):
#     """Génère un rapport HTML à partir des données JSON"""
    
#     factures_approuvees = data.get("factures_validees", [])
#     factures_rejetees = data.get("factures_rejetees", [])
#     resume = data.get("resume", "")
    
#     # Générer le HTML des factures approuvées
#     html_approuvees = ""
#     for facture in factures_approuvees:
#         html_approuvees += f"""
#             <div class="facture-item">
#                 <div class="facture-icon">✅</div>
#                 <div class="facture-details">
#                     <h3>{facture.get('fournisseur', 'N/A')} - {facture.get('description', 'N/A')}</h3>
#                     <p class="raison">✓ {facture.get('raison', 'Validée')}</p>
#                 </div>
#                 <div style="text-align: right;">
#                     <div class="montant">{facture.get('montant', 0):,.2f} €</div>
#                     <div class="badge approuvee">Approuvée</div>
#                 </div>
#             </div>
#         """
    
#     # Générer le HTML des factures rejetées
#     html_rejetees = ""
#     for facture in factures_rejetees:
#         html_rejetees += f"""
#             <div class="facture-item rejetee">
#                 <div class="facture-icon"></div>
#                 <div class="facture-details">
#                     <h3>{facture.get('fournisseur', 'N/A')} - {facture.get('description', 'N/A')}</h3>
#                     <p class="raison">✗ {facture.get('raison', 'Rejetée')}</p>
#                 </div>
#                 <div style="text-align: right;">
#                     <div class="montant">{facture.get('montant', 0):,.2f} €</div>
#                     <div class="badge rejetee">Rejetée</div>
#                 </div>
#             </div>
#         """
    
#     # Template HTML complet
#     html_template = f"""<!DOCTYPE html>
# <html lang="fr">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Rapport de Validation de Factures</title>
#     <style>
#         * {{
#             margin: 0;
#             padding: 0;
#             box-sizing: border-box;
#         }}
        
#         body {{
#             font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             padding: 40px 20px;
#             min-height: 100vh;
#         }}
        
#         .container {{
#             max-width: 1000px;
#             margin: 0 auto;
#             background: white;
#             border-radius: 15px;
#             box-shadow: 0 20px 60px rgba(0,0,0,0.3);
#             overflow: hidden;
#         }}
        
#         .header {{
#             background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
#             color: white;
#             padding: 40px 30px;
#             text-align: center;
#         }}
        
#         .header h1 {{
#             font-size: 28px;
#             margin-bottom: 10px;
#         }}
        
#         .header p {{
#             font-size: 14px;
#             opacity: 0.9;
#         }}
        
#         .content {{
#             padding: 40px 30px;
#         }}
        
#         .resume-section {{
#             background: #f8f9fa;
#             border-left: 5px solid #667eea;
#             padding: 20px;
#             margin-bottom: 30px;
#             border-radius: 8px;
#         }}
        
#         .resume-section h2 {{
#             color: #333;
#             font-size: 16px;
#             margin-bottom: 10px;
#         }}
        
#         .resume-section p {{
#             color: #666;
#             line-height: 1.6;
#             font-size: 14px;
#         }}
        
#         .stats {{
#             display: grid;
#             grid-template-columns: 1fr 1fr;
#             gap: 20px;
#             margin-bottom: 30px;
#         }}
        
#         .stat-card {{
#             padding: 20px;
#             border-radius: 10px;
#             text-align: center;
#             color: white;
#         }}
        
#         .stat-card.approuvees {{
#             background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
#         }}
        
#         .stat-card.rejetees {{
#             background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%);
#         }}
        
#         .stat-card .number {{
#             font-size: 36px;
#             font-weight: bold;
#             margin-bottom: 5px;
#         }}
        
#         .stat-card .label {{
#             font-size: 14px;
#             opacity: 0.9;
#         }}
        
#         .section-title {{
#             font-size: 20px;
#             color: #333;
#             margin-bottom: 20px;
#             padding-bottom: 10px;
#             border-bottom: 3px solid #667eea;
#         }}
        
#         .facture-item {{
#             background: #f8f9fa;
#             border-left: 5px solid #11998e;
#             padding: 20px;
#             margin-bottom: 15px;
#             border-radius: 8px;
#             display: grid;
#             grid-template-columns: auto 1fr auto;
#             gap: 20px;
#             align-items: start;
#         }}
        
#         .facture-item.rejetee {{
#             border-left-color: #ff6a00;
#             background: #fff5f0;
#         }}
        
#         .facture-icon {{
#             font-size: 24px;
#         }}
        
#         .facture-details h3 {{
#             color: #333;
#             font-size: 16px;
#             margin-bottom: 8px;
#         }}
        
#         .facture-details p {{
#             color: #666;
#             font-size: 13px;
#             margin-bottom: 5px;
#             line-height: 1.5;
#         }}
        
#         .montant {{
#             font-weight: bold;
#             color: #667eea;
#             font-size: 16px;
#         }}
        
#         .badge {{
#             display: inline-block;
#             padding: 6px 12px;
#             border-radius: 20px;
#             font-size: 12px;
#             font-weight: bold;
#             text-transform: uppercase;
#             letter-spacing: 0.5px;
#         }}
        
#         .badge.approuvee {{
#             background: #d4edda;
#             color: #155724;
#         }}
        
#         .badge.rejetee {{
#             background: #f8d7da;
#             color: #721c24;
#         }}
        
#         .footer {{
#             background: #f8f9fa;
#             padding: 20px 30px;
#             text-align: center;
#             color: #666;
#             font-size: 12px;
#             border-top: 1px solid #ddd;
#         }}
        
#         .raison {{
#             font-style: italic;
#             color: #888;
#             margin-top: 8px;
#             font-size: 13px;
#         }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <div class="header">
#             <h1>Agent Comptable Autonome</h1>
#             <p>Rapport de Validation des Factures</p>
#         </div>
        
#         <div class="content">
#             <div class="resume-section">
#                 <h2>Résumé</h2>
#                 <p>{resume}</p>
#             </div>
            
#             <div class="stats">
#                 <div class="stat-card approuvees">
#                     <div class="number">{len(factures_approuvees)}</div>
#                     <div class="label">Factures Approuvées</div>
#                 </div>
#                 <div class="stat-card rejetees">
#                     <div class="number">{len(factures_rejetees)}</div>
#                     <div class="label">Factures Rejetées</div>
#                 </div>
#             </div>
            
#             <h2 class="section-title">✅ Factures Approuvées</h2>
#             {html_approuvees}
            
#             <h2 class="section-title">❌ Factures Rejetées</h2>
#             {html_rejetees}
#         </div>
        
#         <div class="footer">
#             <p>Rapport généré par Agent Comptable Autonome © 2024 | Analyse stricte et détection d'anomalies</p>
#         </div>
#     </div>
# </body>
# </html>"""
    
#     return html_template

# def sauvegarder_rapport(html_content, nom_fichier="rapport_factures.html"):
#     """Sauvegarde le rapport HTML dans un fichier"""
#     with open(nom_fichier, 'w', encoding='utf-8') as f:
#         f.write(html_content)
#     print(f"✅ Rapport sauvegardé : {nom_fichier}")

# if __name__ == "__main__":
#     print("=" * 70)
#     print("AGENT COMPTABLE AGENTIQUE - VALIDATION DE FACTURES")
#     print("=" * 70)
#     print("\nL'agent analyse les factures...")
    
#     # Valider les factures
#     resultat = valider_factures()
    
#     if resultat:
#         print("\n✅ Analyse complète !")
#         print(f"   • {len(resultat.get('factures_validees', []))} facture(s) approuvée(s)")
#         print(f"   • {len(resultat.get('factures_rejetees', []))} facture(s) rejetée(s)")
        
#         # Générer le rapport HTML
#         html = generer_html_rapport(resultat)
        
#         # Sauvegarder le rapport
#         sauvegarder_rapport(html)
        
#         print("\nOuvrez 'rapport_factures.html' dans votre navigateur pour voir le rapport !")
#         print("=" * 70)
#     else:
#         print("Erreur lors de l'analyse")





