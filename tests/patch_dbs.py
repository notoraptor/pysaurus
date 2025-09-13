from pysaurus.core.informer import Information
from pysaurus.interface.api.feature_api import FeatureAPI


def main():
    with Information() as informer:
        api = FeatureAPI(informer.notifier())
        for name in api.application.get_database_names():
            api.application.open_database_from_name(name, False)


if __name__ == "__main__":
    main()
