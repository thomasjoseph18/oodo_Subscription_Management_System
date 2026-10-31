import re

from rest_framework import serializers


def validate_password_rule(password):
    """More than eight characters, with upper case, lower case and a special character."""
    problems = []
    if len(password) <= 8:
        problems.append("more than 8 characters")
    if not re.search(r"[A-Z]", password):
        problems.append("an uppercase letter")
    if not re.search(r"[a-z]", password):
        problems.append("a lowercase letter")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("a special character")
    if problems:
        raise serializers.ValidationError(f"Password needs {', '.join(problems)}.")
    return password
