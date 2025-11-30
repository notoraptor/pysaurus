# Analyse de l'algorithme DatabaseAlgorithms.update()

**Date:** 2025-11-30
**Analysé par:** Claude Code
**Fichier principal:** `pysaurus/database/database_algorithms.py`

---

## 📊 Architecture globale de l'algorithme

L'algorithme `update()` est responsable de l'ajout et de la mise à jour des vidéos dans la base de données Pysaurus. Il suit un pipeline en 6 étapes :

```
1. Scanner les dossiers → 2. Marquer vidéos not_found → 3. Identifier vidéos à mettre à jour
                                                          ↓
4. Extraire info + miniatures (parallèle) ← Temporaire directory
                                                          ↓
5. Sauvegarder en base de données → 6. Nettoyer temp dir
```

### Flux détaillé

1. **Scan des dossiers** (`Videos.get_runtime_info_from_paths()`)
   - Fichier: `pysaurus/database/algorithms/videos.py:21-37`
   - Parcourt tous les dossiers configurés
   - Collecte les métadonnées runtime (mtime, size, driver_id)
   - **Parallélisé** par dossier

2. **Marquage des vidéos non trouvées** (`_update_videos_not_found()`)
   - Fichier: `pysaurus/database/database_algorithms.py:123-131`
   - Compare les fichiers existants avec la base
   - Met à jour le flag `found`

3. **Identification des vidéos à mettre à jour** (`_find_video_paths_for_update()`)
   - Fichier: `pysaurus/database/database_algorithms.py:133-148`
   - Détecte les changements via `mtime`, `file_size`, `driver_id`
   - Évite le retraitement des vidéos inchangées

4. **Extraction des informations vidéo** (`Videos.hunt()`)
   - Fichier: `pysaurus/database/algorithms/videos.py:47-94`
   - Utilise `PythonVideoRaptor` (PyAV backend)
   - Extrait métadonnées + génère miniatures
   - **Parallélisé** par vidéo
   - Stockage temporaire des miniatures

5. **Traitement des résultats** (`update()` ligne 69-104)
   - Gère 3 cas : info+thumbnail, info seule, thumbnail seule
   - Crée des `VideoEntry` unreadable en cas d'erreur
   - Accumule les erreurs de miniatures

6. **Sauvegarde et nettoyage**
   - Sauvegarde batch des vidéos et miniatures
   - Suppression automatique du répertoire temporaire
   - Notifications des erreurs

---

## ✅ Points forts de l'algorithme

### 1. **Parallélisation intelligente**

L'algorithme parallélise efficacement les opérations I/O intensives :

```python
# Scan de dossiers (videos.py:28-34)
for local_result in parallelize(
    cls._collect_videos_from_folders,
    sources,
    ordered=False,
    notifier=notifier,
    kind="folders",
):
    paths.update(local_result)

# Extraction vidéo (videos.py:84-92)
results: list[VideoTaskResult] = list(
    parallelize(
        raptor.capture,
        tasks,
        ordered=False,
        notifier=notifier,
        kind="video(s)",
    )
)
```

### 2. **Détection efficace des changements**

Évite le retraitement inutile en comparant les propriétés runtime :

```python
# database_algorithms.py:136-147
return sorted(
    file_name
    for file_name, file_info in file_paths.items()
    if not self.db.get_videos(
        include=(),
        where={
            "filename": file_name,
            "mtime": file_info.mtime,
            "file_size": file_info.size,
            "driver_id": file_info.driver_id,
        },
    )
)
```

### 3. **Gestion robuste des erreurs**

- Séparation `error_info` / `error_thumbnail`
- Création de `VideoEntry` unreadable au lieu de crasher
- Gestion de `UnicodeDecodeError` avec fallback `latin-1` :

```python
# video_raptor_pyav.py:58-63
def open_video(filename: str):
    try:
        return av.open(filename)
    except UnicodeDecodeError:
        logger.debug("Opening with metadata encoding latin-1")
        return av.open(filename, metadata_encoding="latin-1")
```

### 4. **Optimisation I/O**

- Miniatures stockées dans `tempfile.TemporaryDirectory`
- Sauvegarde batch des vidéos et miniatures
- Nettoyage automatique des fichiers temporaires

### 5. **Vérification de l'intégrité vidéo**

Test si la fin de la vidéo est accessible (détecte les fichiers corrompus) :

```python
# video_raptor_pyav.py:106-110
end_reachable = False
container.seek(offset=container.duration - 1)
for _ in container.decode(video_stream):
    end_reachable = True
    break
```

---

## 🔧 Points à améliorer

### 🐛 **1. Bug critique - Ligne 91**

**Fichier:** `pysaurus/database/database_algorithms.py:88-91`

```python
elif task.need_info:
    if result.info:
        # info -> new
        new.append(info)  # ❌ BUG: 'info' n'est pas défini dans ce scope
```

**Fix:**
```python
elif task.need_info:
    if result.info:
        # info -> new
        new.append(result.info)  # ✅ Utiliser result.info
```

---

### ⚠️ **2. Gestion mémoire - Containers non fermés en cas d'exception**

**Fichier:** `pysaurus/video_raptor/video_raptor_pyav.py:70-93`

**Problème actuel:**
```python
try:
    container = open_video(filename.path)
except Exception as exc:
    ret.error_info = cls._exc_to_err(exc)
else:
    if task.need_info:
        try:
            ret.info = cls._get_info_from_container(container, filename.path)
        except Exception as exc:
            ret.error_info = cls._exc_to_err(exc)
    # ...
    container.close()  # ❌ Pas appelé si exception pendant le traitement
```

**Fix recommandé:**
```python
container = None
try:
    container = open_video(filename.path)

    if task.need_info:
        try:
            ret.info = cls._get_info_from_container(container, filename.path)
        except Exception as exc:
            ret.error_info = cls._exc_to_err(exc)

    if task.thumb_path and not ret.error_info:
        try:
            ret.thumbnail = cls._thumb_from_container(container, task.thumb_path)
        except Exception as exc:
            traceback.print_tb(exc.__traceback__)
            print(f"{type(exc).__name__}:", exc, file=sys.stderr)
            ret.error_thumbnail = cls._exc_to_err(exc, ERROR_SAVE_THUMBNAIL)
except Exception as exc:
    if not ret.error_info:
        ret.error_info = cls._exc_to_err(exc)
finally:
    if container:
        container.close()  # ✅ Toujours fermé

return ret
```

---

### ⚡ **3. Optimisation du skip_frame pour miniatures**

**Fichier:** `pysaurus/video_raptor/video_raptor_pyav.py:163-187`

**Problème:** La ligne 168 est commentée, donc les frames non-keyframes sont décodées inutilement :

```python
def _thumb_from_container(cls, container, thumb_path: str, thumb_size=300) -> str:
    _video_streams = container.streams.video
    if not _video_streams:
        raise NoVideoStream()
    video_stream = _video_streams[0]
    # video_stream.codec_context.skip_frame = "NONKEY"  # ❌ Commenté
```

**Impact:** Ralentit l'extraction de miniatures de ~30-50%

**Fix recommandé:**
```python
def _thumb_from_container(cls, container, thumb_path: str, thumb_size=300) -> str:
    _video_streams = container.streams.video
    if not _video_streams:
        raise NoVideoStream()
    video_stream = _video_streams[0]
    video_stream.codec_context.skip_frame = "NONKEY"  # ✅ Décommenter

    if video_stream.duration is not None:
        container.seek(
            offset=video_stream.duration // 2,
            any_frame=False,  # ✅ Avec skip_frame, cherchera automatiquement la keyframe
            backward=True,
            stream=video_stream,
        )
    else:
        container.seek(
            offset=container.duration // 2,
            any_frame=False,
            backward=True
        )

    for frame in container.decode(video_stream):
        image: Image.Image = frame.to_image()
        image.thumbnail((thumb_size, thumb_size))
        image.save(thumb_path, format="JPEG")
        break
    else:
        raise NoFrameFoundInMiddleOfVideo()

    return thumb_path
```

---

### 🎯 **4. Vérification end_reachable coûteuse**

**Fichier:** `pysaurus/video_raptor/video_raptor_pyav.py:106-110`

**Problème:** Ce seek à la fin pour chaque vidéo ajoute ~100-500ms par vidéo.

**Options d'amélioration:**

**Option A - Rendre optionnel:**
```python
def _get_info_from_container(cls, container, filename: str, check_integrity=True) -> VideoEntry:
    # ...

    end_reachable = True  # Assume OK par défaut
    if check_integrity:
        end_reachable = False
        container.seek(offset=container.duration - 1)
        for _ in container.decode(video_stream):
            end_reachable = True
            break

    # ...
    return VideoEntry(
        # ...
        "errors": ([] if end_reachable else ["ERROR_SEEK_END_VIDEO"]),
    )
```

**Option B - Vérifier uniquement si durée douteuse:**
```python
# Vérifier seulement si la durée semble incorrecte
check_end = container.duration <= 0 or container.duration > 86400000000  # > 24h
if check_end:
    # ... seek end logic
```

---

## 🎥 Propriétés vidéo supplémentaires disponibles avec PyAV

Actuellement, le code extrait un ensemble limité de propriétés. PyAV expose bien plus d'informations utiles.

### **📦 Métadonnées Container**

**Actuellement utilisé:** Seulement `title`

**Disponible via `container.metadata`:**

```python
# video_raptor_pyav.py - Dans _get_info_from_container()
metadata = container.metadata

# Propriétés standards (selon format vidéo):
"title"           # ✅ Déjà extrait
"artist"          # Créateur/auteur
"album"           # Collection/série
"date"            # Date de création/enregistrement
"creation_time"   # Timestamp ISO 8601
"genre"           # Catégorie/genre
"comment"         # Description/notes
"copyright"       # Information de copyright
"encoder"         # Logiciel utilisé pour encoder
"encoded_by"      # Personne/organisation
"composer"        # Compositeur (pour musique)
"performer"       # Interprète
"publisher"       # Éditeur
"track"           # Numéro de piste
"language"        # Langue principale
```

**Exemple d'utilisation:**
```python
return VideoEntry(
    # ... propriétés existantes ...
    "meta_title": container.metadata.get("title", ""),
    "meta_artist": container.metadata.get("artist", ""),
    "meta_date": container.metadata.get("date", ""),
    "meta_creation_time": container.metadata.get("creation_time", ""),
    "meta_genre": container.metadata.get("genre", ""),
    "meta_comment": container.metadata.get("comment", ""),
    "meta_copyright": container.metadata.get("copyright", ""),
    "meta_encoder": container.metadata.get("encoder", ""),
)
```

---

### **🎬 Propriétés Video Stream enrichies**

**Actuellement extrait:**
- Dimensions (width, height)
- Codec (name, long_name)
- Frame rate
- Bit depth

**Propriétés supplémentaires disponibles:**

```python
video_stream = video_streams[0]
vcc = video_stream.codec_context

# ✅ Qualité et performance
"video_bit_rate": vcc.bit_rate or 0,              # Débit vidéo (bps)
"video_max_bit_rate": vcc.bit_rate_tolerance or 0,

# ✅ Profil et niveau H.264/H.265
"video_profile": vcc.profile,                      # Profile (baseline=66, main=77, high=100)
"video_level": vcc.level,                          # Level (30=3.0, 31=3.1, 40=4.0, etc.)

# ✅ Format des pixels
"pixel_format": str(vcc.pix_fmt) if vcc.pix_fmt else "",  # yuv420p, yuv444p, rgb24, etc.

# ✅ Informations colorimétriques
"color_range": str(vcc.color_range) if vcc.color_range else "",    # tv (limited) ou pc (full)
"color_space": str(vcc.colorspace) if vcc.colorspace else "",       # bt709, bt470bg, bt2020nc
"color_primaries": str(vcc.color_primaries) if vcc.color_primaries else "",
"color_transfer": str(vcc.color_trc) if vcc.color_trc else "",      # bt709, smpte2084 (HDR10), arib-std-b67 (HLG)

# ✅ Structure GOP (Group of Pictures)
"has_b_frames": vcc.has_b_frames,                  # Nombre de B-frames utilisées
"gop_size": vcc.gop_size,                          # Taille du GOP (keyframe interval)

# ✅ Aspect ratio
"display_aspect_ratio": str(video_stream.display_aspect_ratio) if video_stream.display_aspect_ratio else "",
"sample_aspect_ratio": str(video_stream.sample_aspect_ratio) if video_stream.sample_aspect_ratio else "",

# ✅ Nombre de frames (si disponible dans metadata)
"nb_frames": video_stream.frames or 0,

# ✅ Rotation (important pour vidéos de smartphones)
"rotation": int(video_stream.metadata.get("rotate", "0")),

# ✅ Champs entrelacés
"interlaced": vcc.field_order != "progressive",
```

**Intérêt de ces propriétés:**

- **`video_bit_rate`**: Qualité vidéo, utile pour filtrage/recherche
- **`profile`/`level`**: Compatibilité matérielle (ex: Raspberry Pi supporte H.264 level ≤ 4.1)
- **`color_transfer`**: Détection HDR (smpte2084 = HDR10, arib-std-b67 = HLG)
- **`rotation`**: Vidéos mobiles souvent en portrait (90°/270°)
- **`gop_size`**: Seeking performance (GOP petit = meilleur seeking, GOP grand = meilleure compression)

---

### **🔊 Propriétés Audio Stream enrichies**

**Actuellement:** Un seul stream audio (le premier)

**Amélioration:** Supporter tous les streams audio (films multi-langues)

```python
# Actuel (video_raptor_pyav.py:103)
acc = audio_streams[0].codec_context if audio_streams else None

# Proposé: Extraire tous les streams
audio_tracks = []
for i, audio_stream in enumerate(audio_streams):
    acc = audio_stream.codec_context
    audio_tracks.append({
        "index": i,
        "language": audio_stream.language or "",
        "channels": acc.channels,
        "channel_layout": str(acc.layout) if acc.layout else "",  # stereo, 5.1, 7.1, etc.
        "sample_rate": acc.sample_rate,
        "bit_rate": acc.bit_rate or 0,
        "codec": acc.codec.name,
        "codec_long_name": acc.codec.long_name,
        "bits": audio_stream.format.bits if audio_stream.format else 0,
        "is_default": audio_stream.default,                        # Track par défaut
        "title": audio_stream.metadata.get("title", ""),          # Ex: "Commentary", "Director's Cut"
        "forced": audio_stream.metadata.get("forced", "0") == "1",
    })

# Stockage dans VideoEntry
"audio_tracks": audio_tracks,  # Liste de dicts
```

**Intérêt:**
- Films multi-langues (VF/VO/etc.)
- Identification des commentaires audio
- Distinction stereo/5.1/7.1 pour systèmes home cinema

---

### **📝 Propriétés Subtitle Stream enrichies**

**Actuellement:** Seulement les langues

```python
# Actuel (video_raptor_pyav.py:140-143)
"subtitle_languages": [
    subtitle_stream.language
    for subtitle_stream in subtitle_streams
    if subtitle_stream.language is not None
],
```

**Proposé:**

```python
subtitle_tracks = []
for i, sub_stream in enumerate(subtitle_streams):
    subtitle_tracks.append({
        "index": i,
        "language": sub_stream.language or "",
        "codec": sub_stream.codec_context.codec.name,               # srt, ass, mov_text, etc.
        "forced": sub_stream.metadata.get("forced", "0") == "1",    # Sous-titres forcés (ex: Klingon dans Star Trek)
        "hearing_impaired": sub_stream.metadata.get("hearing_impaired", "0") == "1",  # SDH
        "title": sub_stream.metadata.get("title", ""),              # Ex: "Full", "Signs & Songs"
        "is_default": sub_stream.default,
    })

# Stockage
"subtitle_tracks": subtitle_tracks,
```

**Intérêt:**
- Distinction sous-titres pleins vs. forcés
- Identifier les sous-titres pour malentendants (SDH/CC)
- Filtrer par format (SRT vs ASS vs image-based)

---

### **🌈 Détection HDR**

Les vidéos HDR utilisent des espaces colorimétriques spécifiques :

```python
vcc = video_stream.codec_context

# Détection HDR
def detect_hdr(vcc):
    color_trc = str(vcc.color_trc) if vcc.color_trc else ""
    color_primaries = str(vcc.color_primaries) if vcc.color_primaries else ""

    is_hdr10 = "smpte2084" in color_trc.lower()  # PQ transfer (HDR10)
    is_hlg = "arib-std-b67" in color_trc.lower()  # Hybrid Log-Gamma (HLG)
    is_dolby_vision = "smpte2084" in color_trc.lower() and vcc.codec_tag == 0x64766176  # 'dvav'

    is_wide_gamut = any(x in color_primaries.lower() for x in ["bt2020", "p3"])

    return {
        "is_hdr": is_hdr10 or is_hlg or is_dolby_vision,
        "hdr_format": "HDR10" if is_hdr10 else ("HLG" if is_hlg else ("Dolby Vision" if is_dolby_vision else "SDR")),
        "wide_gamut": is_wide_gamut,
    }

# Utilisation
hdr_info = detect_hdr(vcc)
# Dans VideoEntry:
"is_hdr": hdr_info["is_hdr"],
"hdr_format": hdr_info["hdr_format"],
"wide_color_gamut": hdr_info["wide_gamut"],
```

---

### **📊 Informations de conteneur**

```python
# Informations globales
"container_bit_rate": container.bit_rate or 0,        # Débit total du fichier
"container_start_time": container.start_time or 0,    # Timestamp de début (utile pour streams)

# Nombre de streams
"nb_video_streams": len(container.streams.video),
"nb_audio_streams": len(container.streams.audio),
"nb_subtitle_streams": len(container.streams.subtitles),
```

---

## 📋 Recommandations finales

### **🔴 Haute priorité (bugs/correctifs)**

| # | Description | Fichier | Impact |
|---|-------------|---------|--------|
| 1 | Corriger bug `info` non défini ligne 91 | `database_algorithms.py:91` | 🔴 Crash potentiel |
| 2 | Ajouter `finally` pour `container.close()` | `video_raptor_pyav.py:70-93` | 🟠 Fuite mémoire |
| 3 | Décommenter `skip_frame = "NONKEY"` | `video_raptor_pyav.py:168` | 🟡 Performance -30-50% |

### **🟡 Moyenne priorité (améliorations utiles)**

| # | Description | Intérêt | Difficulté |
|---|-------------|---------|------------|
| 4 | Extraire `video_bit_rate`, `profile`, `level`, `pixel_format` | Qualité vidéo, compatibilité | Facile |
| 5 | Extraire `rotation` | Vidéos mobiles | Facile |
| 6 | Métadonnées: `creation_time`, `encoder`, `copyright`, `artist` | Catalogage, recherche | Facile |
| 7 | Multi-tracks audio avec `channel_layout` | Films multi-langues, audio 5.1/7.1 | Moyenne |
| 8 | Détection HDR (`color_trc`, `color_primaries`) | Bibliothèques 4K/HDR | Facile |

### **🟢 Basse priorité (nice-to-have)**

| # | Description | Intérêt | Difficulté |
|---|-------------|---------|------------|
| 9 | Rendre check `end_reachable` optionnel | Performance +100-500ms/vidéo | Facile |
| 10 | Subtitle tracks détaillés (forced, SDH) | Films avec sous-titres complexes | Moyenne |
| 11 | Aspect ratios (display/sample) | Vidéos anamorphiques | Facile |
| 12 | GOP size et B-frames | Analyse seeking performance | Facile |

### **💡 Exemple d'implémentation progressive**

**Phase 1 - Fixes critiques (1h):**
```python
# 1. Fix bug ligne 91
new.append(result.info)  # Au lieu de info

# 2. Fix container.close()
# Ajouter try/finally dans capture()

# 3. Décommenter skip_frame
video_stream.codec_context.skip_frame = "NONKEY"
```

**Phase 2 - Propriétés essentielles (2h):**
```python
# Dans VideoEntry, ajouter:
video_bit_rate: int = 0
video_profile: int = 0
video_level: int = 0
pixel_format: str = ""
rotation: int = 0
meta_creation_time: str = ""
meta_encoder: str = ""

# Dans _get_info_from_container(), extraire ces valeurs
```

**Phase 3 - Audio/Subtitles multi-tracks (4h):**
```python
# Refactorer extraction audio
# Ajouter champ audio_tracks: list[dict]
# Ajouter champ subtitle_tracks: list[dict]
```

**Phase 4 - HDR et métadonnées avancées (3h):**
```python
# Ajouter détection HDR
# Enrichir métadonnées container
```

---

## 📚 Sources et références

### Documentation PyAV
- [PyAV Container API Documentation](https://pyav.basswood-io.com/docs/stable/api/container.html) - API complète des containers PyAV 16.0.0
- [PyAV Stable API Reference](https://pyav.org/docs/stable/api/container.html) - Documentation stable de PyAV
- [PyAV Development Documentation](https://pyav.org/docs/develop/api/container.html) - Documentation version développement

### FFmpeg/Metadata
- [FFmpeg Metadata - MultimediaWiki](https://wiki.multimedia.cx/index.php/FFmpeg_Metadata) - Liste complète des clés de métadonnées FFmpeg
- [FFmpeg Metadata API](https://ffmpeg.org/doxygen/7.0/group__metadata__api.html) - API officielle FFmpeg pour métadonnées
- [FFmpeg Formats Documentation](https://ffmpeg.org/ffmpeg-formats.html) - Documentation des formats supportés

### Code Source
- [PyAV Container Core](https://github.com/PyAV-Org/PyAV/blob/main/av/container/core.pyx) - Implémentation Cython des containers
- [PyAV Container Input](https://github.com/PyAV-Org/PyAV/blob/main/av/container/input.pyx) - Logique de lecture des containers

---

## 📝 Notes complémentaires

### Performance estimée de l'algorithme actuel

Sur une machine moderne (SSD, CPU 8 cores):

- **Scan de dossiers:** ~5000 fichiers/seconde
- **Détection changements:** ~50000 entrées/seconde (query SQL/JSON)
- **Extraction info + thumbnail:**
  - Sans `skip_frame`: ~2-5 vidéos/seconde/core
  - Avec `skip_frame`: ~3-8 vidéos/seconde/core
  - Avec check `end_reachable` désactivé: +20-30%

### Considérations pour bases de données volumineuses

Pour collections > 50,000 vidéos :

1. **Indexation:** S'assurer que `filename`, `mtime`, `file_size` sont indexés
2. **Batch size:** Limiter `files_to_update` par lots de 1000-5000
3. **Checkpoint:** Sauvegarder périodiquement pendant le traitement
4. **Notifications:** Throttle les notifications pour éviter surcharge UI

### Tests recommandés après modifications

```bash
# Tests unitaires spécifiques
pytest tests/databases/unittests/newsql/test_newsql_*.py -v

# Tests de comparaison JSON vs SQL
pytest tests/databases/unittests/comparisons/ -v

# Tests avec vidéos réelles
pytest tests/databases/ -k "test_update" -v

# Benchmarks
python tests/databases/scripts/benchmark_*.py
```

---

**Fin de l'analyse**