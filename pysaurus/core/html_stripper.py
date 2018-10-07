from html.parser import HTMLParser


class HTMLStripper(HTMLParser):
    """ HTML parser class to remove HTML tags from a string.
        Example:
            text = HTMLStripper.strip(text)
        Reference: (2018/09/24) https://stackoverflow.com/a/925630
    """

    # pylint: disable=abstract-method

    def __init__(self):
        """ Constructor """
        super(HTMLStripper, self).__init__(convert_charrefs=True)
        self.fed = []

    def handle_data(self, data):
        """ Split text to blank delimiters and store text pieces. """
        self.fed.extend(data.split())

    def get_data(self):
        """ Return filtered text pieces, joined with space.
            Each spaces sequence should contain only 1 space in returned text.
        """
        return ' '.join(self.fed)

    @classmethod
    def strip(cls, msg):
        """ Remove HTML tags from given message and return stripped message. """
        html_stripper = HTMLStripper()
        html_stripper.feed(msg)
        return html_stripper.get_data()
