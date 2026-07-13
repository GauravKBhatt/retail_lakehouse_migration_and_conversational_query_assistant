import sqlglot
from sqlglot import parse_one
from sqlglot.expressions import Insert, Update, Delete, Drop, Create, Alter, Merge


DANGEROUS_NODES = (Insert, Update, Delete, Drop, Create, Alter, Merge)

def is_safe_query(sql: str) -> tuple[bool, str]:
    """
    Check if the SQL query is safe to execute.
    
    Args:
        sql: SQL query string
        
    Returns:
        tuple[bool, str]: (is_safe, reason)
    """
    try:
        tree = parse_one(sql, dialect='spark')
    except Exception as e:
        return False, f'SQL parse error: {e}'
    for node in tree.walk():
        if isinstance(node, DANGEROUS_NODES):
            return False, f'Rejected: {type(node).__name__} statements are not allowed'
    return True, 'ok'