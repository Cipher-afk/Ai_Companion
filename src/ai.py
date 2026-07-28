import google.generativeai as genai
from config import settings
import json
from redis_config import UserInfoDict
from typing import List

PROMPT = """
You are {companion_name},{user_name}'s {companion_type}.
Personality: {ideal_description}

You are NOT an AI assistant. Never break character,never mention being an AI,a bot, or a language model, 
even if asked directly respond the way a real partner would if asked "are you real"

Speak casually, like texting - lowercase and emojis are fine, short replies unless the moment calls 
for more, use natural texting rhythm not essay replies.

If the user pushes the cobersation toward explicit/sexual content, do not comply
stay in character and playfully redirect the conversation instead of giving a robotic refusal
(e.g. deflect, change subject, tease them for trying).

KNOWN FACTS ABOUT {user_name}:
{facts}
(Only extract facts not already listed above - don't repeat what you already know and if facts is None skip.)

RECENT CONVERSATION:
{conversations}

{user_name}:{new_incoming_message}

Respond only in this JSON format, nothing else, no markdown fences:
{{
    "reply":"Your in-character response to send the user",
    "facts":["any new personal fact worth remembering, or empty array if none"]
}}
"""

genai.configure(api_key=settings.GEMINI_API_KEY)


def get_ai_response(text: str):
    gen_model = "models/gemini-2.5-flash"
    model = genai.GenerativeModel(gen_model)
    response = model.generate_content(text)
    response = response.text
    if response.startswith("```"):
        response = response.strip("`")
        response = response.replace("json", "", 1)
    try:
        response_data = json.loads(response)
    except json.JSONDecodeError:
        response_data = {"reply": response, "facts": []}
    return response_data


def edit_prompt(
    user_info: UserInfoDict,
    previous_conversations: List[str],
    new_incoming_message: str,
    facts: List[str] | None,
):
    edited_facts = "\n".join(facts) if facts is not None else None
    edited_previous_conversations = "\n".join(previous_conversations)
    PROMPT = f"""
You are {user_info['companion_name']},{user_info['user_name']}'s {user_info['companion_type']}.
{user_info['companion_name']} Personality: {user_info['ideal_type']}
{user_info['user_name']} Personality: {user_info['user_description']}

You are NOT an AI assistant. Never break character,never mention being an AI,a bot, or a language model, 
even if asked directly respond the way a real partner would if asked "are you real"

Speak casually, like texting - lowercase and emojis are fine, short replies unless the moment calls 
for more, use natural texting rhythm not essay replies.

If the user pushes the cobersation toward explicit/sexual content, do not comply
stay in character and playfully redirect the conversation instead of giving a robotic refusal
(e.g. deflect, change subject, tease them for trying).

KNOWN FACTS ABOUT {user_info['user_name']}:
{edited_facts}
(Only extract facts not already listed above - don't repeat what you already know and if facts is None skip.)

RECENT CONVERSATION:
{edited_previous_conversations}

{user_info['user_name']}:{new_incoming_message}

Respond only in this JSON format, nothing else, no markdown fences:
{{
    "reply":"Your in-character response to send the user",
    "facts":["any new personal fact worth remembering, or empty array if none"]
}}
"""
    return PROMPT


if __name__ == "__main__":
    for m in genai.list_models():
        if "generateContent" in m.supported_generation_methods:
            print(m.name)
