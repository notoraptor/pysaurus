import os
import sys
from typing import Any, List

import ujson as json

from pysaurus.core.components.absolute_path import AbsolutePath
from pysaurus.core.database.database import Database
from pysaurus.core.utils.classes import StringPrinter
from pysaurus.core.utils.functions import timestamp_microseconds
from pysaurus.core.video_raptor import alignment as native_alignment
from pysaurus.core.video_raptor.alignment_utils import Miniature
from pysaurus.public.api import API

PRINT_STEP = 500
SIM_LIMIT = 0.9
MIN_VAL = 0
MAX_VAL = 255
GAP_SCORE = -1


class Node:
    __slots__ = ('node', 'edges')

    def __init__(self, value):
        self.node = value
        self.edges = {}

    def add_edge(self, node, weight):
        self.edges[node] = weight

    def min_weight(self):
        return min(self.edges.values()) if self.edges else 0

    def max_weight(self):
        return max(self.edges.values()) if self.edges else 0

    def __hash__(self):
        return hash(self.node)

    def __eq__(self, other):
        return self.node == other.node

    def __lt__(self, other):
        return self.node < other.node


def similar_group_to_html_file(group_id, group, miniatures, database, html_dir, unique_id):
    # type: (int, List[Node], List[Miniature], Database, AbsolutePath, Any) -> None
    size = len(group)
    min_score = min(node.min_weight() for node in group)
    max_score = max(node.max_weight() for node in group)
    html = StringPrinter()
    html.write('<html>')
    html.write('<header>')
    html.write('<meta charset="utf-8"/>')
    html.write('<title>Thumbnails similarities for group %03d</title>' % group_id)
    html.write('<link rel="stylesheet" href="similarities.css"/>')
    html.write('</header>')
    html.write('<body>')
    html.write('<h1>Group %s, %d files, min score %s, max score %s</h1>' % (group_id, size, min_score, max_score))
    html.write('<table>')
    html.write('<thead>')
    html.write('<tr><th class="header-images">Image</th><th class="header-details">Details</th></tr>')
    html.write('<tbody>')
    for node in sorted(group):
        miniature_i = miniatures[node.node]
        thumb_path = database.get_video_from_filename(miniature_i.identifier).get_thumbnail_path()
        html.write('<tr>')
        html.write('<td class="image">')
        html.write('<img src="file://%s"/>' % thumb_path)
        html.write('</td>')
        html.write('<td class="details">')
        html.write('<div class="image-file"><strong><code>"%s"</code></strong></div>' % thumb_path)
        html.write('<div class="origin-file"><em><code>"%s"</em></strong></div>' % miniature_i.identifier)
        html.write('<div><code><strong><em>[%s]</em></strong></code></div>' % node.node)
        for output_node in sorted(node.edges):
            html.write('<div class="score"><code><em>With %s</em>: <strong>%s</strong></code></div>' % (
                output_node, node.edges[output_node]))
        html.write('</td>')
        html.write('</tr>')
    html.write('</tbody>')
    html.write('</thead>')
    html.write('</table>')
    html.write('</body>')
    html.write('</html>')

    output_file_name = AbsolutePath.join(html_dir, 'sim.%s.%03d.html' % (unique_id, group_id))
    with open(output_file_name.path, 'wb') as file:
        file.write(str(html).encode())


def extract_linked_nodes(graph):
    # type: (dict) -> List[List[Node]]
    groups = []
    while graph:
        node_in, linked_nodes = next(iter(graph.items()))
        group = {node_in: Node(node_in)}
        del graph[node_in]
        nodes_out = [(node_in, node_out, weight) for (node_out, weight) in linked_nodes]
        while nodes_out:
            v_in, v_out, w = nodes_out.pop()
            if v_out not in group:
                group[v_out] = Node(v_out)
                group[v_out].add_edge(v_in, w)
                group[v_in].add_edge(v_out, w)
                if v_out in graph:
                    nodes_out.extend((v_out, other_v, other_w) for (other_v, other_w) in graph.pop(v_out))
        groups.append(sorted(group.values()))
    return groups


def find_similar_images(miniatures):
    # type: (List[Miniature]) -> List[List[Node]]
    edges = native_alignment.classify_similarities(miniatures)
    graph = {}
    nb_miniatures = len(miniatures)
    min_score = None
    max_score = None
    for index, score in enumerate(edges):
        if score >= SIM_LIMIT:
            i = int(index / nb_miniatures)
            j = index % nb_miniatures
            graph.setdefault(i, []).append((j, score))
            graph.setdefault(j, []).append((i, score))
            min_score = score if min_score is None else min(min_score, score)
            max_score = score if max_score is None else max(max_score, score)
    print('Min score', min_score)
    print('Max score', max_score)
    groups = extract_linked_nodes(graph)
    return [group for group in groups if len(group) > 1]


def main():
    list_file_path = sys.argv[1] if len(sys.argv) > 1 else None
    database = API.load_database(list_file_path=list_file_path)
    miniatures = sorted(database.ensure_miniatures().values(), key=lambda m: m.identifier)
    print('Extracted miniatures from %d/%d videos.' % (len(miniatures), database.nb_valid))

    sim_groups = find_similar_images(miniatures)
    print('Finally found', len(sim_groups), 'similarity groups.')
    print(sum(len(g) for g in sim_groups), 'similar images from', len(miniatures), 'total images.')
    sim_groups.sort(key=lambda group: len(group))

    html_dir = AbsolutePath('.html')
    unique_id = timestamp_microseconds()
    if sim_groups:
        if html_dir.isdir():
            for file_name in html_dir.listdir():
                if file_name.endswith('.html'):
                    AbsolutePath.join(html_dir, file_name).delete()
        elif html_dir.isfile():
            raise OSError('Path .html is a file, not a directory.')
        else:
            os.makedirs(html_dir.path, exist_ok=True)

    for i, g in enumerate(sim_groups):
        similar_group_to_html_file(i + 1, g, miniatures, database, html_dir, unique_id)

    json_groups = [
        {miniatures[node.node].identifier.path:
             database.get_video_from_filename(miniatures[node.node].identifier).get_thumbnail_path().path
         for node in group}
        for group in sim_groups]

    json_output_file_name = 'similarities.json'
    with open(json_output_file_name, 'w') as file:
        json.dump(json_groups, file)

    print('Similarities saved in', json_output_file_name)


if __name__ == '__main__':
    main()
