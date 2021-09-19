from pysaurus.database.backend_pyav import get_infos, get_thumbnail
from qt_vlc_player import PATHS


def _lookup(obj):
    print(":", type(obj).__name__)
    for name in dir(obj):
        if name.startswith("_"):
            continue
        print("\t", name, type(getattr(obj, name)))


def main():
    _path = PATHS[0]
    # _path = r"I:\donnees\autres\p\Violet Starr, Liv Wild - domination is passive-addictive.mp4"
    _path = r"J:\donnees\divers\autres\p\7512205_grandmasterb - RY_720p.flv"
    _path = r"I:\donnees\autres\p\[Sangen-Rips] Shinjin Tour Conductor (Dark Tours) (新人ツアーコンダクター里奈 ツアーオプション⇔添乗員、強制乱交) [DVDR-720p-HEVC-AC3-PCM] [Dual-Audio] [Uncensored] [RAW]\[Sangen-Rips] Dark Tours OVA [DVDR-720p-HEVC-AC3-PCM] [RAW] [598DC24B].mkv"
    _path = r"I:\donnees\autres\p\Gabbie Carter, Eliza Ibarra - perfect massage for a beginner.mp4"
    _path = r"I:\donnees\autres\p\Dressed Up.XXX.1080p.WEB.MP4-PR0N.mp4"
    default_thumb_name = "thumb.png"
    for k, v in get_infos(_path).items():
        print(k, "=", v)
    assert get_thumbnail(_path, default_thumb_name) is None


if __name__ == "__main__":
    main()
