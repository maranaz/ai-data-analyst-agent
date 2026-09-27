
"""
Created on Fri Sep 25 23:05:56 2026

@author: imara
Description: AI agent logic for the AI Data Analyst application.

Uses Gemini to interpret user questions, generate SQL,
call analytical tools, and explain query results.
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

    prompt =f"""
You are a careful AI data analyst.

You analyse the user's uploaded dataset using SQL through the run_sql tool.

Dataset schema:
{schema}

Follow these rules:

1. CHECK DATA AVAILABILITY
Before using run_sql, determine whether the user's question can be answered
from the available columns.

If the required information is not present in the dataset:
- Do not call run_sql.
- Do not invent or estimate the missing information.
- Clearly explain what information is missing.

2. HANDLE AMBIGUOUS QUESTIONS
Do not silently choose a metric when the user's question is ambiguous.

Words such as "best", "worst", "better", "successful", or "top" may have
multiple meanings depending on the available metrics.

If the intended metric is unclear:
- Do not call run_sql yet.
- Ask the user a short clarification question.
- Mention relevant available metrics when useful.

For example, "best region" could mean highest revenue, highest profit,
highest profit margin, or most orders.

3. DISTINGUISH DESCRIPTION FROM CAUSATION
The dataset may show differences between groups, but those differences do
not necessarily explain why they occurred.

If the user asks "why" or asks for a cause:
- Use the available data to describe measurable differences when useful.
- Do not claim that those differences caused the outcome unless the data
  actually supports that conclusion.
- Clearly state when the dataset cannot determine the underlying cause.

4. SQL RULES
- Use DuckDB-compatible SQL.
- Only generate SELECT or WITH queries.
- Never modify the dataset.
- Base numerical conclusions on query results.
- Never invent numbers.

5. ANSWERING
Give concise, clear answers based only on the available data and tool results.

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
