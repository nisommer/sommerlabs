"""Maquette 3D du Compagnon de table, forme « Onigiri » (prototype de travail).

Reprend les cotes de la maquette OpenSCAD Onigiri.scad : 92 mm de large,
78 mm de haut, 42 mm de profondeur, arêtes biseautées de 1,2 mm, façade
« nori » vert foncé de 55 × 35 mm, fenêtre du visage 40 × 24 mm centrée
à 28 mm au-dessus de la table, objectif de 5 mm à 51 mm.

Génère appareils/modeles/onigiri.glb (navigateur, Android) et
appareils/modeles/onigiri.usdz (iPhone, Coup d'œil en réalité augmentée).
Dimensions réelles en mètres, le dessous posé à y = 0, la façade vers +z.

    pip install trimesh numpy scipy shapely mapbox_earcut usd-core
    python3 outils/maquette_onigiri.py
"""
from pathlib import Path

import numpy as np
import trimesh
from shapely.geometry import Point, Polygon, box

import maquette_appareil as base

SORTIE = Path(__file__).resolve().parent.parent / "appareils" / "modeles"
MM = 0.001

LARGEUR, HAUTEUR, PROFONDEUR = 92, 78, 42
CHANFREIN = 1.2
EPAISSEUR_NORI = 1.2
ECRAN = (40, 24)          # fenêtre du visage
CENTRE_ECRAN = 28
NORI = (55, 35)
CENTRE_CAMERA, DIAMETRE_CAMERA = 51, 5
PROF = PROFONDEUR - EPAISSEUR_NORI   # profondeur de la coque

# Couleurs linéaires (glTF et USD) : le vert nori de la maquette (0.17, 0.23, 0.17 en sRGB) donne ici 0.05, 0.08, 0.05.
MATIERES = {
    "coque": dict(couleur=(0.96, 0.91, 0.78), rugosite=0.7, emission=(0, 0, 0)),
    "nori": dict(couleur=(0.05, 0.08, 0.05), rugosite=0.55, emission=(0, 0, 0)),
    "ecran": dict(couleur=(0.08, 0.10, 0.11), rugosite=0.15, emission=(0, 0, 0)),
    "led": dict(couleur=(0.45, 0.92, 0.78), rugosite=0.3, emission=(0.35, 0.9, 0.72)),
    "objectif": dict(couleur=(0.04, 0.04, 0.05), rugosite=0.1, emission=(0, 0, 0)),
}

# Moitié droite du contour de Onigiri.scad (x ≥ 0), en mm ; la gauche est symétrique.
DEMI_CONTOUR = [
    (35, 0), (36.68692, 0.09230324), (38.24537, 0.3634259), (39.67188, 0.8046875),
    (40.96296, 1.407407), (42.11516, 2.162905), (43.125, 3.0625), (43.989, 4.097512),
    (44.7037, 5.259259), (45.26562, 6.539062), (45.6713, 7.928241), (45.91725, 9.418113),
    (46, 11), (45.93924, 12.25), (45.76389, 13.5), (45.48438, 14.75), (45.11111, 16),
    (44.65451, 17.25), (44.125, 18.5), (43.53299, 19.75), (42.88889, 21), (42.20312, 22.25),
    (41.48611, 23.5), (40.74826, 24.75), (40, 26), (37.71065, 29.80729), (35.35185, 33.70833),
    (32.9375, 37.67188), (30.48148, 41.66667), (27.99769, 45.66146), (25.5, 49.625),
    (23.00231, 53.52604), (20.51852, 57.33333), (18.0625, 61.01562), (15.64815, 64.54167),
    (13.28935, 67.88021), (11, 71), (10.17818, 72.06204), (9.358796, 73.0463), (8.535937, 73.95),
    (7.703704, 74.77037), (6.856192, 75.50463), (5.9875, 76.15), (5.091725, 76.7037),
    (4.162963, 77.16296), (3.195312, 77.525), (2.18287, 77.78704), (1.119734, 77.9463), (0, 78),
]


def contour():
    droite = [(x * LARGEUR / 92, y * HAUTEUR / 78) for x, y in DEMI_CONTOUR]
    gauche = [(-x, y) for x, y in reversed(droite[:-1])][:-1]
    return Polygon(droite + gauche)


def capsule(l, h, r, cy):
    return box(-l / 2 + r, cy - h / 2 + r, l / 2 - r, cy + h / 2 - r).buffer(r, resolution=12)


def anneau(poly, z):
    """Sommets du contour (mm) à la profondeur z (mm)."""
    xy = np.array(poly.exterior.coords[:-1])
    return np.column_stack([xy, np.full(len(xy), z)])


def coque():
    """Prisme du contour, arêtes avant et arrière biseautées (enveloppe convexe, comme le hull() du .scad)."""
    c = contour()
    retrait = c.buffer(-CHANFREIN, join_style=2)
    pts = np.vstack([anneau(retrait, 0), anneau(c, CHANFREIN),
                     anneau(c, PROF - CHANFREIN), anneau(retrait, PROF)])
    return trimesh.convex.convex_hull(pts)


def extrusion(poly, epaisseur, z0):
    m = trimesh.creation.extrude_polygon(poly, epaisseur)
    m.apply_translation([0, 0, z0])
    return m


def pieces():
    """Liste (nom, matière, maillage) en mètres. Le .scad travaille en z = profondeur depuis la façade."""
    out = [("coque", "coque", coque())]
    fenetre = capsule(*ECRAN, 2, CENTRE_ECRAN)
    nori = capsule(*NORI, 5, CENTRE_ECRAN).difference(fenetre)
    out.append(("nori", "nori", extrusion(nori, EPAISSEUR_NORI, -EPAISSEUR_NORI)))

    # Écran sombre derrière la fenêtre, un peu en retrait de la façade nori
    out.append(("ecran", "ecran", extrusion(fenetre, 0.4, -0.4)))
    z_visage = -0.4 - 0.5

    # Visage lumineux : deux yeux et un sourire en points
    for x in (-8, 8):
        out.append((f"oeil_{'g' if x < 0 else 'd'}", "led", extrusion(Point(x, CENTRE_ECRAN + 4).buffer(2.8, resolution=12), 0.5, z_visage)))
    for k, t in enumerate(np.linspace(-1, 1, 5)):
        p = Point(7.5 * t, CENTRE_ECRAN - 5.5 + 2.4 * t * t).buffer(1.15, resolution=8)
        out.append((f"sourire_{k}", "led", extrusion(p, 0.5, z_visage)))

    # Objectif de la caméra, au-dessus de la façade
    out.append(("objectif", "objectif", extrusion(Point(0, CENTRE_CAMERA).buffer(DIAMETRE_CAMERA / 2, resolution=16), 0.4, -0.3)))

    # Repère glTF : y vers le haut, façade vers +z (z_gltf = -z_scad), en mètres
    T = np.diag([MM, MM, -MM, 1.0])
    for _, _, m in out:
        m.apply_transform(T)
        m.fix_normals()
    centre_z = -(PROF - EPAISSEUR_NORI) / 2 * MM   # recentrer l'objet en profondeur pour la rotation
    for _, _, m in out:
        m.apply_translation([0, 0, -centre_z])
    return out


if __name__ == "__main__":
    base.MATIERES = MATIERES          # les exports de maquette_appareil lisent ce dictionnaire
    SORTIE.mkdir(parents=True, exist_ok=True)
    liste = pieces()
    base.exporter_glb(liste, SORTIE / "onigiri.glb")
    base.exporter_usdz(liste, SORTIE / "onigiri.usdz")
    t = trimesh.util.concatenate([m for _, _, m in liste])
    taille = (t.bounds[1] - t.bounds[0]) * 100
    print("taille (cm) l × h × p :", " × ".join(f"{x:.1f}" for x in taille))
    for f in ("onigiri.glb", "onigiri.usdz"):
        print(f, (SORTIE / f).stat().st_size // 1024, "Ko")
