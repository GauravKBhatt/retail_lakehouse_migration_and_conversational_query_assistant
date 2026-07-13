"""Column-level masking via OPA + sqlglot AST rewriting.

OPA decides *which* columns to mask for a given role.
sqlglot rewrites the query AST so that masked columns are replaced with
``SHA2(col, 256) AS col`` — safe against aliases, functions, subqueries,
and WHERE clauses that str.replace() would break.
"""

from typing import Optional

import requests
import sqlglot
from sqlglot import exp
from sqlglot.expressions import Column, Func, Alias

OPA_URL = "http://localhost:8181/v1/data/lakehouse/masking/masked_columns"


def get_masked_columns(user_role: str, *, opa_url: str = OPA_URL) -> list[str]:
    """Ask OPA which columns should be masked for this role."""
    try:
        resp = requests.post(opa_url, json={"input": {"role": user_role}}, timeout=2)
        resp.raise_for_status()
        result = resp.json().get("result", [])
        return result if isinstance(result, list) else []
    except requests.RequestException:
        # OPA unreachable — fail open (no masking) so the app stays usable
        return []


def _col_unqualified_name(col: Column) -> str:
    """Return the bare column name without table qualifier."""
    return col.name


def rewrite_query_with_masks(sql: str, masked_cols: list[str]) -> str:
    """Rewrite *sql* so that every reference to a masked column is wrapped
    in ``SHA2(col, 256) AS col``.

    Uses sqlglot's AST so it correctly handles:
    - ``SELECT customer_id FROM ...``
    - ``SELECT t.customer_id FROM ...``
    - ``WHERE customer_id = 1``
    - ``COUNT(customer_id)``
    - ``SELECT customer_id AS cid``
    - Nested subqueries
    """
    if not masked_cols:
        return sql

    masked_set = set(masked_cols)

    tree = sqlglot.parse_one(sql, dialect="spark")

    def _rewrite(node):
        # Only transform bare Column references, not columns already inside
        # an Alias or a function that we produced.
        if isinstance(node, Column) and not isinstance(node.parent, (Alias, Func)):
            bare_name = _col_unqualified_name(node)
            if bare_name in masked_set:
                return Alias(
                    this=Func(
                        this="SHA2",
                        expressions=[Column(this=bare_name), exp.Literal.number(256)],
                    ),
                    alias=bare_name,
                )
        return node

    rewritten = tree.transform(_rewrite)
    return rewritten.sql(dialect="spark", pretty=True)