import pathlib
import re
from typing import Dict, List, Tuple

import pytest

ROBOTS_TXT = pathlib.Path(__file__).parent.parent / "static" / "robots.txt"

# Full user-agent strings as logged in production
GOOGLEBOT = "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
BINGBOT = "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm) Chrome/116.0.1938.76 Safari/537.36"
APPLEBOT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1.1 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)"
BROWSER = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"
SEO_BOTS = [
    "Mozilla/5.0 (compatible; SemrushBot/7~bl; +http://www.semrush.com/bot.html)",
    "Mozilla/5.0 (compatible; DotBot/1.2; +https://opensiteexplorer.org/dotbot; help@moz.com)",
    "Mozilla/5.0 (compatible; MJ12bot/v1.4.8; http://mj12bot.com/)",
    "Mozilla/5.0 (compatible; AhrefsBot/7.0; +http://ahrefs.com/robot/)",
]
AI_CRAWLERS = [
    "Mozilla/5.0 (compatible; ExaSearchBot/1.0; +https://crawler.exa.ai/)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; Amazonbot/0.1; +https://developer.amazon.com/support/amazonbot) Chrome/119.0.6045.214 Safari/537.36",
    "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko); compatible; GPTBot/1.2; +https://openai.com/gptbot",
    "LinkupBot/1.0 (LinkupBot for web indexing; https://linkup.so/bot; bot@linkup.so)",
]
SHARED_DISALLOWED = [
    "/_/account/favorites/1",
    "/account",
    "/account/login",
    "/admin",
    "/mytba",
    "/suggest/match/video",
]
PUBLIC_PAGES = ["/", "/team/254", "/team/254/2026", "/event/2026casj", "/events"]


class Robots:
    """
    Minimal RFC 9309 matcher. urllib.robotparser checks groups in file order,
    so `*` would shadow every named group; real crawlers pick their own group.
    """

    def __init__(self, text: str) -> None:
        self.groups: Dict[str, List[Tuple[bool, str]]] = {}
        agents: List[str] = []
        in_rules = False
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if ":" not in line:
                continue
            key, value = (part.strip() for part in line.split(":", 1))
            key = key.lower()
            if key == "user-agent":
                if in_rules:
                    agents, in_rules = [], False
                agents.append(value.lower())
                for agent in agents:
                    self.groups.setdefault(agent, [])
            elif key in ("allow", "disallow"):
                in_rules = True
                for agent in agents:
                    self.groups[agent].append((key == "allow", value))

    def can_fetch(self, user_agent: str, path: str) -> bool:
        ua = user_agent.lower()
        named = [a for a in self.groups if a != "*" and a in ua]
        rules = self.groups[max(named, key=len)] if named else self.groups["*"]
        best: Tuple[int, bool] = (-1, True)
        for allow, pattern in rules:
            if pattern and re.match(
                re.escape(pattern).replace(r"\*", ".*").replace(r"\$", "$"), path
            ):
                best = max(best, (len(pattern), allow))
        return best[1]


@pytest.fixture(scope="module")
def robots() -> Robots:
    return Robots(ROBOTS_TXT.read_text())


@pytest.mark.parametrize("agent", [GOOGLEBOT, BINGBOT, APPLEBOT, BROWSER])
def test_search_engines_crawl_everything_public(
    robots: Robots, agent: str
) -> None:
    for path in PUBLIC_PAGES + ["/match/2026casj_qm1"]:
        assert robots.can_fetch(agent, path), path
    for path in SHARED_DISALLOWED:
        assert not robots.can_fetch(agent, path), path


@pytest.mark.parametrize("agent", SEO_BOTS)
def test_seo_bots_blocked_everywhere(robots: Robots, agent: str) -> None:
    for path in PUBLIC_PAGES + ["/match/2026casj_qm1"]:
        assert not robots.can_fetch(agent, path), path


@pytest.mark.parametrize("agent", AI_CRAWLERS)
def test_ai_crawlers_skip_match_pages(robots: Robots, agent: str) -> None:
    assert not robots.can_fetch(agent, "/match/2026casj_qm1")
    for path in PUBLIC_PAGES:
        assert robots.can_fetch(agent, path), path
    for path in SHARED_DISALLOWED:
        assert not robots.can_fetch(agent, path), path


def test_every_group_repeats_shared_disallows() -> None:
    # A crawler only obeys its own group, so each group must carry the shared rules
    groups = re.split(r"\n\s*\n", ROBOTS_TXT.read_text().strip())
    rule_groups = [g for g in groups if "Disallow:" in g]
    shared = {
        line
        for line in rule_groups[0].splitlines()
        if line.startswith("Disallow:")
    }
    for group in rule_groups[1:]:
        rules = {line for line in group.splitlines() if line.startswith("Disallow:")}
        assert "Disallow: /" in rules or shared <= rules, group
