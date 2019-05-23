import urllib.parse

from pysaurus.core import utils
from pysaurus.core.video import Video
from pysaurus.core.video_duration import VideoDuration


def get_same_sizes(database: dict):
    sizes = {}
    for video in database.values():
        if video.exists():
            sizes.setdefault(video.size, []).append(video)
    duplicated_sizes = {size: elements for (size, elements) in sizes.items() if len(elements) > 1}
    if duplicated_sizes:
        print()
        utils.print_title('%d DUPLICATE CASE(S)' % len(duplicated_sizes))
        for size in sorted(duplicated_sizes.keys()):
            elements = duplicated_sizes[size]  # type: list
            elements.sort(key=lambda v: v.filename)
            print(size, 'bytes,', len(elements), 'video(s)')
            for video in elements:
                print('\t"%s"' % video.filename)


def get_same_lengths(database: dict):
    durations = {}
    for video in database.values():
        if video.exists():
            durations.setdefault(video.get_duration(), []).append(video)
    same_lengths = {duration: elements for duration, elements in durations.items() if len(elements) > 1}
    if same_lengths:
        whole_info = '%d same length(S), %d video(s)' % (
            len(same_lengths), sum(len(elements) for elements in same_lengths.values()))
        html = utils.StringPrinter()
        html.write('<!DOCTYPE html>')
        html.write('<html>')
        html.write('<head>')
        html.write('<meta charset="utf-8"/>')
        html.write('<title>%s</title>' % whole_info)
        html.write("""<style>
        body {
            font-family: "Trebuchet MS", Helvetica, sans-serif;
            margin:0;
            padding:0;
        }
        img {display: block; max-height: 5rem;}
        td.link {width: 20%;}
        div.group {
            margin-top: 20px;
            padding-top: 10px;
            padding-bottom: 10px;
            border-top: 1px solid grey;
            font-weight: bold;
            font-size: 1.5rem;
        }
        </style>""")
        html.write('</head>')
        html.write('<body>')
        html.write('<h1>%s</h1>' % whole_info)
        html.write('<table cellspacing="0">')
        for duration in sorted(same_lengths.keys()):
            elements = same_lengths[duration]  # type: list
            elements.sort(key=lambda v: v.filename)
            html.write(
                '<tr><td colspan="7"><div class="group">%s, %d video(s)</div></td></tr>' % (duration, len(elements)))
            for video in elements:  # type: Video
                html.write('<tr>')
                html.write('<td rowspan="2"><img src="file:///%s"/></td>' % video.thumbnail)
                html.write('<td class="link"><a target="_blank" href="file:///%s">%s</a></td>' % (
                    urllib.parse.quote(video.filename.path), video.get_title()))
                html.write('<td>%s</td>' % video.get_size())
                html.write('<td>%d x %d</td>' % (video.width, video.height))
                html.write('<td>format %s</td>' % video.container_format)
                html.write('<td>video %s</td>' % video.video_codec)
                html.write('<td>audio %s</td>' % video.audio_codec)
                html.write('</tr>')
                html.write('<tr><td colspan="6"><pre>del "%s"</pre></td></tr>' % (video.filename))
        html.write('</table>')
        html.write('</body>')
        html.write('</html>')
        return str(html)
    return ''


def find(database: dict, term: str):
    term = term.lower()
    found = []
    for video in database.values():  # type: Video
        if video.exists() and (term in video.title.lower() or term in video.filename.path.lower()):
            found.append(video)
    print(len(found), 'FOUND', term)
    found.sort(key=lambda v: v.get_duration())
    for video in found:
        print('\t"%s"\t%s' % (video.filename, VideoDuration(video)))
