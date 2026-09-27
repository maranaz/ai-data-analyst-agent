# -*- coding: utf-8 -*-
"""
Created on Fri Sep 25 23:05:56 2026

@author: imara
"""

import os
import json

from dotenv import load_dotenv
from google import genai

from data_tools import run_sql


# Load GEMINI_API_KEY from .env
load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# Tell Gemini that this function exists
RUN_SQL_TOOL = {
    "type": "function",
    "name": "run_sql",
    "description": (
        "Runs a read-only DuckDB SQL query against the uploaded dataset. "
        "The table is named data. Use this tool whenever calculations, "
        "filtering, grouping, comparisons or numerical analysis are required."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "sql": {
                "type": "string",
                "description": (
                    "A DuckDB SELECT query. "
                    "The uploaded dataset table is called data."
                )
            }
        },
        "required": ["sql"]
    }
}


def ask_agent(question, df):

    # Give Gemini the actual dataset structure
    schema = "\n".join(
        f"- {column}: {dtype}"
        for column, dtype in df.dtypes.items()
    )

    prompt = f"""
You are a careful data analyst.

The user uploaded a dataset.

The DuckDB table name is:

data

Dataset columns:

{schema}

Rules:
- Use run_sql when answering questions about the data.
- Never invent numbers.
- Use DuckDB-compatible SQL.
- Only generate SELECT or WITH queries.
- Base conclusions on query results.
- Keep the final answer concise.

User question:

{question}
"""

    # Ask Gemini what it wants to do
    interaction = client.interactions.create(
        model="gemini-3.8-flash",
        input=prompt,
        tools=[RUN_SQL_TOOL]
    )

    # Look for a tool call
    for step in interaction.steps:

        if step.type == "function_call" and step.name == "run_sql":

            arguments = step.arguments

            # Depending on SDK response, arguments may already be a dict
            if isinstance(arguments, str):
                arguments = json.loads(arguments)

            sql = arguments["sql"]

            # OUR Python code actually executes the query
            result = run_sql(
                df,
                sql
            )

            # Convert result to something Gemini can read
            result_json = result.to_json(
                orient="records"
            )

            # Send the tool result back to Gemini
            final_interaction = client.interactions.create(
                model="gemini-3.8-flash",
                previous_interaction_id=interaction.id,
                tools=[RUN_SQL_TOOL],
                input=[
                    {
                        "type": "function_result",
                        "name": step.name,
                        "call_id": step.id,
                        "result": [
                            {
                                "type": "text",
                                "text": result_json
                            }
                        ]
                    }
                ]
            )

            return (
                final_interaction.output_text,
                sql,
                result
            )

    # Gemini chose not to call SQL
    return (
        interaction.output_text,
        None,
        None
    )