"""
prompt_store.py

Defines the `PromptStore` class, which provides a centralized way to manage SQL query templates
and generate SQL statements dynamically by substituting parameters into predefined templates.

Features:
- Centralized management of SQL query templates for various database operations.
- Dynamic SQL generation by substituting parameters into predefined templates.
- Support for common operations like insert, update, delete, and search.
- Index creation for optimizing database queries.

Author: Patrick Scheich
Date: 2025-03-28
"""


class QueryStore:
    """
    prompt_store.py
    ===============
    This module defines the `PromptStore` class, which provides a centralized way 
    to manage SQL query templates and generate SQL statements dynamically by substituting parameters
    into predefined templates.
    Classes:
    --------
    - PromptStore: A utility class for managing and formatting SQL query templates.
    Usage:
    ------
    The `PromptStore` class contains a dictionary of SQL templates (`SQL_TEMPLATES`) 
    for various database operations such as inserting, updating, deleting, and searching records.
    The `get_sql` method allows users to retrieve
    and format a specific SQL query by providing the query name and the required parameters.
    """

    SQL_TEMPLATES = {
        # ===== TABLE CREATION =================================
        "create_jira_issue_table": """
        CREATE TABLE jira_issue (
            key TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            summary_vector VECTOR(1024),
            description TEXT,
            description_vector VECTOR(1024),
            issue_type TEXT,
            status TEXT,
            status_category TEXT,
            project TEXT,
            assignee TEXT,
            reporter TEXT,
            created TIMESTAMP,
            updated TIMESTAMP,
            time_spent_seconds INT,
            url TEXT
        );
        """,
        "create_jira_subtask_table": """
        CREATE TABLE jira_subtask (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key TEXT NOT NULL,
            parent_key TEXT,
            summary TEXT NOT NULL,
            summary_vector VECTOR(1024),
            description TEXT,
            description_vector VECTOR(1024),
            status TEXT,
            status_category TEXT,
            assignee TEXT,
            created TIMESTAMP,
            updated TIMESTAMP,
            time_spent_seconds INT,
            url TEXT
        );
        """,
        "create_jira_task_table": """
        CREATE TABLE jira_task (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key TEXT NOT NULL,
            parent_key TEXT,
            summary TEXT NOT NULL,
            summary_vector VECTOR(1024),
            description TEXT,
            description_vector VECTOR(1024),
            issue_type TEXT,
            status TEXT,
            status_category TEXT,
            project TEXT,
            assignee TEXT,
            reporter TEXT,
            created TIMESTAMP,
            updated TIMESTAMP,
            time_spent_seconds INT,
            url TEXT
        );
        """,
        "create_jira_bug_table": """
        CREATE TABLE jira_bug (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key TEXT NOT NULL,
            parent_key TEXT,
            summary TEXT NOT NULL,
            summary_vector VECTOR(1024),
            description TEXT,
            description_vector VECTOR(1024),
            issue_type TEXT,
            status TEXT,
            status_category TEXT,
            project TEXT,
            assignee TEXT,
            reporter TEXT,
            created TIMESTAMP,
            updated TIMESTAMP,
            time_spent_seconds INT,
            url TEXT
        );""",
        # ===== TABLE DELETION ================================
        "delete_jira_issue": """
        DELETE FROM jira_issue WHERE key = '{key}';
        """,
        "delete_jira_subtask": """
        DELETE FROM jira_subtask WHERE key = '{key}';
        """,
        "delete_jira_task": """
        DELETE FROM jira_task WHERE key = '{key}';
        """,
        "delete_jira_bug": """
        DELETE FROM jira_bug WHERE key = '{key}';
        """,
        # ===== TABLE DROP ===============================
        "drop_jira_issue_table": """
        DROP TABLE IF EXISTS jira_issue;
        """,
        "drop_jira_subtask_table": """
        DROP TABLE IF EXISTS jira_subtask;
        """,
        "drop_jira_task_table": """
        DROP TABLE IF EXISTS jira_task;
        """,
        "drop_jira_bug_table": """
        DROP TABLE IF EXISTS jira_bug;
        """,
        # ===== INSERTION ==================================
        "insert_jira_issue": """
        INSERT INTO jira_issue (key, summary, summary_vector, description, description_vector, issue_type, status, 
        status_category, project, assignee, reporter, created, updated, time_spent_seconds, url)
        VALUES ('{key}', '{summary}', '{summary_vector}', '{description}', '{description_vector}', '{issue_type}', 
        '{status}', '{status_category}', '{project}', '{assignee}', '{reporter}', '{created}', '{updated}', 
        {time_spent_seconds}, '{url}');
        """,
        "insert_jira_subtask": """
        INSERT INTO jira_subtask (key, parent_key, summary, summary_vector, description, description_vector, status, status_category, assignee, 
        created, updated, time_spent_seconds, url)
        VALUES ('{key}', '{parent_key}', '{summary}', '{summary_vector}', '{description}', '{description_vector}', '{status}', '{status_category}', 
        '{assignee}', '{created}', '{updated}', {time_spent_seconds}, '{url}');
        ""","insert_jira_task": """
        INSERT INTO jira_task (key, parent_key, summary, summary_vector, description, description_vector, issue_type,
        status, status_category, project, assignee, reporter, created, updated, time_spent_seconds, url)
        VALUES ('{key}', '{parent_key}', '{summary}', '{summary_vector}', '{description}', '{description_vector}', 
        '{issue_type}', '{status}', '{status_category}', '{project}', '{assignee}', '{reporter}', '{created}', 
        '{updated}', {time_spent_seconds}, '{url}');
        """,
        "insert_jira_bug": """
        INSERT INTO jira_bug (key, summary, summary_vector, description, description_vector, issue_type,
        status, status_category, project, assignee, reporter, created, updated, time_spent_seconds, url)
        VALUES ('{key}', '{summary}', '{summary_vector}', '{description}', '{description_vector}', '{issue_type}', 
        '{status}', '{status_category}', '{project}', '{assignee}', '{reporter}', '{created}', '{updated}', 
        {time_spent_seconds}, '{url}');
        """,
        # ===== INDEX CREATION ==================================
        "issue_exists": """
        SELECT EXISTS(
            SELECT 1 FROM jira_issue WHERE key = '{key}'
            UNION ALL
            SELECT 1 FROM jira_bug WHERE key = '{key}'
            UNION ALL
            SELECT 1 FROM jira_task WHERE key = '{key}'
        );
        """,
    }

    @staticmethod
    def get_sql(query_name, **params):
        """
        Retrieves and formats a SQL query template by substituting parameters into the template.
        Returns the formatted SQL query string.
        Raises:
            ValueError: If the query name is not found in the SQL_TEMPLATES dictionary.
        """
        if query_name in QueryStore.SQL_TEMPLATES:
            return QueryStore.SQL_TEMPLATES[query_name].format(**params)
        raise ValueError(f"Query '{query_name}' not found in QueryStore.")
