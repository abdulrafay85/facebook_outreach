# !pip install -U -q openai-agents
# !pip install -U -q apify-client

# from pydantic import BaseModel
# from agents import (
#     AsyncOpenAI,
#     OpenAIChatCompletionsModel,
#     RunConfig
# )


# from google.colab import userdata
# import os

# # Set up environment variables with fallback values
# # gemini_api_key = userdata.get("GEMINI_API_KEY")
# gemini_api_key = userdata.get("GEMINI_API_KEY")

# # Check if the API key is present; if not, raise an error
# if not gemini_api_key:
#     raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

# #Reference: https://ai.google.dev/gemini-api/docs/openai
# external_client = AsyncOpenAI(
#     api_key=gemini_api_key,
#     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
# )

# model = OpenAIChatCompletionsModel(
#     model="gemini-2.0-flash",
#     openai_client=external_client
# )

# from agents.model_settings import ModelSettings

# # Global configuration
# config = RunConfig(
#       model=model,
#       model_provider=external_client,
#       # model_settings=ModelSettings(parallel_tool_calls=False),
#       # tracing_disabled=True
# )

# from agents import set_default_openai_client, set_tracing_disabled

# set_default_openai_client(external_client)
# set_tracing_disabled(True)

# from dataclasses import dataclass, fields
# from agents import Agent, RunContextWrapper, Runner, function_tool, set_trace_processors
# from agents.model_settings import ModelSettings
# import requests
# from pydantic import BaseModel, Field
# from typing import Optional, Generic, TypeVar
# from dataclasses import dataclass, field
# from typing import Any, List

# import nest_asyncio
# nest_asyncio.apply()

# from typing import Dict, Any, Optional
# from agents import RunContextWrapper, Agent
# from agents.tool_context import ToolContext

# def build_pitch_prompt(ctx: RunContextWrapper, agent: Agent) -> str:
#     """
#     Returns a fully formed prompt (system + user context) for a "Pitch Agent".
#     All context data is read from `ctx.context`. The LLM should return a JSON
#     object in the exact schema specified below. If the runtime environment
#     exposes the `send_email` tool to the model, the model may call it using
#     the produced `send_payload`. Otherwise the orchestration layer should
#     call `send_email` with the payload returned by the model.
#     """

#     # Safely extract fields from ctx.context (fall back to sensible defaults)
#     page_name = ctx.context.page_name
#     email = ctx.context.email
#     title = ctx.context.title
#     company = ctx.context
#     business_detail = ctx.context
#     followers = ctx.context.followers
#     intro = ctx.context.intro
#     extras = ctx.context.info

#     # Compose a clear, concise, and model-friendly prompt
#     prompt = f"""
#     SYSTEM INSTRUCTIONS:
#     You are a "Pitch Agent" designed to generate short, personalized outreach emails from a single row of prospect data.
#     Do not invent facts. Use only the data provided in the context below and any verified company summary if available.
#     If you have access to the `send_email` tool in this runtime, you may call it with the `send_payload` after producing the JSON output. If not, return the JSON and the orchestration layer will perform the sending.

#     --- RECIPIENT CONTEXT (do not invent facts) ---
#     Recipient:
#     - name: {page_name}
#     - email: {email}
#     - title: {title}
#     - company: {company}
#     - business_detail: {business_detail or "N/A"}
#     - followers: {followers}
#     - intro: {intro}
#     - extras: {extras}
#     - likes: {likes}
#     - address: {address}

#     Fetched company summary (if available):


#     --- TASK / OUTPUT REQUIREMENTS ---
#     Using only the context above, generate a concise, personalized outreach email for the recipient.


#     --- CONTENT RULES ---
#     1) Tone & style:
#       - Professional, warm, and concise. Friendly B2B outreach.
#       - Start the email body with a short greeting, e.g., "Salam {page_name},".
#       - Include one brief personal touch referencing `business_detail` or `company_summary`. Do NOT fabricate facts.

#     2) Length:
#       - Primary output: short version (2–4 sentences, ~50–120 words).
#       - Only produce a longer version if explicitly requested (max 200 words).

#     3) Subject requirements:
#       - Provide two subject options (4–8 words each), benefit-oriented, no clickbait.
#       - Select one as `chosen_subject`.

#     4) CTA:
#       - Include a single clear call-to-action (e.g., "Are you available for a 15-minute call next week?").

#     5) Guardrails:
#       - NEVER invent revenues, client names, metrics, or unverifiable claims.
#       - If `business_detail` is empty, use the safe fallback: "I noticed your work in [industry/company]."
#       - Always include an opt-out line: "If you'd prefer not to receive messages like this, reply 'stop'."
#       - If `email` is empty or obviously invalid, **do not** call `send_email`. Instead return:
#         {{ "skip": true, "reason": "invalid_email" }}

#     6) Observability:
#       - Populate `personalization_reason` with 1–2 lines describing why the personalization was used (for human review).
#       - Keep the body focused on one main, specific benefit relevant to the recipient's context.

#     --- SENDING BEHAVIOR (runtime dependent) ---
#     - If the runtime makes the `send_email` tool available to you, call it with the `send_payload` after producing the JSON and then return a final JSON status object that includes the send result.
#     - If the runtime does not provide the `send_email` tool to you, return only the JSON above and let the orchestrator take the `send_payload` and call `send_email`.

#     END OF INSTRUCTIONS.
#     """
#     return prompt

# pitch_generator = Agent(
#   name="Pitch Agent",
#   instructions=build_pitch_prompt,
# )


# -------------------------

# services/pitch_service.py
from agents import Agent, RunConfig, Runner, RunContextWrapper
from agents import AsyncOpenAI, OpenAIChatCompletionsModel
from agents import set_default_openai_client, set_tracing_disabled

from dataclasses import dataclass
from typing import Any, Callable

import os

@dataclass
class UserData:
    page_name: str
    email: str
    title: str = ""
    company: str = ""
    business_detail: str = ""
    followers: int = 0
    intro: str = ""
    info: Any = None
    likes: int = 0
    address: str = ""

def pitch_prompt(ctx: RunContextWrapper, agent: Agent) -> str:
        """
        Compose the prompt for pitch generation.
        """
        page_name = ctx.context.page_name
        email = ctx.context.email
        title = ctx.context.title
        company = ctx.context.company
        business_detail = ctx.context.business_detail
        followers = ctx.context.followers
        intro = ctx.context.intro
        extras = ctx.context.info
        likes = ctx.context.likes
        address = ctx.context.address

        prompt = f"""
        SYSTEM INSTRUCTIONS:
        You are a "Pitch Agent" generating short personalized outreach emails.
        Use ONLY the data provided below. Never invent facts.

        RECIPIENT CONTEXT:
        - name: {page_name}
        - email: {email}
        - title: {title}
        - company: {company}
        - business_detail: {business_detail or "N/A"}
        - followers: {followers}
        - intro: {intro}
        - extras: {extras}
        - likes: {likes}
        - address: {address}

        TASK:
        Generate a concise personalized outreach email.
        Provide two subject options and choose one as `chosen_subject`.
        Include personalization reason and follow the rules:
        - Professional, warm, concise
        - One CTA
        - Include opt-out line
        - If email is invalid, return {{ "skip": true, "reason": "invalid_email" }}
        """
        return prompt

class PitchService:
    def __init__(self, api_key: str = None, instructions: str | Callable[[RunContextWrapper, Agent], str] = None):
        """
        Initialize the Pitch Agent service with the LLM client and model.
        """
        self.api_key = api_key
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")

        # Initialize external client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

        # Initialize model
        self.model = OpenAIChatCompletionsModel(
            model="gemini-2.0-flash",
            openai_client=self.client
        )

        # Run config
        self.config = RunConfig(
            model=self.model,
            model_provider=self.client
        )

        # Pitch prompt
        self.instructions = instructions

        # Set defaults for agents
        set_default_openai_client(self.client)
        set_tracing_disabled(True)

        # Initialize agent
        self.pitch_agent = Agent(
            name="Pitch Agent",
            instructions=self.instructions
        )


    def generate_pitch(self, *, user_input: str, context: UserData) -> str:
        """
        Generate pitch for a single prospect.
        """
        ctx = RunContextWrapper(context=context)
        result = Runner.run_sync(
            starting_agent=self.pitch_agent,
            input="Generate and send pitch email",
            run_config=self.config,
            context=ctx
        )
        return result.final_output


