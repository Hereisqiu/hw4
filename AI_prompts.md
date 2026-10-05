# AI Prompts — Homework 4: Campus Customs

This file records the prompts I typed to my vibe coder (Claude Code), one section per problem.

## Problem 1: Vibe coder prompts

**Prompt:**
> Create `AI_prompts.md` at the beginning of the assignment and keep it updated as you work. This file should record the prompts I type to my vibe coder. All prompts I provide will be in my own words. Create one section for each problem, including the problem number and its original title, at least one prompt I typed, and any follow-up prompt I needed, along with one sentence explaining what was missing after the first attempt.

**Follow-up:** None needed.

## Problem 2: Analyze the database

**Prompt:**
> Inspect data/campus_customs.db to understand each table and its fields, including at least catalogue, inventory, and users. Create output/harness.md. List each table and its fields, with one short sentence per field explaining its purpose for the shop or chatbot. Expand this file in later problems to document models, tools, safety, and specifications.

**Follow-up:** None needed.

## Problem 3: Build the Campus Customs website

**Prompt:**
> Build a React + Vite + TypeScript frontend for Campus Customs with a top navigation bar linking to Home, Products, About Us, Log in, and Create account. Use yalebulldogblue.com to guide the tone and content of Home and About Us, but write original wording. On Products, display cards with catalogue images using the database image paths, plus each product's name, price, and short description. Clicking a card should open a dedicated product page with a large image on one side and full product details on the other, including description, price, and sizes and stock when available. Add a chat interface in the bottom-right corner. A floating panel with a placeholder for a future backend call is sufficient. You may start a simple FastAPI app in backend/main.py to serve products and images from the database.

**Follow-up:** None needed.

## Problem 4: Create account and login

**Prompt:**
> Build a standard account registration and login flow. Create account: first name, last name, email, and password, optionally a confirm-password field. Log in: email and password. Save new accounts in the users table. Securely hash passwords rather than storing readable passwords, and prevent people or AI from accessing them. Use the existing test account (test@campuscustoms.yale.edu / password) to verify login. Confirm that both the test user and a newly created account can log in successfully. Update output/harness.md to explain how authentication works, what user information is stored, and how passwords are protected.

**Follow-up:** None needed.

## Problem 5: PydanticAI agent backend

**Prompt:**
> Build a PydanticAI shop chatbot behind FastAPI and connect it to the frontend chat widget. Put the API app in backend/main.py and organize the agent into backend/prompts/prompt.md (system prompt), backend/agent.py (agent setup and wiring), backend/tools.py (tools the agent can call), and backend/models.py (Pydantic / PydanticAI structured types). In main.py, add a chat route that receives website messages and returns agent replies. Configure your AI model API key. Include Campus Customs' voice and basic safety rules in prompts/prompt.md. Update output/harness.md to explain how the frontend communicates with FastAPI and how the agent loads its prompt file and model. Ensure the backend runs from the backend/ folder with `uvicorn main:app --reload --port 8000`.

**Follow-up:** None needed.

## Problem 6: Tools: product info and stock

**Prompt:**
> Add agent tools that retrieve product descriptions, prices, and stock quantities from campus_customs.db, including stock by size when requested. The agent must use database results for prices and quantities and never invent them. It should clearly state when a requested size is out of stock. Expand prompts/prompt.md to instruct the agent to call these tools for price and stock questions. Add or update tool return types in models.py. In output/harness.md, list each tool and explain which model fields you selected for lookup results and why.

**Follow-up:** None needed.

## Problem 7: Chat search that updates the page

**Prompt:**
> When a customer asks about a product category, such as "What hoodies do you have?", have the agent search the catalogue and return structured product matches through the API. The frontend should dynamically display matching product cards with an image, name, price, and short description. Every card, including those displayed through chat search, must open the product detail page from Problem 3 when clicked, showing a large image and full product information. Update prompts/prompt.md and output/harness.md to explain how search results pass from the agent through the API to the page.

**Follow-up:** None needed.

## Problem 8: Customer memory

**Prompt:**
> For logged-in shoppers, save chat history in an appropriate database table and reload it when they return. Give the agent access to the shopper's name and email through agent dependencies, tools, or another clear approach. Pass enough page context for the agent to identify the current product when a shopper asks something like "Do you have this in pink?" You can include the product code in the agent context. Guests must still be able to chat, but their history does not need to persist. Document in output/harness.md how chat history is stored, which customer fields the agent sees, and how page context is passed.

**Follow-up:** None needed.

## Problem 9: Usability improvements

**Prompt:**
> Choose and implement four improvements: two frontend improvements that make the site more attractive and easier to use, and two agent/backend improvements that improve response quality, accuracy, or safety, add useful tools, or reduce runtime or cost. Write output/usability.md explaining for each improvement what you added, why, and how it benefits Campus Customs shoppers or the business. Ensure all four improvements work in the running app.

**Follow-up:** None needed.

## Problem 10: Style the website

**Prompt:**
> Give the site a creative, attractive, and easy-to-navigate design that feels like a real Campus Customs storefront. Consider fonts, colors, visual hierarchy, motion, product presentation, and the chat experience. Imaginative and innovative design earns more points. Write a brief, concrete explanation in output/design.md describing what you changed, why, and exactly how those changes should encourage customers to stay and buy.

**Follow-up:** None needed.

## Problem 11: Site testing (app check)

**Prompt:**
> Test the running website and document the results in output/app_check.html, which must open by double-clicking. Include clear screenshots and short captions showing: chat retrieving an item's inventory level and accurate stock/price information from the database; dynamic product cards appearing after a category question, such as asking about hoodies; and one usability feature implemented in Problem 9. Give each check a heading, screenshot, and one or two sentences explaining what it proves. Save screenshots in output/app_check_images/ and reference them in the HTML using relative paths.

**Follow-up:** None needed.

## Problem 12: Audit trail, safety, finish harness

**Prompt:**
> Maintain an append-only output/audit_trail.json recording agent-loop activity including items like time, tool name, short arguments/results, and reason for stopping. Preserve existing entries between runs. Develop safety rules for the agent and add them to prompts/prompt.md. Complete output/harness.md so it clearly explains the fields in models.py and the reasons I chose them, tools and agent abilities, safety rules, and specifications, including loop limits, result caps, models used, and how to run the frontend and backend.

**Follow-up:** None needed.

## Problem 13: Push to GitHub and submit the URL

**Prompt:**
> Place the project in a folder named hw4 and push it to a public GitHub repository. Use .gitignore to exclude the real .env, campus_customs.db, and product images, and include .env.example with placeholders only. Follow the expected file layout and keep the agent in four files under backend/: prompts/prompt.md, agent.py, tools.py, and models.py. In README.md, explain where to place the data pack and how to run the frontend and backend afterward.

**Follow-up:** None needed.
