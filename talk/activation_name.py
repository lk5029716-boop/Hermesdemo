"""Activation name (wake word) matching with fuzzy Levenshtein distance.

Ported from OpenClaw src/talk/activation-name.ts
"""

from __future__ import annotations

import re

REALTIME_VOICE_ACTIVATION_NAME_MAX_WORDS = 2


def realtime_voice_activation_name_word_count(value: str) -> int:
    return len(re.findall(r"[a-z0-9]+", value, re.IGNORECASE))


def normalize_realtime_voice_activation_name(value: str) -> str | None:
    normalized = re.sub(r"\s+", " ", value.lower()).strip()
    return normalized or None


def normalize_realtime_voice_activation_name_prefix(
    value: str,
    max_words: int = REALTIME_VOICE_ACTIVATION_NAME_MAX_WORDS,
) -> str | None:
    words = re.findall(r"[a-z0-9]+", value, re.IGNORECASE)
    if not words:
        return None
    return " ".join(words[:max_words])


def is_supported_realtime_voice_activation_name(
    value: str,
    max_words: int = REALTIME_VOICE_ACTIVATION_NAME_MAX_WORDS,
) -> bool:
    count = realtime_voice_activation_name_word_count(value)
    return 1 <= count <= max_words


def normalize_supported_realtime_voice_activation_name(
    value: str | None,
    max_words: int = REALTIME_VOICE_ACTIVATION_NAME_MAX_WORDS,
) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = normalize_realtime_voice_activation_name(value)
    if normalized and is_supported_realtime_voice_activation_name(normalized, max_words):
        return normalized
    return None


def sort_realtime_voice_activation_names(names: list[str]) -> list[str]:
    return sorted(names, key=lambda x: (-len(x), x))


def _levenshtein_distance(left: str, right: str) -> int:
    if left == right:
        return 0
    if not left:
        return len(right)
    if not right:
        return len(left)

    previous = list(range(len(right) + 1))
    current = [0] * (len(right) + 1)

    for i in range(len(left)):
        current[0] = i + 1
        for j in range(len(right)):
            cost = 0 if left[i] == right[j] else 1
            current[j + 1] = min(current[j] + 1, previous[j + 1] + 1, previous[j] + cost)
        previous, current = current, previous

    return previous[len(right)]


_VOWELS = set("aeiouy")
_LIQUIDS = set("lr")


def _has_only_phonetic_substitutions(left: str, right: str) -> bool:
    if len(left) != len(right):
        return False
    substitutions = 0
    for lc, rc in zip(left, right):
        if lc == rc:
            continue
        vowel_like = lc in _VOWELS and rc in _VOWELS
        liquid_like = lc in _LIQUIDS and rc in _LIQUIDS
        if not vowel_like and not liquid_like:
            return False
        substitutions += 1
    return substitutions > 0


def _common_prefix_length(left: str, right: str) -> int:
    limit = min(len(left), len(right))
    for i in range(limit):
        if left[i] != right[i]:
            return i
    return limit


def _is_fuzzy_activation_name_match(
    strong_boundary: bool,
    edge: str,
    heard_compact: str,
    activation_compact: str,
) -> bool:
    if not heard_compact or not activation_compact or len(activation_compact) < 5:
        return False
    if not strong_boundary:
        return False
    if heard_compact[0] != activation_compact[0]:
        return False

    distance = _levenshtein_distance(heard_compact, activation_compact)

    if edge == "trailing":
        return (
            len(heard_compact) == len(activation_compact)
            and _has_only_phonetic_substitutions(heard_compact, activation_compact)
        )

    if distance <= 1:
        return True
    if (
        distance == 2
        and len(heard_compact) >= 4
        and len(activation_compact) >= 5
        and (
            len(heard_compact) != len(activation_compact)
            or _has_only_phonetic_substitutions(heard_compact, activation_compact)
            or _common_prefix_length(heard_compact, activation_compact) >= 6
        )
    ):
        return True
    if (
        distance == 3
        and len(heard_compact) >= 7
        and len(activation_compact) >= 7
        and len(heard_compact) != len(activation_compact)
        and _common_prefix_length(heard_compact, activation_compact) >= 5
    ):
        return True
    return False


def _normalize_candidate(value: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()
    return normalized or None


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value)


def _leading_candidates(text: str, max_words: int) -> list[dict]:
    opener = re.match(r"^\s*(?:(?:hey|ok|okay)(?:\s*[-,:;]+\s*|\s+))?", text, re.IGNORECASE)
    name_start = len(opener.group()) if opener else 0
    candidates: list[dict] = []
    candidate_starts = [0, name_start] if name_start > 0 else [0]

    for start_idx in candidate_starts:
        token_pattern = re.compile(r"[a-z0-9]+", re.IGNORECASE)
        start_candidates: list[dict] = []
        pos = start_idx

        for word_count in range(max_words):
            match = token_pattern.search(text, pos)
            if not match:
                break
            prev_end = start_idx if word_count == 0 else start_candidates[-1]["end_index"]
            between = text[prev_end: match.start()]
            if word_count > 0 and not re.match(r"^[\s'-]+$", between):
                break
            end_idx = match.start() + len(match.group())
            heard = _normalize_candidate(text[start_idx:end_idx])
            if not heard:
                break
            boundary = re.match(r"\s*([,.:;!?-]|$)", text[end_idx:])
            start_candidates.append({
                "edge": "leading",
                "heard_name": heard,
                "start_index": start_idx,
                "end_index": end_idx,
                "strong_boundary": bool(boundary),
            })
            pos = end_idx

        candidates.extend(start_candidates)

    return candidates


def _trailing_candidates(text: str, max_words: int) -> list[dict]:
    tokens = list(re.finditer(r"[a-z0-9]+", text, re.IGNORECASE))
    candidates: list[dict] = []
    token_count = min(len(tokens), max_words)

    for word_count in range(1, token_count + 1):
        start_token = tokens[len(tokens) - word_count]
        end_token = tokens[-1]
        if not start_token or not end_token:
            break
        start_idx = start_token.start()
        end_idx = end_token.end()

        if not re.match(r"^\s*(?:[,.:;!?-]+\s*)?$", text[end_idx:]):
            break
        if not re.match(r"(^|[\s,.:;!?-])$", text[:start_idx]):
            break

        direct_address = re.match(r"(^|[,.:;!?-]\s*)$", text[:start_idx])
        trailing_question = re.search(r"\?\s*$", text)

        if word_count > 1:
            prev_token = tokens[len(tokens) - word_count + 1]
            between = text[start_idx + len(start_token.group()): prev_token.start()]
            if not re.match(r"^[\s'-]+$", between):
                break

        heard = _normalize_candidate(text[start_idx:end_idx])
        if not heard:
            break

        candidates.append({
            "edge": "trailing",
            "heard_name": heard,
            "start_index": start_idx,
            "end_index": end_idx,
            "strong_boundary": bool(direct_address) and bool(trailing_question),
        })

    return candidates


def match_realtime_voice_activation_name(
    text: str,
    activation_names: list[str],
    max_words: int = REALTIME_VOICE_ACTIVATION_NAME_MAX_WORDS,
) -> dict | None:
    """Match activation names in transcript text with fuzzy matching.

    Returns a dict with match details or None if no match found.
    """
    prepared = []
    for name in activation_names:
        normalized = _normalize_candidate(name)
        if normalized:
            prepared.append({"activation_name": name, "compact": _compact(normalized)})

    if not prepared:
        return None

    candidates = [
        *(_leading_candidates(text, max_words)),
        *(_trailing_candidates(text, max_words)),
    ]

    prepared_candidates = sorted(
        [
            {"candidate": c, "compact": _compact(c["heard_name"])}
            for c in candidates
        ],
        key=lambda x: -len(x["compact"]),
    )

    for pc in prepared_candidates:
        for pn in prepared:
            heard_compact = pc["compact"]
            activation_compact = pn["compact"]
            exact = heard_compact == activation_compact
            fuzzy = _is_fuzzy_activation_name_match(
                pc["candidate"]["strong_boundary"],
                pc["candidate"]["edge"],
                heard_compact,
                activation_compact,
            )
            if exact or fuzzy:
                # Strip the activation name from text
                c = pc["candidate"]
                if c["edge"] == "leading":
                    stripped = re.sub(r"^\s*(?:[-,:;.!?]+\s*)?", "", text[c["end_index"]:]).strip()
                else:
                    stripped = re.sub(r"\s*(?:[-,:;.!?]+\s*)?$", "", text[:c["start_index"]]).strip()
                return {
                    "allowed": True,
                    "text": stripped,
                    "activation_name": pn["activation_name"],
                    "heard_name": c["heard_name"],
                    "match": "exact" if exact else "fuzzy",
                    "edge": c["edge"],
                }

    return None
