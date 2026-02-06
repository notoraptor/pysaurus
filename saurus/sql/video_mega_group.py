from typing import Sequence

from pysaurus.core.classes import Selector
from pysaurus.core.datestring import Date
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.core.functions import compute_nb_pages
from pysaurus.core.lookup_array import LookupArray
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video.video_sorting import VideoSorting
from pysaurus.video_provider.view_tools import GroupDef, SearchDef
from saurus.sql.grouping_utils import SqlFieldFactory
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider_utils import (
    GroupCount,
    ProviderVideoParser,
    convert_dict_to_sql,
    search_to_sql,
)
from saurus.sql.sql_utils import QueryMaker, SQLWhereBuilder, TableDef
from saurus.sql.sql_video_wrapper import VIDEO_TABLE_FIELD_NAMES
from saurus.sql.video_mega_utils import _get_videos


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
        if grouping.is_property:
            if grouping.sorting == grouping.FIELD:
                order_field = f"value {order_direction}"
            elif grouping.sorting == grouping.LENGTH:
                # Secondary sort by value for deterministic ordering
                order_field = (
                    f"LENGTH(value || '') {order_direction}, value {order_direction}"
                )
            else:
                # grouping.sorting == grouping.COUNT
                # Secondary sort by value for deterministic ordering when counts are equal
                # Both sorts use same direction to match JSON behavior
                order_field = f"size {order_direction}, value {order_direction}"

            if classifier:
                placeholders = ["?"] * len(classifier)
                query = f"""
                SELECT v.video_id
                FROM video AS v
                JOIN video_property_value AS vv
                ON v.video_id = vv.video_id
                JOIN property AS p
                ON vv.property_id = p.property_id
                LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id
                WHERE
                v.discarded = 0 AND {source_query} AND p.name = ?
                AND vv.property_value IN ({",".join(placeholders)})
                GROUP BY vv.video_id
                HAVING COUNT(vv.property_value) = ?
                """
                params = (
                    source_params + [grouping.field] + classifier + [len(classifier)]
                )
                nb_classified_videos = len(sql_db.query_all(query, params))
                super_query = f"""
                SELECT xv.property_value AS value, COUNT(x.video_id) AS size
                FROM
                (SELECT v.video_id AS video_id
                FROM video AS v
                JOIN video_property_value AS vv
                ON v.video_id = vv.video_id
                JOIN property AS p
                ON vv.property_id = p.property_id
                LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id
                WHERE
                v.discarded = 0 AND {source_query} AND p.name = ?
                AND vv.property_value IN ({",".join(placeholders)})
                GROUP BY vv.video_id
                HAVING COUNT(vv.property_value) = ?)
                AS x
                JOIN video_property_value AS xv ON x.video_id = xv.video_id
                JOIN property AS xp ON xv.property_id = xp.property_id
                WHERE xp.name = ? AND value NOT IN ({",".join(placeholders)})
                GROUP BY value {without_singletons}
                ORDER BY {order_field}
                """
                super_params = params + [grouping.field] + classifier
                grouping_rows = [(None, nb_classified_videos)] + sql_db.query_all(
                    super_query, super_params
                )
            else:
                # Get property metadata (default value and whether it's multiple)
                prop_info = sql_db.query_one(
                    """SELECT p.multiple, pe.enum_value
                       FROM property p
                       LEFT JOIN property_enumeration pe ON p.property_id = pe.property_id
                       WHERE p.name = ?
                       ORDER BY pe.rank
                       LIMIT 1""",
                    [grouping.field],
                )
                is_multiple = prop_info[0] if prop_info else 0
                default_value = (
                    prop_info[1] if (prop_info and len(prop_info) > 1) else None
                )

                # For multiple properties, use NULL for videos without the property (to match JSON behavior)
                # For single properties, use the default value
                if is_multiple:
                    # Multiple property: videos without the property should have NULL
                    super_query = f"""
                    SELECT xv.property_value AS value, COUNT(DISTINCT x.video_id) AS size
                    FROM
                    (SELECT v.video_id AS video_id
                    FROM video AS v
                    LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id
                    WHERE v.discarded = 0 AND {source_query})
                    AS x
                    LEFT JOIN (
                        SELECT pv.video_id, pv.property_value
                        FROM video_property_value pv
                        JOIN property p ON pv.property_id = p.property_id
                        WHERE p.name = ?
                    ) AS xv ON x.video_id = xv.video_id
                    GROUP BY value {without_singletons}
                    ORDER BY {order_field}
                    """
                    super_params = source_params + [grouping.field]
                else:
                    # Single property: use default value for videos without the property
                    super_query = f"""
                    SELECT
                    IIF(x.have_property = 0, ?, xv.property_value) AS value,
                    COUNT(DISTINCT x.video_id) AS size
                    FROM
                    (SELECT
                    v.video_id AS video_id,
                    SUM(IIF(p.name = ?, 1, 0)) AS have_property
                    FROM video AS v
                    LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                    LEFT JOIN property AS p ON pv.property_id = p.property_id
                    LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id
                    WHERE v.discarded = 0 AND {source_query}
                    GROUP BY v.video_id)
                    AS x
                    LEFT JOIN video_property_value AS xv ON x.video_id = xv.video_id
                    LEFT JOIN property AS xp ON xv.property_id = xp.property_id
                    WHERE
                    (x.have_property > 0 AND xp.name = ?) OR (x.have_property = 0)
                    GROUP BY value {without_singletons}
                    ORDER BY {order_field}
                    """
                    super_params = (
                        [default_value, grouping.field]
                        + source_params
                        + [grouping.field]
                    )
                grouping_rows = sql_db.query(super_query, super_params)
        else:
            field = field_factory.get_field(grouping.field)
            if grouping.sorting == grouping.FIELD:
                order_field = field_factory.get_sorting(
                    grouping.field, grouping.reverse
                )
            elif grouping.sorting == grouping.LENGTH:
                order_field = (
                    field_factory.get_length(grouping.field) + " " + order_direction
                )
            else:
                # grouping.sorting == grouping.COUNT
                order_field = f"COUNT(v.video_id) {order_direction}"

            where_similarity_id = ""
            if grouping.field == "similarity_id":
                where_similarity_id = (
                    " AND v.similarity_id IS NOT NULL AND v.similarity_id != -1"
                )
            grouping_rows = sql_db.query(
                f"SELECT {field}, COUNT(v.video_id) AS size "
                f"FROM video AS v "
                f"LEFT JOIN video_thumbnail AS vt ON v.video_id = vt.video_id "
                f"WHERE v.discarded = 0 AND {source_query} {where_similarity_id} "
                f"GROUP BY {field} {without_singletons} "
                f"ORDER BY {order_field}",
                source_params,
            )

        output_groups.clear()
        # Convert raw SQL values to appropriate types (FileSize for bit_rate, Date for dates, etc.)
        if grouping and grouping.field in ("bit_rate", "size"):
            output_groups.extend(
                GroupCount(
                    tuple(FileSize(v) if v is not None else None for v in row[:-1]),
                    row[-1],
                )
                for row in grouping_rows
            )
        elif grouping and grouping.field in (
            "date",
            "date_entry_modified",
            "date_entry_opened",
        ):
            output_groups.extend(
                GroupCount(
                    tuple(Date(v) if v is not None else None for v in row[:-1]), row[-1]
                )
                for row in grouping_rows
            )
        elif grouping and grouping.field == "length":
            # length is duration in seconds (not microseconds)
            output_groups.extend(
                GroupCount(
                    tuple(
                        Duration(v * 1_000_000) if v is not None else None
                        for v in row[:-1]
                    ),
                    row[-1],
                )
                for row in grouping_rows
            )
        elif grouping and grouping.field in ("size_length", "move_id"):
            # Tuple fields: (file_size, length_microseconds)
            output_groups.extend(
                GroupCount(
                    tuple(
                        (FileSize(row[0]), Duration(row[1] * 1_000_000))
                        if row[0] is not None
                        else None
                    ),
                    row[2],
                )
                for row in grouping_rows
            )
        else:
            output_groups.extend(
                GroupCount(tuple(row[:-1]), row[-1]) for row in grouping_rows
            )

        output.group_id = min(max(0, output.group_id), len(output_groups) - 1)

        if not output_groups:
            # Make sure to find nothing
            query_maker.where.append_query("0")
            _compute_results_and_stats(sql_db, output, query_maker, include=include)
            return output

        group = output_groups[output.group_id]
        if grouping.is_property:
            (field_value,) = group.value

            # Get property metadata (default value and whether it's multiple)
            prop_meta_info = sql_db.query_one(
                """SELECT p.multiple, pe.enum_value
                   FROM property p
                   LEFT JOIN property_enumeration pe ON p.property_id = pe.property_id
                   WHERE p.name = ?
                   ORDER BY pe.rank
                   LIMIT 1""",
                [grouping.field],
            )
            is_multiple = prop_meta_info[0] if prop_meta_info else 0
            default_value = (
                prop_meta_info[1]
                if (prop_meta_info and len(prop_meta_info) > 1)
                else None
            )

            if classifier:
                expected = list(classifier)
                if field_value is not None:
                    expected.append(field_value)
                placeholders = ["?"] * len(expected)
                query = f"""
                SELECT v.video_id
                FROM video_property_value AS v
                JOIN property AS p
                ON v.property_id = p.property_id
                WHERE
                p.name = ?
                AND v.property_value IN ({",".join(placeholders)})
                GROUP BY v.video_id
                HAVING COUNT(v.property_value) = ?
                """
                params = [grouping.field] + expected + [len(expected)]
            elif field_value is None:
                # For both single and multiple properties: videos without the property
                query = """
                SELECT
                v.video_id AS video_id
                FROM video AS v
                LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                LEFT JOIN property AS p ON pv.property_id = p.property_id
                GROUP BY v.video_id HAVING SUM(IIF(p.name = ?, 1, 0)) = 0
                """
                params = [grouping.field]
            elif not is_multiple and field_value == default_value:
                # For single properties with default value: videos without property OR with explicit default
                query = """
                SELECT DISTINCT v.video_id
                FROM video AS v
                LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                LEFT JOIN property AS p ON pv.property_id = p.property_id
                WHERE
                    (p.name = ? AND pv.property_value = ?)
                    OR v.video_id IN (
                        SELECT vv.video_id
                        FROM video AS vv
                        LEFT JOIN video_property_value AS pvv ON vv.video_id = pvv.video_id
                        LEFT JOIN property AS pp ON pvv.property_id = pp.property_id
                        GROUP BY vv.video_id
                        HAVING SUM(IIF(pp.name = ?, 1, 0)) = 0
                    )
                """
                params = [grouping.field, field_value, grouping.field]
            else:
                query = """
                SELECT v.video_id FROM video_property_value AS v
                JOIN property AS p ON v.property_id = p.property_id
                WHERE p.name = ? AND v.property_value = ?
                """
                params = [grouping.field, field_value]
            where_group_query = f"v.video_id IN ({query})"
            where_group_params = params
        else:
            # Extract raw values from FileSize/Date/Duration objects for SQL queries
            def extract_raw(v):
                if isinstance(v, (FileSize, Date)):
                    return float(v)
                elif isinstance(v, Duration):
                    return v.t / 1_000_000  # Convert microseconds to seconds
                else:
                    return v

            raw_values = tuple(extract_raw(v) for v in group.value)
            where_group_query, where_group_params = convert_dict_to_sql(
                field_factory.get_conditions(grouping.field, raw_values)
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

    if (
        context.selection_count
        and context.page_size
        and context.page_number is not None
    ):
        query_maker_view = query_maker_select.copy()
        query_maker_view.set_field(field_video_id)
        view_indices = [row[0] for row in db.query(*query_maker_view.to_sql())]

        nb_pages = compute_nb_pages(context.selection_count, context.page_size)
        context.nb_pages = nb_pages
        context.page_number = min(max(0, context.page_number), nb_pages - 1)
        start = context.page_size * context.page_number
        end = min(start + context.page_size, context.selection_count)
        page_view = view_indices[start:end]

        query_maker_page.where.clear()
        query_maker_page.where.append_query(
            f"{field_video_id} IN ({','.join(['?'] * len(page_view))})", *page_view
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

    # print()
    # print(query_maker_count)
    # print(query_maker_select)
    # print(query_maker_page)
    # print("COUNT", context.view_count)
    # print("FILE SIZE", context.selection_file_size)
    # print("MICROSECONDS", context.selection_duration)
    # print("PAGE", len(context.result_page))
