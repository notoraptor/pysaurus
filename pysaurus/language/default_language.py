from pysaurus.core.functions import object_to_dict


def make_text(*paragraphs, sep="\n\n"):
    return sep.join(paragraphs)


def language_to_dict(lang, extend=True):
    dct = object_to_dict(lang, value_wrapper=str.strip)
    if extend:
        dct["__language__"] = lang.__language__
    return dct


class DefaultLanguage:
    __slots__ = ()
    __language__ = "english"

    profile_collect_thumbnails = "Collect thumbnails"
    profile_collect_videos = "Collect videos ({cpu_count} threads)"
    profile_generate_miniatures = "Generating miniatures."
    profile_check_video_thumbnails = "Check videos thumbnails"
    profile_check_unique_thumbnails = "Check unique thumbnails"
    profile_collect_video_infos = "Collect videos info ({cpu_count} threads)"
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
    message_similarity_no_new_videos = "No new videos to check."
    message_similarity_todo = "To do: {count} / {total} comparisons ({percent} %)."
    message_similarity_count_found = (
        "Finally found {nb_similarities} new similarity groups with {nb_images} images."
    )
    message_similarity_count_old = "Found {count} old similarities."
    message_similarity_count_final = "Found {count} total similarities after merging."
    message_similarity_count_pure_new = "Found {count} pure new similarities."
    message_predictor_opt_converged = "Converged in {count} last steps."
    message_predictor_training_set = "Training set: false {count0}, true {count1}"
    message_count_readable_sorted = "{count} readable sorted"
    message_count_unreadable_not_sorted = "{count} unreadable not sorted"
    error_moving_file = "Error {name}: {message}"

    job_step_predictor_opt_converged = (
        "Converged, # {step}, \u00A9 {cost}, \u03b8 [{min_theta}; {max_theta}]"
    )
    job_step_predictor_opt = (
        "# {step}, \u00A9 {cost}, \u03b8 [{min_theta}; {max_theta}]"
    )

    player_title = "Media Player"
    player_text_play = "\u25B6"
    player_text_pause = "\u23F8"
    player_text_next = "Next"
    player_text_repeat = "Repeat"
    player_tooltip_play = "Play"
    player_tooltip_pause = "Pause"
    player_tooltip_position = "Position"
    player_tooltip_volume = "Volume"
