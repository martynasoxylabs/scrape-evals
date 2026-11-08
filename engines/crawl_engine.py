"""scrape-evals engine adapter: Hermes /crawl (scripts/ensemble.crawl).

Maps the /crawl result contract onto scrape-evals' ScrapeResult:
  text (markdown) -> content, format="markdown"
  status_code     -> status_code (200 inferred when text was obtained but the
                     ensemble did not propagate a status; 500 when the engine
                     produced nothing, matching the harness' own convention)
  completeness/failure_class -> error string when no text was obtained
title/links are not part of the ScrapeResult schema and are not scored.

If CRAWL_EVAL_DIAG is set, a sidecar JSONL records the raw ensemble fields
per URL for post-hoc failure attribution (the harness schema cannot carry them).
"""
import concurrent.futures
import json
import os
import sys
import threading
from datetime import datetime

from .base import Scraper, ScrapeResult

# Point CRAWL_REPO at a checkout of the crawler repo
# (github.com/structurebased/crawl, currently private). No default: the
# adapter refuses to guess a personal path.
CRAWL_REPO = os.environ.get("CRAWL_REPO") or ""
# Bounded worker pool: wait_for can abandon a stuck crawl() thread, so cap how
# many stragglers one run can accumulate.
_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="crawl-eval")
_DIAG_LOCK = threading.Lock()


class HermesCrawlScraper(Scraper):
    def __init__(self):
        if CRAWL_REPO not in sys.path:
            sys.path.insert(0, CRAWL_REPO)
        # Eval hygiene: disable the shared on-disk result + capability caches so
        # concurrent workers cannot poison each other or read box-local state.
        os.environ["CRAWL_ENSEMBLE_CACHE"] = "0"
        os.environ["CRAWL_CAP_CACHE"] = "0"
        from scripts.ensemble import crawl
        self._crawl = crawl

    def _diag(self, url: str, res: dict, content, status) -> None:
        path = os.environ.get("CRAWL_EVAL_DIAG")
        if not path:
            return
        comp = res.get("completeness") or {}
        row = {
            "url": url,
            "status_code": status,
            "failure_class": res.get("failure_class"),
            "engine_error": res.get("error"),
            "level": comp.get("level"),
            "blocked_by": comp.get("blocked_by"),
            "known_missing": comp.get("known_missing"),
            "ensemble_used": res.get("ensemble_used"),
            "ensemble_skipped": res.get("ensemble_skipped"),
            "text_source": res.get("text_source"),
            "page_type": res.get("page_type"),
            "elapsed_s": res.get("elapsed_s"),
            "text_len": len(content or ""),
            "raw_html_len": len(res.get("raw_html") or ""),
            "pointer": bool(res.get("pointer")),
        }
        with _DIAG_LOCK:
            with open(path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    async def scrape(self, url: str, run_id: str) -> ScrapeResult:
        import asyncio
        now = datetime.now().isoformat
        timeout_s = float(os.environ.get("CRAWL_ADAPTER_TIMEOUT_S", "75"))
        try:
            res = await asyncio.wait_for(
                asyncio.get_running_loop().run_in_executor(_EXECUTOR, self._crawl, url),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            # /crawl's own contract deadline is 45s; if crawl() ignores it the
            # benchmark must not hang. Abandoned thread dies with the process.
            return ScrapeResult(
                run_id=run_id, scraper="crawl_engine", url=url,
                status_code=408,
                error=f"adapter_timeout: ensemble did not return within {timeout_s}s (contract deadline 45s)",
                content_size=0, format="markdown", created_at=now(), content=None,
            )
        except Exception as e:  # engine crash = engine failure, not a crash
            return ScrapeResult(
                run_id=run_id, scraper="crawl_engine", url=url,
                status_code=500, error=f"{type(e).__name__}: {e}",
                content_size=0, format="markdown", created_at=now(), content=None,
            )

        if res.get("pointer"):
            # Pointer shape: the inline payload carries only a summary; the
            # engine's full result is on disk at pointer.out_dir. Read it
            # (the contract's own on-demand path), never re-crawl.
            try:
                from pathlib import Path
                d = Path(res["pointer"]["out_dir"])
                full = json.loads(
                    (d / res["pointer"].get("manifest", "result.json")).read_text(encoding="utf-8")
                )
                res.update({k: v for k, v in full.items() if v is not None})
                full_txt = d / "text_full.txt"
                if full_txt.exists():
                    res["text"] = full_txt.read_text(encoding="utf-8")
            except Exception as e:
                res.setdefault("error", f"pointer_read_failed: {type(e).__name__}: {e}")

        content = (res.get("text") or "").strip() or None
        status = res.get("status_code")
        if status is None and content:
            status = 200  # text obtained => the fetch succeeded; status was not propagated

        error = res.get("error")
        if not content and not error:
            comp = res.get("completeness") or {}
            fc = res.get("failure_class")
            missing = ";".join(comp.get("known_missing") or [])
            error = f"no_text: level={comp.get('level')}; failure_class={fc}; {missing}".rstrip("; ")
        if status is None:
            status = 500  # schema requires int; engine produced nothing

        self._diag(url, res, content, status)
        return ScrapeResult(
            run_id=run_id, scraper="crawl_engine", url=url,
            status_code=status, error=error,
            content_size=len(content.encode("utf-8")) if content else 0,
            format="markdown", created_at=now(), content=content,
        )
