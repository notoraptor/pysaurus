# Analyse de FileCopier (`pysaurus/core/file_copier.py`)

## Vue d'ensemble

`FileCopier` gère le déplacement physique de fichiers vidéo, appelé depuis
`GuiAPI.move_video_file()`. Il est distinct du déplacement logique d'entrées DB
(`DatabaseAlgorithms.move_video_entries()`).

## Fonctionnement actuel

- **Même disque** : `os.rename()` (instantané)
- **Disques différents** : copie manuelle par blocs de 32 Mo avec progression et annulation
- Préserve `atime`/`mtime` après copie
- Vérifie l'espace disque avant de commencer
- Supprime le fichier partiel si annulation ou erreur

## Qualité du code

Le code est correct et raisonnablement bien fait :
- Vérification espace disque en amont
- Optimisation same-drive via `rename`
- Nettoyage en cas d'erreur ou d'annulation
- Progression notifiée via le système de notifications

## Modules Python existants

Il n'existe **pas de module Python standard** qui combine copie de fichier + progression + annulation :

| Module             | Progression | Annulation | Note           |
|--------------------|-------------|------------|----------------|
| `shutil.copy2`     | Non         | Non        | stdlib         |
| `shutil.move`      | Non         | Non        | stdlib         |
| `tqdm` + copie     | Oui (barre) | Non natif  | tiers, maintenu|

La copie manuelle par blocs est donc l'approche classique et justifiée.

## Améliorations possibles

### 1. `shutil.copystat` au lieu de `utime` seul

Copierait aussi les permissions, pas seulement les timestamps :

```python
# Actuel
FileSystem.utime(self.dst.path, (src_stat.st_atime, src_stat.st_mtime))
# Alternative
shutil.copystat(self.src.path, self.dst.path)
```

### 2. Thread safety du flag `cancel`

`self.cancel = True` depuis un autre thread fonctionne en pratique (grâce au GIL
pour les booléens), mais un `threading.Event` serait plus propre :

```python
self._cancel_event = threading.Event()
# Dans copy_file:
while not self._cancel_event.is_set():
    ...
# Pour annuler:
self._cancel_event.set()
```

### 3. Remplacer `assert` par une exception explicite

Ligne 100 : `assert self.total == self.dst.get_size() == size` crashe en mode
normal ou est ignoré en mode optimisé (`-O`). Une exception explicite serait
plus robuste pour gérer la corruption ou les race conditions.

### 4. `os.sendfile` (Linux uniquement)

Sur Linux, `os.sendfile()` fait la copie dans le kernel sans transiter par
l'espace utilisateur, ce qui est plus rapide. Mais ça complique le suivi de
progression et la portabilité Windows.

## Conclusion

Le code n'a pas besoin d'être réécrit. Les améliorations ci-dessus sont
mineures et optionnelles. Le `TODO` dans `gui_api.py:85`
(`# TODO Rethink Move/Copy feature`) pourrait être résolu en appliquant ces
ajustements.
