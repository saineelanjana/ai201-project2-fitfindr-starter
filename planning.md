# FitFindr — planning.md

> Complete this document before writing any implementation code.
> Your spec and agent diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Your planning.md will be reviewed as part of your submission.
> Update it before starting any stretch features.

---

## Tools

List every tool your agent will use. For each tool, fill in all four fields.
You must have at least 3 tools. The three required tools are listed — add any additional tools below them.

### Tool 1: search_listings

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`This tool is used to search the mock listings dataset and return matching items for what the user has described.`

**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `description` (str): `This represents a description of the clothing item user is looking for`
- `size` (str): `This represents the size of clothing item the user is looking for and can be S, M, L, XL, or even a number or other formats`
- `max_price` (float): `This is the maximum price of a clothing item a user is willing to pay for`

**What it returns:**
<!-- Describe the return value — what fields does a result contain? -->
`This tool will return a list of dicts of clothing items. Each clothing item will have the following fields`

`{
    "id": "lst_001",
    "title": "Vintage Levi's 501 Jeans — Medium Wash",
    "description": "Classic 501s in a perfect medium wash. Some light fading at the knees which adds to the vintage look. No rips or stains.",
    "category": "bottoms",
    "style_tags": ["vintage", "classic", "denim", "streetwear"],
    "size": "W30 L30",
    "condition": "good",
    "price": 38.00,
    "colors": ["blue", "indigo"],
    "brand": "Levi's",
    "platform": "depop"
}`

**What happens if it fails or returns nothing:**
<!-- What should the agent do if no listings match? -->
`If there are no matching listings, the agent should return a message to the user saying "There are no listings that match 'description' of size 'size' under $'max_price'"`
---

### Tool 2: suggest_outfit

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`This tool will take a users wardrobe in addition to a new clothing item and suggest one or more complete outfit combinations`
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `new_item` (dict): `It represents a clothing item that can be returned from search_listings with multiple sub fields`
- `wardrobe` (dict): `It represents the user's wardrobe with multiple pices of clothing`

**What it returns:**
<!-- Describe the return value -->
`It will return a list of multiple clothing combinations that each makeup a full outfit from tops, bottoms, outerwear, shoes, and accessories.`
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the wardrobe is empty or no outfit can be suggested? -->
`If the wardrobe is empty, return a message to the user that the current wardrobe is empty aqnd the new item cannot be paired with anything. Suggest adding items to their wardrobe to expand it first`
---

### Tool 3: create_fit_card

**What it does:**
<!-- Describe what this tool does in 1–2 sentences -->
`This tool generates a short, shareable description of a complete outfit — the kind of thing someone would caption an Instagram post with.`
**Input parameters:**
<!-- List each parameter, its type, and what it represents -->
- `outfit` (dict): `It represents a complete outfit combination that was created by the suggest_outfit tool`
- `new_item` (dict): `It represents a clothing item that can be returned from search_listings with multiple sub fields`

**What it returns:**
<!-- Describe the return value -->
`It should return a string value equivalent to a caption describing the complete outfit and emphasising the new item incorporated into the outfit`
**What happens if it fails or returns nothing:**
<!-- What should the agent do if the outfit data is incomplete? -->
`If outfit data is incomplete, or tool call fails/returns nothing, return a message to the user informing them of that. Try to create a short description with the given clolothing items anyways `
---

### Additional Tools (if any)

<!-- Copy the block above for any tools beyond the required three -->

---

## Planning Loop

**How does your agent decide which tool to call next?**
<!-- Describe the logic your planning loop uses. What does it look at? What conditions change its behavior? How does it know when it's done? -->
```
Initial Trigger (Search): The loop begins by extracting the user's preferences (description, size, and max price) from the query and invoking search_listings().

First Conditional Branch (Results Evaluation):

If results is empty []: The loop sets an error message in the session state explaining that no matches were found, bypasses all subsequent tools, and returns early to prompt the user for adjusted constraints.

If results contains items: The loop stores the top result as session["selected_item"] = results[0] and proceeds.

Outfit Generation:
The loop passes session["selected_item"] and the user's wardrobe into suggest_outfit(). (Note: If the wardrobe is empty, internal tool logic gracefully falls back to general styling advice).

Second Conditional Branch (Outfit Evaluation):

If the outfit suggestion fails/is empty: The loop sets an error message in the session state and exits early.

If successful: The loop saves the response as session["outfit_suggestion"] and proceeds.

Caption Creation:
The loop invokes create_fit_card() using both session["outfit_suggestion"] and session["selected_item"].

Termination:

If create_fit_card returns an empty string: The loop catches the error message, saves it to the session, and exits.

If successful: The loop saves the final caption to session["fit_card"], marks the execution as complete, and returns the session state to the user interface.
```
---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->
```
The agent manages state across a multi-step workflow by using a centralized, mutable session dictionary. Because individual tool calls and LLM invocations are inherently stateless, this session dictionary acts as the agent's short-term memory, capturing the output of preceding tools and transforming them into inputs for subsequent ones.

The session state actively monitors and tracks the following key-value pairs throughout a single interaction lifecycle:

selected_item (dict): The top matching listing object returned by search_listings(), containing properties like title, price, size, and platform.
outfit_suggestion (str): The styling combination and advice generated by suggest_outfit().
fit_card (str): The final social-media-ready caption produced by create_fit_card().
error (str / None): A descriptive error message tracking exactly where a failure occurred if a tool path breaks or returns empty results.

From Search to Suggestion: After search_listings() executes successfully, the planning loop extracts the first listing element (results[0]) and assigns it to session["selected_item"]. When suggest_outfit() is called next, the loop pulls this exact dictionary from the session and feeds it into the tool along with the user's wardrobe data.

From Suggestion to Caption: Once suggest_outfit() returns its LLM-generated text, the loop commits it to session["outfit_suggestion"]. Finally, create_fit_card() accesses both session["outfit_suggestion"] and session["selected_item"] directly from the session store to build the final, context-aware caption.
```
---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | The planning loop immediately intercepts the empty list, sets a descriptive error message in the session state (e.g., "No listings found matching your criteria. Try loosening your price or size constraints."), bypasses all downstream tools, and performs an early return to display the advice to the user.|
| suggest_outfit | Wardrobe is empty | Instead of crashing, the tool's internal logic catches the empty wardrobe state and modifies its LLM prompt to request general, standalone styling advice (e.g., universal pairings, seasonal vibes, or silhouette rules) for the selected item, rather than cross-referencing specific wardrobe pieces|
| create_fit_card | Outfit input is missing or incomplete | The tool catches the invalid string input and returns a descriptive error string (e.g., "Error: Cannot generate a fit card without valid outfit details.") directly to the planning loop instead of throwing a Python exception, allowing the agent to exit cleanly.|

---

## Architecture

<!-- Draw a diagram of your agent showing how the components connect:
     User input → Planning Loop → Tools (search_listings, suggest_outfit, create_fit_card)
                                                                          ↕
                                                                   State / Session
     Show what triggers each tool, how state flows between them, and where error paths branch off.
     ASCII art, a Mermaid diagram (https://mermaid.js.org/syntax/flowchart.html), or an embedded
     sketch are all fine. You'll share this diagram with an AI tool when asking it to implement
     the planning loop and each individual tool. -->

```
graph TD
%% Define Elements
User([User Input]) --> |Query: item, size, max_price| Loop[Planning Loop]

    subgraph State Management [Centralized Session State Dictionary]
        Session[(session dict)]
    end

    subgraph Core Agent Tools
        T1[search_listings]
        T2[suggest_outfit]
        T3[create_fit_card]
    end

    %% Step 1: Search
    Loop -->|1. Invoke with query params| T1
    T1 -->|Returns results list| C1{Is list empty?}
    
    %% Step 1 Error Path
    C1 -->|Yes| E1[Set session error<br>Early Return to User]
    E1 -.->|Writes error| Session
    
    %% Step 1 Success Path
    C1 -->|No| S1[Set session selected_item = results 0]
    S1 -.->|Writes item dict| Session

    %% Step 2: Outfit Suggestion
    S1 -->|2. Invoke with selected_item & wardrobe| T2
    Session -.->|Reads selected_item & wardrobe| T2
    T2 -->|Returns suggestion text| C2{Is layout empty/missing?}
    
    %% Step 2 Error Path
    C2 -->|Yes| E2[Set session error<br>Early Return to User]
    E2 -.->|Writes error| Session
    
    %% Step 2 Success Path (Handles empty wardrobe fallback internally)
    C2 -->|No| S2[Set session outfit_suggestion]
    S2 -.->|Writes text string| Session

    %% Step 3: Caption Creation
    S2 -->|3. Invoke with outfit_suggestion & selected_item| T3
    Session -.->|Reads outfit_suggestion & selected_item| T3
    T3 -->|Returns fit card text| C3{Is return string empty?}
    
    %% Step 3 Error Path
    C3 -->|Yes| E3[Set session error<br>Clean Exit]
    E3 -.->|Writes error string| Session
    
    %% Step 3 Success Path
    C3 -->|No| S3[Set session fit_card]
    S3 -.->|Writes final caption| Session
    
    %% Final Output Flow
    S3 -->|4. Final Complete State| UI([Display App Panels])
    E1 --> UI
    E2 --> UI
    E3 --> UI

    %% Styling
    style Session fill:#f9f,stroke:#333,stroke-width:2px
    style Loop fill:#bbf,stroke:#333,stroke-width:2px
    style E1 fill:#fbb,stroke:#333,stroke-width:1px
    style E2 fill:#fbb,stroke:#333,stroke-width:1px
    style E3 fill:#fbb,stroke:#333,stroke-width:1px
```
---

## AI Tool Plan

<!-- For each part of the implementation below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, your agent diagram)
     - What you expect it to produce
     - How you'll verify the output matches your spec before moving on

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Tool 1 spec (inputs, return value, failure mode) and ask it to implement
     search_listings() using load_listings() from the data loader — then test it against 3 queries
     before trusting it" is a plan. -->

**Milestone 3 — Individual tool implementations:**
- I plan to use claude by giving it the tool blocks from planning.md as well as the functions and commments from tools.py. I will ask it to implement the functions and use load_listings() from data loader for search_listings(). I expect it to produce code for my tool functions in tool.py. I will verify by checking each tool is using all params passed in to filter and work through the logic. I will also run 3 queries and test the tools.

**Milestone 4 — Planning loop and state management:**
- I plan to give claude the planning loop, state management, and error handling blocks form planning.md as well as the functions and comments from agent.py. I will ask it to implement the run_agent() function and verify it has logic to call each of my tools. I will also test it by running 3 queries.
---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->
```
Agent Action: The planning loop parses the user's natural language input to extract key constraints (item description, sizing if provided, and maximum budget). It initializes the session state and triggers the first tool to find matching inventory.

Tool Called: search_listings(description="vintage graphic tee", size=None, max_price=30.0)

Output / State Change: The tool searches the database and returns a list of matching items.
Happy Path: It finds a match and returns [{"id": 102, "title": "Faded 90s Band Tee", "price": 22.0, "size": "M", "platform": "Depop", "condition": "Good"}]. The planning loop intercepts this list, extracts the first result, and saves it to the state as session["selected_item"].

Error Branch: If the database returns an empty list [], the loop writes an error message to session["error"] and terminates early.
```
**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->
```
Agent Action: Because an item was successfully found and stored in the session, the planning loop moves forward. It automatically pulls the newly discovered item data and the user's existing wardrobe data to generate a custom styling layout.

Tool Called: suggest_outfit(new_item=session["selected_item"], wardrobe=user_wardrobe)

Output / State Change: The tool feeds the item details and wardrobe items into the LLM.

Execution: The LLM returns a tailored advice string: "Pair this Faded 90s Band Tee with your baggy jeans and chunky sneakers. Throw an oversized flannel over it left unbuttoned to lean into that relaxed, vintage grunge aesthetic."

State Change: The planning loop commits this string directly to session["outfit_suggestion"]. (If the user's wardrobe had been empty, the tool's internal fallback would have generated general styling rules for graphic tees instead of crashing).
```
**Step 3:**
<!-- Continue until the full interaction is complete -->
```
Agent Action: With both the item details and the outfit styling plan locked into the session state, the planning loop triggers the final creative tool to package the results into an engaging output.

Tool Called: create_fit_card(outfit=session["outfit_suggestion"], new_item=session["selected_item"])

Output / State Change: The LLM uses the context to generate a short, high-energy, platform-ready caption.

Execution: It returns: "just grabbed this faded 90s band tee off depop for $22 and honestly it pairs perfectly with my baggy jeans agenda 🖤 full look in bio"

State Change: The loop saves this text to session["fit_card"]. If the input text had been missing or malformed, the tool would return a clean error string to save to the session instead of raising an exception.
```
**Final output to user:**
<!-- What does the user actually see at the end? -->
```
Agent Action: The planning loop verifies that the final tool executed successfully, marks the workflow as complete, and returns the entire session dictionary to the interface.

What the User Sees: The user interface (app.py) parses the final session state and populates three separate display panels simultaneously:

Found Item Panel: Faded 90s Band Tee — $22.00 on Depop (Good condition)

Styling Advice Panel: "Pair this Faded 90s Band Tee with your baggy jeans and chunky sneakers..."

Fit Card Panel: "just grabbed this faded 90s band tee off depop for $22..."
```