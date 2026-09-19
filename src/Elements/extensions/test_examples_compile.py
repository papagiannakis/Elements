"""
Unit test
Employing the unittest standard python test framework
https://docs.python.org/3/library/unittest.html

Syntax-only smoke test for every example in examples/E.Extended -- the extended examples that
exercise the extensions in this package.

The examples can't simply be imported or run here: each one builds a Scene, calls scene.init()
(which needs a real OpenGL context and opens a window) and then blocks in its own render loop
until the user closes it. So this test compiles them instead -- the same check the interpreter
does when it first loads a module, minus the executing.

What that catches, cheaply and headlessly: syntax errors, stray/unbalanced brackets, bad
indentation, and Python-version-incompatible constructs left behind by an edit. What it does
*not* catch: anything that only fails at run time, most notably a name that no longer exists
(a moved asset path, a constant dropped from an import line) -- compiling never resolves names.

@Copyright 2021-2022 Dr. George Papagiannakis
"""

import py_compile
import tempfile
import unittest
from pathlib import Path

#: Repo root is four levels up: extensions -> Elements -> src -> <repo>.
#: Only present in a source checkout; a pip-installed Elements ships no examples/ folder.
EXAMPLES_DIR = Path(__file__).resolve().parents[3] / "examples" / "E.Extended"


class TestExtendedExamplesCompile(unittest.TestCase):

    def setUp(self):
        if not EXAMPLES_DIR.is_dir():
            self.skipTest(
                "examples/E.Extended not found at {} -- expected when running against an "
                "installed Elements rather than a source checkout".format(EXAMPLES_DIR)
            )
        self.examples = sorted(EXAMPLES_DIR.glob("*.py"))

    def test_examples_are_discovered(self):
        """Guard against the glob silently matching nothing (moved/renamed folder), which would
        otherwise make test_examples_compile below pass by doing zero work."""
        print("\nTestExtendedExamplesCompile:test_examples_are_discovered() START")

        self.assertTrue(self.examples, "No .py files found in {}".format(EXAMPLES_DIR))

        print("Found {} examples in {}".format(len(self.examples), EXAMPLES_DIR))
        print("TestExtendedExamplesCompile:test_examples_are_discovered() END")

    def test_examples_compile(self):
        """Compile each example on its own, so a failure names the offending file instead of
        stopping the whole sweep at the first one."""
        print("\nTestExtendedExamplesCompile:test_examples_compile() START")

        # The bytecode goes into a temp dir, so running the test doesn't litter __pycache__
        # entries next to the examples themselves.
        with tempfile.TemporaryDirectory() as bytecode_dir:
            for example in self.examples:
                with self.subTest(example=example.name):
                    py_compile.compile(
                        str(example),
                        cfile=str(Path(bytecode_dir) / (example.stem + ".pyc")),
                        doraise=True,
                    )

        print("All {} examples compiled".format(len(self.examples)))
        print("TestExtendedExamplesCompile:test_examples_compile() END")


if __name__ == "__main__":
    unittest.main(argv=[''], verbosity=3, exit=False)
