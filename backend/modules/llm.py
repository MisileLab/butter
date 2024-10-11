from .config import api_key
from . import memory, llm_function, vtube

from langchain_openai import ChatOpenAI

functions = {**llm_function.functions, **memory.functions}
middle_converting_functions = {**llm_function.middle_converting_functions, **memory.middle_converting_functions}

llm = ChatOpenAI(model="gpt-4o", api_key=api_key).bind_tools(list(functions.values()))
llm_vtube = ChatOpenAI(model="gpt-4o", api_key=api_key).with_structured_output(vtube.VTubeModel, strict=True)
