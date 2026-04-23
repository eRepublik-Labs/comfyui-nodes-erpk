[Skip to main content](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview#main-content)

[![Gemini API](https://ai.google.dev/_static/googledevai/images/gemini-api-logo.svg)](https://ai.google.dev/)

`/`

Language

- [English](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview)
- [Deutsch](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=de)
- [Español – América Latina](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=es-419)
- [Français](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=fr)
- [Indonesia](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=id)
- [Italiano](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=it)
- [Polski](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=pl)
- [Português – Brasil](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=pt-br)
- [Shqip](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=sq)
- [Tiếng Việt](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=vi)
- [Türkçe](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=tr)
- [Русский](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=ru)
- [עברית](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=he)
- [العربيّة](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=ar)
- [فارسی](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=fa)
- [हिंदी](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=hi)
- [বাংলা](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=bn)
- [ภาษาไทย](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=th)
- [中文 – 简体](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=zh-cn)
- [中文 – 繁體](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=zh-tw)
- [日本語](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=ja)
- [한국어](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview?hl=ko)

[Get API key](https://aistudio.google.com/apikey) [Cookbook](https://github.com/google-gemini/cookbook) [Community](https://discuss.ai.google.dev/c/gemini-api/)

[Sign in](https://ai.google.dev/_d/signin?continue=https%3A%2F%2Fai.google.dev%2Fgemini-api%2Fdocs%2Fmodels%2Fgemini-3.1-flash-image-preview&prompt=select_account)

- On this page
- [Documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview#documentation)
- [gemini-3.1-flash-image-preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview#gemini-31-flash-image-preview)

Try the new [Gemini 3.1 Flash TTS Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview) model for expressive, multilingual speech generation.


- [Home](https://ai.google.dev/)
- [Gemini API](https://ai.google.dev/gemini-api)
- [Docs](https://ai.google.dev/gemini-api/docs)



 Send feedback



# Gemini 3.1 Flash Image Preview

- On this page
- [Documentation](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview#documentation)
- [gemini-3.1-flash-image-preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-image-preview#gemini-31-flash-image-preview)

**Nano Banana 2** provides high-quality image generation and conversational
editing at a mainstream price point and low latency. It serves as the
high-efficiency counterpart to [Gemini 3 Pro Image](https://ai.google.dev/gemini-api/docs/models/gemini-3-pro-image-preview), optimized for speed and
high-volume developer use cases.

**Key updates:**

- New output resolution options:
  - New support for 0.5K, 2K and 4K, default 1K
- New Image Search Grounding:
  - Integration of both text and image search results to inform generation with
    real-time web data
  - Supported with Thinking on or off
- New 1:4, 4:1, 1:8 and 8:1 aspect ratios
- Improved aspect ratio adherence
- Improved image quality and consistency
- Improved i18n text rendering

[Try in Google AI Studio](https://aistudio.google.com/?model=gemini-3.1-flash-image-preview)

## Documentation

Visit the [Image generation](https://ai.google.dev/gemini-api/docs/image-generation) page for full
coverage of features and capabilities.

## gemini-3.1-flash-image-preview

| Property | Description |
| --- | --- |
| id\_cardModel code | `gemini-3.1-flash-image-preview` |
| saveSupported data types | **Inputs**<br>Text and Image / PDF<br>**Output**<br>Image and Text |
| token\_autoToken limits[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens) | **Input token limit**<br>131,072<br>**Output token limit**<br>32,768 |
| handymanCapabilities | **Audio generation**<br>Not supported<br>**Batch API**<br>Supported<br>**Caching**<br>Not supported<br>**Code execution**<br>Not supported<br>**File search**<br>Not supported<br>**Function calling**<br>Not supported<br>**Grounding with Google Maps**<br>Not supported<br>**Image generation**<br>Supported<br>**Live API**<br>Not supported<br>**Search grounding**<br>Supported<br>**Structured outputs**<br>Not supported<br>**Thinking**<br>Supported<br>**URL context**<br>Not supported |
| 123Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details.<br>- `Preview: gemini-3.1-flash-image-preview` |
| calendar\_monthLatest update | February 2026 |
| cognition\_2Knowledge cutoff | January 2025 |



 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-02-26 UTC.


Need to tell us more?






\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2026-02-26 UTC."\],\[\],\[\]\]
