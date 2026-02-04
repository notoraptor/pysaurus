# À faire

[x] Quand on classe par similarity_id, les différences entre les file titles ne sont plus visibles, alors qu'elles l'étaient, avant.
    **Corrigé** : Le bug était dans `VideoFeatures.get_file_title_diffs()` qui mettait toujours une liste vide pour la première vidéo (référence), même si elle avait un suffixe unique. Maintenant, la référence calcule ses diffs par rapport à la deuxième vidéo.
