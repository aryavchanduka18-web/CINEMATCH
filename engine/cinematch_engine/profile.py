"""User stage (spec section 6.1).

The stage depends ONLY on the behavioral interaction count b: distinct films the user rated, liked,
disliked, added to My List or marked watched. Onboarding picks are counted separately
(onboarding_count) and never add to b; views, Quick Views and search clicks do not count either.
"""
COLD, WARMING, ESTABLISHED = "cold", "warming", "established"
STAGES = (COLD, WARMING, ESTABLISHED)
BEHAVIORAL_EVENTS = {"rate", "like", "dislike", "list_add", "watched"}


def stage_of(b: int) -> str:
    if b <= 2:
        return COLD
    if b <= 10:
        return WARMING
    return ESTABLISHED


def behavioral_count(events) -> int:
    """events: iterable of (event_type, movie_id). Counts distinct films with a behavioral event."""
    return len({movie for kind, movie in events if kind in BEHAVIORAL_EVENTS})