"""Plan-aware search retaining source text for passage retrieval."""

from concurrent.futures import ThreadPoolExecutor

from agents.plan_schema import ResearchPlan
from tools.web_search import scrape_page, search_web


def _search_queries(query: str, plan: ResearchPlan | None) -> list[str]:
    queries = [query] + (plan.key_questions[:3] if plan else [])
    seen: set[str] = set()
    unique = []
    for q in queries:
        normalized = q.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(q.strip())
    return unique[:4]


def search_agent(query: str, plan: ResearchPlan | None = None) -> dict:
    queries = _search_queries(query, plan)[:2]
    hits = []
    seen = set()
    warnings = []
    for search_query in queries:
        for hit in search_web(search_query, max_results=4):
            url = hit.get("href", "")
            if not url:
                warnings.append("Web search was unavailable for a query.")
                continue
            if url in seen:
                continue
            seen.add(url)
            hits.append((hit, search_query))
    hits = hits[:6]
    with ThreadPoolExecutor(max_workers=4) as pool:
        pages = list(pool.map(lambda pair: scrape_page(pair[0]["href"]), hits))
    results = []
    for (hit, search_query), page in zip(hits, pages, strict=True):
        text = page or hit.get("body", "")
        if not text:
            continue
        results.append(
            {
                "url": hit["href"],
                "title": hit.get("title") or hit["href"],
                "search_query": search_query,
                "snippet": text[:500],
                "text": text,
                "status": "page" if page else "snippet",
            }
        )
        if not page:
            warnings.append(f"Only a search snippet was available for {hit['href']}.")
    return {
        "query": query,
        "search_queries": queries,
        "web_results": results,
        "raw_content": "\n\n".join(f"[{r['title']}] ({r['url']})\n{r['text']}" for r in results),
        "warnings": list(dict.fromkeys(warnings)),
    }
