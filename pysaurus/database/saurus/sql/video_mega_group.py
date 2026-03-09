from typing import Callable, Iterable, Sequence

from pysaurus.core.classes import Selector, StringedTuple
from pysaurus.core.datestring import Date
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.core.functions import compute_nb_pages
from pysaurus.core.lookup_array import LookupArray
from pysaurus.video.video_constants import SIMILARITY_FIELDS as _SIMILARITY_FIELDS
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video.video_sorting import VideoSorting
from pysaurus.video_provider.view_tools import GroupDef, SearchDef
from pysaurus.database.saurus.sql.grouping_utils import SqlFieldFactory
from pysaurus.database.saurus.sql.pysaurus_connection import PysaurusConnection
from pysaurus.database.saurus.sql.saurus_provider_utils import (
    GroupCount,
    ProviderVideoParser,
    convert_dict_to_sql,
    search_to_sql,
)
from pysaurus.database.saurus.sql.sql_utils import (
    QueryMaker,
    SQLWhereBuilder,
    TableDef,
    sql_placeholders,
)
from pysaurus.database.saurus.sql.sql_video_wrapper import VIDEO_TABLE_FIELD_NAMES
from pysaurus.database.saurus.sql.video_mega_utils import _get_videos


def video_mega_group(
    sql_db: PysaurusConnection,
    *,
    sources: Sequence[list[str]] = (),
    grouping: GroupDef = GroupDef(),
    classifier: Sequence[str] = (),
    group=0,
    search: SearchDef = SearchDef(),
    sorting: Sequence[str] = (),
    selector: Selector = None,
    page_size: int = None,
    page_number: int = None,
    include: Sequence[str] = None,
    with_moves=False,
) -> VideoSearchContext:
    output_groups = LookupArray[GroupCount](GroupCount, (), GroupCount.keyof)
    output = VideoSearchContext(
        sources=sources,
        grouping=grouping,
        classifier=classifier,
        group_id=group,
        search=search,
        sorting=sorting,
        selector=selector,
        page_size=page_size,
        page_number=page_number,
        with_moves=with_moves,
        result_groups=output_groups,
    )

    query_maker = QueryMaker("video", "v")
    field_video_id = query_maker.get_main_table().get_alias_field("video_id")
    query_maker.add_field(field_video_id)
    video_thumbnail_table = TableDef("video_thumbnail", "vt")
    query_maker.add_left_join(video_thumbnail_table, "video_id")

    if search and search.cond == "id":
        query_maker.where.append_field(field_video_id, int(search.text))
        _compute_results_and_stats(sql_db, output, query_maker, include=include)
        return output

    field_factory = SqlFieldFactory(sql_db)
    parser = ProviderVideoParser()
    source_query_builder = SQLWhereBuilder.combine(
        [
            SQLWhereBuilder.build(parser.parse(flag, True) for flag in source)
            for source in sources
        ],
        use_or=True,
    )
    source_query = source_query_builder.get_clause()
    source_params = source_query_builder.get_parameters()

    where_group_query = None
    where_group_params = None
    if grouping:
        without_singletons = ""
        if not grouping.allow_singletons:
            without_singletons = "HAVING size > 1"
        order_direction = "DESC" if grouping.reverse else "ASC"
        prop_value_converter = None
        if grouping.is_property:
            order_field = _get_property_order_field(grouping, order_direction)
            prop_value_converter = _get_property_value_converter(sql_db, grouping.field)
            prop_meta = _get_property_metadata(sql_db, grouping.field)
            if classifier:
                grouping_rows = _query_property_groups_with_classifier(
                    sql_db,
                    source_query,
                    source_params,
                    grouping,
                    classifier,
                    order_field,
                    without_singletons,
                    prop_meta,
                )
            else:
                grouping_rows = _query_property_groups_without_classifier(
                    sql_db,
                    source_query,
                    source_params,
                    grouping,
                    order_field,
                    without_singletons,
                    prop_meta,
                )
        else:
            grouping_rows = _query_field_groups(
                sql_db, source_query, source_params, grouping, field_factory
            )

        output_groups.clear()
        output_groups.extend(
            _convert_grouping_rows(grouping.field, grouping_rows, prop_value_converter)
        )

        if not output_groups:
            # Make sure to find nothing
            query_maker.where.append_query("0")
            _compute_results_and_stats(sql_db, output, query_maker, include=include)
            return output

        output.group_id = min(max(0, output.group_id), len(output_groups) - 1)
        group = output_groups[output.group_id]
        if grouping.is_property:
            (field_value,) = group.value
            where_group_query, where_group_params = _filter_by_selected_property_group(
                grouping, classifier, field_value, prop_meta
            )
        else:
            where_group_query, where_group_params = _filter_by_selected_field_group(
                group, grouping, field_factory
            )

    where_builder = query_maker.where
    where_builder.append_query("v.discarded = 0")
    where_builder.append_query(source_query, *source_params)

    if where_group_query:
        where_builder.append_query(where_group_query, *where_group_params)

    if search:
        where_search, params_search = search_to_sql(search)
        where_builder.append_query(f"v.video_id IN ({where_search})", *params_search)

    sql_sorting = [
        field_factory.get_sorting(field, reverse)
        for field, reverse in VideoSorting(sorting)
    ]

    for sorting in sql_sorting:
        query_maker.order_by_complex(sorting)
    _compute_results_and_stats(sql_db, output, query_maker, include=include)
    return output


def _compute_results_and_stats(
    db: PysaurusConnection,
    context: VideoSearchContext,
    query_maker: QueryMaker,
    include: Sequence[str] | None = None,
):
    query_maker_count = query_maker.copy()
    query_maker_select = query_maker.copy()
    query_maker_page = query_maker.copy()

    field_video_id = query_maker.get_main_table().get_alias_field("video_id")

    query_maker_count.set_field(f"COUNT({field_video_id})")
    (row_count,) = db.query_all(*query_maker_count.to_sql())
    context.view_count = row_count[0] or 0

    if context.selector is not None:
        select_query, select_params = context.selector.to_sql(field_video_id)
        query_maker_select.where.append_query(select_query, *select_params)
        query_maker_page.where.append_query(select_query, *select_params)

    query_maker_select.set_fields(
        (
            f"SUM({query_maker.get_main_table().get_alias_field('file_size')})",
            f"SUM({query_maker.get_main_table().get_alias_field('length_microseconds')})",
            f"COUNT({field_video_id})",
        )
    )
    (row_stats,) = db.query_all(*query_maker_select.to_sql())
    context.selection_file_size = FileSize(row_stats[0] or 0)
    context.selection_duration = Duration(row_stats[1] or 0)
    context.selection_count = row_stats[2]

    if context.page_size and context.page_number is not None:
        nb_pages = compute_nb_pages(context.selection_count, context.page_size)
        context.nb_pages = nb_pages
        context.page_number = min(max(0, context.page_number), nb_pages - 1)

        if context.selection_count:
            query_maker_view = query_maker_select.copy()
            query_maker_view.set_field(field_video_id)
            with db:
                view_indices = [row[0] for row in db.query(*query_maker_view.to_sql())]

            start = context.page_size * context.page_number
            end = min(start + context.page_size, context.selection_count)
            page_view = view_indices[start:end]

            query_maker_page.where.clear()
            query_maker_page.where.append_query(
                f"{field_video_id} IN ({sql_placeholders(len(page_view))})", *page_view
            )

    thumb_table = query_maker_page.find_table("video_thumbnail")
    field_thumbnail = thumb_table.get_alias_field("thumbnail")
    query_maker_page.set_fields(
        [
            f"{query_maker_page.get_main_table().get_alias_field(field)} AS {field}"
            for field in VIDEO_TABLE_FIELD_NAMES
        ]
        + [
            f"{field_thumbnail} AS thumbnail",
            f"IIF(LENGTH({field_thumbnail}), 1, 0) AS with_thumbnails",
        ]
    )

    context.result = _get_videos(
        db, *query_maker_page.to_sql(), include=include, with_moves=context.with_moves
    )

    # Compute similarity diff fields now that result is populated.
    # (VideoSearchContext.__post_init__ can't do it because result is set after init)
    if (
        context.result
        and context.grouping
        and context.grouping.field in _SIMILARITY_FIELDS
    ):
        from pysaurus.video.video_constants import COMMON_FIELDS
        from pysaurus.video.video_features import VideoFeatures

        context.common_fields = VideoFeatures.get_common_fields(
            context.result, fields=COMMON_FIELDS
        )
        context.file_title_diffs = VideoFeatures.get_file_title_diffs(context.result)


def _thumbnail_join_if_needed(source_query: str) -> str:
    """Return LEFT JOIN video_thumbnail clause if source_query references vt."""
    if "vt." in source_query:
        return "LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id"
    return ""


def _get_property_order_field(grouping: GroupDef, order_direction: str) -> str:
    if grouping.sorting == grouping.FIELD:
        return f"value {order_direction}"
    elif grouping.sorting == grouping.LENGTH:
        # Secondary sort by value for deterministic ordering
        return f"LENGTH(value || '') {order_direction}, value {order_direction}"
    else:
        # grouping.sorting == grouping.COUNT
        # Secondary sort by value for deterministic ordering when counts are equal
        # Both sorts use same direction to match JSON behavior
        return f"size {order_direction}, value {order_direction}"


def _query_property_groups_with_classifier(
    sql_db: PysaurusConnection,
    source_query: str,
    source_params: list,
    grouping: GroupDef,
    classifier: Sequence[str],
    order_field: str,
    without_singletons: str,
    prop_meta: tuple[int, bool, str | None],
) -> list[tuple]:
    prop_id, _, _ = prop_meta
    placeholders = ["?"] * len(classifier)
    vt_join = _thumbnail_join_if_needed(source_query)
    query = f"""
    SELECT v.video_id
    FROM video AS v
    {vt_join}
    JOIN video_property_value AS vv
        ON v.video_id = vv.video_id AND vv.property_id = ?
    WHERE v.discarded = 0 AND {source_query}
    AND vv.property_value IN ({",".join(placeholders)})
    GROUP BY v.video_id
    HAVING COUNT(vv.property_value) = ?
    """
    params = [prop_id] + source_params + classifier + [len(classifier)]
    nb_classified_videos = len(sql_db.query_all(query, params))
    super_query = f"""
    SELECT xv.property_value AS value, COUNT(x.video_id) AS size
    FROM
    (SELECT v.video_id AS video_id
    FROM video AS v
    {vt_join}
    JOIN video_property_value AS vv
        ON v.video_id = vv.video_id AND vv.property_id = ?
    WHERE v.discarded = 0 AND {source_query}
    AND vv.property_value IN ({",".join(placeholders)})
    GROUP BY v.video_id
    HAVING COUNT(vv.property_value) = ?)
    AS x
    JOIN video_property_value AS xv
        ON x.video_id = xv.video_id AND xv.property_id = ?
    WHERE value NOT IN ({",".join(placeholders)})
    GROUP BY value {without_singletons}
    ORDER BY {order_field}
    """
    super_params = params + [prop_id] + classifier
    return [(None, nb_classified_videos)] + sql_db.query_all(super_query, super_params)


def _query_property_groups_without_classifier(
    sql_db: PysaurusConnection,
    source_query: str,
    source_params: list,
    grouping: GroupDef,
    order_field: str,
    without_singletons: str,
    prop_meta: tuple[int, bool, str | None],
) -> list[Sequence]:
    prop_id, is_multiple, default_value = prop_meta
    vt_join = _thumbnail_join_if_needed(source_query)

    if is_multiple:
        query = f"""
        SELECT pv.property_value AS value, COUNT(DISTINCT v.video_id) AS size
        FROM video AS v
        {vt_join}
        LEFT JOIN video_property_value AS pv
            ON v.video_id = pv.video_id AND pv.property_id = ?
        WHERE v.discarded = 0 AND {source_query}
        GROUP BY value {without_singletons}
        ORDER BY {order_field}
        """
        params = [prop_id] + source_params
    else:
        query = f"""
        SELECT
            COALESCE(pv.property_value, ?) AS value,
            COUNT(v.video_id) AS size
        FROM video AS v
        {vt_join}
        LEFT JOIN video_property_value AS pv
            ON v.video_id = pv.video_id AND pv.property_id = ?
        WHERE v.discarded = 0 AND {source_query}
        GROUP BY value {without_singletons}
        ORDER BY {order_field}
        """
        params = [default_value, prop_id] + source_params
    return sql_db.query_all(query, params)


def _query_field_groups(
    sql_db: PysaurusConnection,
    source_query: str,
    source_params: list,
    grouping: GroupDef,
    field_factory: SqlFieldFactory,
) -> list[Sequence]:
    order_direction = "DESC" if grouping.reverse else "ASC"
    field = field_factory.get_field(grouping.field)
    if grouping.sorting == grouping.FIELD:
        order_field = field_factory.get_sorting(grouping.field, grouping.reverse)
    elif grouping.sorting == grouping.LENGTH:
        order_field = field_factory.get_length(grouping.field) + " " + order_direction
    else:
        # grouping.sorting == grouping.COUNT
        order_field = f"COUNT(v.video_id) {order_direction}"

    without_singletons = ""
    if not grouping.allow_singletons:
        without_singletons = "HAVING size > 1"

    where_similarity_id = ""
    if grouping.field in _SIMILARITY_FIELDS:
        where_similarity_id = (
            f" AND v.{grouping.field} IS NOT NULL AND v.{grouping.field} != -1"
        )

    if grouping.field == "move_id":
        return _query_move_id_groups(
            sql_db, source_query, source_params, order_direction, without_singletons
        )

    return sql_db.query_all(
        f"SELECT {field}, COUNT(v.video_id) AS size "
        f"FROM video AS v "
        f"LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id "
        f"WHERE v.discarded = 0 AND {source_query} {where_similarity_id} "
        f"GROUP BY {field} {without_singletons} "
        f"ORDER BY {order_field}",
        source_params,
    )


def _query_move_id_groups(
    sql_db: PysaurusConnection,
    source_query: str,
    source_params: list,
    order_direction: str,
    without_singletons: str,
) -> list[Sequence]:
    """Query move_id groups matching JSON behavior.

    Videos with potential moves (same file_size/duration/time_base
    with both found and not-found entries) get (file_size, length).
    Videos without moves get NULL, forming one group.
    """
    length_expr = "(v.duration * 1.0 / COALESCE(NULLIF(v.duration_time_base, 0), 1))"
    query = f"""
    WITH move_candidates AS (
        SELECT file_size, duration, duration_time_base_not_null
        FROM video
        WHERE unreadable = 0 AND discarded = 0
        GROUP BY file_size, duration, duration_time_base_not_null
        HAVING COUNT(*) > 1
            AND SUM(is_file) > 0
            AND SUM(is_file) < COUNT(*)
    )
    SELECT
        IIF(mc.file_size IS NOT NULL, v.file_size, NULL) AS move_file_size,
        IIF(mc.file_size IS NOT NULL, {length_expr}, NULL) AS move_length,
        COUNT(v.video_id) AS size
    FROM video AS v
    LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id
    LEFT JOIN move_candidates AS mc
        ON v.file_size = mc.file_size
        AND v.duration = mc.duration
        AND v.duration_time_base_not_null = mc.duration_time_base_not_null
    WHERE v.discarded = 0 AND {source_query}
    GROUP BY move_file_size, move_length {without_singletons}
    ORDER BY move_file_size {order_direction}, move_length {order_direction}
    """
    return sql_db.query_all(query, source_params)


_FIELD_CONVERTERS: dict[str, Callable] = {
    "bit_rate": FileSize,
    "size": FileSize,
    "date": Date,
    "date_entry_modified": Date,
    "date_entry_opened": Date,
    "length": lambda v: Duration(v * 1_000_000),
    "year": int,
    "watched": bool,
}


def _convert_grouping_rows(
    grouping_field: str,
    grouping_rows: list[tuple],
    prop_value_converter: Callable | None = None,
) -> Iterable[GroupCount]:
    if grouping_field in ("size_length", "move_id"):
        # Composite fields: (file_size, length) or None for videos without moves
        return (
            GroupCount(
                StringedTuple((FileSize(row[0]), Duration(row[1] * 1_000_000)))
                if row[0] is not None
                else None,
                row[2],
            )
            for row in grouping_rows
        )

    converter = _FIELD_CONVERTERS.get(grouping_field, prop_value_converter)
    if converter is not None:
        return (
            GroupCount(
                tuple(converter(v) if v is not None else None for v in row[:-1]),
                row[-1],
            )
            for row in grouping_rows
        )
    return (GroupCount(tuple(row[:-1]), row[-1]) for row in grouping_rows)


def _filter_by_selected_property_group(
    grouping: GroupDef,
    classifier: Sequence[str],
    field_value,
    prop_meta: tuple[int, bool, str | None],
) -> tuple[str, list]:
    prop_id, is_multiple, default_value = prop_meta

    if classifier:
        expected = list(classifier)
        if field_value is not None:
            expected.append(field_value)
        placeholders = ["?"] * len(expected)
        query = f"""
        SELECT video_id
        FROM video_property_value
        WHERE property_id = ?
        AND property_value IN ({",".join(placeholders)})
        GROUP BY video_id
        HAVING COUNT(property_value) = ?
        """
        params = [prop_id] + expected + [len(expected)]
    elif field_value is None:
        query = """
        SELECT video_id FROM video
        WHERE video_id NOT IN (
            SELECT video_id FROM video_property_value WHERE property_id = ?
        )
        """
        params = [prop_id]
    elif not is_multiple and field_value == default_value:
        query = """
        SELECT video_id FROM video_property_value
        WHERE property_id = ? AND property_value = ?
        UNION
        SELECT video_id FROM video
        WHERE video_id NOT IN (
            SELECT video_id FROM video_property_value WHERE property_id = ?
        )
        """
        params = [prop_id, field_value, prop_id]
    else:
        query = """
        SELECT video_id FROM video_property_value
        WHERE property_id = ? AND property_value = ?
        """
        params = [prop_id, field_value]
    return f"v.video_id IN ({query})", params


def _filter_by_no_moves() -> tuple[str, list]:
    """Filter for videos that have no potential moves."""
    query = """
    v.video_id NOT IN (
        SELECT v2.video_id FROM video AS v2
        JOIN (
            SELECT file_size, duration, duration_time_base_not_null
            FROM video
            WHERE unreadable = 0 AND discarded = 0
            GROUP BY file_size, duration, duration_time_base_not_null
            HAVING COUNT(*) > 1
                AND SUM(is_file) > 0
                AND SUM(is_file) < COUNT(*)
        ) AS mc
        ON v2.file_size = mc.file_size
        AND v2.duration = mc.duration
        AND v2.duration_time_base_not_null = mc.duration_time_base_not_null
        WHERE v2.unreadable = 0 AND v2.discarded = 0
    )
    """
    return query, []


def _filter_by_selected_field_group(
    group: GroupCount, grouping: GroupDef, field_factory: SqlFieldFactory
) -> tuple[str, list]:
    if grouping.field == "move_id" and group.value is None:
        # Videos without potential moves
        return _filter_by_no_moves()

    # Extract raw values from FileSize/Date/Duration objects for SQL queries
    def extract_raw(v):
        if isinstance(v, (FileSize, Date)):
            return float(v)
        elif isinstance(v, Duration):
            return v.t / 1_000_000  # Convert microseconds to seconds
        else:
            return v

    raw_values = tuple(extract_raw(v) for v in group.value)
    return convert_dict_to_sql(field_factory.get_conditions(grouping.field, raw_values))


def _get_property_value_converter(
    sql_db: PysaurusConnection, property_name: str
) -> Callable:
    """Return a converter function for property values from SQL (TEXT) to Python types."""
    from pysaurus.properties.properties import PROP_UNIT_CONVERTER

    row = sql_db.query_one("SELECT type FROM property WHERE name = ?", [property_name])
    prop_type = row["type"] if row else "str"
    return PROP_UNIT_CONVERTER[prop_type]


def _get_property_metadata(
    sql_db: PysaurusConnection, property_name: str
) -> tuple[int, bool, str | None]:
    prop_info = sql_db.query_one(
        """SELECT p.property_id, p.multiple, pe.enum_value
           FROM property p
           LEFT JOIN property_enumeration pe ON p.property_id = pe.property_id
           WHERE p.name = ?
           ORDER BY pe.rank
           LIMIT 1""",
        [property_name],
    )
    if not prop_info:
        return 0, False, None
    default_value = prop_info[2] if len(prop_info) > 2 else None
    return prop_info[0], prop_info[1], default_value
