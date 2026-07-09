import json
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Query


SUPPORTED_DOMAIN_OPERATORS = {
    "=",
    "!=",
    "ilike",
    "like",
    ">",
    "<",
    ">=",
    "<=",
    "in",
    "not_in",
    "is_null",
    "is_not_null",
}


class DomainError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


def parse_domain(raw_domain: str | None) -> list[list[Any]]:
    if not raw_domain:
        return []

    try:
        domain = json.loads(raw_domain)
    except json.JSONDecodeError:
        raise DomainError("Invalid domain JSON")

    if not isinstance(domain, list):
        raise DomainError("Domain must be a list")

    normalized = []

    for condition in domain:
        if not isinstance(condition, list):
            raise DomainError("Each domain condition must be a list")

        if len(condition) not in (2, 3):
            raise DomainError("Each domain condition must have 2 or 3 items")

        field = condition[0]
        operator = condition[1]
        value = condition[2] if len(condition) == 3 else None

        if not isinstance(field, str) or not field:
            raise DomainError("Domain field must be a non-empty string")

        if not isinstance(operator, str) or operator not in SUPPORTED_DOMAIN_OPERATORS:
            raise DomainError(f"Unsupported domain operator '{operator}'")

        if operator in {"is_null", "is_not_null"} and len(condition) != 2:
            raise DomainError(f"Operator '{operator}' must not receive a value")

        if operator not in {"is_null", "is_not_null"} and len(condition) != 3:
            raise DomainError(f"Operator '{operator}' requires a value")

        if operator in {"in", "not_in"} and not isinstance(value, list):
            raise DomainError(f"Operator '{operator}' requires a list value")

        normalized.append([field, operator, value])

    return normalized


def get_model_column(model, field: str):
    columns = model.__table__.columns
    print(f"Available columns for model {model.__name__}: {[c.name for c in columns]}")
    if field not in columns:
        raise DomainError(f"Unknown domain field '{field}'")

    return columns[field]


def apply_domain(query: Query, model, raw_domain: str | None) -> Query:
    print(f"Applying domain: {raw_domain} to model: {model.__name__}")
    domain = parse_domain(raw_domain)

    for field, operator, value in domain:
        column = get_model_column(model, field)

        if operator == "=":
            query = query.filter(column == value)
        elif operator == "!=":
            query = query.filter(column != value)
        elif operator == "ilike":
            query = query.filter(column.ilike(f"%{value}%"))
        elif operator == "like":
            query = query.filter(column.like(f"%{value}%"))
        elif operator == ">":
            query = query.filter(column > value)
        elif operator == "<":
            query = query.filter(column < value)
        elif operator == ">=":
            query = query.filter(column >= value)
        elif operator == "<=":
            query = query.filter(column <= value)
        elif operator == "in":
            query = query.filter(column.in_(value))
        elif operator == "not_in":
            query = query.filter(~column.in_(value))
        elif operator == "is_null":
            query = query.filter(column.is_(None))
        elif operator == "is_not_null":
            query = query.filter(column.is_not(None))

    return query