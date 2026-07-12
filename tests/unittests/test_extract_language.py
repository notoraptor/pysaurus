from pysaurus.core.dict_file_format import dff_dump, dff_load
from pysaurus.core.language import key_of
from pysaurus.scripts.extract_language import (
    extract_texts,
    merge_catalog,
    run,
    validate_placeholders,
)


class TestExtractTexts:
    def test_literal(self):
        source = (
            "from pysaurus.core.language import say\n"
            "x = say('Hello')\n"
            'y = say("Error {name}", name=exc)\n'
        )
        texts, violations = extract_texts(source)
        assert not violations
        assert texts == {
            key_of("Hello"): "Hello",
            key_of("Error {name}"): "Error {name}",
        }

    def test_adjacent_literals_are_folded(self):
        texts, violations = extract_texts("say('Hello ' 'world')\n")
        assert not violations
        assert texts == {key_of("Hello world"): "Hello world"}

    def test_fstring_is_violation(self):
        texts, violations = extract_texts("say(f'Hello {x}')\n", "module.py")
        assert not texts
        assert len(violations) == 1
        assert violations[0].path == "module.py"
        assert "string literal" in violations[0].reason

    def test_variable_is_violation(self):
        texts, violations = extract_texts("say(message)\n")
        assert not texts
        assert len(violations) == 1

    def test_no_args_is_violation(self):
        texts, violations = extract_texts("say()\n")
        assert not texts
        assert len(violations) == 1

    def test_methods_named_say_are_ignored(self):
        texts, violations = extract_texts("obj.say('Hello')\n")
        assert not texts
        assert not violations

    def test_trailing_whitespace_is_violation(self):
        texts, violations = extract_texts("say('Hello ')\nsay('World\\n')\n")
        assert not texts
        assert len(violations) == 2
        assert all("whitespace" in v.reason for v in violations)

    def test_aliased_import_is_violation(self):
        source = "from pysaurus.core.language import say as tr\ntr('Hello')\n"
        texts, violations = extract_texts(source)
        assert not texts
        assert len(violations) == 1
        assert "alias" in violations[0].reason

    def test_module_attribute_call_is_violation(self):
        source = "from pysaurus.core import language\nlanguage.say('Hello')\n"
        texts, violations = extract_texts(source)
        assert not texts
        assert len(violations) == 1
        assert "language.say" in violations[0].reason


class TestMergeCatalog:
    def test_merge(self):
        english = {"A": "Alpha", "B": "Beta"}
        existing = {"A": "Alphe", "C": "Gamma trad"}
        merged, orphans = merge_catalog(english, existing)
        assert merged == {"A": "Alphe", "B": "Beta"}
        assert orphans == {"C": "Gamma trad"}


class TestValidatePlaceholders:
    def test_ok(self):
        english = {"K": "Error {name}: {message}"}
        merged = {"K": "Erreur {name} : {message}"}
        assert validate_placeholders(english, merged, "fr") == []

    def test_untranslated_ignored(self):
        english = {"K": "Error {name}"}
        merged = {"K": "Error {name}"}
        assert validate_placeholders(english, merged, "fr") == []

    def test_mismatch(self):
        english = {"K": "Error {name}"}
        merged = {"K": "Erreur {nom}"}
        errors = validate_placeholders(english, merged, "fr")
        assert len(errors) == 1
        assert "placeholders differ" in errors[0]

    def test_subscript_or_attribute_is_mismatch(self):
        """{name[0]} and {name.x} are NOT equivalent to {name}."""
        english = {"K": "Error {name}", "L": "Hi {name}"}
        merged = {"K": "Erreur {name[0]}", "L": "Salut {name.x}"}
        errors = validate_placeholders(english, merged, "fr")
        assert len(errors) == 2
        assert all("placeholders differ" in error for error in errors)

    def test_malformed(self):
        english = {"K": "Error {name}"}
        merged = {"K": "Erreur {name"}
        errors = validate_placeholders(english, merged, "fr")
        assert len(errors) == 1
        assert "malformed" in errors[0]


class TestRun:
    def test_end_to_end(self, tmp_path, capsys):
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "module.py").write_text(
            "say('Hello')\nsay('Error {name}', name='x')\n", encoding="utf-8"
        )
        languages = tmp_path / "languages"
        languages.mkdir()
        # Existing French file: one live key (translated), one orphan.
        dff_dump({key_of("Hello"): "Bonjour", "Old_1": "Vieux"}, languages / "fr.txt")

        assert run(str(package), str(languages)) == 0
        assert "i18n: OK" in capsys.readouterr().out

        english = dff_load(languages / "en.txt")
        assert english == {
            key_of("Hello"): "Hello",
            key_of("Error {name}"): "Error {name}",
        }
        french = dff_load(languages / "fr.txt")
        assert french == {
            key_of("Hello"): "Bonjour",
            key_of("Error {name}"): "Error {name}",
        }
        obsolete = dff_load(languages / "fr.obsolete.txt")
        assert obsolete == {"Old_1": "Vieux"}

    def test_idempotent(self, tmp_path):
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "module.py").write_text("say('Hello')\n", encoding="utf-8")
        languages = tmp_path / "languages"

        assert run(str(package), str(languages)) == 0
        first = (languages / "en.txt").read_bytes()
        mtime = (languages / "en.txt").stat().st_mtime_ns
        assert run(str(package), str(languages)) == 0
        assert (languages / "en.txt").read_bytes() == first
        # Unchanged content must not be rewritten (mtime untouched).
        assert (languages / "en.txt").stat().st_mtime_ns == mtime

    def test_reports_violations(self, tmp_path, capsys):
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "module.py").write_text("say(f'Hello {x}')\n", encoding="utf-8")
        assert run(str(package), str(tmp_path / "languages")) == 1
        err = capsys.readouterr().err
        assert "string literal" in err
        assert "i18n: FAILED (1 violation(s))" in err

    def test_reports_placeholder_errors(self, tmp_path, capsys):
        package = tmp_path / "pkg"
        package.mkdir()
        (package / "module.py").write_text("say('Error {name}')\n", encoding="utf-8")
        languages = tmp_path / "languages"
        languages.mkdir()
        dff_dump({key_of("Error {name}"): "Erreur {nom}"}, languages / "fr.txt")
        assert run(str(package), str(languages)) == 1
        err = capsys.readouterr().err
        assert "placeholders differ" in err
        assert "i18n: FAILED (1 placeholder error(s))" in err
