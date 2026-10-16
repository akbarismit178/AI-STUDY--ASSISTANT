import os

from flask import current_app


def resolve_path(db_path):
    """
    Database me stored relative path ko
    absolute filesystem path me convert karta hai.
    """

    if not db_path:
        return None

    if os.path.isabs(db_path):
        return db_path

    return os.path.join(
        current_app.root_path,
        db_path
    )