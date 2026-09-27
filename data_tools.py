# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 22:08:03 2026

@author: imara
Description: Data analysis tools used by the AI agent.

Provides safe, read-only SQL execution against Pandas
DataFrames using DuckDB.
"""

import duckdb
import re


def run_sql(df, sql):

    sql_clean = sql.strip()

    # Only allow analytical queries
    if not sql_clean.lower().startswith(("select", "with")):
        raise ValueError("Only SELECT queries are allowed.")

    forbidden = r"\b(insert|update|delete|drop|create|alter|copy|attach|install|load|pragma)\b"

    if re.search(forbidden, sql_clean, flags=re.IGNORECASE):
        raise ValueError("Unsafe SQL operation detected.")

    con = duckdb.connect(database=":memory:")

    con.register("data", df)

    result = con.execute(sql_clean).fetchdf()

    con.close()

    return result