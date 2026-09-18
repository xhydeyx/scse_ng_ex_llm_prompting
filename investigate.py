## Import the necessary modules
import json
from ollama import chat
## Import the function from the module parse_data
from parse_data import load_items, get_unclaimed_items, save_result

## Build your prompt based on the description the user provides 
## and the items that are available in the lost-and-found database.
## The model must follow the rules listed in the README file
## The function should return the system prompt and the user prompt.
## You may need to use json.dumps() to convert the available_items list into a JSON string.

def build_prompt(description, available_items):
    system_prompt = """
You are a lost-and-found assistant. Your task is to match a user's description of a lost item with the available unclaimed items.
You must use ONLY the provided list of available items. Not all details need to match; a possible match can be based on partial information.
You must return ONLY a valid JSON object with exactly the following structure:
{
    "matches": ["ITEM_ID1", "ITEM_ID2", ...],
    "confidence": "LOW" | "MEDIUM" | "HIGH"
}
- "matches" contains a list of item IDs (as strings) that are possible matches.
- "confidence" is your confidence level: "LOW", "MEDIUM", or "HIGH".
- If there are no matches, "matches" must be an empty list.
Do not include any other text, markdown, or explanation outside the JSON.
"""
    items_json = json.dumps(available_items, indent=2)
    user_prompt = f"""
User's description: {description}

Available unclaimed items:
{items_json}

Return the JSON result.
"""
    return system_prompt, user_prompt
    
## Logic to ask Qwen for all the possible matches based on the system prompt and user prompt.
## The function should return the response from Qwen.
def ask_qwen(system_prompt, user_prompt):
    response = chat(
        model="qwen3:8b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.message.content

## Logic to parse the response from Qwen and return the result. 
## You may need to use json.loads() to convert the response string into a suitable Python data structure.
def parse_response(response_text):
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None
    
## Logic to validate the result returned by Qwen.
## It should check if the result is a dictionary, contains the keys "matches" and "confidence", and that the values are of the correct type.
## If everything is correct, then it should check if the item IDs in the "matches" list are valid IDs .
def validate_result(result, available_items):
    if not isinstance(result, dict):
        return False
    if "matches" not in result or "confidence" not in result:
        return False
    if not isinstance(result["matches"], list):
        return False
    if result["confidence"] not in ("LOW", "MEDIUM", "HIGH"):
        return False
    valid_ids = {item["id"] for item in available_items}
    for item_id in result["matches"]:
        if item_id not in valid_ids:
            return False
    return True

## Logic to display the matches found by Qwen in a user-friendly format.
## It should look something like this:
""" 
CAMPUS LOST-AND-FOUND ASSISTANT
==================================================

Describe the item you lost: I lost a black bag somewhere

Searching for possible matches...

MATCH RESULT
--------------------------------------------------
Confidence: MEDIUM

Possible matches:

ID: F101
Item: backpack
Color: black
Location: Library 2nd floor
Date found: 2026-09-15

Result saved to output/match_result.json
 """
## If no matches are found, it should display a message indicating that no matches were found, along with the empty list
def display_matches(result, available_items):
    print("\nMATCH RESULT")
    print("-" * 50)
    print(f"Confidence: {result['confidence']}")
    if result["matches"]:
        print("\nPossible matches:")
        items_by_id = {item["id"]: item for item in available_items}
        for item_id in result["matches"]:
            item = items_by_id.get(item_id)
            if item:
                print(f"\nID: {item['id']}")
                print(f"Item: {item['item']}")
                print(f"Color: {item['color']}")
                print(f"Location: {item['location']}")
                print(f"Date found: {item['date']}")
    else:
        print("\nNo matches found.")
    
## Control center for the entire program.
def main():
    print("CAMPUS LOST-AND-FOUND ASSISTANT")
    print("=" * 50)
    description = input("\nDescribe the item you lost: ").strip()
    if not description:
        print("Description cannot be empty.")
        return

    items = load_items("found_items.json")
    unclaimed = get_unclaimed_items(items)

    system_prompt, user_prompt = build_prompt(description, unclaimed)
    print("\nSearching for possible matches...")
    response_text = ask_qwen(system_prompt, user_prompt)

    result = parse_response(response_text)
    if not result or not validate_result(result, unclaimed):
        print("\nError: The model returned an invalid response.")
        result = {"matches": [], "confidence": "LOW"}

    display_matches(result, unclaimed)

    save_result(result, "output/match_result.json")
    print("\nResult saved to output/match_result.json")

if __name__ == "__main__":
    main()