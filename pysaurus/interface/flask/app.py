"""Flask application factory and route definitions."""

import random
import secrets
from functools import wraps

from flask import Flask, Response, flash, redirect, render_template, request, url_for

from pysaurus.core.core_exceptions import ApplicationError
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.dbview.view_context import ViewContext
from pysaurus.interface.common.common import FIELD_MAP
from pysaurus.interface.flask.context import FlaskContext

DEFAULT_PAGE_SIZE = 20

_PROP_PARSERS = {
    "bool": lambda v: v.lower() in ("true", "1", "yes", "oui"),
    "int": int,
    "float": float,
    "str": str,
}

_PROP_DEFAULTS = {"bool": False, "int": 0, "float": 0.0, "str": ""}


def _parse_prop_value(value: str, ptype: str):
    """Convert a string form value to the appropriate Python type."""
    return _PROP_PARSERS[ptype](value)


def _ctx() -> FlaskContext:
    return FlaskContext.instance


def require_database(f):
    """Redirect to index if no database is open."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if _ctx().database is None:
            flash("Veuillez d'abord ouvrir une base de données.")
            return redirect(url_for("index"))
        return f(*args, **kwargs)

    return wrapper


def require_no_operation(f):
    """Redirect to operation progress page if an operation is running."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        if _ctx().operation_running:
            return redirect(url_for("operation_progress"))
        return f(*args, **kwargs)

    return wrapper


def handle_errors(f):
    """Catch ApplicationError and display as flash message."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ApplicationError as e:
            flash(str(e), "error")
            return redirect(request.referrer or url_for("index"))

    return wrapper


def _build_view() -> ViewContext:
    """Build an ephemeral ViewContext from the current request's query params."""
    view = ViewContext()

    # Search
    q = request.args.get("q", "").strip()
    cond = request.args.get("cond", "and").strip()
    if q:
        view.set_search(q, cond)

    # Sorting
    sort = request.args.get("sort", "").strip()
    if sort:
        view.set_sort(sort.split(","))

    # Grouping
    group_field = request.args.get("group_field", "").strip()
    if group_field:
        view.set_grouping(
            group_field,
            is_property=request.args.get("group_is_property", "0") == "1",
            sorting=request.args.get("group_sorting", "field"),
            reverse=request.args.get("group_reverse", "0") == "1",
            allow_singletons=request.args.get("group_singletons", "1") == "1",
        )
        group = request.args.get("group", "0")
        try:
            view.set_group(int(group))
        except ValueError:
            pass

    return view


def _keep_query_params(**overrides) -> dict:
    """Return current query params merged with overrides, for building URLs."""
    params = dict(request.args)
    params.update(overrides)
    # Remove empty values
    return {k: v for k, v in params.items() if v not in (None, "")}


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = secrets.token_hex(32)

    @app.context_processor
    def inject_context():
        ctx = _ctx()
        return {
            "database_name": ctx.get_database_name(),
            "has_database": ctx.database is not None,
        }

    # =================================================================
    # Databases
    # =================================================================

    @app.route("/")
    def index():
        databases = _ctx().get_database_names()
        return render_template("databases.html", databases=databases)

    @app.route("/open", methods=["POST"])
    @handle_errors
    def open_database():
        name = request.form.get("name", "").strip()
        if name:
            _ctx().open_database(name)
            return redirect(url_for("videos"))
        return redirect(url_for("index"))

    @app.route("/create", methods=["POST"])
    @handle_errors
    def create_database():
        name = request.form.get("name", "").strip()
        folders_text = request.form.get("folders", "")
        folders = [line.strip() for line in folders_text.splitlines() if line.strip()]
        if name:
            ctx = _ctx()
            ctx.create_database(name, folders)
            ctx.start_operation(ctx.algos.refresh, redirect_url="/videos")
            return redirect(url_for("operation_progress"))
        return redirect(url_for("index"))

    @app.route("/delete", methods=["POST"])
    @handle_errors
    def delete_database():
        name = request.form.get("name", "").strip()
        if name:
            _ctx().delete_database(name)
            flash(f"Base de données « {name} » supprimée.")
        return redirect(url_for("index"))

    @app.route("/close", methods=["POST"])
    def close_database():
        _ctx().close_database()
        return redirect(url_for("index"))

    # =================================================================
    # Videos
    # =================================================================

    @app.route("/videos")
    @require_database
    @require_no_operation
    @handle_errors
    def videos():
        page_size = request.args.get("page_size", DEFAULT_PAGE_SIZE, type=int)
        page = request.args.get("page", 1, type=int)
        page_number = max(page - 1, 0)  # ViewContext uses 0-based pages

        view = _build_view()
        ctx = _ctx()
        context = ctx.database.query_videos(view, page_size, page_number)

        # Groupable fields for the grouping form
        group_fields = [(f.name, f.title) for f in FIELD_MAP.allowed]
        prop_types = ctx.get_prop_types()

        # Page-level stats
        videos_list = context.result or []
        page_total_size = FileSize(sum(v.file_size for v in videos_list))
        page_total_duration = Duration(sum(v.length.t for v in videos_list))

        return render_template(
            "videos.html",
            videos=videos_list,
            page=page,
            nb_pages=context.nb_pages or 1,
            page_size=page_size,
            view_count=context.view_count,
            page_total_size=page_total_size,
            page_total_duration=page_total_duration,
            search_text=view.search.text or "",
            search_cond=view.search.cond,
            sorting=",".join(view.sorting),
            grouping=view.grouping,
            group_id=context.group_id,
            classifier_stats=context.classifier_stats,
            keep_params=_keep_query_params,
            group_fields=group_fields,
            prop_types=prop_types,
        )

    @app.route("/videos/random")
    @require_database
    @require_no_operation
    @handle_errors
    def random_video():
        db = _ctx().database
        candidates = db.get_videos(
            include=["video_id"],
            where={"found": True, "readable": True, "watched": False},
        )
        if not candidates:
            flash("Aucune vidéo non vue disponible.", "error")
            return redirect(url_for("videos"))
        video = random.choice(candidates)
        return redirect(url_for("video_detail", video_id=video.video_id))

    @app.route("/videos/search", methods=["POST"])
    @require_database
    def search_videos():
        q = request.form.get("q", "").strip()
        cond = request.form.get("cond", "and").strip()
        params = _keep_query_params(q=q, cond=cond, page="1")
        # Remove search params if query is empty
        if not q:
            params.pop("q", None)
            params.pop("cond", None)
        return redirect(url_for("videos", **params))

    @app.route("/videos/sort", methods=["POST"])
    @require_database
    def sort_videos():
        sort = request.form.get("sort", "").strip()
        params = _keep_query_params(sort=sort, page="1")
        if not sort:
            params.pop("sort", None)
        return redirect(url_for("videos", **params))

    @app.route("/videos/group", methods=["POST"])
    @require_database
    def group_videos():
        field = request.form.get("group_field", "").strip()
        if field:
            params = _keep_query_params(
                group_field=field,
                group_is_property=request.form.get("group_is_property", "0"),
                group_sorting=request.form.get("group_sorting", "field"),
                group_reverse=request.form.get("group_reverse", "0"),
                group_singletons=request.form.get("group_singletons", "1"),
                group="0",
                page="1",
            )
        else:
            # Clear grouping
            params = dict(request.args)
            for key in list(params):
                if key.startswith("group"):
                    del params[key]
            params["page"] = "1"
        return redirect(url_for("videos", **params))

    # =================================================================
    # Video detail (stub for phase 3)
    # =================================================================

    @app.route("/video/<int:video_id>")
    @require_database
    @require_no_operation
    @handle_errors
    def video_detail(video_id):
        ctx = _ctx()
        video = ctx.get_video(video_id)
        if not video:
            flash("Vidéo introuvable.", "error")
            return redirect(url_for("videos"))
        prop_types = ctx.get_prop_types()
        return render_template("video_detail.html", video=video, prop_types=prop_types)

    @app.route("/video/<int:video_id>/toggle-watched", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def toggle_watched(video_id):
        _ctx().ops.mark_as_read(video_id)
        return redirect(url_for("video_detail", video_id=video_id))

    @app.route("/video/<int:video_id>/rename", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def rename_video(video_id):
        new_title = request.form.get("new_title", "").strip()
        if new_title:
            _ctx().ops.change_video_file_title(video_id, new_title)
            flash("Vidéo renommée.")
        return redirect(url_for("video_detail", video_id=video_id))

    @app.route("/video/<int:video_id>/play", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def play_video(video_id):
        _ctx().ops.open_video(video_id)
        flash("Vidéo ouverte dans le lecteur.")
        return redirect(url_for("video_detail", video_id=video_id))

    @app.route("/video/<int:video_id>/open-folder", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def open_folder(video_id):
        filename = _ctx().ops.get_video_filename(video_id)
        filename.locate_file()
        flash("Dossier ouvert.")
        return redirect(url_for("video_detail", video_id=video_id))

    @app.route("/video/<int:video_id>/trash", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def trash_video(video_id):
        _ctx().ops.trash_video(video_id)
        flash("Vidéo mise à la corbeille.")
        return redirect(url_for("videos"))

    @app.route("/video/<int:video_id>/delete", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def delete_video(video_id):
        _ctx().ops.delete_video(video_id)
        flash("Vidéo supprimée définitivement.")
        return redirect(url_for("videos"))

    @app.route("/video/<int:video_id>/properties", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def update_properties(video_id):
        ctx = _ctx()
        prop_types = ctx.get_prop_types()
        properties = {}
        for pt in prop_types:
            name = pt["name"]
            field_name = f"prop_{name}"
            ptype = pt["type"]
            if pt["multiple"]:
                raw_values = request.form.getlist(field_name)
                values = [v.strip() for v in raw_values if v.strip()]
            else:
                raw = request.form.get(field_name, "").strip()
                values = [raw] if raw else []
            if not values:
                properties[name] = pt["defaultValues"]
            else:
                properties[name] = [_parse_prop_value(v, ptype) for v in values]
        ctx.database.video_entry_set_tags(video_id, properties)
        flash("Propriétés mises à jour.")
        return redirect(url_for("video_detail", video_id=video_id))

    # =================================================================
    # Properties
    # =================================================================

    @app.route("/properties")
    @require_database
    @require_no_operation
    def properties():
        prop_types = _ctx().get_prop_types()
        return render_template("properties.html", prop_types=prop_types)

    @app.route("/properties/create", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def create_prop_type():
        db = _ctx().database
        name = request.form.get("name", "").strip()
        prop_type = request.form.get("type", "str").strip()
        multiple = request.form.get("multiple") == "1"
        default_text = request.form.get("default", "").strip()
        enum_text = request.form.get("enumeration", "").strip()

        # Build definition
        if enum_text and prop_type == "str":
            definition = [v.strip() for v in enum_text.split(",") if v.strip()]
        else:
            definition = (
                _parse_prop_value(default_text, prop_type)
                if default_text
                else _PROP_DEFAULTS[prop_type]
            )

        db.prop_type_add(name, prop_type, definition, multiple)
        flash(f"Propriété « {name} » créée.")
        return redirect(url_for("properties"))

    @app.route("/properties/<name>/rename", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def rename_prop_type(name):
        new_name = request.form.get("new_name", "").strip()
        if new_name:
            _ctx().database.prop_type_set_name(name, new_name)
            flash(f"Propriété renommée en « {new_name} ».")
        return redirect(url_for("properties"))

    @app.route("/properties/<name>/delete", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def delete_prop_type(name):
        _ctx().database.prop_type_del(name)
        flash(f"Propriété « {name} » supprimée.")
        return redirect(url_for("properties"))

    # =================================================================
    # Sources
    # =================================================================

    @app.route("/sources")
    @require_database
    @require_no_operation
    def sources():
        folders = _ctx().database.get_folders()
        return render_template("sources.html", folders=[str(f) for f in folders])

    @app.route("/sources/update", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def update_sources():
        folders_text = request.form.get("folders", "")
        folders = [line.strip() for line in folders_text.splitlines() if line.strip()]
        _ctx().ops.set_folders(folders)
        flash("Dossiers sources mis à jour.")
        return redirect(url_for("sources"))

    # =================================================================
    # Long operations
    # =================================================================

    @app.route("/operation/progress")
    def operation_progress():
        op = _ctx().operation_state
        if not op.running and not op.done:
            return redirect(url_for("index"))
        return render_template("operation_progress.html")

    @app.route("/operation/status")
    def operation_status():
        op = _ctx().operation_state
        return {
            "percent": op.percent,
            "message": op.message,
            "done": op.done,
            "error": op.error,
            "redirect": op.redirect_url,
        }

    @app.route("/operation/start", methods=["POST"])
    @require_database
    @require_no_operation
    @handle_errors
    def start_operation():
        op_name = request.form.get("operation", "").strip()
        ctx = _ctx()
        if op_name == "update":
            ctx.start_operation(ctx.algos.refresh, redirect_url="/videos")
        else:
            flash("Opération inconnue.", "error")
            return redirect(url_for("videos"))
        return redirect(url_for("operation_progress"))

    # =================================================================
    # Thumbnails
    # =================================================================

    @app.route("/thumbnail/<int:video_id>")
    @require_database
    def thumbnail(video_id):
        thumb_data = _ctx().get_thumbnail_data(video_id)
        if thumb_data:
            return Response(thumb_data, mimetype="image/jpeg")
        # 1x1 transparent GIF as placeholder
        return Response(
            b"GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff"
            b"\x00\x00\x00!\xf9\x04\x00\x00\x00\x00\x00,\x00"
            b"\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
            mimetype="image/gif",
        )

    return app
