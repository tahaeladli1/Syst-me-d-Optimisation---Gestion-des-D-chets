# 🗑️ Système d'Optimisation — Gestion des Déchets
### EMSI — 3ème Année Ingénierie Informatique et Réseaux — 2025/2026

**Équipe :** Yahya Zaizi · Taki Mohamed Imrane ·  · Youssef Et-talhaouy · Taha Aideli

---

## 📦 Installation rapide

```bash
# 1. Cloner / décompresser le projet
cd waste_management

# 2. Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate      # Linux/Mac
venv\Scripts\activate         # Windows

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Vérifier l'installation (Étape 1)
python setup_check.py

# 5. Lancer la démo CLI
python main.py --mode cli
```

---

## 🗂️ Structure du Projet

```
waste_management/
├── main.py                   ← Point d'entrée principal
├── setup_check.py            ← Vérification Étape 1
├── requirements.txt
├── README.md
├── config/
│   └── settings.py           ← Paramètres globaux
├── modules/                  ← Algorithmes (Étapes 2, 3, 4)
│   ├── linear_prog.py
│   ├── simplex.py
│   ├── iot_sensors.py
│   └── route_optimizer.py
├── ui/                       ← Interfaces (Étape 5)
│   ├── dashboard.py
│   └── web_app.py
├── data/
│   └── sample_data.json      ← Données de simulation
├── assets/                   ← Images & icônes
├── exports/                  ← Rapports générés
└── tests/
    └── test_etape1.py
```

---

## 🚀 Étapes du Projet

| Étape | Titre | Statut |
|-------|-------|--------|
| **1** | Configuration & Structure | ✅ Complète |
| **2** | Algorithmes d'Optimisation (LP + Simplexe) | 🔜 |
| **3** | Intégration IoT (ROHITH-M10) | 🔜 |
| **4** | Optimisation des Routes (jtsimoes) | 🔜 |
| **5** | Interface GUI & Dashboard Web | 🔜 |

---

## 🔑 Modèle Mathématique

**Chapitre 1** — Max Z = 8x₁ + 6x₂ (2 variables, méthode graphique)
→ Solution : x₁=11, x₂=1, **Z = 94 t/jour**

**Chapitre 2** — Max Z = 8x₁ + 7x₂ + 11x₃ (3 variables, simplexe)
→ Solution : x₁=2, x₂=5, x₃=5, **Z = 106 t/jour ★**

---

## 🔗 Projets de Référence

- **IoT Monitoring** : https://github.com/ROHITH-M10/IOT-Smart-Waste-Management-System
- **Route Optimizer** : https://github.com/jtsimoes/smart-city-waste-management
