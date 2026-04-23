[Skip to main content](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash#main-content)

[![Google Cloud Documentation](https://www.gstatic.com/devrel-devsite/prod/v2f052e0cca7362dede225b85c12aee59eabee5b8fbb05d44fc345ffb54861aec/clouddocs/images/lockup.svg)](https://docs.cloud.google.com/)

`/`

[Console](https://console.cloud.google.com/)Language

- [English](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash)
- [Deutsch](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=de)
- [Español](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=es)
- [Español – América Latina](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=es-419)
- [Français](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=fr)
- [Indonesia](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=id)
- [Italiano](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=it)
- [Português](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=pt)
- [Português – Brasil](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=pt-br)
- [עברית](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=he)
- [中文 – 简体](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=zh-cn)
- [中文 – 繁體](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=zh-tw)
- [日本語](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=ja)
- [한국어](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-flash?hl=ko)

[Sign in](https://docs.cloud.google.com/_d/signin?continue=https%3A%2F%2Fdocs.cloud.google.com%2Fvertex-ai%2Fgenerative-ai%2Fdocs%2Fmodels%2Fgemini%2F3-flash&prompt=select_account)

[![](https://docs.cloud.google.com/_static/clouddocs/images/icons/products/vertex-ai-color.svg)](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)

- [Vertex AI](https://docs.cloud.google.com/vertex-ai/docs)
- [Generative AI on Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)

[Start free](https://console.cloud.google.com/freetrial)

- [Home](https://docs.cloud.google.com/)
- [Documentation](https://docs.cloud.google.com/docs)
- [AI and ML](https://docs.cloud.google.com/docs/ai-ml)
- [Vertex AI](https://docs.cloud.google.com/vertex-ai/docs)
- [Generative AI on Vertex AI](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)
- [Guides](https://docs.cloud.google.com/vertex-ai/generative-ai/docs)

Was this helpful?



 Send feedback



# Gemini 3 Flash    Stay organized with collections      Save and categorize content based on your preferences.

Gemini 3 Flash combines Gemini 3 Pro's reasoning capabilities
with the Flash line's levels on latency, efficiency, and cost. It not only
enables everyday tasks with improved reasoning, but is designed to tackle the
most complex agentic workflows.

Gemini 3 Flash uses several new features to improve performance,
control, and multimodal fidelity:

- **Thinking level**: Use the `thinking_level` parameter to control the amount
of internal reasoning the model performs ( _minimal_, _low_, _medium_, or
_high_) to balance response quality, reasoning complexity, latency, and
cost. The `thinking_level` parameter replaces `thinking_budget` for
Gemini 3 models.

For details on the different thinking levels, see
[Thinking](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/thinking#gemini-3-and-later-models).

- **Thought signatures**: Stricter validation of [thought signatures](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/thought-signatures)
improves reliability in multi-turn function calling.

- **Media resolution**: Use the `media_resolution` parameter ( _low_, _medium_,
_high_, or _ultra high_) to control vision processing for multimodal inputs,
impacting token usage and latency. See [Get started with\\
Gemini 3](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/get-started-with-gemini-3#media_resolution)
for default resolution settings.

  - The _ultra high_ media resolution level is only available for the
    `IMAGE` modality.
  - PDF token counts will be listed under the `IMAGE` modality instead of
    the `DOCUMENT` modality in `usage_metadata`.
- **Multimodal function responses**: Function responses can now include
[multimodal objects like images and PDFs in addition to\\
text](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling#mm-fr).

- **Streaming Function calling**: [Stream partial function call arguments](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling#streaming-fc)
to improve user experience during tool use.


For more information on using these features, see [Get started with\\
Gemini\\
3](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/get-started-with-gemini-3).

[Try in Vertex AI](https://console.cloud.google.com/vertex-ai/generative/multimodal/create/text?model=gemini-3-flash-preview) [View in Model Garden](https://console.cloud.google.com/vertex-ai/publishers/google/model-garden/gemini-3-flash-preview) [(Preview) Deploy example app](https://console.cloud.google.com/vertex-ai/studio/multimodal?suggestedPrompt=How%20does%20AI%20work&deploy=true&model=gemini-3-flash-preview)

Note: To use the "Deploy example app" feature, you need a Google Cloud project with billing and Vertex AI API enabled.

| Model ID | `gemini-3-flash-preview` |
| Supported inputs & outputs | - Inputs:<br>   Text, <br>   <br>   Code, <br>   <br>   Images, <br>   <br>   Audio, <br>   <br>   Video, <br>   <br>   PDF<br>- Outputs:<br>   Text |
| Token limits | - Maximum input tokens: 1,048,576<br>- Maximum output tokens: 65,536 |
| Capabilities | Supported<br>- [Grounding with Google Search](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/grounding/grounding-with-google-search)<br>- [Code execution](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/code-execution)<br>- [System instructions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/prompts/system-instruction-introduction)<br>- [Structured output](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/control-generated-output)<br>- [Function calling](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)<br>- [Count Tokens](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/get-token-count)<br>- [Thinking](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/thinking)<br>- [Implicit context caching](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview)<br>- [Explicit context caching](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/context-cache/context-cache-overview)<br>- [Vertex AI RAG Engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)<br>- [Chat completions](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview)<br>- [Computer Use](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/computer-use) previewPreview feature<br>Not supported<br>- [Gemini Live API](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/live-api)<br>- [Content Credentials (C2PA)](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/content-credentials) |
| Consumption options | Supported<br>- [Provisioned Throughput](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/provisioned-throughput)<br>- [Standard PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/standard-paygo)<br>- [Flex PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/flex-paygo)<br>- [Priority PayGo](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/priority-paygo)<br>- [Batch prediction](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/batch-prediction-gemini)<br>Not supported |
| See [Consumption options](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deploy/consumption-options) for more information. |
| Technical specifications |
| **Images** photo | - Maximum images per prompt:<br>   <br>   3000<br>   <br>   <br>- Maximum file size per file for inline data or direct uploads through the console:<br>   <br>   7 MB<br>   <br>   <br>- Maximum file size per file from Google Cloud Storage:<br>   <br>   30 MB<br>   <br>   <br>- Default resolution tokens:<br>   <br>   1120<br>   <br>   <br>- Supported MIME types:<br>   `image/png`, <br>   <br>   `image/jpeg`, <br>   <br>   `image/webp`, <br>   <br>   `image/heic`, <br>   <br>   `image/heif` |
| **Documents** description | - Maximum number of files per prompt:<br>   <br>   3000<br>   <br>   <br>- Maximum number of pages per file:<br>   <br>   3000<br>   <br>   <br>- Maximum file size per file for the API or Cloud Storage imports:<br>   <br>   50 MB<br>   <br>   <br>- Maximum file size per file for direct uploads through the console:<br>   <br>   7 MB<br>   <br>   <br>- Default resolution tokens:<br>   <br>   560<br>   <br>   <br>- OCR for scanned PDFs:<br>   <br>   Not used by default<br>   <br>   <br>- Supported MIME types:<br>   `application/pdf`, <br>   <br>   `text/plain` |
| **Video** videocam | - Maximum video length (with audio):<br>   <br>   Approximately 45 minutes<br>   <br>   <br>- Maximum video length (without audio):<br>   <br>   Approximately 1 hour<br>   <br>   <br>- Maximum number of videos per prompt:<br>   <br>   10<br>   <br>   <br>- Default resolution tokens per frame:<br>   <br>   70<br>   <br>   <br>- Supported MIME types:<br>   `video/x-flv`, <br>   <br>   `video/quicktime`, <br>   <br>   `video/mpeg`, <br>   <br>   `video/mpegs`, <br>   <br>   `video/mpg`, <br>   <br>   `video/mp4`, <br>   <br>   `video/webm`, <br>   <br>   `video/wmv`, <br>   <br>   `video/3gpp` |
| **Audio** mic | - Maximum audio length per prompt:<br>   <br>   Approximately 8.4 hours, or up to 1 million tokens<br>   <br>   <br>- Maximum number of audio files per prompt:<br>   <br>   1<br>   <br>   <br>- Speech understanding for:<br>   <br>   Audio summarization, transcription, and translation<br>   <br>   <br>- Supported MIME types:<br>   `audio/x-aac`, <br>   <br>   `audio/flac`, <br>   <br>   `audio/mp3`, <br>   <br>   `audio/m4a`, <br>   <br>   `audio/mpeg`, <br>   <br>   `audio/mpga`, <br>   <br>   `audio/mp4`, <br>   <br>   `audio/ogg`, <br>   <br>   `audio/pcm`, <br>   <br>   `audio/wav`, <br>   <br>   `audio/webm` |
| **Parameter defaults** tune | - Temperature: 0.0-2.0 (default 1.0)<br>- topP: 0.0-1.0 (default 0.95)<br>- topK: 64 (fixed)<br>- candidateCount: 1–8 (default 1) |
| Supported regions |
| Model availability | Global<br>- global |
| See [Deployments and endpoints](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/learn/locations) for more information. |
| Knowledge cutoff date | January 2025 |
| Versions | - `gemini-3-flash-preview`<br>  - Launch stage: Public preview<br>  - Release date: December 17, 2025 |
| Supported languages | See [Supported languages](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models#expandable-1). |
| Pricing | See [Pricing](https://docs.cloud.google.com/vertex-ai/generative-ai/pricing). |

Was this helpful?



 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-04-17 UTC.


Need to tell us more?






\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Hard to understand","hardToUnderstand","thumb-down"\],\["Incorrect information or sample code","incorrectInformationOrSampleCode","thumb-down"\],\["Missing the information/samples I need","missingTheInformationSamplesINeed","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2026-04-17 UTC."\],\[\],\[\]\]
