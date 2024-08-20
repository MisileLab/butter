from modules.llm_function import print_it
from .config import api_key, config

from pydantic import BaseModel, Field
from mem0 import Memory

from os import environ

mem0_config = {
  "llm": {
    "provider": "openai",
    "config": {
      "model": "gpt-4o-mini",
      "temperature": 0.2,
      "max_tokens": 1500
    }
  },
  "vector_store": {
    "provider": "qdrant",
    "config": {
      "host": config['qdrant']['url']
    }
  },
}

environ['OPENAI_API_KEY'] = api_key

m: Memory = Memory.from_config(mem0_config)

@print_it
def save_memory(content: str, username: str | None = None):
  return m.add(content, username)

@print_it
def get_all_memories(username: str | None = None):
  return m.get_all(username)

@print_it
def get_memory(id: str):
  return lambda: m.get(id)

@print_it
def search_memory(query: str, username: str | None = None):
  return m.search(query, username, limit=10)

@print_it
def update_memory(id: str, content: str):
  return m.update(id, content)

@print_it
def get_memory_history(id: str):
  return m.history(id)

@print_it
def delete_memory(id: str):
  return m.delete(id)

class saveMemoryBase(BaseModel):
  """Save memory and returns id of memory"""
  content: str = Field(description="The content of the memory")
  username: str | None = Field(None, description="The most related user's username")

class getAllMemoryBase(BaseModel):
  """Get all memories (limit is 100)"""
  username: str | None = Field(None, description="The most related user's username")

class getMemoryBase(BaseModel):
  """Get memory"""
  id: str = Field(description="The id of the memory")

class searchMemoryBase(BaseModel):
  """Search memory (limit is 10)"""
  query: str = Field(description="The query of the memory")
  username: str | None = Field(None, description="The most related user's username")

class updateMemoryBase(BaseModel):
  """Update memory that has specific id to content"""
  id: str = Field(description="The id of the memory")
  content: str = Field(description="The content of the memory")

class getMemoryHistoryBase(BaseModel):
  """Get memory history with id"""
  id: str = Field(description="The id of the memory")

class deleteMemoryBase(BaseModel):
  """Delete memory with id"""
  id: str = Field(description="The id of the memory")

functions = {
  "saveMemoryBase": saveMemoryBase,
  "getAllMemoryBase": getAllMemoryBase,
  "getMemoryBase": getMemoryBase,
  "searchMemoryBase": searchMemoryBase,
  "updateMemoryBase": updateMemoryBase,
  "getMemoryHistoryBase": getMemoryHistoryBase,
  "deleteMemoryBase": deleteMemoryBase
}

middle_converting_functions = {
  saveMemoryBase: save_memory,
  getAllMemoryBase: get_all_memories,
  getMemoryBase: get_memory,
  searchMemoryBase: search_memory,
  updateMemoryBase: update_memory,
  getMemoryHistoryBase: get_memory_history,
  deleteMemoryBase: delete_memory
}
