# Anderson Computer Consulting Website

Jekyll-based GitHub Pages site for Anderson Computer Consulting.

## Tech Stack

- **Framework:** Jekyll (GitHub Pages native)
- **Styling:** Custom CSS (MAC-OPS color scheme)
- **Icons:** Bootstrap Icons
- **Code highlight:** highlight.js
- **Chatbot:** Botpress (free tier)
- **Forms:** Formspree (free tier)

## Local Development

```bash
gem install bundler
bundle install
bundle exec jekyll serve --livereload
```

Site runs at `http://localhost:4000`

## Deploying to GitHub Pages

1. Push to `main` branch
2. GitHub Actions deploys automatically via `.github/workflows/deploy.yml`
3. Enable GitHub Pages in repo Settings → Pages → Source: GitHub Actions

## Chatbot Setup (Botpress)

1. Sign up at [botpress.com](https://botpress.com)
2. Create a bot and configure responses
3. Go to Share → Embed → copy webchat URL
4. Edit `assets/js/chatbot.js` — set `BOTPRESS_EMBED_URL` to your URL

## Contact Form Setup (Formspree)

1. Sign up at [formspree.io](https://formspree.io)
2. Create a form and get your form ID
3. Edit `contact/index.html` — replace `YOUR_FORM_ID` in the form action URL

## Adding Content

### Knowledge Base Article
Create `_kb/<category>/article-name.md` with front matter:
```yaml
---
title: Article Title
description: One-line description
category: Networking
tags: [cisco, ios]
updated: 2026-03-28
---
```

### Code Snippet
Create `_snippets/<language>/snippet-name.md` with front matter:
```yaml
---
title: Snippet Title
description: What it does
language: Ansible
tags: [ansible, freeipa]
---
```

### Blog Post
Create `_posts/YYYY-MM-DD-post-title.md` with front matter:
```yaml
---
layout: post
title: "Post Title"
date: YYYY-MM-DD
category: Category
author: Mike Anderson
read_time: 5
excerpt: Brief description
---
```

### Download File
Place file in `assets/downloads/<category>/` and add an entry to `downloads/index.html`.

## Structure

```
anderson-computer-consulting/
├── _config.yml          # Site config
├── _data/               # Navigation, services data
├── _includes/           # Header, footer, chatbot
├── _layouts/            # Page templates
├── _kb/                 # Knowledge base articles
├── _snippets/           # Code share snippets
├── _posts/              # Blog posts
├── assets/              # CSS, JS, images, downloads
├── services/            # Service pages
├── markets/             # Market pages
├── about/               # About pages
├── knowledge-base/      # KB index
├── code-share/          # Code share index
├── downloads/           # Downloads index
├── blog/                # Blog index
├── contact/             # Contact form
├── case-studies/        # Case studies
└── legal/               # Privacy, terms
```
