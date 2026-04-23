Models

Models overview

Copy page

## Choosing a model

If you're unsure which model to use, consider starting with **Claude Opus 4.7** for the most complex tasks. It is our most capable generally available model, with a step-change improvement in agentic coding over Claude Opus 4.6.

All current Claude models support text and image input, text output, multilingual capabilities, and vision. Models are available via the Claude API, Amazon Bedrock, Vertex AI, and Microsoft Foundry.

Once you've picked a model, [learn how to make your first API call](https://platform.claude.com/docs/en/get-started).

### Latest models comparison

| Feature | Claude Opus 4.7 | Claude Sonnet 4.6 | Claude Haiku 4.5 |
| --- | --- | --- | --- |
| **Description** | Our most capable generally available model for complex reasoning and agentic coding | The best combination of speed and intelligence | The fastest model with near-frontier intelligence |
| **Claude API ID** | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5-20251001 |
| **Claude API alias** | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5 |
| **AWS Bedrock ID** | anthropic.claude-opus-4-73 | anthropic.claude-sonnet-4-6 | anthropic.claude-haiku-4-5-20251001-v1:0 |
| **GCP Vertex AI ID** | claude-opus-4-7 | claude-sonnet-4-6 | claude-haiku-4-5@20251001 |
| **Pricing** 1 | $5 / input MTok<br>$25 / output MTok | $3 / input MTok<br>$15 / output MTok | $1 / input MTok<br>$5 / output MTok |
| **[Extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking)** | No | Yes | Yes |
| **[Adaptive thinking](https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking)** | Yes | Yes | No |
| **[Priority Tier](https://platform.claude.com/docs/en/api/service-tiers)** | Yes | Yes | Yes |
| **Comparative latency** | Moderate | Fast | Fastest |
| **Context window** | 1M tokens | 1M tokens | 200k tokens |
| **Max output** | 128k tokens | 64k tokens | 64k tokens |
| **Reliable knowledge cutoff** | Jan 20262 | Aug 20252 | Feb 2025 |
| **Training data cutoff** | Jan 2026 | Jan 2026 | Jul 2025 |

_1 - See the [pricing page](https://platform.claude.com/docs/en/about-claude/pricing) for complete pricing information including batch API discounts, prompt caching rates, extended thinking costs, and vision processing fees._

_2 - **Reliable knowledge cutoff** indicates the date through which a model's knowledge is most extensive and reliable. **Training data cutoff** is the broader date range of training data used. For more information, see [Anthropic's Transparency Hub](https://www.anthropic.com/transparency)._

_3 - Claude Opus 4.7 on AWS is available through [Claude in Amazon Bedrock](https://platform.claude.com/docs/en/build-with-claude/claude-in-amazon-bedrock) (the Messages-API Bedrock endpoint)._

[Claude Mythos Preview](https://anthropic.com/glasswing) is offered separately as a research preview model for defensive cybersecurity workflows as part of [Project Glasswing](https://anthropic.com/glasswing). Access is invitation-only and there is no self-serve sign-up.

Models with the same snapshot date (e.g., 20240620) are identical across all platforms and do not change. The snapshot date in the model name ensures consistency and allows developers to rely on stable performance across different environments.

Starting with **Claude Sonnet 4.5 and all subsequent models** (including Claude Sonnet 4.6), AWS Bedrock offers two endpoint types: **global endpoints** (dynamic routing for maximum availability) and **regional endpoints** (guaranteed data routing through specific geographic regions). Google Vertex AI offers three endpoint types: global endpoints, **multi-region endpoints** (dynamic routing within a geographic area), and regional endpoints. For more information, see the [third-party platform pricing section](https://platform.claude.com/docs/en/about-claude/pricing#third-party-platform-pricing).

You can query model capabilities and token limits programmatically with the [Models API](https://platform.claude.com/docs/en/api/models/list). The response includes `max_input_tokens`, `max_tokens`, and a `capabilities` object for every available model.

The Max output values above apply to the synchronous Messages API. On the [Message Batches API](https://platform.claude.com/docs/en/build-with-claude/batch-processing#extended-output-beta), Opus 4.7, Opus 4.6, and Sonnet 4.6 support up to 300k output tokens by using the `output-300k-2026-03-24` beta header.

### Legacy models

## Prompt and output performance

Claude 4 models excel in:

- **Performance**: Top-tier results in reasoning, coding, multilingual tasks, long-context handling, honesty, and image processing. See the [Claude 4 blog post](http://www.anthropic.com/news/claude-4) for more information.

- **Engaging responses**: Claude models are ideal for applications that require rich, human-like interactions.
  - If you prefer more concise responses, you can adjust your prompts to guide the model toward the desired output length. Refer to the [prompt engineering guides](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering) for details.
  - For prompting best practices, see the [prompting best practices guide](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices).
- **Output quality**: When migrating from previous model generations to Claude 4, you may notice larger improvements in overall performance.


## Migrating to Claude Opus 4.7

If you're currently using Claude Opus 4.6 or older Claude models, consider migrating to Claude Opus 4.7 to take advantage of improved intelligence and a step-change jump in agentic coding. For detailed migration instructions, see [Migrating to Claude Opus 4.7](https://platform.claude.com/docs/en/about-claude/models/migration-guide).

## Get started with Claude

If you're ready to start exploring what Claude can do for you, dive in! Whether you're a developer looking to integrate Claude into your applications or a user wanting to experience the power of AI firsthand, the following resources can help.

Looking to chat with Claude? Visit [claude.ai](http://www.claude.ai/)!

[Intro to Claude\\
\\
Explore Claude's capabilities and development flow.](https://platform.claude.com/docs/en/intro) [Quickstart\\
\\
Learn how to make your first API call in minutes.](https://platform.claude.com/docs/en/get-started) [Claude Console\\
\\
Craft and test powerful prompts directly in your browser.](https://platform.claude.com/)

If you have any questions or need assistance, don't hesitate to reach out to the [support team](https://support.claude.com/) or consult the [Discord community](https://www.anthropic.com/discord).

Was this page helpful?

Ask Docs
![Chat avatar](https://platform.claude.com/docs/images/book-icon-light.svg)
