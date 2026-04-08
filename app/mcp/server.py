from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from app.memory.service import get_memory_service
from app.models.schemas import AnswerRequest, MemoryInput, SearchRequest

mcp = FastMCP("cortexos")
service = get_memory_service()


@mcp.tool()
def add_memory(text: str, wing: str | None = None, room: str | None = None, source: str = "mcp"):
    result = service.add_memory(MemoryInput(text=text, wing=wing, room=room, source=source))
    return result.model_dump()


@mcp.tool()
def search_memory(
    query: str,
    wing: str | None = None,
    room: str | None = None,
    explain: bool = False,
):
    result = service.search(SearchRequest(query=query, wing=wing, room=room, explain=explain))
    return result.model_dump()


@mcp.tool()
def answer_with_memory(query: str, wing: str | None = None, room: str | None = None):
    return service.answer(AnswerRequest(query=query, wing=wing, room=room)).model_dump()


@mcp.tool()
def list_wings():
    return {"wings": service.list_wings()}


@mcp.tool()
def list_rooms(wing: str | None = None):
    return {"rooms": service.list_rooms(wing)}


@mcp.tool()
def get_conflicts():
    return {"conflicts": [item.model_dump() for item in service.get_conflicts()]}


@mcp.tool()
def get_superseded():
    return {"superseded": [item.model_dump() for item in service.get_superseded()]}


def main() -> None:
    mcp.run()
