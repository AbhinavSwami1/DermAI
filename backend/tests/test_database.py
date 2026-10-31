from sqlalchemy import inspect


def test_database_tables_created(db_session):
    inspector = inspect(db_session.get_bind())

    expected_tables = {
    "users",
    "roles",
    "user_roles",
    "cases",
    "images",
    "model_versions",
    "predictions",
    "refresh_tokens",
}

    actual_tables = set(inspector.get_table_names())

    assert expected_tables.issubset(actual_tables)