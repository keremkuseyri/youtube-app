import random
import time
import re
import logging

from googleapiclient.discovery import build
from google import genai

from config import Config

client = genai.Client(api_key=Config.GEMINI_API_KEY)
logger = logging.getLogger(__name__)

REQUESTS_PER_MINUTE = 30
MIN_INTERVAL_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE
MAX_PROMPT_LENGTH = 1200

_last_gemini_call = 0.0
_ai_cooldown_until = 0.0


def _trim_prompt(prompt: str, max_length: int = MAX_PROMPT_LENGTH) -> str:
    if len(prompt) <= max_length:
        return prompt
    trimmed = prompt[:max_length].rsplit("\n", 1)[0]
    return trimmed or prompt[:max_length]


def _throttle_requests():
    global _last_gemini_call
    elapsed = time.time() - _last_gemini_call
    wait = MIN_INTERVAL_BETWEEN_REQUESTS - elapsed
    if wait > 0:
        time.sleep(wait)
    _last_gemini_call = time.time()


def _is_quota_or_rate_error(exc) -> bool:
    message = str(exc)
    normalized = message.lower()
    return (
        "429" in normalized
        or "resource_exhausted" in normalized
        or "quota" in normalized
        or "rate limit" in normalized
    )


def _is_hard_quota_exhausted(exc) -> bool:
    message = str(exc).lower()
    return (
        "limit: 0" in message
        or "requestsperday" in message
        or "inputtokenspermodelperminute-freetier" in message
    )


def _parse_retry_delay_seconds(exc) -> int:
    message = str(exc)

    retry_info = re.search(r"retrydelay['\"]?\s*:\s*['\"]?(\d+)s", message, re.IGNORECASE)
    if retry_info:
        return int(retry_info.group(1))

    retry_text = re.search(r"retry in\s*([0-9]+(?:\.[0-9]+)?)s", message, re.IGNORECASE)
    if retry_text:
        return max(1, int(float(retry_text.group(1))))

    return 0


def _is_model_unavailable_error(exc) -> bool:
    message = str(exc).lower()
    return (
        "model not found" in message
        or "unsupported model" in message
        or "permission denied" in message
        or "not allowed" in message
        or "invalid argument" in message
    )


def _candidate_models():
    ordered = [Config.AI_MODEL] + Config.AI_FALLBACK_MODELS
    models = []
    seen = set()

    for model in ordered:
        if model and model not in seen:
            models.append(model)
            seen.add(model)

    return models


def gemini_generate_with_backoff(prompt, max_retries=5):
    global _ai_cooldown_until

    now = time.time()
    if now < _ai_cooldown_until:
        remaining = int(_ai_cooldown_until - now)
        raise RuntimeError(f"Gemini scoring is in cooldown for {remaining}s due to quota exhaustion")

    trimmed_prompt = _trim_prompt(prompt)
    last_exc = RuntimeError("No AI model configured")

    for model in _candidate_models():
        for attempt in range(1, max_retries + 1):
            _throttle_requests()
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=trimmed_prompt,
                    config={"temperature": 0},
                )
                return response, model
            except Exception as exc:
                last_exc = exc

                if _is_model_unavailable_error(exc):
                    logger.warning("Skipping unavailable model '%s': %s", model, exc)
                    break

                if not _is_quota_or_rate_error(exc):
                    logger.warning("Model '%s' failed, trying next fallback: %s", model, exc)
                    break

                retry_delay = _parse_retry_delay_seconds(exc)
                if _is_hard_quota_exhausted(exc):
                    cooldown_seconds = max(retry_delay, 600)
                    _ai_cooldown_until = time.time() + cooldown_seconds
                    logger.warning(
                        "Hard quota exhausted for model '%s'. Cooling down AI scoring for %ss",
                        model,
                        cooldown_seconds,
                    )
                    break

                if attempt == max_retries:
                    break
                delay = max(retry_delay, min(60, 2 ** (attempt - 1))) + random.random()
                time.sleep(delay)

    raise last_exc


def _search_video_ids_by_duration(youtube, query, duration, max_results=25):
    response = youtube.search().list(
        q=query,
        part="id",
        type="video",
        videoDuration=duration,
        maxResults=max_results,
    ).execute()

    return [
        item["id"]["videoId"]
        for item in response.get("items", [])
        if item.get("id", {}).get("videoId")
    ]


def _format_iso8601_duration(duration):
    match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration or "")
    if not match:
        return "N/A"

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    if hours > 0:
        return f"{hours}:{minutes:02}:{seconds:02}"
    return f"{minutes}:{seconds:02}"


def _abbreviate_count(value):
    try:
        num = int(value)
    except (TypeError, ValueError):
        return "0"

    if num < 1_000:
        return str(num)
    if num < 1_000_000:
        return f"{num/1000:.1f}".rstrip("0").rstrip(".") + "K"
    if num < 1_000_000_000:
        return f"{num/1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    return f"{num/1_000_000_000:.1f}".rstrip("0").rstrip(".") + "B"


def _to_float_score(value):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError, AttributeError):
        return -1.0


def _safe_score_text(raw_text):
    score = _to_float_score(raw_text)
    if score < 0:
        return "N/A"
    return f"{max(0.0, min(10.0, score)):.1f}"


def _extract_scores(response_text, expected_count):
    matches = re.findall(r"\b(?:10(?:\.0+)?|[0-9](?:\.\d+)?)\b", response_text or "")
    extracted = []

    for match in matches:
        numeric = _to_float_score(match)
        if numeric < 0:
            continue
        extracted.append(f"{max(0.0, min(10.0, numeric)):.1f}")
        if len(extracted) >= expected_count:
            break

    return extracted


def _extract_scores_by_video_id(response_text, valid_video_ids):
    pattern = re.compile(
        r"([A-Za-z0-9_-]{6,}):\s*(10(?:\.0+)?|[0-9](?:\.\d+)?)"
    )
    valid_ids = set(valid_video_ids)
    parsed = {}

    for video_id, raw_score in pattern.findall(response_text or ""):
        if video_id not in valid_ids:
            continue
        parsed[video_id] = f"{max(0.0, min(10.0, _to_float_score(raw_score))):.1f}"

    return parsed


def _get_best_video_thumbnail(snippet):
    thumbnails = snippet.get("thumbnails", {})
    for key in ("maxres", "standard", "high", "medium", "default"):
        url = thumbnails.get(key, {}).get("url")
        if url:
            return url
    return ""


def search_videos(query):
    youtube = build("youtube", "v3", developerKey=Config.YT_API_KEY)

    video_ids = []
    for duration in ("medium", "long"):
        if len(video_ids) >= 4:
            break
        for video_id in _search_video_ids_by_duration(youtube, query, duration):
            if video_id not in video_ids:
                video_ids.append(video_id)
            if len(video_ids) >= 4:
                break

    videos = []
    if video_ids:
        stats_res = youtube.videos().list(
            id=",".join(video_ids[:4]),
            part="statistics,snippet,contentDetails",
        ).execute()
        videos = stats_res.get("items", [])

    prompt_items = "\n".join(
        [f"{v['id']}: {v['snippet']['title']}" for v in videos]
    )

    batch_prompt = (
        "Score these YouTube videos from 1-10 for educational quality. "
        "Return ONLY one item per line in format video_id:score. "
        "No extra text, no explanation.\n"
        f"Videos:\n{prompt_items}"
    )

    ai_scores_by_id = {}
    ai_model_used = "unknown"
    ai_error_message = None

    if videos:
        try:
            response, ai_model_used = gemini_generate_with_backoff(batch_prompt)
            response_text = getattr(response, "text", "") or ""
            ai_scores_by_id = _extract_scores_by_video_id(response_text, [v["id"] for v in videos])

            if len(ai_scores_by_id) < len(videos):
                scores = _extract_scores(response_text, len(videos))
                for idx, video in enumerate(videos):
                    if video["id"] not in ai_scores_by_id and idx < len(scores):
                        ai_scores_by_id[video["id"]] = _safe_score_text(scores[idx])
        except Exception as exc:
            ai_scores_by_id = {}
            ai_error_message = str(exc)
            logger.warning("Gemini scoring failed after retries: %s", ai_error_message)

    ranked_results = []
    for video in videos:
        score_text = ai_scores_by_id.get(video["id"])
        if not score_text or score_text == "N/A":
            score_text = "N/A"
            score_source = "unavailable"
            score_model = "none"
        else:
            score_source = "ai"
            score_model = ai_model_used

        ranked_results.append(
            {
                "id": video["id"],
                "title": video["snippet"]["title"],
                "thumbnail": _get_best_video_thumbnail(video["snippet"]),
                "duration": _format_iso8601_duration(video["contentDetails"]["duration"]),
                "views": _abbreviate_count(video["statistics"].get("viewCount", 0)),
                "likes": _abbreviate_count(video["statistics"].get("likeCount", 0)),
                "channel": video["snippet"]["channelTitle"],
                "score": score_text,
                "scoreSource": score_source,
                "scoreModel": score_model,
                "aiError": ai_error_message if score_source == "unavailable" else None,
            }
        )

    ranked_results.sort(key=lambda x: _to_float_score(x["score"]), reverse=True)
    return ranked_results