from collections import defaultdict
from typing import Iterable, Sequence

from pysaurus.core.classes import Selector
from pysaurus.core.components import AbsolutePath
from pysaurus.core.duration import Duration
from pysaurus.core.file_size import FileSize
from pysaurus.core.functions import compute_nb_pages
from pysaurus.properties.properties import PropTypeValidator
from pysaurus.video.video_pattern import VideoPattern
from pysaurus.video.video_search_context import VideoSearchContext
from pysaurus.video.video_sorting import VideoSorting
from pysaurus.video_provider.view_tools import GroupDef, LookupArray, SearchDef
from saurus.sql.grouping_utils import SqlFieldFactory
from saurus.sql.prop_type_search import prop_type_search
from saurus.sql.pysaurus_connection import PysaurusConnection
from saurus.sql.saurus_provider_utils import (
    GroupCount,
    ProviderVideoParser,
    convert_dict_to_sql,
    search_to_sql,
)
from saurus.sql.sql_utils import QueryMaker, SQLWhereBuilder, TableDef
from saurus.sql.sql_video_wrapper import (
    FORMATTED_VIDEO_TABLE_FIELDS,
    VIDEO_TABLE_FIELD_NAMES,
    SQLVideoWrapper,
)
from saurus.sql.video_parser import VideoFieldQueryParser


def video_mega_search(
    db: PysaurusConnection,
    *,
    include: Sequence[str] = None,
    with_moves: bool = False,
    where: dict = None,
) -> list[VideoPattern]:
    where_builder = SQLWhereBuilder()
    selection_builder = SQLWhereBuilder(use_or=True)
    vid_query = None
    parser = VideoFieldQueryParser()
    seen = set()
    for key, value in (where or {}).items():
        parsed = parser.parse(key, value)
        assert parsed.field not in seen
        seen.add(parsed.field)
        if parsed.field in ("video_id", "filename"):
            builder = selection_builder
            if parsed.field == "video_id":
                vid_query = parsed
        else:
            builder = where_builder
        builder.append_field_query(parsed)
    if selection_builder:
        where_builder.append_query_builder(selection_builder)

    query_with = ""
    query_with_join = ""
    query_with_order = ""
    if vid_query and len(vid_query.values) > 1:
        query_with = (
            f"WITH vid_order(video_id, rank) AS "
            f"(VALUES {','.join(f'({v},{r})' for r, v in enumerate(vid_query.values))})"
        )
        query_with_join = "LEFT JOIN vid_order AS vo ON v.video_id = vo.video_id"
        query_with_order = "ORDER BY vo.rank"

    query = f"""
    {query_with}
    SELECT
        {FORMATTED_VIDEO_TABLE_FIELDS},
        t.thumbnail AS thumbnail,
        IIF(LENGTH(t.thumbnail), 1, 0) AS with_thumbnails
    FROM video AS v LEFT JOIN video_thumbnail AS t
    ON v.video_id = t.video_id
    {query_with_join}
    {where_builder.get_where_clause()}
    {query_with_order}
    """
    return _get_videos(
        db,
        query,
        where_builder.get_parameters(),
        include=include,
        with_moves=with_moves,
    )


def _get_videos(
    db: PysaurusConnection,
    query: str,
    parameters: Sequence,
    *,
    include: Sequence[str] = None,
    with_moves: bool = False,
) -> list[VideoPattern]:
    videos = [SQLVideoWrapper(row) for row in db.query(query, parameters)]
    # print(query)
    # print(parameters)
    # print(len(videos))

    video_indices = [video.data["video_id"] for video in videos]
    placeholders = ", ".join(["?"] * len(video_indices))

    errors = defaultdict(list)
    languages = {"a": defaultdict(list), "s": defaultdict(list)}
    properties = defaultdict(dict)
    json_properties = {}
    with_errors = include is None or "errors" in include
    with_audio_languages = include is None or "audio_languages" in include
    with_subtitle_languages = include is None or "subtitle_languages" in include
    with_properties = include is None or "properties" in include
    if with_errors:
        for row in db.query(
            f"SELECT video_id, error FROM video_error "
            f"WHERE video_id IN ({placeholders})",
            video_indices,
        ):
            errors[row[0]].append(row[1])
    if with_audio_languages or with_subtitle_languages:
        for row in db.query(
            f"SELECT stream, video_id, lang_code FROM video_language "
            f"WHERE video_id IN ({placeholders}) "
            f"ORDER BY stream ASC, video_id ASC, rank ASC",
            video_indices,
        ):
            languages[row[0]][row[1]].append(row[2])
    if with_properties:
        prop_types: dict[int, PropTypeValidator] = {
            desc["property_id"]: PropTypeValidator(desc)
            for desc in prop_type_search(db)
        }
        for row in db.query(
            f"SELECT video_id, property_id, property_value "
            f"FROM video_property_value WHERE video_id IN ({placeholders})",
            video_indices,
        ):
            properties[row[0]].setdefault(row[1], []).append(row[2])
        json_properties = {
            video_id: {
                prop_types[property_id].name: prop_types[property_id].from_strings(
                    values
                )
                for property_id, values in raw_properties.items()
            }
            for video_id, raw_properties in properties.items()
        }

    if with_errors:
        for video in videos:
            video.errors = errors.get(video.video_id, [])
    if with_audio_languages:
        for video in videos:
            video.audio_languages = languages["a"].get(video.video_id, [])
    if with_subtitle_languages:
        for video in videos:
            video.subtitle_languages = languages["s"].get(video.video_id, [])
    if with_properties:
        for video in videos:
            video.properties = json_properties.get(video.video_id, {})
    if with_moves:
        moves = {
            video_id: video_moves for video_id, video_moves in _get_video_moves(db)
        }
        for video in videos:
            video.moves = moves.get(video.video_id, [])

    return videos


def _get_video_moves(db: PysaurusConnection) -> Iterable[tuple[int, list[dict]]]:
    for row in db.query(
        """
    SELECT group_concat(video_id || '-' || is_file || '-' || hex(filename))
    FROM video
    WHERE unreadable = 0 AND discarded = 0
    GROUP BY file_size, duration, COALESCE(NULLIF(duration_time_base, 0), 1)
    HAVING COUNT(video_id) > 1 AND SUM(is_file) < COUNT(video_id);
    """
    ):
        not_found = []
        found = []
        for piece in row[0].split(","):
            str_video_id, str_is_file, str_hex_filename = piece.split("-")
            video_id = int(str_video_id)
            if int(str_is_file):
                found.append(
                    {
                        "video_id": video_id,
                        "filename": AbsolutePath(
                            bytes.fromhex(str_hex_filename).decode("utf-8")
                        ).standard_path,
                    }
                )
            else:
                not_found.append(video_id)
        assert not_found and found, (not_found, found)
        for id_not_found in not_found:
            yield id_not_found, found


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
                order_field = "value"
            elif grouping.sorting == grouping.LENGTH:
                order_field = "LENGTH(value || '')"
            else:
                assert grouping.sorting == grouping.COUNT
                order_field = "size"

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
                ORDER BY {order_field} {order_direction}
                """
                super_params = params + [grouping.field] + classifier
                grouping_rows = [(None, nb_classified_videos)] + sql_db.query_all(
                    super_query, super_params
                )
            else:
                super_query = f"""
                SELECT
                IIF(x.have_property = 0, NULL, xv.property_value) AS value,
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
                ORDER BY {order_field} {order_direction}
                """
                super_params = [grouping.field] + source_params + [grouping.field]
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
                assert grouping.sorting == grouping.COUNT
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
                query = """
                SELECT
                v.video_id AS video_id
                FROM video AS v
                LEFT JOIN video_property_value AS pv ON v.video_id = pv.video_id
                LEFT JOIN property AS p ON pv.property_id = p.property_id
                GROUP BY v.video_id HAVING SUM(IIF(p.name = ?, 1, 0)) = 0
                """
                params = [grouping.field]
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
            where_group_query, where_group_params = convert_dict_to_sql(
                field_factory.get_conditions(grouping.field, group.value)
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
    include: Sequence[str] = None,
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
