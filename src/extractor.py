import os
import json
import pdfplumber
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from mistralai.client import Mistral

# --- CONFIGURATION DES CHEMINS ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdf")
XML_DIR = os.path.join(BASE_DIR, "data", "xml") # Dossier des flux structurés
OUTPUT_JSON = os.path.join(BASE_DIR, "data", "json", "donnees_extraites.json")
ENV_PATH = os.path.join(BASE_DIR, ".env")

load_dotenv(ENV_PATH)
client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))

def extract_from_xml(xml_path):
    """Extrait les données nativement depuis le flux XML (Norme 2026)."""
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        # On récupère les données selon la structure de notre générateur
        data = {
            "fournisseur": root.find(".//Name").text if root.find(".//Name") is not None else "Inconnu",
            "siret": root.find(".//Siret").text if root.find(".//Siret") is not None else "Non renseigné",
            "date": root.find(".//Date").text if root.find(".//Date") is not None else "",
            "total_ht": float(root.find(".//HT").text),
            "total_ttc": float(root.find(".//TTC").text),
            "tva_taux": float(root.find(".//TVA_Rate").text),
            "methode": "Flux XML (Natif 2026)" # Pour le traçage
        }
        return data
    except Exception as e:
        print(f"Erreur lecture XML {xml_path}: {e}")
        return None

def extract_text_from_pdf(pdf_path):
    """Extrait le texte brut du PDF pour l'IA."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return pdf.pages[0].extract_text()
    except Exception:
        return ""

def save_as_xml(data, xml_path):
    """Sauvegarde les données extraites par l'IA en XML (même format que le générateur)."""
    from xml.dom import minidom
    invoice_id = os.path.basename(xml_path).replace(".xml", "")
    root = ET.Element("Invoice")
    ET.SubElement(root, "ID").text = invoice_id
    ET.SubElement(root, "Date").text = str(data.get("date", ""))
    seller = ET.SubElement(root, "Seller")
    ET.SubElement(seller, "Name").text = str(data.get("fournisseur", "Inconnu"))
    ET.SubElement(seller, "Siret").text = str(data.get("siret", "Non renseigné"))
    totals = ET.SubElement(root, "Totals")
    ET.SubElement(totals, "HT").text = f"{float(data.get('total_ht', 0)):.2f}"
    ET.SubElement(totals, "TVA_Rate").text = str(data.get("tva_taux", 0))
    ET.SubElement(totals, "TTC").text = f"{float(data.get('total_ttc', 0)):.2f}"
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(xml_str)

def analyze_with_mistral(text_content):
    """Analyse intelligente via Mistral si aucun XML n'est disponible."""
    prompt = f"""
    Tu es un expert comptable. Extrais les infos de cette facture en JSON strict.
    Réponds UNIQUEMENT avec ces clés exactes en français : fournisseur, siret, date, total_ht, total_ttc, tva_taux.
    Si une info est absente, mets null pour les nombres et "Non renseigné" pour les textes.
    Texte de la facture :
    {text_content}
    """
    messages = [{"role": "user", "content": prompt}]
    chat_response = client.chat.complete(
        model="mistral-small-latest",
        messages=messages,
        response_format={"type": "json_object"}
    )
    data = json.loads(chat_response.choices[0].message.content)
    data["methode"] = "Analyse IA (OCR)" # Pour le traçage
    return data

def process_files():
    """Parcourt les PDF et cherche le XML correspondant ou utilise l'IA."""
    results = []
    if not os.path.exists(PDF_DIR):
        print(f"Erreur : Le dossier {PDF_DIR} est introuvable.")
        return results

    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    
    for file in pdf_files:
        print(f"\n--- Traitement de {file} ---")
        xml_name = file.replace(".pdf", ".xml")
        xml_path = os.path.join(XML_DIR, xml_name)
        pdf_path = os.path.join(PDF_DIR, file)
        
        data = None

        # ÉTAPE 1 : On check si le XML (Facture Électronique) existe
        if os.path.exists(xml_path):
            print(f"Flux XML détecté. Extraction haute fiabilité...")
            data = extract_from_xml(xml_path)
        
        # ÉTAPE 2 : Si pas de XML ou erreur, on bascule sur l'IA
        if not data:
            print(f"Pas de XML. Passage à l'analyse intelligente Mistral...")
            raw_text = extract_text_from_pdf(pdf_path)
            if raw_text:
                try:
                    data = analyze_with_mistral(raw_text)
                    save_as_xml(data, xml_path)
                    print(f"XML généré automatiquement : {xml_name}")
                except Exception as e:
                    print(f"Erreur IA : {e}")
            else:
                print(f"Impossible de lire le texte du PDF.")

        if data:
            data["fichier"] = file
            results.append(data)
            print(f"✅ Terminé : {data.get('fournisseur', 'Inconnu')} ({data.get('methode', '?')})")
                
    return results

if __name__ == "__main__":
    print("=== AGENT COMPTABLE : EXTRACTION HYBRIDE (PDF/XML) ===")
    
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    donnees = process_files()
    
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(donnees, f, indent=4, ensure_ascii=False)
        
    print(f"\nPhase d'extraction terminée ! {len(donnees)} factures prêtes pour l'audit.")

# import os
# import json
# import pdfplumber
# from dotenv import load_dotenv
# from mistralai.client import Mistral

# # --- CONFIGURATION DES CHEMINS ---
# # On définit la racine du projet par rapport à ce fichier (src/auditeur.py)
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# PDF_DIR = os.path.join(BASE_DIR, "data", "pdf")
# OUTPUT_JSON = os.path.join(BASE_DIR, "data", "json", "donnees_extraites.json")
# ENV_PATH = os.path.join(BASE_DIR, ".env")

# # 1. Charger la clé API depuis le fichier .env
# load_dotenv(ENV_PATH)
# api_key = os.getenv("MISTRAL_API_KEY")

# # 2. Initialiser le client Mistral
# client = Mistral(api_key=api_key)

# def extract_text_from_pdf(pdf_path): #scanne l'image pour en faire uen chaine de caractére brute (texte plat)
#     """Extrait le texte brut du PDF avec pdfplumber."""
#     try:
#         with pdfplumber.open(pdf_path) as pdf:
#             # On récupère le texte de la première page
#             return pdf.pages[0].extract_text()
#     except Exception as e:
#         print(f"Erreur lors de la lecture du PDF {pdf_path}: {e}")
#         return ""

# def analyze_with_mistral(text_content): #mistral réorganise dans un format json
#     """Envoie le texte à Mistral pour obtenir un JSON propre."""
#     prompt = f"""
#     Tu es un expert comptable. Extrais les infos de cette facture en JSON strict.
#     Champs : fournisseur, siret, date, total_ht, total_ttc, tva_taux.
    
#     Texte de la facture :
#     {text_content}
#     """
    
#     # On utilise un simple dictionnaire au lieu de ChatMessage
#     messages = [
#         {"role": "user", "content": prompt}
#     ]
    
#     chat_response = client.chat.complete(
#         model="mistral-small-latest",
#         messages=messages,
#         response_format={"type": "json_object"} # Force Mistral à répondre en JSON
#     )
    
#     # On transforme la chaîne de caractères reçue en dictionnaire Python
#     return json.loads(chat_response.choices[0].message.content)

# def process_folder(folder_path):#facteur qui va chercher les lettres (PDF), les fait traduire (Mistral), et les range dans un classeur (results)
#     """Parcourt le dossier et traite chaque PDF."""
#     results = []
#     if not os.path.exists(folder_path):
#         print(f"Le dossier {folder_path} n'existe pas.")
#         return results

#     pdf_files = [f for f in os.listdir(folder_path) if f.endswith(".pdf")]#os.listdir(folder_path) : Elle regarde dans data/pdf et fait la liste de tout ce qui s'y trouve.
    
#     for file in pdf_files:
#         full_path = os.path.join(folder_path, file)
#         print(f"Traitement de {file}...")
        
#         raw_text = extract_text_from_pdf(full_path)
        
#         if raw_text:
#             try:
#                 data = analyze_with_mistral(raw_text)
#                 data["fichier"] = file # On garde une trace du nom du fichier
#                 results.append(data)
#                 print(f"Données extraites pour {data.get('fournisseur', 'Inconnu')}")
#             except Exception as e:
#                 print(f"Erreur d'analyse IA pour {file}: {e}")
#         else:
#             print(f"Aucun texte trouvé dans {file}")
                
#     return results

# if __name__ == "__main__":
#     print("=== AGENT COMPTABLE : PHASE D'EXTRACTION ===")
    
#     # S'assurer que le dossier data/interim existe
#     os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    
#     # Lancement du processus sur le dossier data/pdf
#     donnees = process_folder(PDF_DIR)
    
#     # Sauvegarde dans data/interim/donnees_extraites.json
#     with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
#         json.dump(donnees, f, indent=4, ensure_ascii=False)
        
#     print(f"\nTerminé ! {len(donnees)} factures enregistrées dans '{OUTPUT_JSON}'.")