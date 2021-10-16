class DefaultLanguage:
    __language__ = "english"

    profile_collect_thumbnails = "Collect thumbnails"
    profile_collect_videos = "Collect videos ({cpu_count} threads)"
    profile_generate_miniatures = "Generating miniatures."
    profile_check_video_thumbnails = "Check videos thumbnails"
    profile_check_unique_thumbnails = "Check unique thumbnails"
    profile_collect_video_thumbnails = (
        "Get thumbnails from JSON through {cpu_count} thread(s)"
    )
    profile_reset_thumbnail_errors = "Reset thumbnail errors"
    profile_collect_comparisons = "Collect comparisons."
    profile_compare_old_vs_new_miniatures = "Cross compare classifiers."
    profile_link_miniature_comparisons = "Link videos ..."
    profile_find_similar_videos = "Find similar videos."
    profile_allocate_edge_map = "Allocating edges map"
    profile_merge_old_and_new_similarities = "Merge new similarities with old ones."
    profile_train = "Train"
    profile_predict = "Predict"
    profile_batch_compute_groups = "batch_compute_groups(n={n}, cpu={cpu_count})"
    profile_classify_similarities_python = (
        "Python images comparison ({cpu_count} thread(s))"
    )
    profile_classify_similarities_native = (
        "Finding similar images using simpler NATIVE comparison."
    )
    profile_allocate_native_data = "Allocate native data"
    profile_move = "Move"
