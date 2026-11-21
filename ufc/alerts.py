#!/usr/bin/env python3
"""Cageside alerts: follows a UFC card while it's on and sends the moments worth looking up for
(a fight starting, a knockdown, each result, the main card about to start) to an ntfy topic,
which the ntfy iPhone app shows on the lock screen. Standard library only.

    CAGESIDE_TOPIC=cageside-ufc-7rk2 python3 alerts.py

It reads ESPN's fight centre (the card, results, live stats) and UFC.com's fight-tracker feed
(walkouts, knockdowns and the result a little sooner), the same feeds as the Cageside page.
It stays quiet about anything already over when it starts, and stops once the card is finished.
"""
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone

TOPIC = os.environ.get("CAGESIDE_TOPIC", "cageside-ufc-7rk2")
STATE_FILE = os.environ.get("CAGESIDE_STATE", "cageside-alerts-state.json")
MAX_HOURS = float(os.environ.get("CAGESIDE_MAX_HOURS", "8"))
# Leave straight away when nothing is on and the first fight is further off than this.
LEAD_HOURS = float(os.environ.get("CAGESIDE_LEAD_HOURS", "2.5"))
APP = "https://is.gd/cagesideufc"
ESPN_SB = "https://site.api.espn.com/apis/site/v2/sports/mma/ufc/scoreboard"
ESPN_FC = "https://site.web.api.espn.com/apis/common/v3/sports/mma/ufc/fightcenter/{}?region=gb&lang=en"
UFC = "https://d29dxerjsp82wz.cloudfront.net/api/v3"
UFC_SEED = {"600061665": 1348}
UK = None
try:
    from zoneinfo import ZoneInfo
    UK = ZoneInfo("Europe/London")
except Exception:
    pass


def log(*a):
    print(datetime.now().strftime("%H:%M:%S"), *a, flush=True)


def get(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Cageside alerts)", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def notify(title, message, tags=(), priority=3):
    body = {"topic": TOPIC, "title": title, "message": message, "tags": list(tags), "priority": priority, "click": APP}
    req = urllib.request.Request("https://ntfy.sh/", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                log("sent:", title, "|", message, r.status)
                return True
        except Exception as e:
            log("ntfy failed", attempt, e)
            time.sleep(3 * (attempt + 1))
    return False  # tried again on the next pass


def norm(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9 ]+", " ", s).split()


def same(a, b):
    x, y = norm(a), norm(b)
    return bool(x) and bool(y) and x[-1] == y[-1]


def uk_time(ms):
    d = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
    if UK:
        d = d.astimezone(UK)
    return d.strftime("%-I:%M %p").lower()


def parse_iso(s):
    if not s:
        return 0
    s = str(s)
    if s.endswith("Z") and len(s) == 17:
        s = s[:-1] + ":00Z"
    try:
        return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp() * 1000)
    except ValueError:
        return 0


# ---------- ESPN fight centre ----------
def fighter(c):
    a = c.get("athlete") or {}
    st = {s.get("name"): s.get("displayValue") for s in c.get("stats") or []}
    return {"last": a.get("lastName") or a.get("displayName") or "", "name": a.get("displayName") or "",
            "rec": c.get("displayRecord") or "", "winner": bool(c.get("winner")), "order": c.get("order") or 9, "st": st}


def card(fc):
    fights = []
    for seg_key, seg in (fc.get("cards") or {}).items():
        for c in seg.get("competitions") or []:
            cs = sorted((fighter(x) for x in c.get("competitors") or []), key=lambda f: f["order"])
            if len(cs) < 2:
                continue
            s = c.get("status") or {}
            t = s.get("type") or {}
            res = s.get("result") or {}
            note = c.get("note") or ""
            fights.append({
                "id": str(c.get("id")), "match": c.get("matchNumber") or 99,
                "seg": (c.get("cardSegment") or {}).get("description") or ("Main Card" if seg_key == "main" else "Prelims"),
                "start": parse_iso(c.get("date")), "weight": (c.get("type") or {}).get("text") or "",
                "main": "main event" in note.lower(), "title": "title" in note.lower() or "championship" in note.lower(),
                "state": t.get("state") or "pre", "period": int(s.get("period") or 0), "clock": s.get("displayClock"),
                "method": res.get("displayName") or "", "how": res.get("displayDescription") or "",
                "red": cs[0], "blue": cs[1],
            })
    fights.sort(key=lambda f: f["match"])
    return fights


def kd(f, corner):
    try:
        return int(float(f[corner]["st"].get("knockDowns") or 0))
    except ValueError:
        return 0


# ---------- UFC.com fight tracker ----------
def ufc_fights(j):
    e = (j or {}).get("LiveEventDetail") or {}
    out = []
    for f in e.get("FightCard") or []:
        ps = f.get("Fighters") or []
        if len(ps) < 2:
            continue
        red, blue = (ps[1], ps[0]) if str(ps[1].get("Corner", "")).lower() == "red" else (ps[0], ps[1])
        out.append({"red": red, "blue": blue, "status": f.get("Status") or "", "log": f.get("FightNightTracking") or [],
                    "result": f.get("Result") or {}, "rounds": (f.get("RuleSet") or {}).get("PossibleRounds") or 3})
    return out


def match_ufc(f, ufs):
    for u in ufs:
        rl, bl = u["red"].get("Name", {}).get("LastName"), u["blue"].get("Name", {}).get("LastName")
        if same(rl, f["red"]["last"]) and same(bl, f["blue"]["last"]):
            return u, False
        if same(rl, f["blue"]["last"]) and same(bl, f["red"]["last"]):
            return u, True
    return None, False


def method_text(f, u, flip):
    m = f["method"] or (u and u["result"].get("Method")) or ""
    m = re.sub(r"^Decision\s*-\s*(\w+)", lambda x: f"{x.group(1)} decision", m, flags=re.I)
    how = f["how"] or (u and (u["result"].get("EndingSubmission") or u["result"].get("EndingStrike"))) or ""
    if how and how.lower() not in m.lower():
        m += f" ({how})"
    rd, tm = "", ""
    if u and u["result"].get("EndingRound"):
        rd, tm = u["result"]["EndingRound"], u["result"].get("EndingTime") or ""
    elif f["state"] == "post" and f["period"]:
        rd, tm = f["period"], (f["clock"] if f["clock"] not in (None, "-") else "")
    when = f"R{rd} {tm}".strip() if rd else ""
    return " · ".join(x for x in (m, when) if x)


def winner_of(f, u, flip):
    if f["red"]["winner"]:
        return 1
    if f["blue"]["winner"]:
        return 2
    if u:
        def won(p):
            return "win" in str((p.get("Outcome") or {}).get("Outcome") or "").lower()
        w = 1 if won(u["red"]) else 2 if won(u["blue"]) else 0
        if not w:
            for t in u["log"]:
                if str(t.get("Type", "")).startswith("unofficial_winner"):
                    fid = t.get("FighterId")
                    w = 1 if fid == u["red"].get("FighterId") else 2 if fid == u["blue"].get("FighterId") else 0
        if w and flip:
            w = 3 - w
        return w
    return 0


def ufc_state(u):
    """'over', 'on' (walkouts or fighting) or '' from UFC.com's log."""
    if not u:
        return ""
    if u["status"].lower() in ("final", "complete"):
        return "over"
    types = [t.get("Type", "") for t in u["log"]]
    if any(t in ("fight_over", "fight_complete", "results") or t.startswith("unofficial_winner") for t in types):
        return "over"
    if any(t in ("fight_open", "walkout", "staredown", "tale_of_the_tape", "round_start") for t in types):
        return "on"
    return ""


def ufc_knockdowns(u, flip):
    """Knockdowns so far by corner from UFC.com's log, ESPN's red/blue."""
    n = {"red": 0, "blue": 0}
    if not u:
        return n
    for t in u["log"]:
        if t.get("Type") == "knockdown":
            side = "red" if t.get("FighterId") == u["red"].get("FighterId") else "blue" if t.get("FighterId") == u["blue"].get("FighterId") else None
            if side:
                if flip:
                    side = "blue" if side == "red" else "red"
                n[side] += 1
    return n


# ---------- the loop ----------
def load_state():
    try:
        with open(STATE_FILE) as fh:
            return json.load(fh)
    except Exception:
        return {}


def save_state(st):
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(st, fh)
    os.replace(tmp, STATE_FILE)


def main():
    began = time.time()
    sb = get(ESPN_SB)
    ev = (sb.get("events") or [{}])[0]
    eid = str(ev.get("id") or "")
    if not eid:
        log("no UFC event on ESPN's scoreboard")
        return
    state = load_state()
    if state.get("event") != eid:
        state = {"event": eid, "sent": [], "primed": False, "pending": {}}
    sent = set(state["sent"])
    ufc_id = UFC_SEED.get(eid)
    ufc_bad = 0
    ufc_next = 0
    ufs = []
    log("following", ev.get("name"), "espn", eid, "ufc", ufc_id, "topic", TOPIC)

    while time.time() - began < MAX_HOURS * 3600:
        try:
            fc = get(ESPN_FC.format(eid))
            fights = card(fc)
        except Exception as e:
            log("ESPN failed:", e)
            time.sleep(15)
            continue
        if ufc_id and time.time() >= ufc_next:
            try:
                ufs = ufc_fights(get(f"{UFC}/event/live/{ufc_id}.json", 8))
                ufc_bad = 0
            except Exception:
                ufc_bad += 1
                ufs = ufs if ufc_bad < 6 else []
            ufc_next = time.time() + (10 if ufc_bad < 3 else 30)

        name = fc.get("event", {}).get("name") or ev.get("name") or "UFC"
        now_ms = time.time() * 1000
        out = []  # (key, title, message, tags, priority)

        # The main card about to start.
        main_start = min((f["start"] for f in fights if f["seg"].lower().startswith("main")), default=0)
        if main_start and main_start - 12 * 60000 <= now_ms <= main_start + 10 * 60000:
            first = max((f for f in fights if f["seg"].lower().startswith("main")), key=lambda f: f["match"], default=None)
            if first and first["state"] == "pre":
                out.append(("main-card-soon", "Main card starting",
                            f"{uk_time(main_start)} on TNT Sports. First up: {first['red']['last']} v {first['blue']['last']}.",
                            ("bell",), 4))

        order = sorted(fights, key=lambda f: -f["match"])  # running order, first fight first
        for i, f in enumerate(order):
            u, flip = match_ufc(f, ufs)
            us = ufc_state(u)
            live = f["state"] == "in" or us == "on"
            over = f["state"] == "post" or us == "over"
            fid = f["id"]
            label = f"{f['red']['name']} ({f['red']['rec']}) v {f['blue']['name']} ({f['blue']['rec']})"
            rounds = (u and u["rounds"]) or (5 if f["main"] or f["title"] else 3)
            if live and not over:
                if f["main"]:
                    out.append((f"{fid}:start", "Main event starting", f"{label} · {f['weight']} · {rounds} rounds", ("boxing_glove", "fire"), 5))
                else:
                    out.append((f"{fid}:start", f"Next fight: {f['red']['last']} v {f['blue']['last']}", f"{label} · {f['weight']} · {rounds} rounds", ("boxing_glove",), 3))
            # Knockdowns: ESPN's count or UFC.com's log, whichever is ahead.
            uk = ufc_knockdowns(u, flip)
            for corner, other in (("red", "blue"), ("blue", "red")):
                n = max(kd(f, corner), uk[corner])
                for k in range(1, n + 1):
                    out.append((f"{fid}:kd:{corner}:{k}", f"Knockdown! {f[corner]['last']} drops {f[other]['last']}",
                                f"{f['red']['last']} v {f['blue']['last']}" + (f" · round {f['period']}" if f["period"] else ""), ("rotating_light",), 4))
            if over:
                w = winner_of(f, u, flip)
                mt = method_text(f, u, flip)
                nxt = next((g for g in order[i + 1:] if g["state"] != "post"), None)
                tail = f"\nUp next: {nxt['red']['last']} v {nxt['blue']['last']}" if nxt else ("\nThat's the card." if f["main"] else "")
                key = f"{fid}:result"
                if w and not mt:
                    # A winner but no method yet: give it 90 s before sending without one.
                    first_seen = state["pending"].setdefault(key, now_ms)
                    if now_ms - first_seen < 90000:
                        continue
                if w:
                    win, lose = (f["red"], f["blue"]) if w == 1 else (f["blue"], f["red"])
                    out.append((key, f"{win['last']} wins" + (" the main event" if f["main"] else ""),
                                f"Beat {lose['name']} · {mt or 'result official'}{tail}", ("trophy",), 5 if f["main"] else 4))
                elif f["state"] == "post" and mt:
                    out.append((key, f"{f['red']['last']} v {f['blue']['last']}: {mt}", f"No winner.{tail}", ("trophy",), 4))

        if not state["primed"]:
            first = min((f["start"] for f in fights), default=0)
            on_now = any(f["state"] == "in" for f in fights)
            if not on_now and (not first or first - now_ms > LEAD_HOURS * 3600e3 or all(f["state"] == "post" for f in fights)):
                log("nothing on: first fight", uk_time(first) if first else "unknown", "- leaving")
                return
            # First look: everything already true is old news.
            for key, *_ in out:
                sent.add(key)
            state["primed"] = True
            done = sum(1 for f in fights if f["state"] == "post")
            notify("Cageside alerts on", f"{name}: {done} of {len(fights)} fights done. You'll get fight starts, knockdowns and results.", ("bell",), 2)
        else:
            for key, title, msg, tags, pr in out:
                if key in sent:
                    continue
                if notify(title, msg, tags, pr):
                    sent.add(key)
        state["sent"] = sorted(sent)
        save_state(state)

        if fights and all(f["state"] == "post" for f in fights) and all(f"{f['id']}:result" in sent for f in fights):
            log("card finished")
            return
        live_now = any(f["state"] == "in" for f in fights) or any(ufc_state(u) == "on" for u in ufs)
        time.sleep(12 if live_now else 30)
    log("stopped after", MAX_HOURS, "hours")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
