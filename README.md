# Système d'Optimisation — Gestion des Déchets

[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-blue)](https://github.com/tahaeladli1/Syst-me-d-Optimisation---Gestion-des-D-chets/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)

Projet académique EMSI pour la gestion intelligente des déchets, avec optimisation linéaire, méthodes simplex, simulation IoT et planification de collecte.

## Équipe

Yahya Zaizi · Taki Mohamed Imrane · Youssef Et-talhaouy · Taha Aideli

## Objectif

Ce projet vise à optimiser la collecte, la planification et la gestion des déchets en combinant :

- modélisation mathématique
- optimisation linéaire
- méthode du simplexe
- simulation de niveaux de remplissage des bennes
- analyse IoT et visualisation
- interface de suivi utilisateur

## Statut du projet

- Phase académique : active
- Objectif principal : optimiser la collecte et la gestion des déchets urbains
- Démos disponibles : CLI, visualisation et planification des tournées

## Installation

```bash
# Cloner le projet
cd path/to/project

# Créer un environnement virtuel
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt
```

## Vérification rapide

```bash
python setup_check.py
python main.py --mode cli
```

## Structure du projet

```text
.
├── README.md
├── requirements.txt
├── main.py
├── setup_check.py
├── config/
│   └── settings.py
├── data/
│   ├── iot_report.json
│   └── sample_data.json
├── modules/
│   ├── iot_analytics.py
│   ├── iot_sensors.py
│   ├── iot_visualisation.py
│   ├── linear_prog.py
│   ├── route_optimizer.py
│   ├── route_visualisation.py
│   ├── simplex.py
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
│   └── rapports et captures générées
├── etape2_demo.py
├── etape3_demo.py
├── etape4_demo.py
├── etape5_demo.py
└── .gitignore
```

## Fonctionnalités principales

- optimisation de la collecte de déchets par méthode graphique et simplex
- modélisation des contraintes de carburant, temps et budget
- simulation de capteurs IoT et alertes de niveau
- optimisation des tournées de collecte
- visualisation des résultats et export de rapports
- interface utilisateur pour dashboard et démonstration

## Modèle mathématique

### Chapitre 1

Maximiser :

Z = 8x₁ + 6x₂

avec solution optimale : x₁ = 11, x₂ = 1, Z = 94 tonnes/jour.

### Chapitre 2

Maximiser :

Z = 8x₁ + 7x₂ + 11x₃

avec solution optimale : x₁ = 2, x₂ = 5, x₃ = 5, Z = 106 tonnes/jour.

## Tests

```bash
python -m pytest -q
```

## Licence

Ce projet est distribué sous licence MIT. Voir le fichier LICENSE pour plus de détails.

## Références

- projet d’optimisation IoT inspiré de solutions de gestion intelligente des déchets
- méthodes d’optimisation linéaire et simplex appliquées à la logistique urbaine
