import asyncio
import os
from typing import Optional

import yaml

from openai import AsyncOpenAI, NotGiven

from core.ai import get_ai_response
from core.utils import PathLike

class LLMManager:

    def __init__(self, config_pth: PathLike):
        with open(config_pth, 'r') as file:
            config = yaml.safe_load(file)

        self.default_llm = config['default_llm']
        self.config = config['llms']

        self.aclients = dict()
        self.model_names = dict()

    def get_clinet_model(self, llm_name):
        if llm_name not in self.config:
            raise ValueError(f"LLM config {llm_name} hasn't been found")
        if not (llm_name in self.aclients and llm_name in self.model_names):
            config = self.config[llm_name]
            base_url = config['baseurl']
            api_key = config.get('api_key', None)
            api_key = api_key or os.getenv(config.get('api_key_env', ""))
            self.aclients[llm_name] = AsyncOpenAI(
                base_url=base_url,
                api_key=api_key
            )
            self.model_names[llm_name] = config.get('model_name', None)
        return self.aclients[llm_name], self.model_names[llm_name]


    async def get_ai_response(self,
                              llm_name: Optional[str],
                              system_prompt: str,
                              prompt: str,
                              **kwargs):
        llm_name = llm_name or self.default_llm
        client, model = self.get_clinet_model(llm_name)
        return await get_ai_response(
            client=client,
            system_prompt=system_prompt,
            prompt=prompt,
            model_name=model,
            **kwargs
        )

    async def close(self):
        await asyncio.gather(
            client.close()
            for client in self.aclients.values()
        )
