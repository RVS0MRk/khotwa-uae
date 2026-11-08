"""Score parity, assets, and a narrow guard for the one untouched HTML sink."""

import json
from pathlib import Path
import random
import re
import shutil
import subprocess
import unittest
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

from test_support import configure_mock_environment

configure_mock_environment()
import app
from scoring import DIMENSIONS, normalize_scores

ROOT = Path(__file__).parent


class EngineeringTests(unittest.TestCase):
    def test_rich_founder_pdf_keeps_all_chart_images(self):
        from test_v22_content import normalized
        from pypdf import PdfReader
        import founder_pdf

        for lang in ("en", "ar"):
            plan = normalized("rich_plan_" + lang, lang)
            with patch.object(founder_pdf.logger, "error") as errors:
                response = app.app.test_client().post("/pdf", json=dict(plan, _lang=lang))
            self.assertEqual(response.status_code, 200)
            errors.assert_not_called()
            reader = PdfReader(io.BytesIO(response.data))
            images = sum(len(page.images) for page in reader.pages)
            self.assertGreaterEqual(images, 3, "Score, timeline and cost chart must be present")
            response.close()

    def test_owner_live_smoke_is_opt_in_and_bounded_with_mock_provider(self):
        from scripts import live_smoke
        from groq_client import GroqCompletion

        with patch("sys.argv", ["live_smoke.py"]), patch.dict("os.environ", {"GROQ_API_KEY": ""}), redirect_stderr(
            io.StringIO()
        ), self.assertRaises(SystemExit) as stopped:
            live_smoke.main()
        self.assertEqual(stopped.exception.code, 2)
        fixtures = [
            json.loads((ROOT / "tests/fixtures" / name).read_text(encoding="utf-8"))
            for name in ("rich_plan_en.json", "rich_plan_ar.json")
        ]
        with patch("sys.argv", ["live_smoke.py", "--confirm-live"]), patch.dict(
            "os.environ", {"GROQ_API_KEY": "mock-only-value"}
        ), patch(
            "groq_client.request_completion",
            side_effect=[GroqCompletion(json.dumps(f), {"completion_tokens": 4000}) for f in fixtures],
        ) as transport, redirect_stdout(
            io.StringIO()
        ) as output:
            self.assertEqual(live_smoke.main(), 0)
        self.assertEqual(transport.call_count, 2)
        self.assertEqual(len(output.getvalue().splitlines()), 2)
        self.assertNotIn("mock-only-value", output.getvalue())
        for line in output.getvalue().splitlines():
            self.assertGreater(json.loads(line)["retention_ratio"], 0.75)

    def test_python_javascript_score_parity_200_objects(self):
        node = shutil.which("node")
        self.assertIsNotNone(node, "Node is required for the score parity contract")
        rng = random.Random(220021)
        scores = []
        for _ in range(200):
            scores.append(
                {
                    key: {
                        "score": rng.choice([None, -1, 0, 1, 3, 5, 6, 2.5, True, "3"]),
                        "reason": rng.choice(
                            [
                                "Specific founder and customer context.",
                                "one line",
                                "",
                                "Not assessed because information is missing.",
                            ]
                        ),
                        "source": rng.choice(["ai_assumption", "fallback", "missing"]),
                    }
                    for key in DIMENSIONS
                }
            )
        script = (ROOT / "static/scoring.js").read_text(encoding="utf-8")
        script += '\nconst fs=require("node:fs");console.log(JSON.stringify(JSON.parse(fs.readFileSync(0,"utf8")).map(aggregateScores)));'
        result = subprocess.run(
            [node, "-e", script], input=json.dumps(scores), text=True, capture_output=True, check=True
        )
        js = json.loads(result.stdout)
        for index, (raw, actual) in enumerate(zip(scores, js)):
            expected = normalize_scores(raw)
            for key in ("total", "assessed_sum", "assessed_count", "status", "maximum"):
                self.assertEqual(actual[key], expected[key], (index, key))

    def test_static_digits_fonts_and_immutable_cache(self):
        paths = list((ROOT / "static").glob("*.js")) + list((ROOT / "templates").rglob("*.html"))
        paths += list((ROOT / "static").glob("*.json")) + list((ROOT / "static").glob("*.css"))
        for path in paths:
            self.assertIsNone(re.search(r"[\u0660-\u0669\u06f0-\u06f9]", path.read_text(encoding="utf-8")), path.name)
        for name in ("inter-latin.woff2", "arabic.woff2"):
            self.assertLess((ROOT / "static/fonts" / name).stat().st_size, 60000)
            version = app.asset_version("fonts/" + name)
            response = app.app.test_client().get("/static/fonts/" + name + "?v=" + version)
            self.assertEqual(response.status_code, 200)
            self.assertIn("immutable", response.headers["Cache-Control"])
            response.close()
        self.assertTrue((ROOT / "fonts/Amiri-Regular.ttf").is_file())
        html = app.app.test_client().get("/").text
        self.assertNotRegex(html, r'<script[^>]+src="[^"]*chart\.umd')

    def test_only_untouched_escaped_plan_persona_html_sink_remains(self):
        sinks = []
        for path in (ROOT / "static").glob("*.js"):
            if path.name in ("chart.umd.min.js", "qrcode.min.js"):
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if re.search(r"\.innerHTML\s*(?:\+?=)", line):
                    sinks.append((path.name, line))
        self.assertEqual(len(sinks), 1, sinks)
        self.assertEqual(sinks[0][0], "app.js")
        source = (ROOT / "static/app.js").read_text(encoding="utf-8")
        self.assertRegex(source, r"p\s*=\s*escapePlan\(rawPlan\)")
        self.assertIn("(p.customer_personas || []).slice(0, 3).forEach(function (per)", source)
        # Persona aliases come only from p (the recursive escaped plan); all
        # remaining expressions are fixed translations or language literals.
        sink = source[source.index("pg.innerHTML") : source.index("// Risk radar")]
        expressions = re.findall(r"\$\{([^{}]+)\}", sink)
        for expression in expressions:
            self.assertRegex(expression, r"^(?:per\.|t\.|lang ===)")

    def test_funding_references_and_eligibility_are_explicit(self):
        entries = json.loads((ROOT / "static/funding.json").read_text(encoding="utf-8"))
        if isinstance(entries, dict):
            entries = entries["programs"]
        self.assertEqual(len(entries), 8)
        for entry in entries:
            for key in ("eligibility_tags", "emirates", "stages", "dated_sources"):
                self.assertTrue(entry[key], (entry.get("id"), key))
            for reference in entry["dated_sources"]:
                self.assertTrue(reference["url"].startswith("https://"))
                self.assertRegex(reference["checked"], r"^2026-11-0[78]$")
        ru = next(e for e in entries if e["id"] == "ruwad")
        self.assertEqual(ru["status"], "dated_official")
