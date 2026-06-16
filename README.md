# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for loading the data
├── planning.md                # Your planning template — fill this out first
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

---

## Reflection

### Tool Inventory

#### Tool 1: `search_listings`
**Signature:** `search_listings(description: str, size: str | None = None, max_price: float | None = None) -> list[dict]`

**Inputs:**
- `description` (str): Keywords describing the clothing item (e.g. `"vintage graphic tee"`). Required.
- `size` (str | None): Size string to filter by (e.g. `"M"`, `"W30 L30"`). Case-insensitive substring match — `"M"` matches `"S/M"`. Optional, defaults to `None` (no size filter).
- `max_price` (float | None): Maximum price in dollars, inclusive. Optional, defaults to `None` (no price filter).

**Output:** A `list[dict]` of matching listing dicts sorted by relevance score, highest first. Each dict contains: `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand`, `platform`. Returns an empty list if nothing matches — does not raise an exception.

**Purpose:** Filters the mock listings dataset by price and size, then ranks remaining items by how many description keywords appear across their title, description, category, style tags, colors, and brand fields.

---

#### Tool 2: `suggest_outfit`
**Signature:** `suggest_outfit(new_item: dict, wardrobe: dict) -> str`

**Inputs:**
- `new_item` (dict): A listing dict as returned by `search_listings` — must include `title`, `category`, `size`, `condition`, `price`, `platform`, `style_tags`, and `colors`.
- `wardrobe` (dict): A wardrobe dict with an `"items"` key containing a list of wardrobe item dicts. Can be empty — handled gracefully.

**Output:** A non-empty string containing 1–2 outfit suggestions. If the wardrobe is empty, the string contains general styling advice for the item rather than specific pairings.

**Purpose:** Calls the Groq LLM (`llama-3.3-70b-versatile`) with either a wardrobe-specific pairing prompt or a general styling prompt depending on whether the wardrobe is populated. Returns the raw LLM response.

---

#### Tool 3: `create_fit_card`
**Signature:** `create_fit_card(outfit: str, new_item: dict) -> str`

**Inputs:**
- `outfit` (str): The outfit suggestion string returned by `suggest_outfit`. Must be a non-empty, non-whitespace string.
- `new_item` (dict): A listing dict — uses `title`, `price`, and `platform` to anchor the caption.

**Output:** A 2–4 sentence string styled as a casual Instagram/TikTok caption. If `outfit` is empty or whitespace-only, returns the error string `"Error: Cannot generate a fit card without valid outfit details."` instead of raising an exception.

**Purpose:** Calls the Groq LLM at `temperature=1.0` (higher than the other tools) to generate a caption that mentions the item name, price, and platform naturally once each, captures the outfit vibe in specific terms, and sounds authentic rather than product-description-like.

---

### How the Planning Loop Works

`run_agent()` in `agent.py` executes a strictly sequential, non-iterative loop with one conditional branch that can trigger an early exit.

**Step 1 — Query parsing:** `_parse_query()` sends the raw user query to the LLM and asks it to extract three fields — `description` (str), `size` (str or null), and `max_price` (float or null) — as a JSON object. The result is stored in `session["parsed"]`. This LLM call uses `temperature=0` so the extraction is deterministic.

**Step 2 — Search with conditional exit:** `search_listings()` is called with the three parsed values. The result list is stored in `session["search_results"]`. The loop then checks `if not results` — if the list is empty, it immediately sets `session["error"]` to a human-readable message (e.g. `"No listings found matching 'designer ballgown' size XXS under $5.00. Try loosening your price or size constraints."`) and returns the session early. Steps 3–5 are never reached.

**Step 3 — Item selection:** If results exist, `results[0]` (the highest-relevance-scored item) is stored in `session["selected_item"]`. No branching here — the search tool already sorted by relevance.

**Step 4 — Outfit suggestion:** `suggest_outfit()` is called with `session["selected_item"]` and the `wardrobe` argument. The returned string is stored in `session["outfit_suggestion"]`. The empty-wardrobe branch lives inside the tool itself, not in the planning loop.

**Step 5 — Fit card generation:** `create_fit_card()` is called with `session["outfit_suggestion"]` and `session["selected_item"]`. The result is stored in `session["fit_card"]` and the session is returned.

The loop never re-calls any tool or prompts the LLM for a second opinion. The only decision it makes is after Step 2: proceed or exit early.

---

### State Management Approach

All state lives in a single mutable dict initialized by `_new_session()` at the top of `run_agent()`. The dict has seven keys:

| Key | Type | Set at | Used by |
|-----|------|--------|---------|
| `query` | str | init | `_parse_query` |
| `parsed` | dict | Step 2 | Step 3 (search args) |
| `search_results` | list[dict] | Step 3 | Step 4 (item selection) |
| `selected_item` | dict | Step 4 | Steps 5 and 6, plus the UI |
| `wardrobe` | dict | init | Step 5 |
| `outfit_suggestion` | str | Step 5 | Step 6 and the UI |
| `fit_card` | str | Step 6 | the UI |
| `error` | str or None | Step 3 (on failure) | the UI and early return guard |

Each tool receives its inputs as direct function arguments assembled from the session at the point of the call — tools do not read from the session dict directly. For example, `suggest_outfit(session["selected_item"], wardrobe)` extracts the value first, then passes it as a positional argument. This means if the session value were ever wrong, the bug would be caught at the call site rather than silently inside the tool.

---

### Error Handling Strategy

**`search_listings` — no matching results:**
The tool itself returns an empty list (never raises). The planning loop checks for this immediately after the call: `if not results`. On a test with `"designer ballgown size XXS under $5"`, the LLM parsed `size="XXS"` and `max_price=5.0`, the tool found zero listings passing both filters, and the loop set `session["error"] = "No listings found matching 'designer ballgown' size XXS under $5.00..."` and returned — `selected_item`, `outfit_suggestion`, and `fit_card` all remained `None`. The Gradio UI surfaces this error string in the first panel with the other two panels left empty.

**`suggest_outfit` — empty wardrobe:**
The tool checks `if not items` before building its prompt. When called with `get_empty_wardrobe()`, it switches to a general styling advice prompt instead of a wardrobe-specific one. The planning loop sees a non-empty string either way and continues normally — it never needs to check for this case itself.

**`create_fit_card` — empty or whitespace-only outfit string:**
The tool opens with `if not outfit or not outfit.strip()` and returns `"Error: Cannot generate a fit card without valid outfit details."` as a plain string. This means the planning loop and UI always receive a string, never an exception, even if `suggest_outfit` somehow returned blank output upstream.

---

### Spec Reflection

**One way the spec helped:** Defining the exact session dict keys and their types in the State Management section of planning.md before writing any code made `run_agent()` straightforward to implement. Because I had already decided what `selected_item`, `outfit_suggestion`, and `fit_card` would hold and when each would be populated, the loop was essentially an execution of the diagram rather than a design exercise. Without that pre-work, the state handoff between tools would have required significant back-and-forth debugging.

**One way the implementation diverged:** The planning.md spec defined `suggest_outfit`'s return value as "a list of multiple clothing combinations" and described `create_fit_card`'s `outfit` parameter as a `dict`. In the actual implementation, `suggest_outfit` returns a plain `str` (the LLM's raw text response) and `create_fit_card` accepts that same `str` directly. The spec was written with a structured data model in mind, but once I was building against the Groq API it became clear that parsing the LLM's outfit response into a structured dict would add fragile extraction logic with no real benefit — the caption prompt works better with the full natural language text anyway. The function signature was changed to match what actually flows through the system.

---

### AI Usage

**Instance 1 — Implementing `search_listings` with keyword scoring:**
I gave Claude the Tool 1 spec from planning.md and the function stub with the five numbered TODO steps. I directed it to implement scoring as keyword overlap — counting how many words from `description` appeared across the listing's title, description, category, style_tags, colors, and brand fields. Claude generated the filter loop and the `score()` inner function correctly, but I overrode the model it initially defaulted to for the LLM call (it added an unnecessary LLM call for scoring — I removed it entirely, since pure keyword overlap on the dataset was sufficient and deterministic without an API call).

**Instance 2 — Adding `dispatch_tool` and structured console logging:**
I directed Claude to add demo-friendly console output to `agent.py` following a specific pattern I provided — `→ Tool call: name(args)` before each call and `← Result: ...` (truncated) after, with session state snapshots between steps. I also asked for `━━━` section headers to separate each step visually. Claude implemented the pattern correctly but initially printed the full wardrobe dict inside the session snapshot, which flooded the console during demos. I revised `_log_session()` to exclude the `"wardrobe"` key from the printout, keeping the output readable.