# Système d'Optimisation — Gestion des Déchets

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](https://github.com/tahaeladli1/Syst-me-d-Optimisation---Gestion-des-D-chets/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)

Projet académique et applicatif dédié à l'optimisation de la gestion des déchets urbains, en combinant optimisation mathématique, logique IoT et visualisation de données.

## À propos du projet

Ce projet a été conçu pour optimiser le traitement et la collecte des déchets dans un contexte urbain réaliste. Il met en œuvre plusieurs approches :

- programmation linéaire
- méthode du simplexe
- simulation de niveaux de remplissage des bennes
- analyse de flux de données IoT
- optimisation des itinéraires de collecte
- interface de visualisation et de suivi

## Équipe

Mohamed Taha El Adli · Yahya Zaizi · Taki Mohamed Imrane · Youssef Et-talhaouy 

## Objectifs

- améliorer l'efficacité de la collecte
- réduire les coûts logistiques
- anticiper les alertes liées aux bennes pleines
- proposer une solution technique exploitable en contexte réel

## Compétences démontrées

- Python
- optimisation mathématique
- analyse de données
- visualisation de résultats
- logique de gestion de flotte
- travail sur données structurées et simulations

## Architecture du projet

```text
.
├── main.py
├── setup_check.py
├── requirements.txt
├── README.md
├── LICENSE
├── config/
│   └── settings.py
├── data/
│   ├── iot_report.json
│   └── sample_data.json
├── modules/
│   ├── linear_prog.py
│   ├── simplex.py
│   ├── iot_analytics.py
│   ├── iot_sensors.py
│   ├── iot_visualisation.py
│   ├── route_optimizer.py
│   ├── route_visualisation.py
│   └── visualisation.py
├── ui/
│   ├── dashboard.py
│   └── web_app.py
├── tests/
│   ├── test_etape1.py
│   ├── test_etape2.py
│   ├── test_etape3.py
│   ├── test_etape4.py
│   └── test_etape5.py
├── exports/
│   └── rapports et captures
├── etape2_demo.py
├── etape3_demo.py
├── etape4_demo.py
├── etape5_demo.py
├── .gitignore
└── .github/
    └── workflows/
        └── ci.yml
```

## Problème métier résolu

Le projet répond à un besoin concret de gestion intelligente des déchets :

- éviter les surcharges de bennes
- optimiser les tournées de collecte
- équilibrer les ressources disponibles
- améliorer la surveillance et la prise de décision

## Résultats clés

- modélisation de contraintes de collecte
- optimisation des flux avec méthode graphique et simplex
- simulation de niveaux de remplissage
- génération de rapports et visualisations
- démonstration d'un système de gestion connectée

## Installation

```bash
# Cloner le dépôt
git clone https://github.com/tahaeladli1/Syst-me-d-Optimisation---Gestion-des-D-chets.git

# Accéder au projet
cd Syst-me-d-Optimisation---Gestion-des-D-chets

# Créer un environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Utilisation

```bash
python setup_check.py
python main.py --mode cli
```

## Tests

```bash
python -m pytest -q
```

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier [LICENSE](LICENSE).

## Contact

Pour toute question ou proposition de collaboration, vous pouvez utiliser le dépôt GitHub associé au projet.
