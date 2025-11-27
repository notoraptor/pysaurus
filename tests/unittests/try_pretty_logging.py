import logging
import pprint

from pysaurus.core.prettylogging import PrettyLogging


def main():
    print(logging.getLevelName(logging.root.level))
    logging.basicConfig(level=logging.DEBUG)
    print(logging.getLevelName(logging.root.level))
    logging.debug("hello")
    logging.info("hello")
    logging.warning("hello")

    PrettyLogging.debug("Hello", "world", 12)
    PrettyLogging.debug("hello")
    PrettyLogging.info("hello")
    PrettyLogging.warning("hello")

    d = {f"hello world {i}": f"I am the number {i}" for i in range(10)}
    PrettyLogging.debug(pprint.pformat(d))
    PrettyLogging.log("Hello, hello !!!")
    PrettyLogging.log(pprint.pformat(d))
    print(PrettyLogging.format(pprint.pformat(d)))


if __name__ == "__main__":
    main()
