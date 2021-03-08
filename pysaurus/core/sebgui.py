"""
SErver Based Graphical User Interface
"""
import sys
import tempfile
import urllib.parse
import os
from cefpython3 import cefpython as cef


def _html_to_url(html):
    url = f"data:text/html;charset=UTF-8,{urllib.parse.quote(html)}"
    if len(url) < 2 * 1024 * 1024:
        return url
    # Url is too long, we should better save it in a file.
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.html') as tf:
        tf.write(html)
        return file_path_to_url_path(tf.name)


def file_path_to_url_path(path):
    entry_path = os.path.normpath(path).replace("\\", "/")
    return f"file:///{entry_path}"


class _RequestHandler:
    __slots__ = ("interface",)

    def __init__(self, interface):
        self.interface = interface

    def OnBeforeResourceLoad(self, browser, frame, request):
        url = request.GetUrl()  # type: str
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme == "app":
            page = parsed.netloc
            method = request.GetMethod()
            if method == "POST":
                post = request.GetPostData()
                print(url, 'SIZE', len(post))
                parameters = {
                    k.decode(): v.decode() for k, v in post.items()
                }
            else:
                parameters = {
                    k: v[0] if len(v) == 1 else v
                    for k, v in urllib.parse.parse_qs(parsed.query).items()
                }
            callback = getattr(self.interface, page, None)
            if callable(callback):
                print("Page", page, "with", method, "arguments:", *list(parameters))
                frame.LoadUrl(_html_to_url(callback(**parameters)))
            else:
                print("Unknown", url)
            return True
        return False


class _CEF:
    __slots__ = "settings", "switches"

    def __init__(self, settings=None, switches=None):
        self.settings = settings
        self.switches = switches

    def __enter__(self):
        cef.Initialize(settings=self.settings, switches=self.switches)

    def __exit__(self, exc_type, exc_val, exc_tb):
        cef.Shutdown()


class SebGUI:
    def __init__(self, title, interface):
        self.title = title
        self.interface = interface

    def run(self):
        # Shutdown all CEF processes on error
        sys.excepthook = cef.ExceptHook
        # Browser settings
        settings = {
            "debug": False,
            "log_severity": cef.LOGSEVERITY_INFO,
            # "log_file": "debug.log",
            "remote_debugging_port": 4000,
            "cache_path": tempfile.gettempdir(),
        }
        # Browser switches
        switches = {
            # prevent local CORS exceptions.
            "disable-web-security": ""
        }
        # run CEF instance
        with _CEF(settings=settings, switches=switches):
            browser = cef.CreateBrowserSync(
                url=_html_to_url(self.interface.index()), window_title=self.title
            )
            # Set Javascript bindings.
            handler = _RequestHandler(self.interface)
            browser.SetClientHandler(handler)
            # Load server.
            cef.MessageLoop()


class HTML:
    def __init__(self, *, stylesheets=(), scripts=(), css="", javascript=""):
        self.stylesheets = stylesheets
        self.scripts = scripts
        self.css = css
        self.javascript = javascript

    def __call__(self, body):
        code_stylesheets = "".join(
            f'<link rel="stylesheet" href="{stylesheet}"/>'
            for stylesheet in self.stylesheets
        )
        code_scripts = "".join(
            f'<script src="{script}"></script>' for script in self.scripts
        )
        code_css = f'<style type="text/css">{self.css}</style>' if self.css else ""
        code_javascript = (
            f'<script type="text/javascript">{self.javascript}</script>'
            if self.javascript
            else ""
        )
        return f"""
<html>
    <head>
        <meta charset="utf-8">
        {code_stylesheets}
        {code_css}
        {code_javascript}
    </head>
    <body>
        {body}
        {code_scripts}
    </body>
</html>
"""


def seb_gui(title, interface):
    return SebGUI(title, interface).run()
