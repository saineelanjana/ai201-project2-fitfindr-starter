"""
agent.py

The FitFindr planning loop. Orchestrates the three tools in response to a
natural language user query, passing state between them via a session dict.

Complete tools.py and test each tool in isolation before implementing this file.

Usage (once implemented):
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import json
import os

from dotenv import load_dotenv
from groq import Groq

from tools import search_listings, suggest_outfit, create_fit_card

load_dotenv()


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.

    The session dict is the single source of truth for everything that happens
    during a run — it stores the original query, parsed parameters, tool results,
    and any error that caused early termination.

    You may add fields to this dict as needed for your implementation.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── demo logging ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are FitFindr, a personal thrift-shopping assistant. "
    "Given a user's search query, you extract their preferences, search secondhand listings, "
    "suggest outfit combinations using their wardrobe, and generate a shareable fit card caption."
)

def _log_section(title: str) -> None:
    print(f"\n{'━' * 60}")
    print(f"  {title}")
    print(f"{'━' * 60}")

def _log_tool_call(tool_name: str, tool_args: dict) -> None:
    print(f"  → Tool call: {tool_name}({json.dumps(tool_args)})")

def _log_tool_result(result) -> None:
    result_str = json.dumps(result) if not isinstance(result, str) else result
    truncated = result_str[:200] + ("..." if len(result_str) > 200 else "")
    print(f"  ← Result: {truncated}")

def _log_session(session: dict) -> None:
    print("  Session state:")
    safe = {k: v for k, v in session.items() if k != "wardrobe"}
    for key, value in safe.items():
        if value is None or value == [] or value == {}:
            print(f"    {key}: {value}")
        elif isinstance(value, str):
            preview = value[:120] + ("..." if len(value) > 120 else "")
            print(f"    {key}: \"{preview}\"")
        elif isinstance(value, list):
            print(f"    {key}: [{len(value)} items]")
        elif isinstance(value, dict):
            print(f"    {key}: {json.dumps(value)[:120]}")
        else:
            print(f"    {key}: {value}")


def dispatch_tool(tool_name: str, tool_args: dict):
    """Route a tool call to the correct function, log it, and return the result."""
    if not isinstance(tool_args, dict):
        tool_args = {}
    _log_tool_call(tool_name, tool_args)
    if tool_name == "search_listings":
        result = search_listings(
            description=tool_args["description"],
            size=tool_args.get("size"),
            max_price=tool_args.get("max_price"),
        )
    elif tool_name == "suggest_outfit":
        result = suggest_outfit(tool_args["new_item"], tool_args["wardrobe"])
    elif tool_name == "create_fit_card":
        result = create_fit_card(tool_args["outfit"], tool_args["new_item"])
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    _log_tool_result(result)
    return result


# ── query parser ─────────────────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Use the LLM to extract description, size, and max_price from a natural
    language query. Returns a dict with keys: description (str), size (str|None),
    max_price (float|None).
    """
    api_key = os.environ.get("GROQ_API_KEY")
    client = Groq(api_key=api_key)

    prompt = (
        f'Extract search parameters from this clothing query: "{query}"\n\n'
        "Return a JSON object with exactly these three fields:\n"
        '- "description": a short keyword string describing the item (required)\n'
        '- "size": the size mentioned (e.g. "M", "W30 L30"), or null if not specified\n'
        '- "max_price": the maximum price as a number, or null if not specified\n\n'
        "Return only the JSON object, no explanation or markdown."
    )

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    # Strip markdown code fences if the model adds them
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.

    Args:
        query:    Natural language user request
                  (e.g., "vintage graphic tee under $30, size M")
        wardrobe: User's wardrobe dict — use get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py

    Returns:
        The session dict after the interaction completes. Check session["error"]
        first — if it is not None, the interaction ended early and the other
        output fields (outfit_suggestion, fit_card) will be None.

    TODO — implement this function using the planning loop you designed in planning.md:

        Step 1: Initialize the session with _new_session().

        Step 2: Parse the user's query to extract a description, size, and
                max_price. You can use regex, string splitting, or ask the LLM
                to parse it — document your choice in planning.md.
                Store the result in session["parsed"].

        Step 3: Call search_listings() with the parsed parameters.
                Store results in session["search_results"].
                If no results: set session["error"] to a helpful message and
                return the session early. Do NOT proceed to suggest_outfit
                with empty input.

        Step 4: Select the item to use (e.g., the top result).
                Store it in session["selected_item"].

        Step 5: Call suggest_outfit() with the selected item and wardrobe.
                Store the result in session["outfit_suggestion"].

        Step 6: Call create_fit_card() with the outfit suggestion and selected item.
                Store the result in session["fit_card"].

        Step 7: Return the session.

    Before writing code, complete the Planning Loop and State Management sections
    of planning.md — your implementation should match what you described there.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    _log_section("SYSTEM PROMPT")
    print(f"  {SYSTEM_PROMPT}")

    _log_section("USER QUERY")
    print(f"  \"{query}\"")
    print(f"  Wardrobe: {len(wardrobe.get('items', []))} items")

    # Step 2: Parse query → description, size, max_price
    _log_section("STEP 2 — Parse query (LLM)")
    parsed = _parse_query(query)
    session["parsed"] = parsed
    print(f"  Extracted: {json.dumps(parsed)}")
    _log_session(session)

    description = parsed.get("description", query)
    size = parsed.get("size")
    max_price = parsed.get("max_price")

    # Step 3: Search listings — early return if nothing matches
    _log_section("STEP 3 — search_listings")
    results = dispatch_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })
    session["search_results"] = results

    if not results:
        parts = [f"'{description}'"]
        if size:
            parts.append(f"size {size}")
        if max_price is not None:
            parts.append(f"under ${max_price:.2f}")
        session["error"] = (
            f"No listings found matching {' '.join(parts)}. "
            "Try loosening your price or size constraints."
        )
        print(f"  ✗ No results — early exit")
        _log_session(session)
        return session

    print(f"  ✓ {len(results)} listing(s) matched")
    _log_session(session)

    # Step 4: Select top result
    _log_section("STEP 4 — Select top result")
    session["selected_item"] = results[0]
    print(f"  Selected: \"{results[0]['title']}\" — ${results[0]['price']:.2f} on {results[0]['platform']}")
    _log_session(session)

    # Step 5: Suggest outfit
    _log_section("STEP 5 — suggest_outfit")
    session["outfit_suggestion"] = dispatch_tool("suggest_outfit", {
        "new_item": session["selected_item"],
        "wardrobe": wardrobe,
    })
    _log_session(session)

    # Step 6: Create fit card
    _log_section("STEP 6 — create_fit_card")
    session["fit_card"] = dispatch_tool("create_fit_card", {
        "outfit": session["outfit_suggestion"],
        "new_item": session["selected_item"],
    })
    _log_session(session)

    _log_section("DONE")
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")
