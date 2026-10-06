"""Harvest (010_harvest): paging, reruns that keep what's on disk, and the
checks, against a stand-in for data.nasa.gov's CKAN API."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import requests

from stand_ins import StandInCatalog
from support import use_step

use_step("010_harvest")
import batches                                    # noqa: E402
import ckan_client                                # noqa: E402
import moves                                      # noqa: E402


class Harvest(unittest.TestCase):

    def setUp(self):
        self.cat = StandInCatalog(count=25).__enter__()
        self.real_url, ckan_client.URL = ckan_client.URL, self.cat.url
        self.out = Path(tempfile.mkdtemp())

    def tearDown(self):
        ckan_client.URL = self.real_url
        self.cat.__exit__()
        shutil.rmtree(self.out)

    def harvest(self, page_size=10, max_records=0):
        h = moves.download_catalog({"page_size": page_size, "max_records": max_records, "pause_seconds": 0}, self.out)
        return h, moves.check_complete(h)

    def names(self):
        return [p.name for p in batches.all_batches(self.out)]

    def test_whole_catalog(self):
        h, c = self.harvest()
        self.assertEqual(self.names(), ["batch_00000.json", "batch_00010.json", "batch_00020.json"])
        self.assertEqual((h.reported, h.target, h.new, h.reused), (25, 25, 3, 0))
        self.assertEqual((c.records, c.missing_ids, c.duplicate_ids, c.unique_ids), (25, 1, 1, 23))
        self.assertEqual(c.catalog_sizes, {25})
        self.assertEqual(self.cat.requests, [0, 10, 20])
        b = batches.load_batch(self.out / "batch_00010.json")
        self.assertTrue(ckan_client.same_page(b["request"], 10, 10))
        self.assertEqual(b["catalog_count"], 25)
        self.assertEqual([r.get("id") for r in b["records"]][:2], ["rec-0010", "rec-0011"])
        r = moves.results(h, c)
        self.assertEqual(r.headline, {"records harvested": 25})
        self.assertTrue(any("appears twice" in w for w in r.warnings))
        self.assertTrue(any("has no id" in w for w in r.warnings))

    def test_rerun_keeps_pages(self):
        self.harvest()
        self.cat.requests.clear()
        h, _ = self.harvest()
        self.assertEqual((h.new, h.reused, h.replaced), (0, 3, 0))
        self.assertEqual(self.cat.requests, [0])          # only the first page, for the catalog size

    def test_interrupted_run_resumes(self):
        self.cat.fail_starts = {20}
        with self.assertRaises(requests.HTTPError):
            self.harvest()
        self.assertEqual(self.names(), ["batch_00000.json", "batch_00010.json"])
        self.cat.fail_starts = set()
        h, c = self.harvest()
        self.assertEqual((h.new, h.reused, c.records), (1, 2, 25))

    def test_busy_page_retried(self):
        self.cat.busy_once = {10}
        _, c = self.harvest()
        self.assertEqual(c.records, 25)
        self.assertEqual(self.cat.requests.count(10), 2)

    def test_not_json(self):
        self.cat.not_json_starts = {10}
        with self.assertRaisesRegex(RuntimeError, "isn't JSON"):
            self.harvest()

    def test_other_page_size_replaces(self):
        self.harvest()
        h, c = self.harvest(page_size=20)
        self.assertEqual(self.names(), ["batch_00000.json", "batch_00020.json"])
        self.assertEqual((h.replaced, h.removed, c.records), (2, ["batch_00010.json"], 25))

    def test_trial_then_whole(self):
        h, c = self.harvest(max_records=12)
        self.assertEqual((h.target, c.records), (12, 12))
        self.assertEqual(len(batches.load_batch(self.out / "batch_00010.json")["records"]), 2)
        h, c = self.harvest()
        self.assertEqual((h.reused, h.replaced, c.records), (1, 1, 25))

    def test_smaller_trial_removes_extra(self):
        self.harvest()
        h, c = self.harvest(max_records=10)
        self.assertEqual(self.names(), ["batch_00000.json"])
        self.assertEqual(sorted(h.removed), ["batch_00010.json", "batch_00020.json"])

    def test_catalog_grew(self):
        self.harvest(max_records=10)
        self.cat.count = 30
        h, c = self.harvest()
        self.assertEqual(c.catalog_sizes, {25, 30})
        self.assertTrue(any("size changed" in w for w in moves.results(h, c).warnings))

    def test_ran_dry(self):
        self.cat.count = 25
        real = ckan_client.fetch_page

        def shrunk(session, start, rows):                 # the catalog shrinks after the first page
            result, request = real(session, start, rows)
            if start:
                result = {**result, "results": []}
            return result, request
        ckan_client.fetch_page = shrunk
        try:
            h, c = self.harvest()
        finally:
            ckan_client.fetch_page = real
        self.assertTrue(h.ran_dry)
        self.assertEqual(c.records, 10)
        self.assertTrue(any("empty page" in w for w in moves.results(h, c).warnings))

    def test_leftover_part_removed(self):
        (self.out / "batch_00000.json.part").write_text("{")
        self.harvest()
        self.assertEqual(batches.leftover_parts(self.out), [])

    def test_bad_setting(self):
        with self.assertRaises(ValueError):
            moves.download_catalog({"page_size": 0, "max_records": 0, "pause_seconds": 0}, self.out)


class SamePage(unittest.TestCase):

    def test_same_page(self):
        line = "GET http://x/package_search?rows=10&start=20&sort=metadata_created+asc%2C+id+asc"
        self.assertTrue(ckan_client.same_page(line, 20, 10))
        self.assertFalse(ckan_client.same_page(line, 20, 20))
        self.assertFalse(ckan_client.same_page(line.replace("asc%2C", "desc%2C"), 20, 10))
        self.assertFalse(ckan_client.same_page(None, 20, 10))

    def test_old_format(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "batch_00000.json").write_text(json.dumps([{"id": "a"}]))
            self.assertEqual(batches.load_batch(tmp / "batch_00000.json"), {"records": [{"id": "a"}]})
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
