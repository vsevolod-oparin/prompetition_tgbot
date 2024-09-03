from typing import List, Optional

from openai import AsyncOpenAI, NOT_GIVEN, NotGiven

# Get the value of an environment variable
DEFAULT_MODEL = 'deepseek-chat'

async def get_ai_response(*,
        client: AsyncOpenAI,
        system_prompt: str,
        prompt: str,
        model_name: str = DEFAULT_MODEL,
        temperature: Optional[float] | NotGiven =NOT_GIVEN):
    history_list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    response = await client.chat.completions.create(
        model=model_name,
        messages=history_list,
        temperature=temperature,
        stream=False
    )
    return response

async def stream_ai_response(*,
        client: AsyncOpenAI,
        system_prompt: str,
        prompt: str,
        model_name: str = DEFAULT_MODEL,
        temperature: Optional[float] | NotGiven = NOT_GIVEN,
        collector: Optional[List[str]] = None):
    history_list = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]
    response = await client.chat.completions.create(
        model=model_name,
        messages=history_list,
        temperature=temperature,
        stream=True
    )
    async for chunk in response:
        content = chunk.choices[0].delta.content
        if collector is not None:
            collector.append(content)
        yield content

