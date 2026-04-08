# Operations UI

The Operations Center is intended for local runtime inspection, not cluster orchestration.

Current cards and panels:

- health for API, DB, Qdrant, and Ollama
- configured ports
- storage usage summary
- API service state from `systemctl show`
- Docker container summary from `docker compose ps --format json`
- recent API log lines from `journalctl`
- available Ollama models from `/api/tags`
- smoke test trigger

What it does not do yet:

- restart services from the browser
- change systemd config
- publish externally
- expose dangerous delete controls

This keeps the UI useful without turning it into a fragile remote-control surface.
