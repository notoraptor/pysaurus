import os


class Pysaurus(object):
    def __init__(self, browser):
        self.browser = browser
        self.folder_path = os.path.expanduser("~")
        self.folder_content = []
        self.folder_pages = []
        self.page_size = 100

    def is_valid_folder_path(self, folder, js_callback):
        js_callback.Call(os.path.isdir(folder))

    def open_folder(self, folder, js_callback):
        if folder:
            folder = os.path.abspath(folder)
            if not os.path.isdir(folder):
                js_callback.Call({'error': "Chemin de dossier invalide: %s" % folder})
                return
            self.folder_path = folder
            self.folder_content.clear()
        if not self.folder_content:
            for path in os.listdir(self.folder_path):
                self.folder_content.append((path, os.path.isdir(os.path.join(self.folder_path, path))))
            self.folder_content.sort(key=lambda val: (-val[1], val[0]))
            self.folder_pages.clear()
            index_page = 0
            while index_page < len(self.folder_content):
                self.folder_pages.append(self.folder_content[index_page:(index_page + self.page_size)])
                index_page += self.page_size
        js_callback.Call({
            'nbPages': len(self.folder_pages),
            'idPage': 0,
            'contentPage': self.folder_pages[0] if self.folder_pages else None,
            'folder': self.folder_path
        })