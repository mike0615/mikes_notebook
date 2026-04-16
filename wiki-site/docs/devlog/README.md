# Mike Anderson — Dev Log & Project Wiki

**Lead Systems Engineer · Navy Veteran · 3 Businesses · Florida**

This repo is a living knowledge base: daily dev logs, full project documentation, task lists, research notes, and future project ideas. Updated whenever something gets built, discussed, or decided.

---

## Projects

| Project | Status | Description |
|---------|--------|-------------|
| [lrn_tools](projects/lrn_tools.md) | Active | Sysadmin toolkit — 27 tools, web dashboard, TUI, SSH remote execution |
| [lrn-pxe](projects/lrn-pxe.md) | Active | Network PXE boot server with web UI for Rocky Linux |
| [mac-ops](projects/mac-ops.md) | Active | Maytag Admin Console — unified infra management, Ansible, FreeIPA auth |
| [openclaw](projects/openclaw.md) | Research | Personal AI assistant — local LLM, multi-channel, air-gapped capable |
| [openclaw-airgap](projects/openclaw-airgap.md) | Research | Air-gapped OpenClaw deployment on Rocky 9 with Ollama + Mattermost |
| [anderson-computer-consulting](projects/acc-website.md) | Active | Jekyll/GitHub Pages marketing site for ACC |

---

## Daily Logs

Logs are in `logs/YYYY-MM.md` — one file per month.

- [2026-04](logs/2026-04.md) — lrn_tools v2.x, RPM build, remote hosts, LRN Man

---

## Task Lists

- [lrn_tools Enhancements](tasks/lrn_tools.md)
- [lrn-pxe Enhancements](tasks/lrn-pxe.md)
- [mac-ops Enhancements](tasks/mac-ops.md)
- [Infrastructure Backlog](tasks/infrastructure.md)

---

## Research & Future Projects

- [Research Topics](research/topics.md)
- [Future Project Ideas](research/future-projects.md)
- [Air-Gap Architecture Notes](research/airgap.md)

---

## Stack

| Layer | Technology |
|-------|-----------|
| OS | Rocky Linux 9.7 / RHEL 9 |
| Identity | FreeIPA (Kerberos, LDAP, PKI) |
| Hypervisor | XCP-ng / KVM |
| Automation | Ansible |
| Containers | Docker / Podman |
| Deployment | PXE (lrn-pxe), RPM packages, rsync |
| Backend | Python 3.9 / Flask |
| Frontend | Vanilla JS, Jinja2, ncurses TUI |
| AI (local) | Ollama + llama3 / mistral |
| Design | Air-gapped first — no CDN, no cloud dependencies at runtime |
