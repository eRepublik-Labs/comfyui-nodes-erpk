[![The AI Corner](https://substackcdn.com/image/fetch/$s_!DSM0!,w_40,h_40,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F744d55a9-d679-45b4-922c-b53e6798056d_795x795.png)](https://www.the-ai-corner.com/)

# [The AI Corner](https://www.the-ai-corner.com/)

SubscribeSign in

# Everything Claude Has Shipped in 2026. And How to Actually Use It

### Anthropic shipped a major release roughly every two weeks since January. Here’s what’s live, what matters, and exactly how to set each thing up

[![Ruben Dominguez's avatar](https://substackcdn.com/image/fetch/$s_!mcL6!,w_36,h_36,c_fill,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F3403a50f-4e67-40d2-aa6f-a8d845f19c1c_480x480.png)](https://substack.com/@rubendominguez)

[Ruben Dominguez](https://substack.com/@rubendominguez)

Mar 28, 2026

∙ Paid

93

7

Share

I’ll be honest with you.

Keeping up with Anthropic this year has been genuinely hard. A new release almost every day. A major one every two weeks. New models, new tools, new product categories that didn’t exist three months ago. If you took a few weeks off, you missed more than you think.

[![Anthropic release calendar showing everything Claude shipped in 52 days from February 1 to March 24 2026, including Claude Opus 4.6, Sonnet 4.6, Cowork, Agent Teams, Computer Use, Channels, Dispatch, Scheduled Tasks, Plugins, Projects, and over 40 product releases mapped by date](https://substackcdn.com/image/fetch/$s_!QCuk!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ffb5cc126-441e-4ea5-9f25-859a4f8cb5fc_1456x1682.webp)](https://substackcdn.com/image/fetch/$s_!QCuk!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Ffb5cc126-441e-4ea5-9f25-859a4f8cb5fc_1456x1682.webp) Everything Anthropic shipped in 52 days. February 1 to March 24, 2026. Product releases only. Most people caught five. Source: The Product Compass Newsletter, productcompass.pm

And this isn’t like missing a LinkedIn feature nobody uses. Claude impacts how you work. The people who’ve been paying attention have rebuilt entire workflows. The people who haven’t are still copy-pasting context into every new chat.

This is the guide I wish existed when I started. Everything that’s live as of March 28, 2026. How to set each thing up. When to use what. What’s actually worth your time.

Bookmark it. Come back to it. Share it with your team.

* * *

# The Models

## [Claude Opus 4.6](https://theaicorner1.substack.com/p/claude-opus-4-6-practical-guide)

[![Claude Opus 4.6 official launch image from Anthropic showing the model name against a collage of a vintage Sony monitor with a calendar, a Mars rover, clouds, and green geometric shapes, representing the February 5 2026 release with 1 million token context window](https://substackcdn.com/image/fetch/$s_!WMYN!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd2940d42-3c90-404f-aa4d-bd99aa332840_686x386.webp)](https://substackcdn.com/image/fetch/$s_!WMYN!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2Fd2940d42-3c90-404f-aa4d-bd99aa332840_686x386.webp) Claude Opus 4.6 launched February 5, 2026. 1 million token context window, 78.3% on MRCR v2, and a 14.5 hour task completion window — the highest of any frontier model. Source: Anthropic.

The ceiling. Launched February 5 with a 1 million token context window.

- **78.3% on MRCR v2 at 1M tokens** — highest among frontier models at that length

- **14.5 hour task completion window** — longest of any frontier model

- **$5/$25 per million tokens** on the API

- **128K max output tokens**

- Supports adaptive thinking with a new “max” effort level for peak capability


**Use [Opus 4.6](https://theaicorner1.substack.com/p/claude-opus-4-6-practical-guide) for:** complex analysis across large contexts, codebase refactoring, deep research, high-stakes deliverables, anything where quality matters more than cost.

**Don’t use [Opus](https://theaicorner1.substack.com/p/claude-opus-4-6-practical-guide) for:** anything you’ll run more than a few times a day. At $5/$25 per million tokens, a heavy Opus workflow can burn $50-100 per day. Default to Sonnet. Escalate to Opus only when Sonnet’s output isn’t good enough.

* * *

## Claude [Sonnet 4.6](https://www.the-ai-corner.com/p/anthropic-just-launched-a-030-ai?r=1krivi)

[![Claude Sonnet 4.6 official launch image showing the model name in bold white text on an orange background with a minimalist line drawing of a human head profile and connected nodes, representing the February 17 2026 release as the default model for Claude Free and Pro plans](https://substackcdn.com/image/fetch/$s_!aiaD!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F18b992cc-fe6f-4090-8629-34715c907b89_686x386.webp)](https://substackcdn.com/image/fetch/$s_!aiaD!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F18b992cc-fe6f-4090-8629-34715c907b89_686x386.webp) Claude Sonnet 4.6 launched February 17, 2026. The default model for Free and Pro plans. 1M context window, 30-50% faster than Sonnet 4.5, preferred over the previous flagship Opus 4.5 in 59% of head-to-head tests. Source: Anthropic.

The model most people should default to. Launched February 17. 1M context window GA since March 13.

- Early testers preferred it over Sonnet 4.5 roughly **70% of the time**

- Users chose it over the previous flagship Opus 4.5 in **59% of cases**

- **$3/$15 per million tokens**

- **30-50% faster** than Sonnet 4.5

- Default model for Free and Pro plans on claude.ai


**Use [Sonnet](https://www.the-ai-corner.com/p/anthropic-just-launched-a-030-ai?r=1krivi) for:** everyday work, quick drafts, standard coding tasks, agent workflows where you want speed without sacrificing intelligence. It matches [Opus](https://theaicorner1.substack.com/p/claude-opus-4-6-practical-guide) on many office tasks at roughly 40% lower cost.

* * *

## Claude Haiku 4.5

[![Claude Haiku 4.5 official launch image showing the model name in large white text on an orange background alongside a white minimalist icon of connected nodes and a stylized hand shape, representing Anthropic's fast and low-cost model for high-volume API pipelines and subagent tasks](https://substackcdn.com/image/fetch/$s_!wTaC!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F4a2142bf-03a8-46c9-a998-d3db6313982f_1280x720.webp)](https://substackcdn.com/image/fetch/$s_!wTaC!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F4a2142bf-03a8-46c9-a998-d3db6313982f_1280x720.webp) Claude Haiku 4.5 — Anthropic's fast, low-cost option for high-volume API pipelines and subagent tasks. Important note: Haiku has zero prompt injection protection. Read the docs before deploying in agentic setups that process untrusted input. Source: Anthropic.

The fast, cheap option for high-volume API pipelines and subagent assignments where you want a low-cost read-only worker.

One important caveat: **Haiku has zero prompt injection protection.** If you’re using it in agentic setups where it processes untrusted input, read the docs before deploying.

* * *

## The 1M Context Window at Standard Pricing

[![Official Anthropic tweet from March 13 2026 announcing the 1 million context window as generally available for Claude Opus 4.6 and Claude Sonnet 4.6, showing a long context retrieval benchmark chart comparing MRCR v2 8-needle scores across 128K, 256K, 512K, and 1M input tokens, with Opus 4.6 scoring 78.3% at 1M tokens and Sonnet 4.6 scoring 65.1%, both significantly outperforming GPT-5.4 at 36.6% and Gemini 3.1 Pro at 18.3%](https://substackcdn.com/image/fetch/$s_!-WqT!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F53376eb3-a9b8-46e2-9668-562405361354_1320x1414.webp)](https://substackcdn.com/image/fetch/$s_!-WqT!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F53376eb3-a9b8-46e2-9668-562405361354_1320x1414.webp) The 1M context window is now generally available for Claude Opus 4.6 and Sonnet 4.6 at standard pricing with no surcharge, as of March 13, 2026. Opus 4.6 scores 78.3% on MRCR v2 at 1M tokens, the highest among frontier models at that length. GPT-5.4 scores 36.6%. Gemini 3.1 Pro scores 18.3%. Source: Anthropic, @claudeai on X.

Previously, requests over 200K tokens were billed at a premium. As of March 13, that surcharge is gone completely.

A 900K token request now costs the same per-token rate as a 9K one. No multiplier, no fine print, no beta header.

That’s roughly 750,000 words of context. Entire codebases. Full legal contracts. Months of documentation. All held in working memory simultaneously.

Media limits also jumped to **600 images or PDF pages per request**, up 6x from 100.

> _One company reported that raising their context from 200K to 500K actually reduced total token usage because the model spent less time re-reading earlier information._

* * *

## Four Modes. Most People Only Know One.

**Chat** — the browser and mobile interface. Quick questions, brainstorming, writing drafts. Every conversation starts blank. You’re always driving.

**[Cowork](https://theaicorner1.substack.com/p/claude-cowork-the-tool-that-triggered)** — the desktop agent. Reads and writes to your actual files, executes multi-step tasks autonomously, delivers finished work to your folder. Use it when you want to delegate work, not have a conversation.

**[Code](https://theaicorner1.substack.com/p/claude-code-chief-of-staff-system)** — the developer tool. Runs in your terminal, sees your codebase, writes code, executes commands, manages git.

**Projects** — saved workspaces where you upload files and instructions once. Every new chat in that project starts with full context. Use for recurring work where the context doesn’t change much between sessions.

Quick rule:

1. Chat for quick questions

2. [Cowork](https://theaicorner1.substack.com/p/claude-cowork-setup-guide) for real work on your files

3. [Code](https://theaicorner1.substack.com/p/claude-code-chief-of-staff-system) for development

4. Projects for recurring work with stable context


* * *

## Memory and Personalization

[![Claude Code Memory feature announcement showing a macOS terminal window with the Claude Code welcome screen and a prompt reading 'Try help me refactor auth', alongside text explaining that Claude now remembers project context, debugging patterns, and preferred approaches across sessions without the user having to write anything down](https://substackcdn.com/image/fetch/$s_!pdvw!,w_1456,c_limit,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F55b36661-a40e-447d-8ca1-c236e39ce1e9_640x453.webp)](https://substackcdn.com/image/fetch/$s_!pdvw!,f_auto,q_auto:good,fl_progressive:steep/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F55b36661-a40e-447d-8ca1-c236e39ce1e9_640x453.webp) Claude Code Memory — Claude now remembers your project context, debugging patterns, and preferred approaches across sessions automatically. Available as of March 2026. No setup required. Source: Anthropic.

As of March 2, Claude’s memory from chat history is available to all users including the free tier. Claude remembers relevant context from your conversations and generates a memory summary that carries across sessions. View, edit, and delete memories in **Settings → Capabilities.**

> _Go to Settings → Memory right now and read what Claude already remembers about you. Edit anything wrong. Add context it should know. The more accurate your memory profile, the less you repeat yourself across sessions._

Note: [Cowork](https://theaicorner1.substack.com/p/claude-cowork-setup-guide) sessions don’t carry memory between sessions. Context files are the workaround.

* * *

## This is where the full guide begins

**What’s inside:**

- **The [Cowork setup that changes everything](https://theaicorner1.substack.com/p/claude-cowork-setup-guide)** — the exact folder structure, context files, and global instructions that separate people getting inconsistent results from people writing 10-word prompts that produce client-ready deliverables

- **Every [Cowork feature](https://theaicorner1.substack.com/p/10-claude-cowork-workflows-that-actually) shipped since January** — Connectors, Plugins, Scheduled Tasks, Dispatch, Projects, and Computer Use. What each one does, how to set it up, and the specific prompts that unlock each one

- **The [Claude Code extension system](https://theaicorner1.substack.com/p/claude-code-chief-of-staff-system)** — CLAUDE.md hierarchy, Rules directory, Commands vs Skills vs Agents, Hooks, MCP, and when to use each

- **[Claude Code](https://theaicorner1.substack.com/p/claude-code-chief-of-staff-system) Channels** — the Telegram and Discord integration that lets you message your coding agent from your phone and come back to finished work

- **Agent Teams** — how to spin up parallel agents that coordinate through shared task lists, when they’re worth the token cost, and when they’re not

- **The [Claude Certified Architect certification](https://theaicorner1.substack.com/p/claude-certified-architect-curriculum-2026)** — what Anthropic just launched, who it’s for, and why it matters for consultants and agencies

- **The enterprise numbers** — $14B ARR, $380B valuation, 500+ customers spending $1M+ annually

- **The practical playbook** — what to build this week if you’re a founder, developer, or team lead


This is the reference document. Everything you need to actually rebuild how you work.

[Start your 7 day free trial](https://www.the-ai-corner.com/subscribe?coupon=de1c3205&utm_content=192426210)

_Cancel anytime. First subscribers get [50% off forever](https://www.the-ai-corner.com/subscribe?coupon=de1c3205&utm_content=192426210)._

* * *

# Claude Cowork: The Knowledge Worker’s Operating System

## Keep reading with a 7-day free trial

Subscribe to The AI Corner to keep reading this post and get 7 days of free access to the full post archives.

[Start trial](https://www.the-ai-corner.com/subscribe?simple=true&next=https%3A%2F%2Fwww.the-ai-corner.com%2Fp%2Feverything-claude-shipped-2026-complete-guide&utm_source=paywall-free-trial&utm_medium=web&utm_content=192426210&coupon=a600db30)

[Already a paid subscriber? **Sign in**](https://substack.com/sign-in?redirect=%2Fp%2Feverything-claude-shipped-2026-complete-guide&for_pub=theaicorner1&change_user=false)
