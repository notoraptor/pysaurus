"""
SErver Based Graphical User Interface
"""
import urllib.parse
import sys
import tempfile
import os
from cefpython3 import cefpython as cef


def html_to_url(html):
    # url = f"data:text/html;charset=UTF-8,{urllib.parse.quote(html)}"
    # if len(url) < 2 * 1024 * 1024:
    #     return url
    # Url is too long, we should better save it in a file.
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".html") as tf:
        tf.write(html)
        path = convert_file_path_to_url(tf.name)
        print("To load", path)
        return path


class _PythonAPI:
    def __init__(self, browser, interface):
        self.browser = browser
        self.interface = interface

    def call(self, name, args):
        html = getattr(self.interface, name)(*args)
        self.browser.LoadUrl(html_to_url(html))


class _CEF:
    __slots__ = "settings", "switches"

    def __init__(self, settings=None, switches=None):
        self.settings = settings
        self.switches = switches

    def __enter__(self):
        cef.Initialize(settings=self.settings, switches=self.switches)

    def __exit__(self, exc_type, exc_val, exc_tb):
        cef.Shutdown()


class _SebGUI:
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
                url=html_to_url(self.interface.index()), window_title=self.title
            )
            # Set Javascript bindings.
            python_api = _PythonAPI(browser, self.interface)
            bindings = cef.JavascriptBindings()
            bindings.SetObject("python", python_api)
            browser.SetJavascriptBindings(bindings)
            # Load server.
            cef.MessageLoop()


def convert_file_path_to_url(path):
    entry_path = os.path.normpath(path).replace("\\", "/")
    return f"file:///{entry_path}"


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

        python_bindings = """
        function python_call(name, ...args) {
            python.call(name, args);
        }
        function python_submit(form, pageName) {
            const formData = new FormData(form);
            const data = {};
            for (let pair of formData.entries()) {
                data[pair[0]] = pair[1];
                console.log(`${pair[0]}: ${data[pair[1]]}`);
            }
            python_call(pageName, data);
            return false;
        }
        function webview_submit(form) {
            console.log('we submit');
            const formData = new FormData(form);
            const data = {};
            for (let pair of formData.entries()) {
                data[pair[0]] = pair[1];
            }
            pywebview.api.move(data);
            return false;
        }
        function b64toBlob(b64Data, contentType='', sliceSize=512) {
          const byteCharacters = atob(b64Data);
          const byteArrays = [];
        
          for (let offset = 0; offset < byteCharacters.length; offset += sliceSize) {
            const slice = byteCharacters.slice(offset, offset + sliceSize);
        
            const byteNumbers = new Array(slice.length);
            for (let i = 0; i < slice.length; i++) {
              byteNumbers[i] = slice.charCodeAt(i);
            }
        
            const byteArray = new Uint8Array(byteNumbers);
            byteArrays.push(byteArray);
          }
        
          const blob = new Blob(byteArrays, {type: contentType});
          return blob;
        }
        function webview_image(img, path) {
            console.log(`Loading ${path}`);
            pywebview.api.pywebview_load_image(path).
                then(b64Data => {
                    const blob = b64toBlob(b64Data);
                    const blobUrl = URL.createObjectURL(blob);
                    img.src = blobUrl;
                })
                catch(error => alert(error));
        }
        """

        return f"""
        <html>
            <head>
                <meta charset="utf-8">
                {code_stylesheets}
                {code_css}
                {code_javascript}
                <script type="text/javascript">{python_bindings}</script>
            </head>
            <body>
                {body}
                {code_scripts}
            </body>
        </html>
        """


def seb_gui(title, interface):
    return _SebGUI(title, interface).run()
