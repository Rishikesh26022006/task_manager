import os
import json
import time
import requests


# our own error type, so the route knows what status code to send back
class AIError(Exception):
    def __init__(self, message, status_code=502):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def generate_description(title):
    api_key = os.getenv("GEMINI_API_KEY")
    primary_model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    backup_model = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash-lite")

    # 1. check the key is set
    if not api_key or api_key == "your_gemini_api_key_here":
        raise AIError("AI is not configured. Set GEMINI_API_KEY in the .env file", 503)

    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    # 2. the instruction we send to the AI
    prompt = (
        "Write a clear and short task description (2 to 3 sentences) for a task titled: "
        + title
        + '. Reply only in JSON in this format: {"description": "your text here"}'
    )

    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseMimeType": "application/json"},
    }

    # 3. call the AI service: try the main model, then the backup model
    models_to_try = [primary_model]
    if backup_model and backup_model != primary_model:
        models_to_try.append(backup_model)

    response = None
    last_problem = None

    for model in models_to_try:
        url = "https://generativelanguage.googleapis.com/v1beta/models/" + model + ":generateContent"

        # try each model up to 2 times
        for attempt in range(2):
            try:
                response = requests.post(url, headers=headers, json=body, timeout=30)
            except requests.exceptions.Timeout:
                response = None
                last_problem = "timeout"
                break
            except requests.exceptions.RequestException as error:
                print("Gemini connection error:", error)
                response = None
                last_problem = "network"
                break

            if response.status_code == 200:
                break

            last_problem = response.status_code
            print("Gemini error:", model, response.status_code, response.text[:200])

            # Google is busy: wait 2 seconds and try the same model again
            if response.status_code in (500, 503) and attempt == 0:
                time.sleep(2)
                continue

            break

        # this model worked, so stop trying others
        if response is not None and response.status_code == 200:
            break

    # 4. if no model worked, send the right error back
    if response is None or response.status_code != 200:
        if last_problem == "timeout":
            raise AIError("AI service took too long to respond", 504)
        if last_problem == "network":
            raise AIError("Could not reach the AI service", 502)
        if last_problem == 429:
            raise AIError("AI usage limit reached, please try again later", 429)
        if last_problem in (500, 503):
            raise AIError("AI service is busy right now, please try again in a minute", 503)
        raise AIError("AI service returned an error (check API key and model name)", 502)

    # 5. read the answer out of the response (join all text parts)
    try:
        data = response.json()
        parts = data["candidates"][0]["content"]["parts"]
        text = ""
        for part in parts:
            if "text" in part:
                text = text + part["text"]
    except (ValueError, KeyError, IndexError, TypeError):
        print("Gemini unexpected response:", response.text[:300])
        raise AIError("AI returned an unexpected response", 502)

    # remove ```json fences if the AI added them
    text = text.strip()
    if text.startswith("```"):
        text = text.replace("```json", "").replace("```", "").strip()

    # 6. check the answer has the structure we asked for
    try:
        result = json.loads(text)
    except ValueError:
        print("Gemini answer was not JSON:", text[:300])
        raise AIError("AI did not return valid JSON", 502)

    if not isinstance(result, dict):
        raise AIError("AI response has the wrong format", 502)

    description = result.get("description")

    if not isinstance(description, str) or not description.strip():
        raise AIError("AI response did not contain a description", 502)

    return description.strip()