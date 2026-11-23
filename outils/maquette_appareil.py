"""Maquette 3D de l'appareil de table (prototype de travail).

Génère appareils/modeles/appareil.glb (navigateur, Android) et
appareils/modeles/appareil.usdz (iPhone, Coup d'œil en réalité augmentée).
Dimensions réelles en mètres, le dessous de l'appareil posé à y = 0.

    pip install trimesh numpy scipy usd-core
    python3 outils/maquette_appareil.py
"""
from pathlib import Path

import numpy as np
import trimesh
from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade, UsdUtils, Vt

SORTIE = Path(__file__).resolve().parent.parent / "appareils" / "modeles"

# Matières : couleur de base (sRGB 0-1), rugosité, émission
MATIERES = {
    "coque": dict(couleur=(0.95, 0.93, 0.89), rugosite=0.55, emission=(0, 0, 0)),
    "ecran": dict(couleur=(0.11, 0.13, 0.16), rugosite=0.18, emission=(0, 0, 0)),
    "led": dict(couleur=(0.45, 0.92, 0.78), rugosite=0.3, emission=(0.35, 0.9, 0.72)),
    "objectif": dict(couleur=(0.05, 0.05, 0.06), rugosite=0.1, emission=(0, 0, 0)),
    "bouton": dict(couleur=(0.82, 0.34, 0.17), rugosite=0.45, emission=(0, 0, 0)),
    "pied": dict(couleur=(0.30, 0.32, 0.35), rugosite=0.8, emission=(0, 0, 0)),
}


def superellipsoide(ax, ay, az, e1=0.35, e2=0.35, nu=48, nv=96):
    """Boîte aux coins arrondis (superellipsoïde), centrée sur l'origine."""
    def p(c, e):
        return np.sign(c) * np.abs(c) ** e

    u = np.linspace(-np.pi / 2, np.pi / 2, nu)
    v = np.linspace(-np.pi, np.pi, nv, endpoint=False)
    U, V = np.meshgrid(u, v, indexing="ij")
    x = ax * p(np.cos(U), e1) * p(np.cos(V), e2)
    y = ay * p(np.sin(U), e1)
    z = az * p(np.cos(U), e1) * p(np.sin(V), e2)
    sommets = np.stack([x, y, z], axis=-1).reshape(-1, 3)
    faces = []
    for i in range(nu - 1):
        for j in range(nv):
            a = i * nv + j
            b = i * nv + (j + 1) % nv
            c = (i + 1) * nv + (j + 1) % nv
            d = (i + 1) * nv + j
            faces += [[a, c, b], [a, d, c]]
    m = trimesh.Trimesh(sommets, np.array(faces), process=True)
    m.update_faces(m.nondegenerate_faces())
    m.fix_normals()
    return m


def disque(rayon, epaisseur, axe="z", sections=48):
    m = trimesh.creation.cylinder(radius=rayon, height=epaisseur, sections=sections)
    if axe == "y":
        m.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
    return m


def pieces():
    """Liste (nom, matière, maillage). Unités : mètres."""
    L, H, P = 0.045, 0.050, 0.040   # demi-largeur, demi-hauteur, demi-profondeur
    out = []
    coque = superellipsoide(L, H, P, 0.38, 0.30)
    out.append(("coque", "coque", coque))

    # Écran du visage (verre sombre), légèrement en relief sur la face avant
    ecran = superellipsoide(0.032, 0.021, 0.004, 0.2, 0.2, 24, 64)
    ecran.apply_translation([0, 0.004, P - 0.0012])
    out.append(("ecran", "ecran", ecran))
    zf = P + 0.0028  # surface de l'écran

    # Deux yeux et un sourire en points lumineux (matrice de LED)
    for x in (-0.012, 0.012):
        oeil = disque(0.0042, 0.0012)
        oeil.apply_translation([x, 0.009, zf])
        out.append((f"oeil_{'g' if x < 0 else 'd'}", "led", oeil))  # noms uniques : un nom en double écrase l'autre dans le GLB
    for k, t in enumerate(np.linspace(-0.9, 0.9, 5)):
        point = disque(0.0016, 0.0010, sections=24)
        point.apply_translation([0.010 * t, -0.008 + 0.0035 * t * t, zf])  # arc : plus bas au milieu
        out.append((f"sourire_{k}", "led", point))

    # Petite caméra au-dessus de l'écran
    bague = disque(0.0045, 0.0016)
    bague.apply_translation([0, 0.036, P - 0.0004])
    out.append(("bague", "ecran", bague))
    lentille = disque(0.0028, 0.0018)
    lentille.apply_translation([0, 0.036, P + 0.0004])
    out.append(("objectif", "objectif", lentille))

    # Bouton de démarrage sur le dessus
    bouton = disque(0.0095, 0.004, axe="y")
    bouton.apply_translation([0, H - 0.0008, -0.004])
    out.append(("bouton", "bouton", bouton))

    # Deux pieds
    for x in (-0.022, 0.022):
        pied = superellipsoide(0.012, 0.004, 0.022, 0.5, 0.5, 16, 32)
        pied.apply_translation([x, -H + 0.0015, 0])
        out.append((f"pied_{'g' if x < 0 else 'd'}", "pied", pied))

    # Poser l'appareil sur la table : dessous à y = 0
    bas = min(m.bounds[0][1] for _, _, m in out)
    for _, _, m in out:
        m.apply_translation([0, -bas, 0])
    return out


def exporter_glb(liste, chemin):
    scene = trimesh.Scene()
    for nom, mat, m in liste:
        d = MATIERES[mat]
        m = m.copy()
        m.visual = trimesh.visual.TextureVisuals(material=trimesh.visual.material.PBRMaterial(
            name=mat,
            baseColorFactor=[*d["couleur"], 1.0],
            metallicFactor=0.0,
            roughnessFactor=d["rugosite"],
            emissiveFactor=list(d["emission"]),
        ))
        scene.add_geometry(m, node_name=nom, geom_name=nom)
    chemin.write_bytes(scene.export(file_type="glb"))


def exporter_usdz(liste, chemin):
    usda = chemin.with_suffix(".usdc")
    stage = Usd.Stage.CreateNew(str(usda))
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    racine = UsdGeom.Xform.Define(stage, "/Appareil")
    stage.SetDefaultPrim(racine.GetPrim())

    mats = {}
    for mat, d in MATIERES.items():
        m = UsdShade.Material.Define(stage, f"/Appareil/Matieres/{mat}")
        s = UsdShade.Shader.Define(stage, f"/Appareil/Matieres/{mat}/Surface")
        s.CreateIdAttr("UsdPreviewSurface")
        s.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*d["couleur"]))
        s.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(d["rugosite"])
        s.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.0)
        s.CreateInput("emissiveColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(*d["emission"]))
        m.CreateSurfaceOutput().ConnectToSource(s.ConnectableAPI(), "surface")
        mats[mat] = m

    for nom, mat, m in liste:
        g = UsdGeom.Mesh.Define(stage, f"/Appareil/{nom}")
        g.CreatePointsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, p)) for p in m.vertices]))
        g.CreateFaceVertexCountsAttr(Vt.IntArray([3] * len(m.faces)))
        g.CreateFaceVertexIndicesAttr(Vt.IntArray([int(i) for i in m.faces.reshape(-1)]))
        g.CreateNormalsAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, n)) for n in m.vertex_normals]))
        g.SetNormalsInterpolation(UsdGeom.Tokens.vertex)
        g.CreateSubdivisionSchemeAttr(UsdGeom.Tokens.none)
        g.CreateExtentAttr(Vt.Vec3fArray([Gf.Vec3f(*map(float, m.bounds[0])), Gf.Vec3f(*map(float, m.bounds[1]))]))
        UsdShade.MaterialBindingAPI.Apply(g.GetPrim()).Bind(mats[mat])
    stage.GetRootLayer().Save()
    if chemin.exists():
        chemin.unlink()
    assert UsdUtils.CreateNewARKitUsdzPackage(Sdf.AssetPath(str(usda)), str(chemin))
    usda.unlink()


if __name__ == "__main__":
    SORTIE.mkdir(parents=True, exist_ok=True)
    liste = pieces()
    exporter_glb(liste, SORTIE / "appareil.glb")
    exporter_usdz(liste, SORTIE / "appareil.usdz")
    t = trimesh.util.concatenate([m for _, _, m in liste])
    taille = (t.bounds[1] - t.bounds[0]) * 100
    print("taille (cm) l × h × p :", " × ".join(f"{x:.1f}" for x in taille))
    for f in ("appareil.glb", "appareil.usdz"):
        print(f, (SORTIE / f).stat().st_size // 1024, "Ko")
