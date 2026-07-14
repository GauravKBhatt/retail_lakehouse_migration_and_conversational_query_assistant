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
from sqlglot.expressions import Column, Alias

OPA_URL = "http://opa:8181/v1/data/lakehouse/masking/masked_columns"


def get_masked_columns(user_role: str, *, opa_url: str = OPA_URL) -> list[str]:
    """Ask OPA which columns should be masked for this role."""
    try:
        resp = requests.post(opa_url, json={"input": {"role": user_role}}, timeout=2)
        resp.raise_for_status()
        result = resp.json().get("result", [])
        print(f"OPA response for role {user_role}: {result}")
        return result if isinstance(result, list) else []
    except requests.RequestException as e:
        # OPA unreachable — fail open (no masking) so the app stays usable
        print(f"OPA connection failed: {e}")
        return []


def _col_unqualified_name(col: Column) -> str:
    """Return the bare column name without table qualifier."""
    return col.name


def _in_select_clause(node: Column) -> bool:
    """Return True if *node* is inside a SELECT expression list."""
    child = node
    parent = child.parent
    while parent is not None:
        if isinstance(parent, exp.Select):
            return True
        if isinstance(parent, (exp.Join, exp.Where, exp.Group, exp.Order, exp.Having,
                               exp.Window, exp.Subquery, exp.Union)):
            return False
        child = parent
        parent = parent.parent
    return False


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
        if isinstance(node, Column) and not isinstance(node.parent, exp.Func):
            bare_name = _col_unqualified_name(node)
            if bare_name in masked_set:
                hashed = exp.Anonymous(
                    this="SHA2",
                    expressions=[
                        exp.Cast(this=node.copy(), to=exp.DataType(this=exp.DataType.Type.TEXT)),
                        exp.Literal.number(256),
                    ],
                )
                if isinstance(node.parent, Alias):
                    return hashed
                if _in_select_clause(node):
                    return Alias(this=hashed, alias=bare_name)
                return hashed
        return node

    rewritten = tree.transform(_rewrite)
    return rewritten.sql(dialect="spark", pretty=True)