import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF_DIR = os.path.join(BASE_DIR, "data", "pdf")
XML_DIR = os.path.join(BASE_DIR, "data", "xml")

os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(XML_DIR, exist_ok=True)

styles = getSampleStyleSheet()
style_titre = ParagraphStyle("titre", parent=styles["Heading1"], fontSize=20, textColor=colors.HexColor("#2b5797"))
style_normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=9)
style_droite = ParagraphStyle("droite", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT)

def build_xml(data, filepath):
    root = ET.Element("Invoice")
    ET.SubElement(root, "ID").text = data["numero"]
    ET.SubElement(root, "Date").text = data["date"]
    seller = ET.SubElement(root, "Seller")
    ET.SubElement(seller, "Name").text = data["emetteur"]["nom"]
    ET.SubElement(seller, "Siret").text = data["emetteur"]["siret"].replace(" ", "")
    
    totals = ET.SubElement(root, "Totals")
    ET.SubElement(totals, "HT").text = f"{data['total_ht']:.2f}"
    ET.SubElement(totals, "TVA_Rate").text = str(data["lignes"][0]["tva_pct"])
    ET.SubElement(totals, "TTC").text = f"{data['total_ttc']:.2f}"
    
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="   ")
    with open(filepath.replace(".pdf", ".xml"), "w", encoding="utf-8") as f:
        f.write(xml_str)

def build_pdf(data, filepath):
    doc = SimpleDocTemplate(filepath, pagesize=A4)
    elements = []
    # En-tête simplifié style Sentinel
    header = [[Paragraph(data["emetteur"]["nom"], style_titre), Paragraph(f"Facture {data['numero']}", style_droite)]]
    elements.append(Table(header, colWidths=[10*cm, 7*cm]))
    elements.append(HRFlowable(width="100%", color=colors.HexColor("#2b5797")))
    elements.append(Spacer(1, 20))
    
    # Contenu
    elements.append(Paragraph(f"Date: {data['date']}", style_normal))
    elements.append(Paragraph(f"SIRET: {data['emetteur']['siret']}", style_normal))
    elements.append(Spacer(1, 20))
    
    # Table des lignes
    t_data = [["Description", "Total HT", "TVA", "Total TTC"]]
    t_data.append([data["lignes"][0]["description"], f"{data['total_ht']:.2f}€", f"{data['lignes'][0]['tva_pct']}%", f"{data['total_ttc']:.2f}€"])
    
    t = Table(t_data, colWidths=[9*cm, 3*cm, 2*cm, 3*cm])
    t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#eef4fb")), ('GRID', (0,0), (-1,-1), 0.5, colors.grey)]))
    elements.append(t)
    
    if data.get("notes"):
        elements.append(Spacer(1, 15))
        elements.append(Paragraph(f"Note d'audit: {data['notes']}", style_normal))
        
    doc.build(elements)

# --- JEU DE DONNÉES DE 10 FACTURES ---
FACTURES = [
    # 5 FACTURES OK
    {"numero": "F2026-01", "date": "2026-03-01", "emetteur": {"nom": "Orange Pro", "siret": "38012986600011"}, "total_ht": 45.00, "tva_pct": 20},
    {"numero": "F2026-02", "date": "2026-03-02", "emetteur": {"nom": "Amazon AWS", "siret": "83412345600012"}, "total_ht": 150.20, "tva_pct": 20},
    {"numero": "F2026-03", "date": "2026-03-03", "emetteur": {"nom": "SNCF Voyage", "siret": "55204944700013"}, "total_ht": 89.00, "tva_pct": 10},
    {"numero": "F2026-04", "date": "2026-03-04", "emetteur": {"nom": "Baker Tilly", "siret": "12345678900014"}, "total_ht": 1200.00, "tva_pct": 20},
    {"numero": "F2026-05", "date": "2026-03-05", "emetteur": {"nom": "Apple Store", "siret": "98765432100015"}, "total_ht": 2400.00, "tva_pct": 20},
    
    # 5 FACTURES AVEC ANOMALIES
    {"numero": "F2026-06", "date": "2026-03-06", "emetteur": {"nom": "Luxe Invest", "siret": "11122233300016"}, "total_ht": 8500.00, "tva_pct": 20, "notes": "MONTANT ÉLEVÉ (>5000€)"},
    {"numero": "F2026-07", "date": "2026-03-07", "emetteur": {"nom": "Telecom Error", "siret": "44455566600017"}, "total_ht": 100.00, "tva_pct": 33, "notes": "TVA ILLÉGALE (33%)"},
    {"numero": "F2026-08", "date": "2026-03-08", "emetteur": {"nom": "Inconnu Services", "siret": "NON RENSEIGNÉ"}, "total_ht": 450.00, "tva_pct": 20, "notes": "SIRET MANQUANT"},
    {"numero": "F2026-09", "date": "2026-03-09", "emetteur": {"nom": "Global Tech", "siret": "77788899900019"}, "total_ht": 12000.00, "tva_pct": 20, "notes": "MONTANT CRITIQUE"},
    {"numero": "F2026-10", "date": "2026-03-10", "emetteur": {"nom": "Imprimerie Rapide", "siret": "00011122200020"}, "total_ht": 25.00, "tva_pct": 0, "notes": "TVA À 0% SANS JUSTIFICATION"},
]

if __name__ == "__main__":
    for f in FACTURES:
        f["total_ttc"] = f["total_ht"] * (1 + f["tva_pct"]/100)
        f["lignes"] = [{"description": f"Prestation relative à {f['numero']}", "qte": 1, "pu_ht": f["total_ht"], "tva_pct": f["tva_pct"]}]
        
        path = os.path.join(PDF_DIR, f"{f['numero']}.pdf")
        xml_path = os.path.join(XML_DIR, f"{f['numero']}.xml")
        
        build_pdf(f, path)
        build_xml(f, xml_path)
        print(f"Généré: {f['numero']} (PDF + XML)")
