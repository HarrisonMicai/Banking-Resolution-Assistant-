from datetime import date, datetime


ACCESS_RULES = {
    "Public": ["Public"],
    "Internal": ["Public", "Internal"],
    "Restricted": ["Public", "Internal", "Restricted"],
}


def get_permitted_labels(user_access):
    """Return document labels accessible to the requested user level."""

    if user_access not in ACCESS_RULES:
        raise ValueError("Invalid user access level.")

    return ACCESS_RULES[user_access]


def parse_effective_date(value):
    """Parse supported manifest date formats into a calendar date."""

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    if isinstance(value, int) and not isinstance(value, bool):
        try:
            return date.fromisoformat(f"{value:08d}")
        except ValueError as error:
            raise ValueError(f"Invalid effective_date: {value}") from error

    if not isinstance(value, str) or not value.strip():
        raise ValueError("effective_date must be a non-empty date string.")

    value = value.strip()
    try:
        return date.fromisoformat(value)
    except ValueError:
        for date_format in ("%m/%d/%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue

    raise ValueError(f"Invalid effective_date: {value}")


def build_policy_filter(permitted_labels, as_of_date):
    """Build the shared ChromaDB filter for policy evidence retrieval."""

    cutoff = parse_effective_date(as_of_date)
    return {
        "$and": [
            {"status": {"$eq": "Approved"}},
            {"access_label": {"$in": permitted_labels}},
            {"document_type": {"$ne": "Casebook"}},
            {
                "effective_date": {
                    "$lte": int(cutoff.strftime("%Y%m%d"))
                }
            },
        ]
    }
