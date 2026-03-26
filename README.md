# Agent Comptable Autonome (Mistral AI)

Ce prototype est une démonstration d'un **agent intelligent** capable de simuler un flux de travail comptable complet : génération de documents, extraction de données par IA, et audit automatique de conformité.

## 📂 Structure du Projet

Organisé selon les meilleures pratiques de développement Python :

```text
agent_comptable_demo/
├── data/
│   ├── pdf/                # Factures fictives générées (PDF)
│   └── json/               # Données extraites par l'IA (JSON)
├── src/                    # Scripts Python (Code source)
│   ├── generator.py        # Étape 1 : Création du jeu de données
│   ├── extractor.py        # Étape 2 : OCR et Structuration via Mistral
│   └── auditor.py          # Étape 3 : Audit métier et Rapport HTML
├── reports/                # Rapports d'audit finaux (Visuels)
├── .env                    # Clés API (Mistral) - [À créer]
├── requirements.txt        # Dépendances du projet
└── README.md               # Documentation
```


# Création de l'environnement virtuel - commande dans le terminal
python -m venv venv_compta
### Activation (Windows)
.\venv_compta\Scripts\activate

## Installer les bibliothéques
pip install -r requirements.txt

## Clé API
MISTRAL_API_KEY=votre_cle_api_mistral_ici

# Lancer les scripts dans l'ordre
## 1- Generation des données
python src/generator.py

## 2 - Extraction intelligente
python src/extractor.py

## 3 - Audit et Décision
agent_comptable.py

# Resultat final
Après l'étape 3, ouvrez le fichier rapport/rapport_final.html dans votre navigateur. Vous y trouverez un tableau de bord  classant les factures en "Approuvées" ou "Rejetées" avec la justification de l'IA pour chaque décision.

Démo technique - Architecture modulaire - IA Agentique 2026