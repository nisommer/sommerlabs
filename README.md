# Sommer Labs

Site statique de Sommer Labs (https://sommerlabs.ch), servi par GitHub Pages depuis la racine de la branche `main`.

- `index.html` : accueil, avec les apps et les appareils
- `perspective/` : page de l'app Perspective (images dans `perspective/images/`) et sa politique de confidentialité
- `appareils/` : page des appareils de table, avec le modèle 3D (`appareils/modeles/appareil.glb` pour le navigateur, `appareil.usdz` pour la réalité augmentée sur iPhone et iPad) et la vignette de l'accueil (`appareils/images/`)
- `assets/model-viewer.min.js` : [model-viewer](https://modelviewer.dev) 4.3.1, servi depuis le site (licence BSD dans `assets/model-viewer-LICENSE.txt`)
- `outils/maquette_appareil.py` : génère les deux fichiers du modèle 3D (`pip install trimesh numpy scipy usd-core`, puis `python3 outils/maquette_appareil.py`)
- `style.css` : styles communs (clair et sombre)
- `CNAME` : domaine personnalisé pour GitHub Pages
