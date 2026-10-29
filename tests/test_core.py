import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout

from config_diff.cli import main
from config_diff.core import diff, flatten, load_config, render_markdown, render_text, tomllib

OLD = {"model": {"layers": [64, 32], "dropout": 0.1, "act": "relu"}, "seed": 1, "lr": 0.001, "paths": {"out": "/a"}}
NEW = {"model": {"layers": [64, 32, 16], "dropout": 0.1000000001, "act": "gelu"}, "seed": "1", "lr": 0.001,
       "paths": {"out": "/b"}, "epochs": 10}


class DiffTests(unittest.TestCase):
    def test_flatten(self):
        self.assertEqual(flatten({"a": {"b": [1, {"c": 2}], "e": {}}}), {"a.b[0]": 1, "a.b[1].c": 2, "a.e": {}})

    def test_kinds(self):
        d = {(k, p) for k, p, _, _ in diff(OLD, NEW)}
        self.assertIn(("added", "model.layers[2]"), d)
        self.assertIn(("added", "epochs"), d)
        self.assertIn(("changed", "model.act"), d)
        self.assertIn(("type", "seed"), d)
        self.assertIn(("changed", "model.dropout"), d)

    def test_tolerance_and_ignore(self):
        d = {p for _, p, _, _ in diff(OLD, NEW, ignore=["paths.*"], rel_tol=1e-6)}
        self.assertNotIn("model.dropout", d)
        self.assertNotIn("paths.out", d)
        self.assertEqual(diff({"a": 1}, {"a": 1.0}), [])
        self.assertEqual(diff({"a": True}, {"a": 1})[0][0], "type")

    def test_renderers(self):
        changes = diff({"a": 1, "b": 2}, {"a": 3, "c": 4})
        self.assertEqual(render_text(changes).splitlines(), ["~ a: 1 -> 3", "- b = 2", "+ c = 4"])
        self.assertIn("| `a` | 1 | 3 | changed |", render_markdown(changes))

    def test_ini_coercion_and_cross_format(self):
        with tempfile.TemporaryDirectory() as d:
            ini, js = os.path.join(d, "a.ini"), os.path.join(d, "b.json")
            with open(ini, "w", encoding="utf-8") as fh:
                fh.write("[train]\nlr = 0.01\nepochs = 5\nshuffle = yes\nname = run1\n")
            with open(js, "w", encoding="utf-8") as fh:
                json.dump({"train": {"lr": 0.01, "epochs": 5, "shuffle": True, "name": "run2"}}, fh)
            self.assertEqual(load_config(ini)["train"], {"lr": 0.01, "epochs": 5, "shuffle": True, "name": "run1"})
            with redirect_stdout(io.StringIO()) as buf:
                self.assertEqual(main([ini, js]), 1)
            self.assertEqual(buf.getvalue().strip(), "~ train.name: 'run1' -> 'run2'")
            with self.assertRaises(ValueError):
                load_config(os.path.join(d, "x.yaml"))

    @unittest.skipIf(tomllib is None, "tomllib needs Python 3.11+")
    def test_toml(self):
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "c.toml")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write("[model]\nlayers = [1, 2]\n")
            self.assertEqual(load_config(p), {"model": {"layers": [1, 2]}})


if __name__ == "__main__":
    unittest.main()
