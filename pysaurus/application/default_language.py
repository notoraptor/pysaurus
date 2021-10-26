def join_p(*lines):
    return "\n\n".join(lines)


class DefaultLanguage:
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
        "Converged, \u00A9 {cost}, \u03b8 [{min_theta}; {max_theta}]"
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

    gui_database_welcome = "Welcome to {name}"
    gui_database_create = "Create a database"
    gui_database_paths = "Database folders and files"
    gui_database_add_folder = "Add folder"
    gui_database_add_file = "Add file"
    gui_database_button_create = "create database"
    gui_database_open = "Open a database ({count} available)"
    gui_database_update_after_opening = "update after opening"
    gui_database_click_to_open = "Click on a database to open it"
    gui_database_name_placeholder = "Database name."

    gui_home_collected_files = "**Collected** {count} file(s)"
    gui_home_to_load = "To load"

    gui_properties_title = "Properties Management"
    gui_properties_current = "Current properties"
    gui_properties_add_new = "Add a new property"
    gui_properties_enumeration_values = "Enumeration values"
    gui_properties_enumeration_values_multiple = "Enumeration values (first is default)"
    gui_properties_default_value = "Default value"

    attr_audio_bit_rate = "audio bit rate"
    attr_audio_codec = "audio codec"
    attr_audio_codec_description = "audio codec description"
    attr_bit_depth = "bit depth"
    attr_container_format = "container format"
    attr_date = "date modified"
    attr_day = "day"
    attr_disk = "disk"
    attr_extension = "file extension"
    attr_file_size = "file size (bytes)"
    attr_file_title = "file title"
    attr_file_title_numeric = "file title (with numbers)"
    attr_filename = "file path"
    attr_frame_rate = "frame rate"
    attr_height = "height"
    attr_length = "length"
    attr_move_id = "moved files (potentially)"
    attr_properties = "properties"
    attr_quality = "quality"
    attr_sample_rate = "sample rate"
    attr_similarity_id = "similarity"
    attr_size = "size"
    attr_thumbnail_path = "thumbnail path"
    attr_title = "title"
    attr_title_numeric = "title (with numbers)"
    attr_video_codec = "video codec"
    attr_video_codec_description = "video codec description"
    attr_video_id = "video ID"
    attr_width = "width"

    suffix_fps = "fps"
    suffix_hertz = "Hz"
    suffix_kbps = "Kb/s"
    text_bits = "bits"
    text_similarity_id = "Similarity ID"
    text_not_yet_compared = "(not yet compared)"
    text_no_similarities = "(no similarities)"
    text_confirm_move_to = "Confirm move to"

    search_exact = "exactly"
    search_and = "all terms"
    search_or = "any term"
    search_id = "video ID"
    search_exact_sentence = "exact sentence"

    word_page = "page"
    word_pages = "pages"
    word_all = "all"
    word_video = "video"
    word_videos = "videos"
    word_thumbnail = "thumbnail"
    word_thumbnails = "thumbnails"
    word_property = "Property"

    text_grouped = "Grouped"
    text_ungrouped = "Ungrouped"
    text_searched = "Searched {text}"
    text_sorted_by = "Sorted by"
    text_videos = "video(s)"
    text_no_videos_selected = "No videos selected"
    text_unstack = "unstack"
    text_group = "Group {group}/{count}"
    text_no_group = "No groups"
    text_no_search = "No search"
    text_delete = "DELETE"
    text_select = "select"
    text_database = "Database"
    text_all_groups_selected = "All {count} selected"
    text_groups_selected = "{count} selected"
    text_all_videos_selected = "All {count} video(s)"
    text_videos_selected = "{count} / {total} video(s)"
    text_delete_video = "Delete video"
    text_delete_entry = "Delete entry"
    texte_save = "save"
    text_rename = "rename"
    text_database_saved = "Database saved"
    text_database_loaded = "Database loaded"
    text_nb_entries = "{count} entries"
    text_nb_discarded = "{count} discarded"
    text_nb_unreadable_not_found = "{count} unreadable not found"
    text_nb_unreadable_found = "{count} unreadable found"
    text_nb_readable_not_found = "{count} readable not found"
    text_nb_readable_found_without_thumbnails = (
        "{count} readable found without thumbnails"
    )
    text_nb_valid = "{count} valid"
    text_nb_video_errors = "{count} video error(s)"
    text_nb_thumbnail_errors = "{count} thumbnail error(s)"
    text_nb_miniatures_saved = "{count} miniature(s) saved."
    text_done = "{count} done"
    text_profiling = "PROFILING"
    text_profiled = "PROFILED"
    text_no_groups = "No groups"
    text_no_thumbnail = "no thumbnail"
    text_not_found = "(not found)"
    text_not_found_uppercase = "NOT FOUND"
    text_video_unreadable = "Video unreadable"
    text_no_value = "no value"
    text_dismiss = "dismiss"
    text_reset = "reset"
    text_rename_database = "Rename database"
    text_rename_property = "Rename property"
    text_create = "create"
    text_to_remove = "To remove"
    text_current = "Current"
    text_to_add = "To add"
    text_all_values = "all {count} values"
    text_field_type = "Field type"
    text_allow_singletons = "Allow singletons (groups with only 1 video)"
    text_singletons_auto_disabled = "Will look for groups with at least 2 videos."
    text_sort_using = "Sort using:"
    text_field_value = "Field value"
    text_field_value_length = "Field value length"
    text_group_size = "Group size"
    text_sort_reverse = "sort in reverse order"
    text_fill_videos_without_properties = (
        'only videos without values for property "{name}"'
    )
    text_notification_database_ready = "Database open!"
    text_notification_done = "Done!"
    text_notification_cancelled = "Cancelled."
    text_notification_missing_thumbnails = "Missing {count} thumbnails"
    text_notification_no_missing_thumbnails = "No missing thumbnails!"
    text_nothing = "nothing!"
    text_no_miniatures_saved = "No miniatures saved!"
    text_display_videos = "Display videos"
    text_notification_unknown = "unknown"
    text_boolean = "boolean"
    text_integer = "integer"
    text_float = "floating number"
    text_text = "text"
    text_accept_many_values = "accept many values"
    text_is_enumeration = "Is enumeration"
    text_one_or_many = "one or many"
    text_move = "move"
    word_value = "value"
    word_values = "values"
    word_in = "in"
    word_yes = "yes"
    word_cancel = "cancel"

    dialog_delete_database = "Delete database {name}"
    alert_value_already_in_list = "Value already in list: {value}"
    error_duplicated_shortcut = "Duplicated shortcut {shortcut} for {name1} and {name2}"
    backend_error = "Backend error: {name}: {message}"
    error_duplicated_field = "Duplicated field: {name}"
    error_invalid_bool_value = (
        "Invalid bool value, expected: [false, true], got {value}"
    )
    error_parsing_float = "Unable to parse floating value: {value}"
    error_parsing_enum = "Invalid enum value, expected: [{expected}], got {value}"

    status_loaded = "Loaded."
    status_updated = "updated."
    status_video_not_moved = "Video not moved."
    status_video_moved = "Video moved to {directory}"
    status_ready = "Ready."
    status_prop_val_edited = "Edited property {property} for {count} video(s)."
    status_filled_property_with_keywords = (
        'Filled property "{name}" with video keywords.'
    )
    status_prop_vals_deleted = 'Property value deleted: "{name}" : "{values}"'
    status_prop_vals_edited = (
        'Property value edited: "{name}" : "{values}" -> "{destination}"'
    )
    status_prop_val_moved = (
        'Property value moved: "{values}" from "{name}" to "{destination}"'
    )
    status_opened = "Opened: {path}"
    status_unable_to_open = "Unable to open: {path}"
    status_properties_updated = "Properties updated: {path}"
    status_video_deleted = "Video deleted! {path}"
    status_video_similarity_cancelled = "Current similarity cancelled: {path}"
    status_video_similarity_reset = "Current similarity reset: {path}"
    status_copied_to_clipboard = "Copied to clipboard: {text}"
    status_cannot_copy_meta_title = "Cannot copy meta title to clipboard: {text}"
    status_cannot_copy_file_title = "Cannot copy meta title to clipboard: {text}"
    status_cannot_copy_video_id = "Cannot copy video ID to clipboard: {text}"
    status_cannot_copy_file_path = "Cannot copy file path to clipboard: {text}"
    status_moved = "Moved: {path}"
    status_opened_folder = "Opened folder: {path}"
    status_randomly_opened = "Randomly opened: {path}"

    action_edit = "Edit ..."
    action_group = "Group ..."
    action_search = "Search ..."
    action_display_all_videos = "Display all videos"
    action_display_selected_videos = "Display only selected videos"
    action_select_all = "select all"
    action_deselect_all = "Deselect all"
    action_select_videos = "Select videos ..."
    action_group_videos = "Group ..."
    action_search_videos = "Search ..."
    action_sort_videos = "Sort ..."
    action_unselect_videos = "Reset selection"
    action_ungroup_videos = "Reset group"
    action_unsearch_videos = "Reset search"
    action_unsort_videos = "Reset sorting"
    action_reload_database = "Reload database ..."
    action_manage_properties = "Manage properties ..."
    action_open_random_video = "Open random video"
    action_open_random_player = "Open random player"
    action_go_to_previous_page = "Go to previous page"
    action_go_to_next_page = "Go to next page"
    action_go_to_previous_group = "Go to previous group"
    action_go_to_next_group = "Go to next group"
    action_rename_database = 'Rename database "{name}" ...'
    action_edit_database_folders = "Edit {count} database folders ..."
    action_close_database = "Close database"
    action_delete_database = "Delete database ..."
    action_search_similar_videos = "Search similar videos"
    action_ignore_cache = "Ignore cache"
    action_put_keywords_into_property = "Put keywords into a property ..."
    action_group_videos_by_property = "Group videos by property: {name}"
    action_create_prediction_property = "1) Create a prediction property ..."
    action_populate_prediction_property_manually = (
        "2) Populate a prediction property manually ..."
    )
    action_page_size = "{count} video(s) per page"
    action_confirm_deletion_for_entries_not_found = (
        "confirm deletion for entries not found"
    )
    action_reverse_path = "reverse path"
    action_open_file = "Open file"
    action_open_containing_folder = "Open containing folder"
    action_copy_meta_title = "Copy meta title"
    action_copy_file_title = "Copy file title"
    action_copy_path = "Copy path"
    action_copy_video_id = "Copy video ID"
    action_rename_video = "Rename video"
    action_move_video_to_another_folder = "Move video to another folder ..."
    action_dismiss_similarity = "Dismiss similarity"
    action_reset_similarity = "Reset similarity"
    action_confirm_all_unique_moves = "Confirm all unique moves"

    section_filter = "Filter"
    section_classifier_path = "Classifier path"
    section_groups = "Groups"

    menu_database = "Database ..."
    menu_close_database = "Close database ..."
    menu_videos = "Videos ..."
    menu_filter_videos = "Filter videos ..."
    menu_reset_filters = "Reset filters ..."
    menu_properties = "Properties ..."
    menu_group_videos_by_property = "Group videos by property ..."
    menu_predictors = "Predictors ..."
    menu_compute_prediction = "3) Compute prediction for property ..."
    menu_apply_prediction = "4) Apply prediction from property ..."
    menu_navigation = "Navigation ..."
    menu_navigation_videos = "Videos ..."
    menu_navigation_groups = "Groups ..."
    menu_options = "Options"
    menu_page_size = "Page size ..."
    menu_concatenate_path = "Concatenate path into ..."
    menu_edit_properties = "Edit property ..."
    menu_search_similar_videos_longer = "Search similar videos (longer) ..."

    form_title_populate_predictor_manually = "Populate prediction property manually"
    form_content_populate_predictor_manually = """
Set:

- **1** for video thumbnails that match what you expect
- **0** for video thumbnails that don't match what you expect
- **-1** (default) for videos to ignore

Prediction computation will only use videos tagged with **1** and **0**, 
so you don't need to tag all of them.

There is however some good practices:

- Tag enough videos with **0** and **1** (e.g. 20 videos)
- Try to tag same amount of videos for **0** and for **1** (e.g. 10 videos each)

Once done, move you can compute prediction.
"""
    form_content_confirm_delete_database = """
## Are you sure you want to delete this database?

### Database entries and thumbnails will be deleted.

### Video files won't be touched.
"""
    form_title_edit_property_for_videos = 'Edit property "{name}" for {count} video(s)'
    form_edit_video_properties = "Edit video properties"
    form_title_delete_property = 'Delete property "{name}"?'
    form_content_delete_property = 'Are you sure you want to delete property "{name}"?'
    form_source_currently_selected = "Currently selected:"
    form_source_none_selected = "Currently selected: none"
    form_source_develop = "develop"
    form_title_convert_to_multiple_property = 'Convert to multiple property "{name}"?'
    form_title_convert_to_unique_property = 'Convert to unique property "{name}"?'
    form_convert_to_multiple_property_yes = "convert to multiple"
    form_convert_to_unique_property_yes = "convert to unique"
    form_confirm_convert_to_multiple_property = (
        'Are you sure you want to convert to multiple property "{name}"?'
    )
    form_confirm_convert_to_unique_property = (
        'Are you sure you want to convert to unique property "{name}"?'
    )
    form_title_edit_database_folders = "Edit {count} folders for database: {name}"
    form_title_rename_database = 'Rename database "{name}"'
    form_title_edit_prop_val = 'Property "{name}", value "{value}"'
    form_title_edit_prop_vals = 'Property "{name}", {count} values"'
    form_summary_values = "{count} values ({first} ... {last})"
    form_title_rename_property = 'Rename property "{name}"?'
    form_title_move_file = "Move file to {path}"
    form_title_confirm_delete_video = "Confirm deletion"
    form_head_confirm_delete_video = (
        "## Are you sure you want to !!definitely!! delete this video?"
    )
    form_head_confirm_dismiss = (
        "Are you sure you want to dismiss similarity for this video?"
    )
    form_content_reset_similarity = """
## Are you sure you want to reset similarity for this video?

### Video will then be re-compared at next similarity search
"""
    form_title_new_prediction_property = "New prediction property"
    form_content_new_prediction_property = """
# Property name:

## Final name will be `<?{property name}>`
"""
    form_content_delete_prop_val = """
### Are you sure you want to delete property value

### "{name}" / {value} ?
"""
    form_content_move_prop_val = (
        'Move property "{name}" / {value} to another property of type "{type}".'
    )
    form_content_edit_prop_val = 'Edit property "{name}" / {value}'
    form_title_search_videos = "Search videos"
    form_content_search_videos = """
Type text to search and choose how to search.

You can also type text and then press enter 
to automatically select "AND" as search method.
"""
    form_title_sort_videos = "Sort videos"
    form_content_sort_videos = """
Click on "+" to add a new sorting criterion.

Click on "-" to remove a sorting criterion.

Click on "sort" to validate, or close dialog to cancel.
"""
    form_content_confirm_unique_moves = join_p(
        "# Are you sure you want to confirm all unique moves?",
        "## Each not found video which has one unique other found video with "
        "same size and duration will be moved to the later. "
        "Properties and variable attributes will be copied "
        "from not found to found video, and "
        "not found video entry will be deleted."
    )
