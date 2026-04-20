import math
from typing import Dict

# Try to use vaderSentiment if available (preferred as it bundles the lexicon)
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer  # type: ignore
    _vader = SentimentIntensityAnalyzer()
except Exception:
    _vader = None

# Minimal fallback keywords-based analyzer (very rough)
_NEG = set([
    'sad','anxious','depressed','down','bad','terrible','awful','cry','hopeless','tired',
    'angry','worried','scared','panic','overwhelmed','helpless','worthless','lonely','guilty',
])
_POS = set([
    'happy','good','great','relieved','calm','hopeful','okay','fine','better','improving',
    'proud','grateful','supported','encouraged','strong','confident','peaceful','loved',
])


def _fallback_score(text: str) -> float:
    if not text:
        return 0.0
    t = text.lower()
    pos = sum(w in t for w in _POS)
    neg = sum(w in t for w in _NEG)
    if pos == 0 and neg == 0:
        return 0.0
    raw = (pos - neg) / max(1, (pos + neg))  # range ~[-1,1]
    return max(-1.0, min(1.0, raw))


def analyze_sentiment(text: str) -> Dict:
    """
    Returns a dict with fields:
      - score: float in [-1,1]
      - label: 'negative'|'neutral'|'positive'
    """
    score = 0.0
    try:
        if _vader is not None:
            vs = _vader.polarity_scores(text or '')
            score = float(vs.get('compound', 0.0))
        else:
            score = _fallback_score(text or '')
    except Exception:
        score = _fallback_score(text or '')

    # Label mapping similar to VADER defaults
    if score >= 0.05:
        label = 'positive'
    elif score <= -0.05:
        label = 'negative'
    else:
        label = 'neutral'

    return {
        'score': score,
        'label': label,
    }
