from groq import Groq
import json
import time
from config import GROQ_API_KEY, GROQ_MODEL, MAX_TOKENS, LLM_RETRY_ATTEMPTS


# Initialise Groq client once at module level
client = Groq(api_key=GROQ_API_KEY)


def call_llm(prompt: str) -> dict:
    """
    Send a prompt to Groq (Llama 3) and return the parsed JSON response.
    Retries up to LLM_RETRY_ATTEMPTS times if the response is not valid JSON.
    """
    last_error = None

    for attempt in range(1, LLM_RETRY_ATTEMPTS + 1):
        try:
            print(f"[llm_client] Calling Groq... (attempt {attempt}/{LLM_RETRY_ATTEMPTS})")

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a budget travel planner. Always respond with valid JSON only. No explanation, no markdown, no extra text."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=MAX_TOKENS,
                temperature=0.7,
            )

            raw_text = response.choices[0].message.content.strip()

            # Strip markdown code blocks if present
            if raw_text.startswith("```"):
                raw_text = raw_text.split("```")[1]
                if raw_text.startswith("json"):
                    raw_text = raw_text[4:]
                raw_text = raw_text.strip()

            itinerary = json.loads(raw_text)
            print(f"[llm_client] Success on attempt {attempt}")
            return itinerary

        except json.JSONDecodeError as e:
            last_error = e
            print(f"[llm_client] JSON parse failed on attempt {attempt}: {e}")
            if attempt < LLM_RETRY_ATTEMPTS:
                print(f"[llm_client] Retrying in 2 seconds...")
                time.sleep(2)

        except Exception as e:
            raise Exception(f"Groq API error: {e}")

    raise ValueError(
        f"Groq returned invalid JSON after {LLM_RETRY_ATTEMPTS} attempts. "
        f"Last error: {last_error}"
    )


def call_llm_multi_city(prompts: list[str]) -> list[dict]:
    """
    Call Groq for each city in a multi-city trip, one at a time.
    """
    results = []
    for i, prompt in enumerate(prompts, start=1):
        print(f"\n[llm_client] Generating itinerary for city {i} of {len(prompts)}...")
        result = call_llm(prompt)
        results.append(result)
        if i < len(prompts):
            time.sleep(1)
    return results


def call_chat_llm(messages: list[dict]) -> str:
    """
    Send messages representing a chat history to Groq and return the text response.
    """
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Sorry, I encountered an error: {e}"



# ── Quick test ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    from budget_allocator import allocate_budget
    from geocoder import get_coordinates
    from prompt_builder import build_prompt

    print("=" * 55)
    print("LIVE TEST — calling Groq API for a Goa itinerary")
    print("=" * 55)

    allocation  = allocate_budget(total_budget=12000, num_days=3, group_size=4)
    coordinates = get_coordinates("Goa, India")

    prompt = build_prompt(
        city="Goa",
        days=3,
        group_size=4,
        month="December",
        travel_style="Adventure",
        allocation=allocation,
        coordinates=coordinates,
    )

    itinerary = call_llm(prompt)

    print("\nParsed itinerary JSON:\n")
    print(json.dumps(itinerary, indent=2, ensure_ascii=False))