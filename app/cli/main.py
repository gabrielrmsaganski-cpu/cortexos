from __future__ import annotations

import argparse
import json

from app.memory.service import get_memory_service
from app.models.schemas import AnswerRequest, MemoryInput, SearchRequest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cortexos-cli")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add-memory")
    add.add_argument("--text", required=True)
    add.add_argument("--wing")
    add.add_argument("--room")
    add.add_argument("--source", default="manual")

    search = sub.add_parser("search")
    search.add_argument("--query", required=True)
    search.add_argument("--wing")
    search.add_argument("--room")
    search.add_argument("--explain", action="store_true")

    answer = sub.add_parser("answer")
    answer.add_argument("--query", required=True)
    answer.add_argument("--wing")
    answer.add_argument("--room")

    sub.add_parser("list-wings")
    rooms = sub.add_parser("list-rooms")
    rooms.add_argument("--wing")
    sub.add_parser("conflicts")
    sub.add_parser("superseded")
    return parser


def main() -> None:
    service = get_memory_service()
    args = build_parser().parse_args()
    if args.command == "add-memory":
        result = service.add_memory(
            MemoryInput(text=args.text, wing=args.wing, room=args.room, source=args.source)
        )
    elif args.command == "search":
        result = service.search(
            SearchRequest(
                query=args.query,
                wing=args.wing,
                room=args.room,
                explain=args.explain,
            )
        )
    elif args.command == "answer":
        result = service.answer(AnswerRequest(query=args.query, wing=args.wing, room=args.room))
    elif args.command == "list-wings":
        result = {"wings": service.list_wings()}
    elif args.command == "list-rooms":
        result = {"rooms": service.list_rooms(args.wing)}
    elif args.command == "conflicts":
        result = {"conflicts": service.get_conflicts()}
    else:
        result = {"superseded": service.get_superseded()}

    def serializer(value):
        dumper = getattr(value, "model_dump", None)
        return dumper() if dumper else str(value)

    print(json.dumps(result, default=serializer, indent=2))
