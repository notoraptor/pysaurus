# Test Fixtures

Ce dossier contient des fichiers de test utilisés par la suite de tests de Pysaurus.

## test_video_minimal.mp4

Vidéo de test minimale utilisée pour les tests de cycle de vie complet (ajout/suppression).

### Caractéristiques
- **Taille** : ~1.5 KB
- **Résolution** : 64x64 pixels
- **Durée** : 1 seconde
- **FPS** : 1 frame par seconde
- **Codec** : H.264 (libx264)
- **Audio** : Aucun
- **Contenu** : Frame rouge unie

### Création

Créée avec PyAV :
```bash
python create_test_video.py
```

### Utilisation dans les tests

Cette vidéo est utilisée dans `test_video_lifecycle.py` pour tester :
1. **Ajout de vidéo** via scan de dossier
2. **Suppression de vidéo** (DB + fichier physique)

La vidéo est copiée dans des dossiers temporaires pour chaque test, garantissant l'isolation et la reproductibilité.

### Pourquoi si petite ?

- ✅ **Committable dans git** : < 2 KB ne gonfle pas le repo
- ✅ **Tests rapides** : Scan et traitement instantanés
- ✅ **Valide** : Peut être lue par Pysaurus et FFmpeg
- ✅ **Déterministe** : Toujours les mêmes métadonnées
