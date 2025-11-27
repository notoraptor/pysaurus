"""
Migration script: JSON database -> SQL database.

This script converts an existing Pysaurus JSON database to the new SQL format.
"""

import json
import logging
from pathlib import Path

from pysaurus.core.functions import string_to_pieces
from pysaurus.database.newsql.sql_database import SqlDatabase

logger = logging.getLogger(__name__)


def extract_terms_from_video_dict(
    video_dict: dict, prop_types: dict[str, dict]
) -> list[str]:
    """
    Extract search terms from a video dictionary.

    Terms come from:
    - filename
    - meta_title
    - string property values

    Video schema keys (short -> long):
    - "f" -> filename
    - "n" -> meta_title
    - "p" -> properties
    - "R" -> runtime (contains: "s"=size, "m"=mtime, "d"=driver_id, "f"=is_file)
    """
    term_sources = []

    # Filename (key "f" or "filename")
    filename = video_dict.get("f") or video_dict.get("filename", "")
    term_sources.append(filename)

    # Meta title (key "n" or "meta_title") - directly in video dict, NOT in runtime
    meta_title = video_dict.get("n") or video_dict.get("meta_title", "")
    if meta_title:
        term_sources.append(meta_title)

    # String properties
    properties = video_dict.get("p") or video_dict.get("properties", {})
    for name, values in properties.items():
        # Check if this property is a string type
        pt = prop_types.get(name)
        if pt:
            # Determine type from definition
            definition = pt.get("definition")
            if definition is not None:
                if isinstance(definition, list) and definition:
                    is_string = isinstance(definition[0], str)
                else:
                    is_string = isinstance(definition, str)
                if is_string:
                    term_sources.extend(values)

    # Extract terms (words)
    all_str = " ".join(term_sources)
    terms = string_to_pieces(all_str)
    terms_low = string_to_pieces(all_str.lower())

    if terms == terms_low:
        return terms
    return terms + terms_low


def extract_flags_from_video_dict(video_dict: dict) -> dict[str, bool]:
    """
    Extract boolean flags from a video dictionary.

    Flags: readable, unreadable, found, not_found, with_thumbnails,
           without_thumbnails, discarded

    Video schema keys (short -> long):
    - "U" -> unreadable
    - "R" -> runtime dict with "f" -> is_file
    """
    # Get basic fields (key "U" or "unreadable")
    unreadable = video_dict.get("U", video_dict.get("unreadable", False))
    readable = not unreadable

    # Found status from runtime (key "R" or "runtime", then "f" or "is_file")
    runtime = video_dict.get("R") or video_dict.get("runtime", {})
    if isinstance(runtime, dict):
        is_file = runtime.get("f", runtime.get("is_file", True))
    else:
        is_file = False
    found = is_file
    not_found = not is_file

    # Discarded is computed at load time based on folders,
    # we'll set False by default (will be recomputed when loading)
    discarded = video_dict.get("discarded", False)

    # with_thumbnails will be set later after checking thumbnail table
    # For now, we'll assume based on readability
    with_thumbnails = readable  # Will be updated after thumbnail import
    without_thumbnails = not with_thumbnails

    return {
        "readable": readable,
        "unreadable": unreadable,
        "found": found,
        "not_found": not_found,
        "with_thumbnails": with_thumbnails,
        "without_thumbnails": without_thumbnails,
        "discarded": discarded,
    }


def migrate_json_to_sql(
    json_db_path: Path,
    thumb_sql_path: Path | None,
    index_pkl_path: Path | None,
    output_sql_path: Path,
    *,
    verbose: bool = True,
) -> SqlDatabase:
    """
    Migrate a JSON database to the new SQL format.

    Args:
        json_db_path: Path to database.json
        thumb_sql_path: Path to thumbnails.sql.db (optional)
        index_pkl_path: Path to index.pkl (optional, will rebuild if missing)
        output_sql_path: Path for the new SQL database
        verbose: Print progress messages

    Returns:
        The new SqlDatabase instance
    """

    def log(msg: str):
        if verbose:
            print(msg)
        logger.info(msg)

    log(f"Loading JSON database from {json_db_path}...")

    with open(json_db_path, "r", encoding="utf-8") as f:
        json_data = json.load(f)

    # Extract data from JSON
    version = json_data.get("version", 1)
    date = json_data.get("date", 0)
    folders = json_data.get("folders", [])
    prop_types_list = json_data.get("prop_types", [])
    videos_list = json_data.get("videos", [])

    log(f"  Version: {version}")
    log(f"  Folders: {len(folders)}")
    log(f"  Property types: {len(prop_types_list)}")
    log(f"  Videos: {len(videos_list)}")

    # Convert prop_types to dict for lookup
    prop_types: dict[str, dict] = {}
    for pt in prop_types_list:
        # Use short keys first, fall back to long keys
        name = pt.get("n") if "n" in pt else pt.get("name")
        definition = pt.get("d") if "d" in pt else pt.get("definition")
        multiple = pt.get("m") if "m" in pt else pt.get("multiple", False)
        prop_types[name] = {
            "name": name,
            "definition": definition,
            "multiple": bool(multiple),
        }

    # Create new SQL database
    log(f"Creating SQL database at {output_sql_path}...")

    if output_sql_path.exists():
        output_sql_path.unlink()

    sql_db = SqlDatabase(output_sql_path)
    sql_db.init_schema()

    # Migrate config
    log("Migrating config...")
    sql_db.set_config("version", version)
    sql_db.set_config("date", date)

    # Migrate folders
    log("Migrating folders...")
    sql_db.set_folders(folders)

    # Migrate prop_types
    log("Migrating property types...")
    for name, pt in prop_types.items():
        sql_db.set_prop_type(name, pt["definition"], pt["multiple"])

    # Migrate videos
    log("Migrating videos...")
    sql_db.begin()
    try:
        for i, video_dict in enumerate(videos_list):
            # Get or assign video_id (key "j" or "video_id")
            video_id = video_dict.get("j")
            if video_id is None:
                video_id = video_dict.get("video_id")
            if video_id is None:
                video_id = i

            # Get filename (key "f" or "filename")
            filename = video_dict.get("f") or video_dict.get("filename")
            if not filename:
                log(f"  Warning: Video {i} has no filename, skipping")
                continue

            # Store the full video dict as JSON
            sql_db.insert_video(video_id, filename, video_dict)

            if (i + 1) % 1000 == 0:
                log(f"  Migrated {i + 1}/{len(videos_list)} videos...")

        sql_db.commit()
    except Exception as e:
        sql_db.rollback()
        raise RuntimeError(f"Failed to migrate videos: {e}") from e

    log(f"  Migrated {len(videos_list)} videos")

    # Migrate thumbnails
    if thumb_sql_path and thumb_sql_path.exists():
        log(f"Migrating thumbnails from {thumb_sql_path}...")
        _migrate_thumbnails(sql_db, thumb_sql_path, verbose)
    else:
        log("No thumbnail database found, skipping thumbnails")

    # Build search index
    log("Building search index...")
    _build_search_index(sql_db, prop_types, verbose)

    log("Migration complete!")
    log(f"  Output: {output_sql_path}")
    log(f"  Size: {output_sql_path.stat().st_size / 1024 / 1024:.2f} MB")

    return sql_db


def _migrate_thumbnails(sql_db: SqlDatabase, thumb_sql_path: Path, verbose: bool):
    """Import thumbnails from the old SQLite database."""
    import sqlite3

    old_conn = sqlite3.connect(thumb_sql_path)
    old_conn.row_factory = sqlite3.Row

    cursor = old_conn.execute("SELECT filename, thumbnail FROM video_to_thumbnail")

    sql_db.begin()
    count = 0
    try:
        for row in cursor:
            sql_db.set_thumbnail(row["filename"], row["thumbnail"])
            count += 1
            if verbose and count % 1000 == 0:
                print(f"  Migrated {count} thumbnails...")
        sql_db.commit()
    except Exception as e:
        sql_db.rollback()
        raise RuntimeError(f"Failed to migrate thumbnails: {e}") from e
    finally:
        old_conn.close()

    if verbose:
        print(f"  Migrated {count} thumbnails")


def _build_search_index(
    sql_db: SqlDatabase, prop_types: dict[str, dict], verbose: bool
):
    """Build the search index from video data."""
    videos = sql_db.get_all_videos()

    # Get set of filenames with thumbnails
    thumbnails_filenames = set()
    cursor = sql_db.execute("SELECT filename FROM thumbnails")
    for row in cursor:
        thumbnails_filenames.add(row["filename"])

    sql_db.begin()
    try:
        for i, video in enumerate(videos):
            video_dict = video["data"]
            filename = video["filename"]

            # Extract terms
            terms = extract_terms_from_video_dict(video_dict, prop_types)

            # Extract flags
            flags = extract_flags_from_video_dict(video_dict)

            # Update with_thumbnails based on actual thumbnail presence
            has_thumb = filename in thumbnails_filenames
            flags["with_thumbnails"] = has_thumb
            flags["without_thumbnails"] = not has_thumb

            # Insert into index
            sql_db.add_search_terms(filename, terms)
            sql_db.set_video_flags(filename, flags)

            if verbose and (i + 1) % 1000 == 0:
                print(f"  Indexed {i + 1}/{len(videos)} videos...")

        sql_db.commit()
    except Exception as e:
        sql_db.rollback()
        raise RuntimeError(f"Failed to build search index: {e}") from e

    if verbose:
        print(f"  Indexed {len(videos)} videos")


def migrate_database_folder(
    db_folder: Path, output_filename: str = "newsql.db"
) -> SqlDatabase:
    """
    Migrate a complete database folder to SQL.

    Uses DbWays to locate the correct file paths (json_path.json, etc.)

    Args:
        db_folder: Path to the database folder
        output_filename: Name for the output SQL file

    Returns:
        The new SqlDatabase instance
    """
    from pysaurus.database.db_way_def import DbWays

    db_folder = Path(db_folder)
    ways = DbWays(db_folder)

    json_db_path = ways.db_json_path
    thumb_sql_path = ways.db_thumb_sql_path
    index_pkl_path = ways.db_index_pkl_path
    output_sql_path = db_folder / output_filename

    if not json_db_path.exists():
        raise FileNotFoundError(f"JSON database not found: {json_db_path}")

    return migrate_json_to_sql(
        json_db_path=Path(json_db_path.path),
        thumb_sql_path=Path(thumb_sql_path.path) if thumb_sql_path.exists() else None,
        index_pkl_path=Path(index_pkl_path.path) if index_pkl_path.exists() else None,
        output_sql_path=output_sql_path,
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m pysaurus.database.newsql.migration <db_folder>")
        sys.exit(1)

    db_folder = Path(sys.argv[1])
    migrate_database_folder(db_folder)
