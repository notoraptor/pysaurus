"""
Script to add the 'category' multi-value property to test databases.

This script:
1. Loads both JSON and NewSQL test databases from disk
2. Adds a 'category' multi-value string property if not present
3. Assigns category values to videos based on their folder paths
4. Saves changes to disk
5. Verifies the changes were persisted

Run once to update the test databases:
    python tests/setup_category_property.py
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.utils import get_old_app, get_new_sql_database


def get_categories_for_path(path: str) -> list[str]:
    """Get categories based on video path."""
    path = path.lower()
    if "/action/" in path or "\\action\\" in path:
        return ["action", "thriller"]
    elif "/comedy/" in path or "\\comedy\\" in path:
        return ["comedy", "romance"]
    elif "/drama/" in path or "\\drama\\" in path:
        return ["drama", "thriller"]
    elif "/documentary/" in path or "\\documentary\\" in path:
        return ["documentary"]
    elif "/animation/" in path or "\\animation\\" in path:
        return ["animation", "family"]
    elif "/music/" in path or "\\music\\" in path:
        return ["music", "entertainment"]
    elif "/sports/" in path or "\\sports\\" in path:
        return ["sports", "entertainment"]
    elif "/nature/" in path or "\\nature\\" in path:
        return ["nature", "documentary"]
    elif "/tutorial/" in path or "\\tutorial\\" in path:
        return ["tutorial", "educational"]
    else:
        return ["other"]


def setup_category_property(db, db_name: str) -> dict:
    """
    Add category property to a database if not present.

    Returns dict with stats about what was done.
    """
    stats = {
        "db_name": db_name,
        "property_existed": False,
        "property_created": False,
        "videos_updated": 0,
        "videos_skipped": 0,
        "category_counts": {},
    }

    # Check if property already exists
    prop_types = db.get_prop_types(name="category")
    if prop_types:
        stats["property_existed"] = True
        print(f"  [{db_name}] Property 'category' already exists", flush=True)
    else:
        # Create the multi-value string property
        db.prop_type_add("category", "str", "", True)
        stats["property_created"] = True
        print(f"  [{db_name}] Created property 'category'", flush=True)

    # Get all videos
    videos = db.get_videos(include=["video_id", "filename", "properties"])
    print(f"  [{db_name}] Found {len(videos)} videos", flush=True)

    # Collect assignments for videos that don't have categories yet
    assignments = {}
    for video in videos:
        existing_categories = video.properties.get("category", [])
        if existing_categories:
            stats["videos_skipped"] += 1
            continue

        categories = get_categories_for_path(video.filename.path)
        if categories:
            assignments[video.video_id] = categories
            for cat in categories:
                stats["category_counts"][cat] = stats["category_counts"].get(cat, 0) + 1

    # Bulk update
    if assignments:
        db.videos_tag_set("category", assignments)
        stats["videos_updated"] = len(assignments)
        print(
            f"  [{db_name}] Updated {len(assignments)} videos with categories",
            flush=True,
        )
    else:
        print(f"  [{db_name}] No videos needed updating", flush=True)

    return stats


def verify_category_property(db, db_name: str) -> bool:
    """Verify that category property was properly saved."""
    print(f"  [{db_name}] Verifying...")

    # Check property exists
    prop_types = db.get_prop_types(name="category")
    if not prop_types:
        print(f"  [{db_name}] ERROR: Property 'category' not found!")
        return False

    prop = prop_types[0]
    if not prop.get("multiple"):
        print(f"  [{db_name}] ERROR: Property 'category' is not multiple!")
        return False

    # Check some videos have categories
    videos = db.get_videos(include=["video_id", "properties"])
    videos_with_category = [v for v in videos if v.properties.get("category")]

    if not videos_with_category:
        print(f"  [{db_name}] ERROR: No videos have category property!")
        return False

    print(
        f"  [{db_name}] OK - {len(videos_with_category)}/{len(videos)} videos have categories"
    )

    # Show sample categories
    sample = videos_with_category[:3]
    for v in sample:
        cats = v.properties.get("category", [])
        print(f"    Video {v.video_id}: {cats}")

    return True


def main():
    print("=" * 60)
    print("Setting up 'category' property in test databases")
    print("=" * 60)
    print()

    # Setup JSON database
    print("1. JSON Database (old)")
    print("-" * 40)
    app = get_old_app()
    json_db = app.open_database_from_name("test_database")

    json_stats = setup_category_property(json_db, "JSON")

    # Save JSON database
    print("  [JSON] Saving database...")
    json_db.save()
    json_db.__close__()
    print("  [JSON] Saved")
    print()

    # Setup NewSQL database
    print("2. NewSQL Database")
    print("-" * 40)
    sql_db = get_new_sql_database()

    sql_stats = setup_category_property(sql_db, "SQL")

    # Save NewSQL database (close triggers save)
    print("  [SQL] Saving database...")
    sql_db.__close__()
    print("  [SQL] Saved")
    print()

    # Verify by reloading
    print("3. Verification (reload and check)")
    print("-" * 40)

    # Reload and verify JSON
    app2 = get_old_app()
    json_db2 = app2.open_database_from_name("test_database")
    json_ok = verify_category_property(json_db2, "JSON")
    json_db2.__close__()
    print()

    # Reload and verify SQL
    sql_db2 = get_new_sql_database()
    sql_ok = verify_category_property(sql_db2, "SQL")
    sql_db2.__close__()
    print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("JSON Database:")
    print(f"  - Property created: {json_stats['property_created']}")
    print(f"  - Videos updated: {json_stats['videos_updated']}")
    print(
        f"  - Videos skipped (already had categories): {json_stats['videos_skipped']}"
    )
    print(f"  - Verification: {'PASSED' if json_ok else 'FAILED'}")
    print()
    print("NewSQL Database:")
    print(f"  - Property created: {sql_stats['property_created']}")
    print(f"  - Videos updated: {sql_stats['videos_updated']}")
    print(f"  - Videos skipped (already had categories): {sql_stats['videos_skipped']}")
    print(f"  - Verification: {'PASSED' if sql_ok else 'FAILED'}")
    print()

    if json_stats["category_counts"]:
        print("Category distribution:")
        for cat, count in sorted(json_stats["category_counts"].items()):
            print(f"  {cat}: {count}")

    if json_ok and sql_ok:
        print()
        print("All done! Test databases now have the 'category' property.")
        return 0
    else:
        print()
        print("ERROR: Verification failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
