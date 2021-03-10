from pysaurus.scripts.sebgui import HTML, seb_gui


class Interface:
    def __init__(self):
        self._gen = HTML()
        self.size = 1000

    def index(self):
        fields = "".join(
            f'<div><input type="radio" name="input{i}" value="{i}-0"/><input type="radio" name="input{i}" value="{i}-1" checked/></div>'
            for i in range(self.size)
        )
        return self._gen(
            f"""
        <form onsubmit="return python_submit(this, 'form')">
        <div><input type="submit" value="send"/></div>
        {fields}
        </form>
        """
        )

    def form(self, kwargs):
        assert len(kwargs) == self.size, (len(kwargs), self.size)
        return "ok"


def main():
    seb_gui("App", Interface())


if __name__ == "__main__":
    main()
