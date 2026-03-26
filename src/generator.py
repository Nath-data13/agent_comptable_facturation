"""
Génère des factures fictives au format PDF pour la démo de l'agent comptable.
Certaines factures contiennent des anomalies volontaires (montant élevé, TVA incorrecte,
fournisseur inconnu) pour tester la détection de l'agent.
"""

import os
#bibliothèque reportlab, qui est la référence en Python pour créer des PDF de manière programmable
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

# Dossier de sortie
OUTPUT_DIR = "../data/pdf"
os.makedirs(OUTPUT_DIR, exist_ok=True)

styles = getSampleStyleSheet()

# Styles personnalisés
style_titre = ParagraphStyle("titre", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#2c3e50"), spaceAfter=4)
style_sous_titre = ParagraphStyle("sous_titre", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#7f8c8d"), spaceAfter=2)
style_section = ParagraphStyle("section", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#2c3e50"), fontName="Helvetica-Bold")
style_normal = ParagraphStyle("normal", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#2c3e50"))
style_droite = ParagraphStyle("droite", parent=styles["Normal"], fontSize=9, alignment=TA_RIGHT, textColor=colors.HexColor("#2c3e50"))
style_total = ParagraphStyle("total", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold", textColor=colors.HexColor("#2c3e50"), alignment=TA_RIGHT)
style_alerte = ParagraphStyle("alerte", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#e74c3c"), fontName="Helvetica-Oblique")


def build_pdf(filename, numero, date, emetteur, client, lignes, notes=None):
    """
    Construit un PDF de facture.
    lignes : liste de dict {description, qte, pu_ht, tva_pct}
    """
    filepath = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        filepath,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    elements = []

    # --- EN-TÊTE ---
    header_data = [
        [
            Paragraph(emetteur["nom"], style_titre),
            Paragraph(f"FACTURE N° {numero}", ParagraphStyle("fac", parent=styles["Heading1"], fontSize=18, alignment=TA_RIGHT, textColor=colors.HexColor("#2980b9")))
        ],
        [
            Paragraph(f"{emetteur['adresse']}<br/>{emetteur['ville']}<br/>{emetteur['siret']}", style_sous_titre),
            Paragraph(f"Date : {date}<br/>Échéance : 30 jours", style_droite)
        ]
    ]
    header_table = Table(header_data, colWidths=[9*cm, 8*cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2980b9"), spaceAfter=12))

    # --- BLOC CLIENT ---
    elements.append(Paragraph("Facturé à :", style_section))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(f"<b>{client['nom']}</b>", style_normal))
    elements.append(Paragraph(f"{client['adresse']}", style_normal))
    elements.append(Paragraph(f"{client['ville']}", style_normal))
    elements.append(Spacer(1, 16))

    # --- TABLEAU DES LIGNES ---
    table_data = [["Description", "Qté", "PU HT", "TVA", "Total HT"]]
    total_ht = 0
    total_tva = 0

    for ligne in lignes:
        ht = ligne["qte"] * ligne["pu_ht"]
        tva_montant = ht * ligne["tva_pct"] / 100
        total_ht += ht
        total_tva += tva_montant
        table_data.append([
            ligne["description"],
            str(ligne["qte"]),
            f"{ligne['pu_ht']:.2f} €",
            f"{ligne['tva_pct']}%",
            f"{ht:.2f} €"
        ])

    total_ttc = total_ht + total_tva

    lines_table = Table(table_data, colWidths=[7.5*cm, 1.5*cm, 2.5*cm, 1.5*cm, 2.5*cm])
    lines_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2980b9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (4, 1), (4, -1), "RIGHT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#ecf0f1"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(lines_table)
    elements.append(Spacer(1, 12))

    # --- TOTAUX ---
    totaux_data = [
        ["", "Total HT :", f"{total_ht:.2f} €"],
        ["", f"TVA :", f"{total_tva:.2f} €"],
        ["", "TOTAL TTC :", f"{total_ttc:.2f} €"],
    ]
    totaux_table = Table(totaux_data, colWidths=[9.5*cm, 3.5*cm, 2.5*cm])
    totaux_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("FONTNAME", (1, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTSIZE", (1, 2), (-1, 2), 11),
        ("LINEABOVE", (1, 2), (-1, 2), 1.5, colors.HexColor("#2980b9")),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(totaux_table)

    # --- NOTES / ANOMALIES ---
    if notes:
        elements.append(Spacer(1, 16))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdc3c7"), spaceAfter=8))
        elements.append(Paragraph("Notes :", style_section))
        elements.append(Paragraph(notes, style_normal))

    # --- PIED DE PAGE ---
    elements.append(Spacer(1, 24))
    elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bdc3c7"), spaceAfter=6))
    elements.append(Paragraph(
        f"Paiement par virement — IBAN : FR76 3000 6000 0112 3456 7890 189 — BIC : BNPAFRPP",
        ParagraphStyle("footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#95a5a6"), alignment=TA_CENTER)
    ))

    doc.build(elements)
    print(f"  Généré : {filepath}  (TTC : {total_ttc:.2f} €)")
    return filepath


# =============================================================================
# DÉFINITION DES FACTURES
# =============================================================================

FACTURES = [
    # ── Facture 1 : Normale – fournitures de bureau
    {
        "filename": "facture_001_fournitures_plus.pdf",
        "numero": "2024-001",
        "date": "2024-01-15",
        "emetteur": {
            "nom": "Fournitures Plus",
            "adresse": "12 rue des Artisans",
            "ville": "75011 Paris",
            "siret": "SIRET : 123 456 789 00012"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Ramettes papier A4 (500 feuilles)", "qte": 10, "pu_ht": 4.50, "tva_pct": 20},
            {"description": "Stylos bille (boîte de 50)", "qte": 3, "pu_ht": 8.90, "tva_pct": 20},
            {"description": "Classeurs A4 rigides", "qte": 20, "pu_ht": 2.99, "tva_pct": 20},
        ],
        "notes": None
    },

    # ── Facture 2 : Normale – cabinet de conseil
    {
        "filename": "facture_002_cabinet_conseil.pdf",
        "numero": "2024-002",
        "date": "2024-01-16",
        "emetteur": {
            "nom": "Cabinet Conseil & Audit",
            "adresse": "8 boulevard Haussmann",
            "ville": "75009 Paris",
            "siret": "SIRET : 987 654 321 00045"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Audit fiscal Q4 2023", "qte": 1, "pu_ht": 1000.00, "tva_pct": 20},
        ],
        "notes": None
    },

    # ── Facture 3 : Normale – Amazon Business
    {
        "filename": "facture_003_amazon_business.pdf",
        "numero": "2024-003",
        "date": "2024-01-17",
        "emetteur": {
            "nom": "Amazon Business France",
            "adresse": "67 boulevard du Général Leclerc",
            "ville": "92110 Clichy",
            "siret": "SIRET : 487 916 340 00021"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Boîtes d'emballage carton (x50)", "qte": 2, "pu_ht": 22.49, "tva_pct": 20},
            {"description": "Ruban adhésif d'emballage (x12)", "qte": 1, "pu_ht": 12.99, "tva_pct": 20},
        ],
        "notes": None
    },

    # ── Facture 4 : ANOMALIE – montant très élevé (>5000€)
    {
        "filename": "facture_004_edf_anomalie_montant.pdf",
        "numero": "2024-004",
        "date": "2024-01-18",
        "emetteur": {
            "nom": "EDF Entreprises",
            "adresse": "22-30 avenue de Wagram",
            "ville": "75008 Paris",
            "siret": "SIRET : 552 081 317 01220"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Consommation électrique bureau – Janvier 2024", "qte": 1, "pu_ht": 4583.33, "tva_pct": 20},
        ],
        "notes": "Consommation exceptionnelle suite à panne système de chauffage."
    },

    # ── Facture 5 : ANOMALIE – fournisseur inconnu + description vague
    {
        "filename": "facture_005_inconnu_anomalie_fournisseur.pdf",
        "numero": "2024-005",
        "date": "2024-01-19",
        "emetteur": {
            "nom": "Services Divers SARL",
            "adresse": "—",
            "ville": "—",
            "siret": "SIRET : non renseigné"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Frais de prestation divers", "qte": 1, "pu_ht": 125.00, "tva_pct": 20},
        ],
        "notes": "Aucune information complémentaire disponible."
    },

    # ── Facture 6 : ANOMALIE – TVA incorrecte (taux aberrant)
    {
        "filename": "facture_006_telecom_anomalie_tva.pdf",
        "numero": "2024-006",
        "date": "2024-01-20",
        "emetteur": {
            "nom": "TélécomPro Solutions",
            "adresse": "3 impasse des Réseaux",
            "ville": "31000 Toulouse",
            "siret": "SIRET : 741 852 963 00031"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Abonnement téléphonie pro – Février 2024", "qte": 1, "pu_ht": 89.00, "tva_pct": 33},
        ],
        "notes": "Taux TVA appliqué : 33% (hors norme — taux légal France : 20%)"
    },

    # ── Facture 7 : Normale – prestation informatique
    {
        "filename": "facture_007_it_solutions.pdf",
        "numero": "2024-007",
        "date": "2024-01-22",
        "emetteur": {
            "nom": "IT Solutions Pro",
            "adresse": "14 rue de la Technologie",
            "ville": "13002 Marseille",
            "siret": "SIRET : 321 654 987 00067"
        },
        "client": {
            "nom": "Mon Entreprise SAS",
            "adresse": "45 avenue de la République",
            "ville": "69003 Lyon"
        },
        "lignes": [
            {"description": "Maintenance serveur mensuelle", "qte": 1, "pu_ht": 350.00, "tva_pct": 20},
            {"description": "Sauvegarde cloud (500 Go)", "qte": 1, "pu_ht": 49.00, "tva_pct": 20},
        ],
        "notes": None
    },
]


if __name__ == "__main__":
    print("=" * 60)
    print("GÉNÉRATION DES FACTURES PDF FICTIVES")
    print("=" * 60)

    for facture in FACTURES:
        build_pdf(
            filename=facture["filename"],
            numero=facture["numero"],
            date=facture["date"],
            emetteur=facture["emetteur"],
            client=facture["client"],
            lignes=facture["lignes"],
            notes=facture["notes"],
        )

    print(f"\n{len(FACTURES)} factures générées dans '{OUTPUT_DIR}/'")
    print("  dont 3 avec anomalies : facture_004, facture_005, facture_006")
    print("=" * 60)
