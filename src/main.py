import os
# Importation des fonctions principales de vos scripts
# Note : Assurez-vous que vos fichiers s'appellent exactement ainsi dans le même dossier
# from generator import FACTURES, build_pdf, build_xml, PDF_DIR, XML_DIR
from extractor import process_files
from auditor import valider_factures, generer_html_rapport, REPORT_OUTPUT

def main():
    print("DÉMARRAGE DU PIPELINE COMPTABLE (PROTOTYPE 2026)\n")

    # # --- ÉTAPE 1 : GÉNÉRATION DES DONNÉES ---
    # print("1️Génération des factures (PDF + XML)...")
    # for f in FACTURES:
    #     f["total_ttc"] = f["total_ht"] * (1 + f["tva_pct"]/100)
    #     f["lignes"] = [{"description": f"Prestation relative à {f['numero']}", "qte": 1, "pu_ht": f["total_ht"], "tva_pct": f["tva_pct"]}]
        
    #     pdf_path = os.path.join(PDF_DIR, f"{f['numero']}.pdf")
    #     xml_path = os.path.join(XML_DIR, f"{f['numero']}.xml")
        
    #     build_pdf(f, pdf_path)
    #     build_xml(f, xml_path)
    # print(f"{len(FACTURES)} factures générées dans data/")

    # --- ÉTAPE 2 : EXTRACTION ---
    print("\n2️Extraction des données (Hybride XML/IA)...")
    donnees_extraites = process_files()
    print(f"Extraction terminée : {len(donnees_extraites)} factures lues.")

    # --- ÉTAPE 3 : AUDIT ET RAPPORT ---
    print("\n3️Analyse de conformité via Mistral AI...")
    try:
        resultats_audit = valider_factures(donnees_extraites)
        html_report = generer_html_rapport(resultats_audit)
        
        os.makedirs(os.path.dirname(REPORT_OUTPUT), exist_ok=True)
        with open(REPORT_OUTPUT, "w", encoding="utf-8") as f:
            f.write(html_report)
            
        print(f"RAPPORT GÉNÉRÉ AVEC SUCCÈS : {REPORT_OUTPUT}")
        print(f"   - Approuvées : {len(resultats_audit.get('factures_validees', []))}")
        print(f"   - Rejetées   : {len(resultats_audit.get('factures_rejetees', []))}")
        
    except Exception as e:
        print(f"Erreur lors de l'audit : {e}")

if __name__ == "__main__":
    main()