from pysaurus.core.utils.image_utils import DEFAULT_THUMBNAIL_SIZE
from pysaurus.core.video_raptor.alignment_utils import Miniature


def main():
    path = r'C:\Users\notoraptor\Downloads\__tachibana_hina_domestic_na_kanojo_drawn_by_sasuga_kei__7c72fac062217baf920a95665c35095b.jpg'
    miniature_in = Miniature.from_file_name(path, DEFAULT_THUMBNAIL_SIZE, path)
    miniature_dict = miniature_in.to_dict()
    miniature_out = Miniature.from_dict(miniature_dict)
    assert miniature_in.r == miniature_out.r
    assert miniature_in.g == miniature_out.g
    assert miniature_in.b == miniature_out.b
    assert miniature_in.identifier == miniature_out.identifier == path
    assert miniature_in.width == miniature_out.width == DEFAULT_THUMBNAIL_SIZE[0]
    assert miniature_in.height == miniature_out.height == DEFAULT_THUMBNAIL_SIZE[1]


if __name__ == '__main__':
    main()
