import { VIDEO_DEFAULT_PAGE_NUMBER, VIDEO_DEFAULT_PAGE_SIZE } from "./constants.js";

export function python_call(name, ...args) {
	return window.backend_call(name, args);
}

export async function python_multiple_call(...calls) {
	const outs = [];
	for (let call of calls) {
		const ret = await python_call(...call);
		if (ret !== null) outs.push(ret);
	}
	return outs.length ? (outs.length === 1 ? outs[0] : outs) : null;
}

export function backend_error(error) {
	const desc = error.string || `${error.name}: ${error.message}`;
	window.alert(desc);
}

export class Backend {
	static async apply_on_view(video_indices, function_name, ...args) {
		return await python_call("apply_on_view", video_indices, function_name, ...args);
	}

	static async backend(page_size = undefined, page_number = undefined) {
		if (page_size === undefined) page_size = VIDEO_DEFAULT_PAGE_SIZE;
		if (page_number === undefined) page_number = VIDEO_DEFAULT_PAGE_NUMBER;
		return await python_call("backend", page_size, page_number);
	}

	static async cancel_copy() {
		return await python_call("cancel_copy");
	}

	static async classifier_reverse() {
		return await python_call("classifier_reverse");
	}

	static async classifier_select_group(index) {
		return await python_call("classifier_select_group", index);
	}

	static async classifier_unstack() {
		return await python_call("classifier_unstack");
	}

	static async classifier_concatenate(output_property_name) {
		return await python_call("classifier_concatenate", output_property_name);
	}

	static async classifier_concatenate_path(output_property_name) {
		return await python_call("classifier_concatenate_path", output_property_name);
	}

	static async classifier_back() {
		return await python_call("classifier_back");
	}

	static async close_app() {
		return await python_call("close_app");
	}

	static async clipboard(text) {
		return await python_call("clipboard", text);
	}

	static async confirm_deletion(video_id) {
		return await python_call("confirm_deletion", video_id);
	}

	static async confirm_move(src_id, dst_id) {
		return await python_call("confirm_move", src_id, dst_id);
	}

	static async confirm_unique_moves() {
		return await python_call("confirm_unique_moves");
	}

	static async copy_file_path(video_id) {
		return await python_call("copy_file_path", video_id);
	}

	static async copy_file_title(video_id) {
		return await python_call("copy_file_title", video_id);
	}

	static async copy_meta_title(video_id) {
		return await python_call("copy_meta_title", video_id);
	}

	static async copy_to_clipboard(field) {
		return await python_call("copy_to_clipboard", field);
	}

	static async copy_video_id(video_id) {
		return await python_call("copy_video_id", video_id);
	}

	static async delete_video(video_id) {
		return await python_call("delete_video", video_id);
	}

	static async delete_video_entry(video_id) {
		return await python_call("delete_video_entry", video_id);
	}

	static async describe_prop_types() {
		return await python_call("describe_prop_types");
	}

	static async edit_properties(video_id) {
		return await python_call("edit_properties", video_id);
	}

	static async fill_property_with_terms(field, onlyEmpty) {
		return await python_call("fill_property_with_terms", field, onlyEmpty);
	}

	static async mark_as_read(video_id) {
		return await python_call("mark_as_read", video_id);
	}

	static async move_video(src_id, dst_id) {
		return await python_call("move_video", src_id, dst_id);
	}

	static async move_video_entry(src_id, dst_id) {
		return await python_call("move_video_entry", src_id, dst_id);
	}

	static async move_video_entry_to_folder(src_id, dst_id) {
		return await python_call("move_video_entry_to_folder", src_id, dst_id);
	}

	static async open_containing_folder(video_id) {
		return await python_call("open_containing_folder", video_id);
	}

	static async open_from_server(video_id) {
		return await python_call("open_from_server", video_id);
	}

	static async open_random_video() {
		return await python_call("open_random_video");
	}

	static async open_video(video_id) {
		return await python_call("open_video", video_id);
	}

	static async open_video_in_folder(video_id) {
		return await python_call("open_video_in_folder", video_id);
	}

	static async playlist() {
		return await python_call("playlist");
	}

	static async really_delete_video(video_id) {
		return await python_call("really_delete_video", video_id);
	}

	static async really_delete_video_entry(video_id) {
		return await python_call("really_delete_video_entry", video_id);
	}

	static async really_dismiss_similarity(video_id) {
		return await python_call("really_dismiss_similarity", video_id);
	}

	static async really_reset_similarity(video_id) {
		return await python_call("really_reset_similarity", video_id);
	}

	static async rename_video(video_id, new_name) {
		return await python_call("rename_video", video_id, new_name);
	}

	static async select_directory(default_directory = null) {
		return await python_call("select_directory", default_directory);
	}

	static async select_file() {
		return await python_call("select_file");
	}

	static async set_language(name) {
		return await python_call("set_language", name);
	}

	static async set_similarities(video_indices, similarities) {
		return await python_call("set_similarities", video_indices, similarities);
	}

	static async set_video_folders(paths) {
		return await python_call("set_video_folders", paths);
	}

	static async set_video_properties(video_id, properties) {
		return await python_call("set_video_properties", video_id, properties);
	}
}
