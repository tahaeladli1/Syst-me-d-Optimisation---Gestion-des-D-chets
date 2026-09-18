# ============================================================
#  EMSI — Optimisation de la Gestion des Déchets 2025/2026
#  config/settings.py  —  Paramètres globaux du projet
# ============================================================

# ── Identité du projet ──────────────────────────────────────
PROJECT_NAME    = "Système d'Optimisation — Gestion des Déchets"
VERSION         = "1.0.0"
SCHOOL          = "EMSI"
ACADEMIC_YEAR   = "2025–2026"
AUTHORS         = [
    "Yahya Zaizi",
    "Taki Mohamed Imrane",
    "Yasser Dalali",
    "Youssef Et-talhaouy",
    "Taha Aideli",
]

# ── Contraintes du modèle linéaire (Chapitre 1 & 2) ─────────
FUEL_LIMIT        = 48    # C1 : carburant disponible (unités/jour)
FLEET_LIMIT       = 40    # C2 : capacité opérationnelle (heures/jour)
BUDGET_LIMIT      = 72    # C3 : budget quotidien (milliers DHS/jour)
MIN_MENAGER       = 2     # C4 : minimum camions ménagers
MIN_RECYCLABLE    = 1     # C5 : minimum camions recyclables
MIN_COLLECTE      = 50    # C6 : quantité minimale à collecter (t/jour)

# ── Coefficients de la fonction objectif ────────────────────
#   Z = coef_x1*x1 + coef_x2*x2 + coef_x3*x3  (tonnes/jour)
COEF_X1 = 8    # Camions ménagers
COEF_X2 = 7    # Camions recyclables   (6 au Ch.1 / 7 au Ch.2)
COEF_X3 = 11   # Camions biomédicaux   (Ch.2 uniquement)

# ── Coefficients des contraintes par type de camion ─────────
#   [fuel, fleet, budget]
TRUCK_CONSTRAINTS = {
    "menager"    : {"fuel": 4, "fleet": 2, "budget": 6},
    "recyclable" : {"fuel": 3, "fleet": 4, "budget": 4},
    "biomedical" : {"fuel": 5, "fleet": 3, "budget": 8},
}

# ── Couleurs de l'interface ──────────────────────────────────
COLORS = {
    "primary"    : "#1F4E79",
    "secondary"  : "#2E75B6",
    "success"    : "#107C41",
    "warning"    : "#C55A11",
    "danger"     : "#C00000",
    "teal"       : "#00B0A0",
    "purple"     : "#7030A0",
    "bg_dark"    : "#1E293B",
    "bg_medium"  : "#334155",
    "bg_light"   : "#F1F5F9",
    "white"      : "#FFFFFF",
    "text_light" : "#94A3B8",
    "menager"    : "#2196F3",
    "recyclable" : "#4CAF50",
    "biomedical" : "#FF9800",
}

# ── Localisation (Marrakech par défaut) ──────────────────────
DEFAULT_CITY    = "Marrakech"
DEPOT_LAT       = 31.6295
DEPOT_LNG       = -7.9811
MAP_ZOOM        = 13

# ── API externes (optionnelles) ──────────────────────────────
IOT_API_URL     = "https://api.iot-waste-sensor.com/v1"
MAPBOX_TOKEN    = ""     # Renseigner votre token Mapbox ici
IOT_POLL_SEC    = 300    # Intervalle de rafraîchissement IoT (secondes)
IOT_THRESHOLD   = 70     # Seuil d'urgence de remplissage (%)

# ── Fenêtre GUI ──────────────────────────────────────────────
WINDOW_WIDTH    = 1200
WINDOW_HEIGHT   = 750
FONT_FAMILY     = "Segoe UI"

# ── Chemins ─────────────────────────────────────────────────
import os
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
ASSETS_DIR  = os.path.join(BASE_DIR, "assets")
EXPORT_DIR  = os.path.join(BASE_DIR, "exports")

for _d in (DATA_DIR, ASSETS_DIR, EXPORT_DIR):
    os.makedirs(_d, exist_ok=True)
