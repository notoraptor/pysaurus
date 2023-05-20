"""
GuiAPI (57)
    AbstractVideoProvider.apply_on_view -> typing.Optional
    GuiAPI.apply_predictor -> None
    FeatureAPI.backend -> typing.Dict[str, typing.Any]
    GuiAPI.cancel_copy -> None
    AbstractVideoProvider.classifier_back -> None
    FeatureAPI.classifier_concatenate_path -> None
    AbstractVideoProvider.classifier_focus_prop_val -> None
    AbstractVideoProvider.classifier_reverse -> typing.List
    AbstractVideoProvider.classifier_select_group -> None
    clipboard_set -> None
    GuiAPI.close_app -> None
    GuiAPI.close_database -> None
    GuiAPI.compute_predictor -> None
    Database.confirm_unique_moves -> <class 'int'>
    JsonDatabase.convert_prop_to_multiple -> None
    JsonDatabase.convert_prop_to_unique -> None
    GuiAPI.create_database -> None
    GuiAPI.create_prediction_property -> None
    JsonDatabase.create_prop_type -> None
    GuiAPI.delete_database -> None
    Database.delete_property_value -> None
    Database.delete_video -> <class 'pysaurus.core.components.AbsolutePath'> (ignored)
    JsonDatabase.describe_prop_types -> typing.List[dict]
    Database.edit_property_value -> <class 'bool'> (ignored)
    Database.fill_property_with_terms -> None
    GuiAPI.find_similar_videos -> None
    GuiAPI.find_similar_videos_ignore_cache -> None
    FeatureAPI.get_constants -> typing.Dict[str, typing.Any]
    Application.get_database_names -> typing.List[str]
    Application.get_language_names -> typing.List[str]
    Database.move_property_value -> None
    GuiAPI.move_video_file -> None
    Database.open_containing_folder -> <class 'str'>
    GuiAPI.open_database -> None
    GuiAPI.open_from_server -> <class 'str'>
    AbstractVideoProvider.choose_random_video -> <class 'str'>
    JsonDatabase.open_video -> None
    AbstractVideoProvider.playlist -> <class 'str'>
    Database.prop_to_lowercase -> None
    Database.prop_to_uppercase -> None
    JsonDatabase.remove_prop_type -> None
    Database.rename -> None
    JsonDatabase.rename_prop_type -> None
    Database.change_video_file_title -> None
    select_directory -> <class 'str'>
    select_file_to_open -> <class 'str'>
    AbstractVideoProvider.set_group -> None
    AbstractVideoProvider.set_groups -> None
    FeatureAPI.set_language -> typing.Dict[str, str]
    AbstractVideoProvider.set_search -> None
    Database.set_video_similarity -> None
    AbstractVideoProvider.set_sort -> None
    AbstractVideoProvider.set_sources -> None
    JsonDatabase.set_folders -> None
    JsonDatabase.move_video_entry -> None
    JsonDatabase.set_video_properties -> typing.List[str] (ignored)
    GuiAPI.update_database -> None
"""
from pysaurus.interface.api.gui_api import GuiAPI

if __name__ == "__main__":
    api = GuiAPI()
    print(api)
