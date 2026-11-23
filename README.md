# Sommer Labs

Site statique de Sommer Labs (https://sommerlabs.ch), servi par GitHub Pages depuis la racine de la branche `main`.

- `index.html` : accueil, avec les apps et les appareils
- `perspective/` : page de l'app Perspective (images dans `perspective/images/`) et sa politique de confidentialité
- `appareils/` : page du Compagnon de table, avec le modèle 3D en forme d'onigiri (`appareils/modeles/onigiri.glb` pour le navigateur, `onigiri.usdz` pour la réalité augmentée sur iPhone et iPad) et la vignette de l'accueil (`appareils/images/onigiri-vignette.png`)
- `assets/model-viewer.min.js` : [model-viewer](https://modelviewer.dev) 4.3.1, servi depuis le site (licence BSD dans `assets/model-viewer-LICENSE.txt`)
- `outils/maquette_onigiri.py` : génère les deux fichiers du modèle 3D d'après les cotes de la maquette Onigiri (`pip install trimesh numpy scipy shapely mapbox_earcut usd-core`, puis `cd outils && python3 maquette_onigiri.py`) ; il reprend les fonctions d'export de `outils/maquette_appareil.py` (première maquette, retirée de la page)
- `style.css` : styles communs (clair et sombre)
- `CNAME` : domaine personnalisé pour GitHub Pages
