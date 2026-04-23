[Skip to main content](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview#main-content)

[![Gemini API](https://ai.google.dev/_static/googledevai/images/gemini-api-logo.svg)](https://ai.google.dev/)

`/`

Language

- [English](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview)
- [Deutsch](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=de)
- [Español – América Latina](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=es-419)
- [Français](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=fr)
- [Indonesia](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=id)
- [Italiano](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=it)
- [Polski](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=pl)
- [Português – Brasil](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=pt-br)
- [Shqip](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=sq)
- [Tiếng Việt](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=vi)
- [Türkçe](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=tr)
- [Русский](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=ru)
- [עברית](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=he)
- [العربيّة](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=ar)
- [فارسی](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=fa)
- [हिंदी](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=hi)
- [বাংলা](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=bn)
- [ภาษาไทย](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=th)
- [中文 – 简体](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=zh-cn)
- [中文 – 繁體](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=zh-tw)
- [日本語](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=ja)
- [한국어](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview?hl=ko)

[Get API key](https://aistudio.google.com/apikey) [Cookbook](https://github.com/google-gemini/cookbook) [Community](https://discuss.ai.google.dev/c/gemini-api/)Sign in

- On this page
- [gemini-3.1-flash-lite-preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview#gemini-31-flash-lite-preview)
- [Developer guide](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview#developer_guide)

Try the new [Gemini 3.1 Flash TTS Preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-tts-preview) model for expressive, multilingual speech generation.


- [Home](https://ai.google.dev/)
- [Gemini API](https://ai.google.dev/gemini-api)
- [Docs](https://ai.google.dev/gemini-api/docs)



 Send feedback



# Gemini 3.1 Flash-Lite Preview

- On this page
- [gemini-3.1-flash-lite-preview](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview#gemini-31-flash-lite-preview)
- [Developer guide](https://ai.google.dev/gemini-api/docs/models/gemini-3.1-flash-lite-preview#developer_guide)

Our most cost-efficient multimodal model, offering the fastest performance for
high-frequency, lightweight tasks. Gemini 3.1 Flash-Lite is best for high-volume
agentic tasks, simple data extraction, and extremely low-latency applications
where budget and speed are the primary constraints.

[Try in Google AI Studio](https://aistudio.google.com/prompts/new_chat?model=gemini-3.1-flash-lite-preview)

## gemini-3.1-flash-lite-preview

| Property | Description |
| --- | --- |
| id\_cardModel code | `gemini-3.1-flash-lite-preview` |
| saveSupported data types | **Inputs**<br>Text, Image, Video, Audio, and PDF<br>**Output**<br>Text |
| token\_autoToken limits[\[\*\]](https://ai.google.dev/gemini-api/docs/tokens) | **Input token limit**<br>1,048,576<br>**Output token limit**<br>65,536 |
| handymanCapabilities | **Audio generation**<br>Not supported<br>**Batch API**<br>Supported<br>**Caching**<br>Supported<br>**Code execution**<br>Supported<br>**Computer use**<br>Not supported<br>**File search**<br>Supported<br>**Flex inference**<br>Supported<br>**Function calling**<br>Supported<br>**Grounding with Google Maps**<br>Supported<br>**Image generation**<br>Not supported<br>**Live API**<br>Not supported<br>**Priority inference**<br>Supported<br>**Search grounding**<br>Supported<br>**Structured outputs**<br>Supported<br>**Thinking**<br>Supported<br>**URL context**<br>Supported |
| 123Versions | Read the [model version patterns](https://ai.google.dev/gemini-api/docs/models/gemini#model-versions) for more details.<br>- `Preview: gemini-3.1-flash-lite-preview` |
| calendar\_monthLatest update | March 2026 |
| cognition\_2Knowledge cutoff | January 2025 |

## Developer guide

Gemini 3.1 Flash-Lite is best at handling straightforward tasks at significant
scale. Here are some use cases best suited for Gemini 3.1 Flash-Lite:

- **Translation**: Fast, cheap, high-volume translation, such as processing
chat messages, reviews, and support tickets at scale. You can use system
instructions to constrain output to only the translated text with no extra
commentary:




```
text = "Hey, are you down to grab some pizza later? I'm starving!"

response = client.models.generate_content(
      model="gemini-3.1-flash-lite-preview",
      config={
          "system_instruction": "Only output the translated text"
      },
      contents=f"Translate the following text to German: {text}"
)

print(response.text)
```

- **Transcription**: Process recordings, voice notes, or any audio content
where you need a text transcript without spinning up a separate
speech-to-text pipeline. Supports multimodal inputs, so you can pass audio
files directly for transcription:




```
# URL = "https://storage.googleapis.com/generativeai-downloads/data/State_of_the_Union_Address_30_January_1961.mp3"

# Upload the audio file to the GenAI File API
uploaded_file = client.files.upload(file='sample.mp3')

prompt = 'Generate a transcript of the audio.'

response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents=[prompt, uploaded_file]
)

print(response.text)
```

- **Lightweight agentic tasks and data extraction**: Entity extraction,
classification, and lightweight data processing pipelines supported with
structured JSON output. For example, extracting structured data from an
e-commerce customer review:




```
from pydantic import BaseModel, Field

prompt = "Analyze the user review and determine the aspect, sentiment score, summary quote, and return risk"
input_text = "The boots look amazing and the leather is high quality, but they run way too small. I'm sending them back."

class ReviewAnalysis(BaseModel):
      aspect: str = Field(description="The feature mentioned (e.g., Price, Comfort, Style, Shipping)")
      summary_quote: str = Field(description="The specific phrase from the review about this aspect")
      sentiment_score: int = Field(description="1 to 5 (1=worst, 5=best)")
      is_return_risk: bool = Field(description="True if the user mentions returning the item")

response = client.models.generate_content(
      model="gemini-3.1-flash-lite-preview",
      contents=[prompt, input_text],
      config={
          "response_mime_type": "application/json",
          "response_json_schema": ReviewAnalysis.model_json_schema(),
      },
)

print(response.text)
```

- **Document processing and summarization**: Parse PDFs and return concise
summaries, like for building a document processing pipeline or quickly
triaging incoming files:




```
import httpx

# Download a sample PDF document
doc_url = "https://storage.googleapis.com/generativeai-downloads/data/med_gemini.pdf"
doc_data = httpx.get(doc_url).content

prompt = "Summarize this document"
response = client.models.generate_content(
      model="gemini-3.1-flash-lite-preview",
      contents=[\
          types.Part.from_bytes(\
              data=doc_data,\
              mime_type='application/pdf',\
          ),\
          prompt\
      ]
)

print(response.text)
```

- **Model routing**: Use a low-latency and low-cost model as a classifier that
routes queries to the appropriate model based on task complexity. This is a
real pattern in production — the open-source [Gemini CLI](https://geminicli.com/docs/core/#model-fallback) uses Flash-Lite to
classify task complexity and route to Flash or Pro accordingly.




```
FLASH_MODEL = 'flash'
PRO_MODEL = 'pro'

CLASSIFIER_SYSTEM_PROMPT = f"""
You are a specialized Task Routing AI. Your sole function is to analyze the user's request and classify its complexity. Choose between `{FLASH_MODEL}` (SIMPLE) or `{PRO_MODEL}` (COMPLEX).
1.  `{FLASH_MODEL}`: A fast, efficient model for simple, well-defined tasks.
2.  `{PRO_MODEL}`: A powerful, advanced model for complex, open-ended, or multi-step tasks.

A task is COMPLEX if it meets ONE OR MORE of the following criteria:
1.  High Operational Complexity (Est. 4+ Steps/Tool Calls)
2.  Strategic Planning and Conceptual Design
3.  High Ambiguity or Large Scope
4.  Deep Debugging and Root Cause Analysis

A task is SIMPLE if it is highly specific, bounded, and has Low Operational Complexity (Est. 1-3 tool calls).
"""

user_input = "I'm getting an error 'Cannot read property 'map' of undefined' when I click the save button. Can you fix it?"

response_schema = {
"type": "object",
"properties": {
    "reasoning": {
      "type": "string",
      "description": "A brief, step-by-step explanation for the model choice, referencing the rubric."
    },
    "model_choice": {
      "type": "string",
      "enum": [FLASH_MODEL, PRO_MODEL]
    }
},
"required": ["reasoning", "model_choice"]
}

response = client.models.generate_content(
    model="gemini-3.1-flash-lite-preview",
    contents=user_input,
    config={
        "system_instruction": CLASSIFIER_SYSTEM_PROMPT,
        "response_mime_type": "application/json",
        "response_json_schema": response_schema
    },
)

print(response.text)
```

- **Thinking**: For better accuracy for tasks that benefit from step-by-step
  reasoning, configure thinking so the model spends additional compute on
  internal reasoning before producing the final output:




  ```
  response = client.models.generate_content(
      model="gemini-3.1-flash-lite-preview",
      contents="How does AI work?",
      config=types.GenerateContentConfig(
          thinking_config=types.ThinkingConfig(thinking_level="high")
      ),
  )

  print(response.text)
  ```




 Send feedback



Except as otherwise noted, the content of this page is licensed under the [Creative Commons Attribution 4.0 License](https://creativecommons.org/licenses/by/4.0/), and code samples are licensed under the [Apache 2.0 License](https://www.apache.org/licenses/LICENSE-2.0). For details, see the [Google Developers Site Policies](https://developers.google.com/site-policies). Java is a registered trademark of Oracle and/or its affiliates.

Last updated 2026-04-01 UTC.


Need to tell us more?






\[\[\["Easy to understand","easyToUnderstand","thumb-up"\],\["Solved my problem","solvedMyProblem","thumb-up"\],\["Other","otherUp","thumb-up"\]\],\[\["Missing the information I need","missingTheInformationINeed","thumb-down"\],\["Too complicated / too many steps","tooComplicatedTooManySteps","thumb-down"\],\["Out of date","outOfDate","thumb-down"\],\["Samples / code issue","samplesCodeIssue","thumb-down"\],\["Other","otherDown","thumb-down"\]\],\["Last updated 2026-04-01 UTC."\],\[\],\[\]\]
