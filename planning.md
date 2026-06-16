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

---

## State Management

**How does information from one tool get passed to the next?**
<!-- Describe how your agent stores and accesses state within a session. What data is tracked? How is it passed between tool calls? -->

---

## Error Handling

For each tool, describe the specific failure mode you're handling and what the agent does in response.

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| search_listings | No results match the query | |
| suggest_outfit | Wardrobe is empty | |
| create_fit_card | Outfit input is missing or incomplete | |

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

**Milestone 4 — Planning loop and state management:**

---

## A Complete Interaction (Step by Step)

Write out what a full user interaction looks like from start to finish — tool call by tool call. Use a specific example query.

**Example user query:** "I'm looking for a vintage graphic tee under $30. I mostly wear baggy jeans and chunky sneakers. What's out there and how would I style it?"

**Step 1:**
<!-- What does the agent do first? Which tool is called? With what input? -->

**Step 2:**
<!-- What happens next? What was returned from step 1? What tool is called now? -->

**Step 3:**
<!-- Continue until the full interaction is complete -->

**Final output to user:**
<!-- What does the user actually see at the end? -->
