from ragna.extensions import hookimpl, Source

from ._llm_api import LlmApi


class OpenaiLlmApi(LlmApi):
    _API_KEY_ENV_VAR = "OPENAI_API_KEY"
    _MODEL: str
    _CONTEXT_SIZE: int

    @classmethod
    def display_name(cls):
        return f"OpenAI/{cls._MODEL}"

    @property
    def context_size(self) -> int:
        return self._CONTEXT_SIZE

    def _make_system_content(self, sources: list[Source]) -> str:
        # See https://github.com/openai/openai-cookbook/blob/main/examples/How_to_format_inputs_to_ChatGPT_models.ipynb
        instruction = (
            "You are an helpful assistant that answers user questions given the context below. "
            "If you don't know the answer, just say so. Don't try to make up an answer.\n"
        )
        return instruction + "\n\n".join(source.text for source in sources)

    def _call_api(self, prompt: str, sources: list[Source], *, max_new_tokens: int):
        import requests

        # See https://platform.openai.com/docs/api-reference/chat/create
        # and https://platform.openai.com/docs/api-reference/chat/object
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            json={
                "messages": [
                    {
                        "role": "system",
                        "content": self._make_system_content(sources),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                "model": self._MODEL,
                "temperature": 0.0,
                "max_tokens": max_new_tokens,
            },
        )
        if not response.ok:
            self._failed_api_call(
                status_code=response.status_code, response=response.json()
            )
        return response.json()["choices"][0]["message"]["content"]


class OpenaiGpt35Turbo16kLlm(OpenaiLlmApi):
    # https://platform.openai.com/docs/models/gpt-3-5
    _MODEL = "gpt-3.5-turbo-16k"
    _CONTEXT_SIZE = 16_384


@hookimpl(specname="ragna_llm")
def openai_gpt_35_turbo_16k_llm():
    return OpenaiGpt35Turbo16kLlm


class OpenaiGpt4Llm(OpenaiLlmApi):
    # https://platform.openai.com/docs/models/gpt-4
    _MODEL = "gpt-4"
    _CONTEXT_SIZE = 8_192


@hookimpl(specname="ragna_llm")
def openai_gpt_4_llm():
    return OpenaiGpt4Llm