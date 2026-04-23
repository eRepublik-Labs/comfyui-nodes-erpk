[Skip to main content](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-pro-preview#main-content)

[![Gemini API](https://ai.google.dev/_static/googledevai/images/gemini-api-logo.svg)](https://ai.google.dev/)

`/`

- English
- Deutsch
- Español – América Latina
- Français
- Indonesia
- Italiano
- Polski
- Português – Brasil
- Shqip
- Tiếng Việt
- Türkçe
- Русский
- עברית
- العربيّة
- فارسی
- हिंदी
- বাংলা
- ภาษาไทย
- 中文 – 简体
- 中文 – 繁體
- 日本語
- 한국어

[Get API key](https://aistudio.google.com/apikey) [Cookbook](https://github.com/google-gemini/cookbook) [Community](https://discuss.ai.google.dev/c/gemini-api/)Sign in

Try the new [Gemini 3.1 Flash TTS Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview) model for expressive, multilingual speech generation.


- [Home](https://ai.google.dev/)
- [Gemini API](https://ai.google.dev/gemini-api)
- [Docs](https://ai.google.dev/gemini-api/docs)



 Send feedback



# Gemini 3.1 Pro Preview

Built to refine the performance and reliability of the Gemini 3 Pro series,
Gemini 3.1 Pro Preview provides better thinking, improved token
efficiency, and a more grounded, factually consistent experience. It's optimized
for software engineering behavior and usability, as well as agentic workflows
requiring precise tool usage and reliable multi-step execution across real-world
domains.

[Try in Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3.1-pro-preview)

## Documentation

Visit the [Gemini 3 Developer Guide](https://ai.google.dev/gemini-api/docs/gemini-3) page for full
coverage of features and capabilities.

## gemini-3.1-pro-preview

| Property | Description |
| --- | --- |
| id\_cardModel code | `gemini-3.1-pro-preview` |
| saveSupported data types | **Inputs**<br>Text, Image, Video, Audio, and PDF<br>**Output**<br>Text |
| token\_autoToken limits[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens) | **Input token limit**<br>1,048,576<br>**Output token limit**<br>65,536 |
| handymanCapabilities | **Audio generation**<br>Not supported<br>**Batch API**<br>Supported<br>**Caching**<br>Supported<br>**Code execution**<br>Supported<br>**File search**<br>Supported (AI Studio only)<br>**Flex inference**<br>Supported<br>**Function calling**<br>Supported<br>**Grounding with Google Maps**<br>Supported<br>**Image generation**<br>Not supported<br>**Live API**<br>Not supported<br>**Priority inference**<br>Supported<br>**Search grounding**<br>Supported<br>**Structured outputs**<br>Supported<br>**Thinking**<br>Supported<br>**URL context**<br>Supported |
| 123Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details.<br>- Preview: `gemini-3.1-pro-preview`<br>- Preview: `gemini-3.1-pro-preview-customtools` \* |
| calendar\_monthLatest update | February 2026 |
| cognition\_2Knowledge cutoff | January 2025 |

#### gemini-3.1-pro-preview-customtools

\\* _For those building with a mix of bash and custom tools, Gemini 3.1 Pro Preview_
_comes with a separate endpoint available via the API called_
_`gemini-3.1-pro-preview-customtools`. This endpoint is better at prioritizing_
_your custom tools (for example `view_file` or `search_code`)._

_Note that while `gemini-3.1-pro-preview-customtools` is optimized for agentic_
_workflows that use custom tools and bash, you may see quality fluctuations in_
_some use cases which don't benefit from such tools._



 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-04-01 UTC.


Need to tell us more?






\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2026-04-01 UTC."\],\[\],\[\]\]
