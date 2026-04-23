[Skip to main content](https://pypi.org/project/google-genai/#content) Switch to mobile version

Join us in Long Beach, CA starting May 13, 2026. Grab your ticket and discounted hotel today before they’re gone!
[REGISTER FOR PYCON US!](https://us.pycon.org/2026/attend/information/)

Search PyPISearch

# google-genai 1.73.1

pip install google-genaiCopy PIP instructions

[Latest version](https://pypi.org/project/google-genai/)

Released: Apr 14, 2026

GenAI Python SDK

### Navigation

### Verified details

_These details have been [verified by PyPI](https://docs.pypi.org/project_metadata/#verified-details)_

###### Maintainers

[![Avatar for gcloudpypi from gravatar.com](https://pypi-camo.freetls.fastly.net/256f37d0c08ce56870522d1b168937f9039b0065/68747470733a2f2f7365637572652e67726176617461722e636f6d2f6176617461722f62366461363362613435623733393138633436356135666564373361616237633f73697a653d3530)gcloudpypi](https://pypi.org/user/gcloudpypi/)[![Avatar for vertex_ai from gravatar.com](https://pypi-camo.freetls.fastly.net/a2bc293e93325c3e56382b9c63d94849c4d8b325/68747470733a2f2f7365637572652e67726176617461722e636f6d2f6176617461722f65313738333038333866623031663634633136626534616233316238316161613f73697a653d3530)vertex\_ai](https://pypi.org/user/vertex_ai/)

### Unverified details

_These details have **not** been verified by PyPI_

###### Project links

- [Homepage](https://github.com/googleapis/python-genai)

###### Meta

- **License Expression:** Apache-2.0


_[SPDX](https://spdx.org/licenses/) [License Expression](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)_
- **Author:** [Google LLC](mailto:googleapis-packages@google.com)
- **Requires:** Python >=3.10

- **Provides-Extra:**`aiohttp`
, `local-tokenizer`
, `pyopenssl`

###### Classifiers

- **Intended Audience**  - [Developers](https://pypi.org/search/?c=Intended+Audience+%3A%3A+Developers)
- **Operating System**  - [OS Independent](https://pypi.org/search/?c=Operating+System+%3A%3A+OS+Independent)
- **Programming Language**  - [Python](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python)
  - [Python :: 3](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3)
  - [Python :: 3.10](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.10)
  - [Python :: 3.11](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.11)
  - [Python :: 3.12](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.12)
  - [Python :: 3.13](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.13)
  - [Python :: 3.14](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.14)
- **Topic**  - [Internet](https://pypi.org/search/?c=Topic+%3A%3A+Internet)
  - [Software Development :: Libraries :: Python Modules](https://pypi.org/search/?c=Topic+%3A%3A+Software+Development+%3A%3A+Libraries+%3A%3A+Python+Modules)

[Report project as malware](https://pypi.org/project/google-genai/submit-malware-report/)

## Project description

# Google Gen AI SDK

[![PyPI version](https://pypi-camo.freetls.fastly.net/bcefeb5f1d13dae2b02b880fb725a08be01c86d5/68747470733a2f2f696d672e736869656c64732e696f2f707970692f762f676f6f676c652d67656e61692e737667)](https://pypi.org/project/google-genai/)![Python support](https://pypi-camo.freetls.fastly.net/c8c78ba4774ab940cff14e239fa198ee044fac69/68747470733a2f2f696d672e736869656c64732e696f2f707970692f707976657273696f6e732f676f6f676c652d67656e6169)[![PyPI - Downloads](https://pypi-camo.freetls.fastly.net/f19390ec6151b52a7f056e3c5dc37cc8f08495b5/68747470733a2f2f696d672e736869656c64732e696f2f707970692f64772f676f6f676c652d67656e6169)](https://pypistats.org/packages/google-genai)

* * *

**Documentation:** [https://googleapis.github.io/python-genai/](https://googleapis.github.io/python-genai/)

* * *

Google Gen AI Python SDK provides an interface for developers to integrate
Google's generative models into their Python applications. It supports the
[Gemini Developer API](https://ai.google.dev/gemini-api/docs) and
[Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)
APIs.

## Code Generation

Generative models are often unaware of recent API and SDK updates and may suggest outdated or legacy code.

We recommend using our Code Generation instructions [`codegen_instructions.md`](https://raw.githubusercontent.com/googleapis/python-genai/refs/heads/main/codegen_instructions.md) when generating Google Gen AI SDK code to guide your model towards using the more recent SDK features. Copy and paste the instructions into your development environment to provide the model with the necessary context.

## Installation

```
pip install google-genai
```

With `uv`:

```
uv pip install google-genai
```

## Imports

```
from google import genai
from google.genai import types
```

## Create a client

Please run one of the following code blocks to create a client for
different services ( [Gemini Developer API](https://ai.google.dev/gemini-api/docs) or [Vertex AI](https://cloud.google.com/vertex-ai/generative-ai/docs/learn/overview)).

```
from google import genai

# Only run this block for Gemini Developer API
client = genai.Client(api_key='GEMINI_API_KEY')
```

```
from google import genai

# Only run this block for Vertex AI API
client = genai.Client(
    vertexai=True, project='your-project-id', location='us-central1'
)
```

## Using types

All API methods support Pydantic types and dictionaries, which you can access
from `google.genai.types`. You can import the types module with the following:

```
from google.genai import types
```

Below is an example `generate_content()` call using types from the types module:

```
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=types.Part.from_text(text='Why is the sky blue?'),
    config=types.GenerateContentConfig(
        temperature=0,
        top_p=0.95,
        top_k=20,
    ),
)
```

Alternatively, you can accomplish the same request using dictionaries instead of
types:

```
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents={'text': 'Why is the sky blue?'},
    config={
        'temperature': 0,
        'top_p': 0.95,
        'top_k': 20,
    },
)
```

**(Optional) Using environment variables:**

You can create a client by configuring the necessary environment variables.
Configuration setup instructions depends on whether you're using the Gemini
Developer API or the Gemini API in Vertex AI.

**Gemini Developer API:** Set the `GEMINI_API_KEY` or `GOOGLE_API_KEY`.
It will automatically be picked up by the client. It's recommended that you
set only one of those variables, but if both are set, `GOOGLE_API_KEY` takes
precedence.

```
export GEMINI_API_KEY='your-api-key'
```

**Gemini API on Vertex AI:** Set `GOOGLE_GENAI_USE_VERTEXAI`,
`GOOGLE_CLOUD_PROJECT` and `GOOGLE_CLOUD_LOCATION`, as shown below:

```
export GOOGLE_GENAI_USE_VERTEXAI=true
export GOOGLE_CLOUD_PROJECT='your-project-id'
export GOOGLE_CLOUD_LOCATION='us-central1'
```

```
from google import genai

client = genai.Client()
```

## Close a client

Explicitly close the sync client to ensure that resources, such as the
underlying HTTP connections, are properly cleaned up and closed.

```
from google.genai import Client

client = Client()
response_1 = client.models.generate_content(
    model=MODEL_ID,
    contents='Hello',
)
response_2 = client.models.generate_content(
    model=MODEL_ID,
    contents='Ask a question',
)
# Close the sync client to release resources.
client.close()
```

To explicitly close the async client:

```
from google.genai import Client

aclient = Client(
    vertexai=True, project='my-project-id', location='us-central1'
).aio
response_1 = await aclient.models.generate_content(
    model=MODEL_ID,
    contents='Hello',
)
response_2 = await aclient.models.generate_content(
    model=MODEL_ID,
    contents='Ask a question',
)
# Close the async client to release resources.
await aclient.aclose()
```

## Client context managers

By using the sync client context manager, it will close the underlying
sync client when exiting the with block and avoid httpx "client has been closed" error like [issues#1763](https://github.com/googleapis/python-genai/issues/1763).

```
from google.genai import Client

with Client() as client:
    response_1 = client.models.generate_content(
        model=MODEL_ID,
        contents='Hello',
    )
    response_2 = client.models.generate_content(
        model=MODEL_ID,
        contents='Ask a question',
    )
```

By using the async client context manager, it will close the underlying
async client when exiting the with block.

```
from google.genai import Client

async with Client().aio as aclient:
    response_1 = await aclient.models.generate_content(
        model=MODEL_ID,
        contents='Hello',
    )
    response_2 = await aclient.models.generate_content(
        model=MODEL_ID,
        contents='Ask a question',
    )
```

### API Selection

By default, the SDK uses the beta API endpoints provided by Google to support
preview features in the APIs. The stable API endpoints can be selected by
setting the API version to `v1`.

To set the API version use `http_options`. For example, to set the API version
to `v1` for Vertex AI:

```
from google import genai
from google.genai import types

client = genai.Client(
    vertexai=True,
    project='your-project-id',
    location='us-central1',
    http_options=types.HttpOptions(api_version='v1')
)
```

To set the API version to `v1alpha` for the Gemini Developer API:

```
from google import genai
from google.genai import types

client = genai.Client(
    api_key='GEMINI_API_KEY',
    http_options=types.HttpOptions(api_version='v1alpha')
)
```

### Faster async client option: Aiohttp

By default we use httpx for both sync and async client implementations. In order
to have faster performance, you may install `google-genai[aiohttp]`. In Gen AI
SDK we configure `trust_env=True` to match with the default behavior of httpx.
Additional args of `aiohttp.ClientSession.request()` ( [see `_RequestOptions` args](https://github.com/aio-libs/aiohttp/blob/v3.12.13/aiohttp/client.py#L170)) can be passed
through the following way:

```
http_options = types.HttpOptions(
    async_client_args={'cookies': ..., 'ssl': ...},
)

client=Client(..., http_options=http_options)
```

### Proxy

Both httpx and aiohttp libraries use `urllib.request.getproxies` from
environment variables. Before client initialization, you may set proxy (and
optional `SSL_CERT_FILE`) by setting the environment variables:

```
export HTTPS_PROXY='http://username:password@proxy_uri:port'
export SSL_CERT_FILE='client.pem'
```

If you need `socks5` proxy, httpx [supports](https://www.python-httpx.org/advanced/proxies/#socks)`socks5` proxy if you pass it via
args to `httpx.Client()`. You may install `httpx[socks]` to use it.
Then, you can pass it through the following way:

```
http_options = types.HttpOptions(
    client_args={'proxy': 'socks5://user:pass@host:port'},
    async_client_args={'proxy': 'socks5://user:pass@host:port'},
)

client=Client(..., http_options=http_options)
```

### Custom base url

In some cases you might need a custom base url (for example, API gateway proxy
server) and bypass some authentication checks for project, location, or API key.
You may pass the custom base url like this:

```
client = Client(
    vertexai=True,
    http_options=types.HttpOptionsDict(
        base_url='https://test-api-gateway-proxy.com',
        base_url_resource_scope=types.ResourceScope.COLLECTION,
    ),
)

response = client.models.generate_content(
    model='gemini-3-pro-preview', contents='Why is the sky blue?'
)
```

If `base_url_resource_scope=types.ResourceScope.COLLECTION`, the resource name
will not include api version, project, or location.

Expected request url will be:
[https://test-api-gateway-proxy.com/publishers/google/models/gemini-3-pro-preview](https://test-api-gateway-proxy.com/publishers/google/models/gemini-3-pro-preview)

## Types

Parameter types can be specified as either dictionaries(`TypedDict`) or
[Pydantic Models](https://pydantic.readthedocs.io/en/stable/model.html).
Pydantic model types are available in the `types` module.

## Models

The `client.models` module exposes model inferencing and model getters.
See the 'Create a client' section above to initialize a client.

### Generate Content

#### with text content input (text output)

```
response = client.models.generate_content(
    model='gemini-2.5-flash', contents='Why is the sky blue?'
)
print(response.text)
```

#### with text content input (image output)

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash-image',
    contents='A cartoon infographic for flying sneakers',
    config=types.GenerateContentConfig(
        response_modalities=["IMAGE"],
        image_config=types.ImageConfig(
            aspect_ratio="9:16",
        ),
    ),
)

for part in response.parts:
    if part.inline_data:
        generated_image = part.as_image()
        generated_image.show()
```

#### with uploaded file (Gemini Developer API only)

Download the file in console.

```
!wget -q https://storage.googleapis.com/generativeai-downloads/data/a11.txt
```

python code.

```
file = client.files.upload(file='a11.txt')
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=['Could you summarize this file?', file]
)
print(response.text)
```

#### How to structure `contents` argument for `generate_content`

The SDK always converts the inputs to the `contents` argument into
`list[types.Content]`.
The following shows some common ways to provide your inputs.

##### Provide a `list[types.Content]`

This is the canonical way to provide contents, SDK will not do any conversion.

##### Provide a `types.Content` instance

```
from google.genai import types

contents = types.Content(
    role='user',
    parts=[types.Part.from_text(text='Why is the sky blue?')]
)
```

SDK converts this to

```
[\
    types.Content(\
        role='user',\
        parts=[types.Part.from_text(text='Why is the sky blue?')]\
    )\
]
```

##### Provide a string

```
contents='Why is the sky blue?'
```

The SDK will assume this is a text part, and it converts this into the following:

```
[\
    types.UserContent(\
        parts=[\
            types.Part.from_text(text='Why is the sky blue?')\
        ]\
    )\
]
```

Where a `types.UserContent` is a subclass of `types.Content`, it sets the
`role` field to be `user`.

##### Provide a list of strings

```
contents=['Why is the sky blue?', 'Why is the cloud white?']
```

The SDK assumes these are 2 text parts, it converts this into a single content,
like the following:

```
[\
    types.UserContent(\
        parts=[\
            types.Part.from_text(text='Why is the sky blue?'),\
            types.Part.from_text(text='Why is the cloud white?'),\
        ]\
    )\
]
```

Where a `types.UserContent` is a subclass of `types.Content`, the
`role` field in `types.UserContent` is fixed to be `user`.

##### Provide a function call part

```
from google.genai import types

contents = types.Part.from_function_call(
    name='get_weather_by_location',
    args={'location': 'Boston'}
)
```

The SDK converts a function call part to a content with a `model` role:

```
[\
    types.ModelContent(\
        parts=[\
            types.Part.from_function_call(\
                name='get_weather_by_location',\
                args={'location': 'Boston'}\
            )\
        ]\
    )\
]
```

Where a `types.ModelContent` is a subclass of `types.Content`, the
`role` field in `types.ModelContent` is fixed to be `model`.

##### Provide a list of function call parts

```
from google.genai import types

contents = [\
    types.Part.from_function_call(\
        name='get_weather_by_location',\
        args={'location': 'Boston'}\
    ),\
    types.Part.from_function_call(\
        name='get_weather_by_location',\
        args={'location': 'New York'}\
    ),\
]
```

The SDK converts a list of function call parts to a content with a `model` role:

```
[\
    types.ModelContent(\
        parts=[\
            types.Part.from_function_call(\
                name='get_weather_by_location',\
                args={'location': 'Boston'}\
            ),\
            types.Part.from_function_call(\
                name='get_weather_by_location',\
                args={'location': 'New York'}\
            )\
        ]\
    )\
]
```

Where a `types.ModelContent` is a subclass of `types.Content`, the
`role` field in `types.ModelContent` is fixed to be `model`.

##### Provide a non function call part

```
from google.genai import types

contents = types.Part.from_uri(
    file_uri: 'gs://generativeai-downloads/images/scones.jpg',
    mime_type: 'image/jpeg',
)
```

The SDK converts all non function call parts into a content with a `user` role.

```
[\
    types.UserContent(parts=[\
        types.Part.from_uri(\
            file_uri: 'gs://generativeai-downloads/images/scones.jpg',\
            mime_type: 'image/jpeg',\
        )\
    ])\
]
```

##### Provide a list of non function call parts

```
from google.genai import types

contents = [\
    types.Part.from_text('What is this image about?'),\
    types.Part.from_uri(\
        file_uri: 'gs://generativeai-downloads/images/scones.jpg',\
        mime_type: 'image/jpeg',\
    )\
]
```

The SDK will convert the list of parts into a content with a `user` role

```
[\
    types.UserContent(\
        parts=[\
            types.Part.from_text('What is this image about?'),\
            types.Part.from_uri(\
                file_uri: 'gs://generativeai-downloads/images/scones.jpg',\
                mime_type: 'image/jpeg',\
            )\
        ]\
    )\
]
```

##### Mix types in contents

You can also provide a list of `types.ContentUnion`. The SDK leaves items of
`types.Content` as is, it groups consecutive non function call parts into a
single `types.UserContent`, and it groups consecutive function call parts into
a single `types.ModelContent`.

If you put a list within a list, the inner list can only contain
`types.PartUnion` items. The SDK will convert the inner list into a single
`types.UserContent`.

### System Instructions and Other Configs

The output of the model can be influenced by several optional settings
available in generate\_content's config parameter. For example, increasing
`max_output_tokens` is essential for longer model responses. To make a model more
deterministic, lowering the `temperature` parameter reduces randomness, with
values near 0 minimizing variability. Capabilities and parameter defaults for
each model is shown in the
[Vertex AI docs](https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash)
and [Gemini API docs](https://ai.google.dev/gemini-api/docs/models) respectively.

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='high',
    config=types.GenerateContentConfig(
        system_instruction='I say high, you say low',
        max_output_tokens=3,
        temperature=0.3,
    ),
)
print(response.text)
```

### List Base Models

To retrieve tuned models, see [list tuned models](https://pypi.org/project/google-genai/#list-tuned-models).

```
for model in client.models.list():
    print(model)
```

```
pager = client.models.list(config={'page_size': 10})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### List Base Models (Asynchronous)

```
async for job in await client.aio.models.list():
    print(job)
```

```
async_pager = await client.aio.models.list(config={'page_size': 10})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Safety Settings

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Say something bad.',
    config=types.GenerateContentConfig(
        safety_settings=[\
            types.SafetySetting(\
                category='HARM_CATEGORY_HATE_SPEECH',\
                threshold='BLOCK_ONLY_HIGH',\
            )\
        ]
    ),
)
print(response.text)
```

### Function Calling

#### Automatic Python function Support

You can pass a Python function directly and it will be automatically
called and responded by default.

```
from google.genai import types

def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return 'sunny'

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(tools=[get_current_weather]),
)

print(response.text)
```

#### Disabling automatic function calling

If you pass in a python function as a tool directly, and do not want
automatic function calling, you can disable automatic function calling
as follows:

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
    ),
)
```

With automatic function calling disabled, you will get a list of function call
parts in the response:

```
function_calls: Optional[List[types.FunctionCall]] = response.function_calls
```

#### Manually declare and invoke a function for function calling

If you don't want to use the automatic function support, you can manually
declare the function and invoke it.

The following example shows how to declare a function and pass it as a tool.
Then you will receive a function call part in the response.

```
from google.genai import types

function = types.FunctionDeclaration(
    name='get_current_weather',
    description='Get the current weather in a given location',
    parameters_json_schema={
        'type': 'object',
        'properties': {
            'location': {
                'type': 'string',
                'description': 'The city and state, e.g. San Francisco, CA',
            }
        },
        'required': ['location'],
    },
)

tool = types.Tool(function_declarations=[function])

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='What is the weather like in Boston?',
    config=types.GenerateContentConfig(tools=[tool]),
)

print(response.function_calls[0])
```

After you receive the function call part from the model, you can invoke the function
and get the function response. And then you can pass the function response to
the model.
The following example shows how to do it for a simple function invocation.

```
from google.genai import types

user_prompt_content = types.Content(
    role='user',
    parts=[types.Part.from_text(text='What is the weather like in Boston?')],
)
function_call_part = response.function_calls[0]
function_call_content = response.candidates[0].content

try:
    function_result = get_current_weather(
        **function_call_part.function_call.args
    )
    function_response = {'result': function_result}
except (
    Exception
) as e:  # instead of raising the exception, you can let the model handle it
    function_response = {'error': str(e)}

function_response_part = types.Part.from_function_response(
    name=function_call_part.name,
    response=function_response,
)
function_response_content = types.Content(
    role='tool', parts=[function_response_part]
)

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[\
        user_prompt_content,\
        function_call_content,\
        function_response_content,\
    ],
    config=types.GenerateContentConfig(
        tools=[tool],
    ),
)

print(response.text)
```

#### Function calling with `ANY` tools config mode

If you configure function calling mode to be `ANY`, then the model will always
return function call parts. If you also pass a python function as a tool, by
default the SDK will perform automatic function calling until the remote calls exceed the
maximum remote call for automatic function calling (default to 10 times).

If you'd like to disable automatic function calling in `ANY` mode:

```
from google.genai import types

def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            disable=True
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```

If you'd like to set `x` number of automatic function call turns, you can
configure the maximum remote calls to be `x + 1`.
Assuming you prefer `1` turn for automatic function calling.

```
from google.genai import types

def get_current_weather(location: str) -> str:
    """Returns the current weather.

    Args:
        location: The city and state, e.g. San Francisco, CA
    """
    return "sunny"

response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the weather like in Boston?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(
            maximum_remote_calls=2
        ),
        tool_config=types.ToolConfig(
            function_calling_config=types.FunctionCallingConfig(mode='ANY')
        ),
    ),
)
```

#### Model Context Protocol (MCP) support (experimental)

Built-in [MCP](https://modelcontextprotocol.io/introduction) support is an
experimental feature. You can pass a local MCP server as a tool directly.

```
import os
import asyncio
from datetime import datetime
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai

client = genai.Client()

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="npx",  # Executable
    args=["-y", "@philschmid/weather-mcp"],  # MCP Server
    env=None,  # Optional environment variables
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Prompt to get the weather for the current day in London.
            prompt = f"What is the weather in London in {datetime.now().strftime('%Y-%m-%d')}?"

            # Initialize the connection between client and server
            await session.initialize()

            # Send request to the model with MCP function declarations
            response = await client.aio.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=genai.types.GenerateContentConfig(
                    temperature=0,
                    tools=[session],  # uses the session, will automatically call the tool using automatic function calling
                ),
            )
            print(response.text)

# Start the asyncio event loop and run the main function
asyncio.run(run())
```

### JSON Response Schema

However you define your schema, don't duplicate it in your input prompt,
including by giving examples of expected JSON output. If you do, the generated
output might be lower in quality.

#### JSON Schema support

Schemas can be provided as standard JSON schema.

```
user_profile = {
    'properties': {
        'age': {
            'anyOf': [\
                {'maximum': 20, 'minimum': 0, 'type': 'integer'},\
                {'type': 'null'},\
            ],
            'title': 'Age',
        },
        'username': {
            'description': "User's unique name",
            'title': 'Username',
            'type': 'string',
        },
    },
    'required': ['username', 'age'],
    'title': 'User Schema',
    'type': 'object',
}

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Give me a random user profile.',
    config={
        'response_mime_type': 'application/json',
        'response_json_schema': user_profile
    },
)
print(response.text)
```

#### Pydantic Model Schema support

Schemas can be provided as Pydantic Models.

```
from pydantic import BaseModel
from google.genai import types

class CountryInfo(BaseModel):
    name: str
    population: int
    capital: str
    continent: str
    gdp: int
    official_language: str
    total_area_sq_mi: int

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_json_schema=CountryInfo.model_json_schema(),
    ),
)
print(response.text)
```

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Give me information for the United States.',
    config=types.GenerateContentConfig(
        response_mime_type='application/json',
        response_json_schema={
            'required': [\
                'name',\
                'population',\
                'capital',\
                'continent',\
                'gdp',\
                'official_language',\
                'total_area_sq_mi',\
            ],
            'properties': {
                'name': {'type': 'STRING'},
                'population': {'type': 'INTEGER'},
                'capital': {'type': 'STRING'},
                'continent': {'type': 'STRING'},
                'gdp': {'type': 'INTEGER'},
                'official_language': {'type': 'STRING'},
                'total_area_sq_mi': {'type': 'INTEGER'},
            },
            'type': 'OBJECT',
        },
    ),
)
print(response.text)
```

### Generate Content (Synchronous Streaming)

Generate content in a streaming format so that the model outputs streams back
to you, rather than being returned as one chunk.

#### Streaming for text content

```
for chunk in client.models.generate_content_stream(
    model='gemini-2.5-flash', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

#### Streaming for image content

If your image is stored in [Google Cloud Storage](https://cloud.google.com/storage),
you can use the `from_uri` class method to create a `Part` object.

```
from google.genai import types

for chunk in client.models.generate_content_stream(
    model='gemini-2.5-flash',
    contents=[\
        'What is this image about?',\
        types.Part.from_uri(\
            file_uri='gs://generativeai-downloads/images/scones.jpg',\
            mime_type='image/jpeg',\
        ),\
    ],
):
    print(chunk.text, end='')
```

If your image is stored in your local file system, you can read it in as bytes
data and use the `from_bytes` class method to create a `Part` object.

```
from google.genai import types

YOUR_IMAGE_PATH = 'your_image_path'
YOUR_IMAGE_MIME_TYPE = 'your_image_mime_type'
with open(YOUR_IMAGE_PATH, 'rb') as f:
    image_bytes = f.read()

for chunk in client.models.generate_content_stream(
    model='gemini-2.5-flash',
    contents=[\
        'What is this image about?',\
        types.Part.from_bytes(data=image_bytes, mime_type=YOUR_IMAGE_MIME_TYPE),\
    ],
):
    print(chunk.text, end='')
```

### Generate Content (Asynchronous Non Streaming)

`client.aio` exposes all the analogous [`async` methods](https://docs.python.org/3/library/asyncio.html)
that are available on `client`. Note that it applies to all the modules.

For example, `client.aio.models.generate_content` is the `async` version
of `client.models.generate_content`

```
response = await client.aio.models.generate_content(
    model='gemini-2.5-flash', contents='Tell me a story in 300 words.'
)

print(response.text)
```

### Generate Content (Asynchronous Streaming)

```
async for chunk in await client.aio.models.generate_content_stream(
    model='gemini-2.5-flash', contents='Tell me a story in 300 words.'
):
    print(chunk.text, end='')
```

### Count Tokens and Compute Tokens

```
response = client.models.count_tokens(
    model='gemini-2.5-flash',
    contents='why is the sky blue?',
)
print(response)
```

#### Compute Tokens

Compute tokens is only supported in Vertex AI.

```
response = client.models.compute_tokens(
    model='gemini-2.5-flash',
    contents='why is the sky blue?',
)
print(response)
```

##### Async

```
response = await client.aio.models.count_tokens(
    model='gemini-2.5-flash',
    contents='why is the sky blue?',
)
print(response)
```

#### Local Count Tokens

```
tokenizer = genai.LocalTokenizer(model_name='gemini-2.5-flash')
result = tokenizer.count_tokens("What is your name?")
```

#### Local Compute Tokens

```
tokenizer = genai.LocalTokenizer(model_name='gemini-2.5-flash')
result = tokenizer.compute_tokens("What is your name?")
```

### Embed Content

```
response = client.models.embed_content(
    model='gemini-embedding-001',
    contents='why is the sky blue?',
)
print(response)
```

```
from google.genai import types

response = client.models.embed_content(
    model='gemini-embedding-001',
    contents=['why is the sky blue?', 'What is your age?'],
    config=types.EmbedContentConfig(output_dimensionality=10),
)

print(response)
```

### Imagen

#### Generate Images

```
from google.genai import types

response1 = client.models.generate_images(
    model='imagen-4.0-generate-001',
    prompt='An umbrella in the foreground, and a rainy night sky in the background',
    config=types.GenerateImagesConfig(
        number_of_images=1,
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response1.generated_images[0].image.show()
```

#### Upscale Image

Upscale image is only supported in Vertex AI.

```
from google.genai import types

response2 = client.models.upscale_image(
    model='imagen-4.0-upscale-preview',
    image=response1.generated_images[0].image,
    upscale_factor='x2',
    config=types.UpscaleImageConfig(
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response2.generated_images[0].image.show()
```

#### Edit Image

Edit image uses a separate model from generate and upscale.

Edit image is only supported in Vertex AI.

```
# Edit the generated image from above
from google.genai import types
from google.genai.types import RawReferenceImage, MaskReferenceImage

raw_ref_image = RawReferenceImage(
    reference_id=1,
    reference_image=response1.generated_images[0].image,
)

# Model computes a mask of the background
mask_ref_image = MaskReferenceImage(
    reference_id=2,
    config=types.MaskReferenceConfig(
        mask_mode='MASK_MODE_BACKGROUND',
        mask_dilation=0,
    ),
)

response3 = client.models.edit_image(
    model='imagen-3.0-capability-001',
    prompt='Sunlight and clear sky',
    reference_images=[raw_ref_image, mask_ref_image],
    config=types.EditImageConfig(
        edit_mode='EDIT_MODE_INPAINT_INSERTION',
        number_of_images=1,
        include_rai_reason=True,
        output_mime_type='image/jpeg',
    ),
)
response3.generated_images[0].image.show()
```

### Veo

Support for generating videos is considered public preview

#### Generate Videos (Text to Video)

```
from google.genai import types

# Create operation
operation = client.models.generate_videos(
    model='veo-3.1-generate-preview',
    prompt='A neon hologram of a cat driving at top speed',
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        duration_seconds=5,
        enhance_prompt=True,
    ),
)

# Poll operation
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

video = operation.response.generated_videos[0].video
video.show()
```

#### Generate Videos (Image to Video)

```
from google.genai import types

# Read local image (uses mimetypes.guess_type to infer mime type)
image = types.Image.from_file("local/path/file.png")

# Create operation
operation = client.models.generate_videos(
    model='veo-3.1-generate-preview',
    # Prompt is optional if image is provided
    prompt='Night sky',
    image=image,
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        duration_seconds=5,
        enhance_prompt=True,
        # Can also pass an Image into last_frame for frame interpolation
    ),
)

# Poll operation
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

video = operation.response.generated_videos[0].video
video.show()
```

#### Generate Videos (Video to Video)

Currently, only Gemini Developer API supports video extension on Veo 3.1 for
previously generated videos. Vertex supports video extension on Veo 2.0.

```
from google.genai import types

# Read local video (uses mimetypes.guess_type to infer mime type)
video = types.Video.from_file("local/path/video.mp4")

# Create operation
operation = client.models.generate_videos(
    model='veo-3.1-generate-preview',
    # Prompt is optional if Video is provided
    prompt='Night sky',
    # Input video must be in GCS for Vertex or a URI for Gemini
    video=types.Video(
        uri="gs://bucket-name/inputs/videos/cat_driving.mp4",
    ),
    config=types.GenerateVideosConfig(
        number_of_videos=1,
        duration_seconds=5,
        enhance_prompt=True,
    ),
)

# Poll operation
while not operation.done:
    time.sleep(20)
    operation = client.operations.get(operation)

video = operation.response.generated_videos[0].video
video.show()
```

## Chats

Create a chat session to start a multi-turn conversations with the model. Then,
use `chat.send_message` function multiple times within the same chat session so
that it can reflect on its previous responses (i.e., engage in an ongoing
conversation). See the 'Create a client' section above to initialize a client.

### Send Message (Synchronous Non-Streaming)

```
chat = client.chats.create(model='gemini-2.5-flash')
response = chat.send_message('tell me a story')
print(response.text)
response = chat.send_message('summarize the story you told me in 1 sentence')
print(response.text)
```

### Send Message (Synchronous Streaming)

```
chat = client.chats.create(model='gemini-2.5-flash')
for chunk in chat.send_message_stream('tell me a story'):
    print(chunk.text)
```

### Send Message (Asynchronous Non-Streaming)

```
chat = client.aio.chats.create(model='gemini-2.5-flash')
response = await chat.send_message('tell me a story')
print(response.text)
```

### Send Message (Asynchronous Streaming)

```
chat = client.aio.chats.create(model='gemini-2.5-flash')
async for chunk in await chat.send_message_stream('tell me a story'):
    print(chunk.text)
```

## Files

Files are only supported in Gemini Developer API. See the 'Create a client'
section above to initialize a client.

```
!gcloud storage cp gs://cloud-samples-data/generative-ai/pdf/2312.11805v3.pdf .
!gcloud storage cp gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf .
```

### Upload

```
file1 = client.files.upload(file='2312.11805v3.pdf')
file2 = client.files.upload(file='2403.05530.pdf')

print(file1)
print(file2)
```

### Get

```
file1 = client.files.upload(file='2312.11805v3.pdf')
file_info = client.files.get(name=file1.name)
```

### Delete

```
file3 = client.files.upload(file='2312.11805v3.pdf')

client.files.delete(name=file3.name)
```

## Caches

`client.caches` contains the control plane APIs for cached content. See the
'Create a client' section above to initialize a client.

### Create

```
from google.genai import types

if client.vertexai:
    file_uris = [\
        'gs://cloud-samples-data/generative-ai/pdf/2312.11805v3.pdf',\
        'gs://cloud-samples-data/generative-ai/pdf/2403.05530.pdf',\
    ]
else:
    file_uris = [file1.uri, file2.uri]

cached_content = client.caches.create(
    model='gemini-2.5-flash',
    config=types.CreateCachedContentConfig(
        contents=[\
            types.Content(\
                role='user',\
                parts=[\
                    types.Part.from_uri(\
                        file_uri=file_uris[0], mime_type='application/pdf'\
                    ),\
                    types.Part.from_uri(\
                        file_uri=file_uris[1],\
                        mime_type='application/pdf',\
                    ),\
                ],\
            )\
        ],
        system_instruction='What is the sum of the two pdfs?',
        display_name='test cache',
        ttl='3600s',
    ),
)
```

### Get

```
cached_content = client.caches.get(name=cached_content.name)
```

### Generate Content with Caches

```
from google.genai import types

response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Summarize the pdfs',
    config=types.GenerateContentConfig(
        cached_content=cached_content.name,
    ),
)
print(response.text)
```

## Interactions (Preview)

> **Warning:** The Interactions API is in **Beta**. This is a preview of an experimental feature. Features and schemas are subject to **breaking changes**.

The Interactions API is a unified interface for interacting with Gemini models and agents. It simplifies state management, tool orchestration, and long-running tasks.

See the [documentation site](https://ai.google.dev/gemini-api/docs/interactions) for more details.

### Basic Interaction

```
interaction = client.interactions.create(
    model='gemini-2.5-flash',
    input='Tell me a short joke about programming.'
)
print(interaction.outputs[-1].text)
```

### Stateful Conversation

The Interactions API supports server-side state management. You can continue a conversation by referencing the `previous_interaction_id`.

```
# 1. First turn
interaction1 = client.interactions.create(
    model='gemini-2.5-flash',
    input='Hi, my name is Amir.'
)
print(f"Model: {interaction1.outputs[-1].text}")

# 2. Second turn (passing previous_interaction_id)
interaction2 = client.interactions.create(
    model='gemini-2.5-flash',
    input='What is my name?',
    previous_interaction_id=interaction1.id
)
print(f"Model: {interaction2.outputs[-1].text}")
```

### Agents (Deep Research)

You can use specialized agents like `deep-research-pro-preview-12-2025` for complex tasks.

```
import time

# 1. Start the Deep Research Agent
initial_interaction = client.interactions.create(
    input='Research the history of the Google TPUs with a focus on 2025 and 2026.',
    agent='deep-research-pro-preview-12-2025',
    background=True
)
print(f"Research started. Interaction ID: {initial_interaction.id}")

# 2. Poll for results
while True:
    interaction = client.interactions.get(id=initial_interaction.id)
    print(f"Status: {interaction.status}")

    if interaction.status == "completed":
        print("\nFinal Report:\n", interaction.outputs[-1].text)
        break
    elif interaction.status in ["failed", "cancelled"]:
        print(f"Failed with status: {interaction.status}")
        break

    time.sleep(10)
```

### Multimodal Input

You can provide multimodal data (text, images, audio, etc.) in the input list.

```
import base64

# Assuming you have an image loaded as bytes
# base64_image = ...

interaction = client.interactions.create(
    model='gemini-2.5-flash',
    input=[\
        {'type': 'text', 'text': 'Describe the image.'},\
        {'type': 'image', 'data': base64_image, 'mime_type': 'image/png'}\
    ]
)
print(interaction.outputs[-1].text)
```

### Function Calling

You can define custom functions for the model to use. The Interactions API handles the tool selection, and you provide the execution result back to the model.

```
# 1. Define the tool
def get_weather(location: str):
    """Gets the weather for a given location."""
    return f"The weather in {location} is sunny."

weather_tool = {
    'type': 'function',
    'name': 'get_weather',
    'description': 'Gets the weather for a given location.',
    'parameters': {
        'type': 'object',
        'properties': {
            'location': {'type': 'string', 'description': 'The city and state, e.g. San Francisco, CA'}
        },
        'required': ['location']
    }
}

# 2. Send the request with tools
interaction = client.interactions.create(
    model='gemini-2.5-flash',
    input='What is the weather in Mountain View, CA?',
    tools=[weather_tool]
)

# 3. Handle the tool call
for output in interaction.outputs:
    if output.type == 'function_call':
        print(f"Tool Call: {output.name}({output.arguments})")

        # Execute your actual function here
        result = get_weather(**output.arguments)

        # Send result back to the model
        interaction = client.interactions.create(
            model='gemini-2.5-flash',
            previous_interaction_id=interaction.id,
            input=[{\
                'type': 'function_result',\
                'name': output.name,\
                'call_id': output.id,\
                'result': result\
            }]
        )
        print(f"Response: {interaction.outputs[-1].text}")
```

### Built-in Tools

You can also use Google's built-in tools, such as **Google Search** or **Code Execution**.

#### Grounding with Google Search

```
interaction = client.interactions.create(
    model='gemini-2.5-flash',
    input='Who won the last Super Bowl?',
    tools=[{'type': 'google_search'}]
)

# Find the text output (not the GoogleSearchResultContent)
text_output = next((o for o in interaction.outputs if o.type == 'text'), None)
if text_output:
    print(text_output.text)
```

#### Code Execution

```
interaction = client.interactions.create(
    model='gemini-2.5-flash',
    input='Calculate the 50th Fibonacci number.',
    tools=[{'type': 'code_execution'}]
)
print(interaction.outputs[-1].text)
```

### Multimodal Output

The Interactions API can generate multimodal outputs, such as images. You must specify the `response_modalities`.

```
import base64

interaction = client.interactions.create(
    model='gemini-3-pro-image-preview',
    input='Generate an image of a futuristic city.',
    response_modalities=['IMAGE']
)

for output in interaction.outputs:
    if output.type == 'image':
        print(f"Generated image with mime_type: {output.mime_type}")
        # Save the image
        with open("generated_city.png", "wb") as f:
            f.write(base64.b64decode(output.data))
```

## Tunings

`client.tunings` contains tuning job APIs and supports supervised fine
tuning through `tune`. Only supported in Vertex AI. See the 'Create a client'
section above to initialize a client.

### Tune

- Vertex AI supports tuning from GCS source or from a [Vertex AI Multimodal Dataset](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/datasets)

```
from google.genai import types

model = 'gemini-2.5-flash'
training_dataset = types.TuningDataset(
    # or gcs_uri=my_vertex_multimodal_dataset
    gcs_uri='gs://your-gcs-bucket/your-tuning-data.jsonl',
)
```

```
from google.genai import types

tuning_job = client.tunings.tune(
    base_model=model,
    training_dataset=training_dataset,
    config=types.CreateTuningJobConfig(
        epoch_count=1, tuned_model_display_name='test_dataset_examples model'
    ),
)
print(tuning_job)
```

### Get Tuning Job

```
tuning_job = client.tunings.get(name=tuning_job.name)
print(tuning_job)
```

```
import time

completed_states = set(
    [\
        'JOB_STATE_SUCCEEDED',\
        'JOB_STATE_FAILED',\
        'JOB_STATE_CANCELLED',\
    ]
)

while tuning_job.state not in completed_states:
    print(tuning_job.state)
    tuning_job = client.tunings.get(name=tuning_job.name)
    time.sleep(10)
```

#### Use Tuned Model

```
response = client.models.generate_content(
    model=tuning_job.tuned_model.endpoint,
    contents='why is the sky blue?',
)

print(response.text)
```

### Get Tuned Model

```
tuned_model = client.models.get(model=tuning_job.tuned_model.model)
print(tuned_model)
```

### List Tuned Models

To retrieve base models, see [list base models](https://pypi.org/project/google-genai/#list-base-models).

```
for model in client.models.list(config={'page_size': 10, 'query_base': False}):
    print(model)
```

```
pager = client.models.list(config={'page_size': 10, 'query_base': False})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```
async for job in await client.aio.models.list(config={'page_size': 10, 'query_base': False}):
    print(job)
```

```
async_pager = await client.aio.models.list(config={'page_size': 10, 'query_base': False})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Update Tuned Model

```
from google.genai import types

model = pager[0]

model = client.models.update(
    model=model.name,
    config=types.UpdateModelConfig(
        display_name='my tuned model', description='my tuned model description'
    ),
)

print(model)
```

### List Tuning Jobs

```
for job in client.tunings.list(config={'page_size': 10}):
    print(job)
```

```
pager = client.tunings.list(config={'page_size': 10})
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```
async for job in await client.aio.tunings.list(config={'page_size': 10}):
    print(job)
```

```
async_pager = await client.aio.tunings.list(config={'page_size': 10})
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

## Batch Prediction

Only supported in Vertex AI. See the 'Create a client' section above to
initialize a client.

### Create

Vertex AI:

```
# Specify model and source file only, destination and job display name will be auto-populated
job = client.batches.create(
    model='gemini-2.5-flash',
    src='bq://my-project.my-dataset.my-table',  # or "gs://path/to/input/data"
)

print(job)
```

Gemini Developer API:

```
# Create a batch job with inlined requests
batch_job = client.batches.create(
    model="gemini-2.5-flash",
    src=[{\
        "contents": [{\
            "parts": [{\
                "text": "Hello!",\
            }],\
            "role": "user",\
        }],\
        "config": {"response_modalities": ["text"]},\
    }],
)

job
```

In order to create a batch job with file name. Need to upload a json file.
For example `myrequests.json`:

```
{"key":"request_1", "request": {"contents": [{"parts": [{"text":\
 "Explain how AI works in a few words"}]}], "generation_config": {"response_modalities": ["TEXT"]}}}
{"key":"request_2", "request": {"contents": [{"parts": [{"text": "Explain how Crypto works in a few words"}]}]}}
```

Then upload the file.

```
# Upload the file
file = client.files.upload(
    file='myrequests.json',
    config=types.UploadFileConfig(display_name='test-json')
)

# Create a batch job with file name
batch_job = client.batches.create(
    model="gemini-2.5-flash",
    src="files/test-json",
)
```

```
# Get a job by name
job = client.batches.get(name=job.name)

job.state
```

```
completed_states = set(
    [\
        'JOB_STATE_SUCCEEDED',\
        'JOB_STATE_FAILED',\
        'JOB_STATE_CANCELLED',\
        'JOB_STATE_PAUSED',\
    ]
)

while job.state not in completed_states:
    print(job.state)
    job = client.batches.get(name=job.name)
    time.sleep(30)

job
```

### List

```
for job in client.batches.list(config=types.ListBatchJobsConfig(page_size=10)):
    print(job)
```

```
pager = client.batches.list(config=types.ListBatchJobsConfig(page_size=10))
print(pager.page_size)
print(pager[0])
pager.next_page()
print(pager[0])
```

#### Async

```
async for job in await client.aio.batches.list(
    config=types.ListBatchJobsConfig(page_size=10)
):
    print(job)
```

```
async_pager = await client.aio.batches.list(
    config=types.ListBatchJobsConfig(page_size=10)
)
print(async_pager.page_size)
print(async_pager[0])
await async_pager.next_page()
print(async_pager[0])
```

### Delete

```
# Delete the job resource
delete_job = client.batches.delete(name=job.name)

delete_job
```

## Error Handling

To handle errors raised by the model service, the SDK provides this [`APIError`](https://github.com/googleapis/python-genai/blob/main/google/genai/errors.py) class.

```
from google.genai import errors

try:
    client.models.generate_content(
        model="invalid-model-name",
        contents="What is your name?",
    )
except errors.APIError as e:
    print(e.code) # 404
    print(e.message)
```

## Extra Request Body

The `extra_body` field in `HttpOptions` accepts a dictionary of additional JSON
properties to include in the request body. This can be used to access new or
experimental backend features that are not yet formally supported in the SDK.
The structure of the dictionary must match the backend API's request structure.

- Vertex AI backend API docs: [https://cloud.google.com/vertex-ai/docs/reference/rest](https://cloud.google.com/vertex-ai/docs/reference/rest)
- Gemini API backend API docs: [https://ai.google.dev/api/rest](https://ai.google.dev/api/rest)

```
response = client.models.generate_content(
    model="gemini-2.5-pro",
    contents="What is the weather in Boston? and how about Sunnyvale?",
    config=types.GenerateContentConfig(
        tools=[get_current_weather],
        http_options=types.HttpOptions(extra_body={'tool_config': {'function_calling_config': {'mode': 'COMPOSITIONAL'}}}),
    ),
)
```

## Project details

### Verified details

_These details have been [verified by PyPI](https://docs.pypi.org/project_metadata/#verified-details)_

###### Maintainers

[![Avatar for gcloudpypi from gravatar.com](https://pypi-camo.freetls.fastly.net/256f37d0c08ce56870522d1b168937f9039b0065/68747470733a2f2f7365637572652e67726176617461722e636f6d2f6176617461722f62366461363362613435623733393138633436356135666564373361616237633f73697a653d3530)gcloudpypi](https://pypi.org/user/gcloudpypi/)[![Avatar for vertex_ai from gravatar.com](https://pypi-camo.freetls.fastly.net/a2bc293e93325c3e56382b9c63d94849c4d8b325/68747470733a2f2f7365637572652e67726176617461722e636f6d2f6176617461722f65313738333038333866623031663634633136626534616233316238316161613f73697a653d3530)vertex\_ai](https://pypi.org/user/vertex_ai/)

### Unverified details

_These details have **not** been verified by PyPI_

###### Project links

- [Homepage](https://github.com/googleapis/python-genai)

###### Meta

- **License Expression:** Apache-2.0


_[SPDX](https://spdx.org/licenses/) [License Expression](https://spdx.github.io/spdx-spec/v3.0.1/annexes/spdx-license-expressions/)_
- **Author:** [Google LLC](mailto:googleapis-packages@google.com)
- **Requires:** Python >=3.10

- **Provides-Extra:**`aiohttp`
, `local-tokenizer`
, `pyopenssl`

###### Classifiers

- **Intended Audience**  - [Developers](https://pypi.org/search/?c=Intended+Audience+%3A%3A+Developers)
- **Operating System**  - [OS Independent](https://pypi.org/search/?c=Operating+System+%3A%3A+OS+Independent)
- **Programming Language**  - [Python](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python)
  - [Python :: 3](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3)
  - [Python :: 3.10](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.10)
  - [Python :: 3.11](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.11)
  - [Python :: 3.12](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.12)
  - [Python :: 3.13](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.13)
  - [Python :: 3.14](https://pypi.org/search/?c=Programming+Language+%3A%3A+Python+%3A%3A+3.14)
- **Topic**  - [Internet](https://pypi.org/search/?c=Topic+%3A%3A+Internet)
  - [Software Development :: Libraries :: Python Modules](https://pypi.org/search/?c=Topic+%3A%3A+Software+Development+%3A%3A+Libraries+%3A%3A+Python+Modules)

## Release history[Release notifications](https://pypi.org/help/\#project-release-notifications) \|  [RSS feed](https://pypi.org/rss/project/google-genai/releases.xml)

This version

![](https://pypi.org/static/images/blue-cube.572a5bfb.svg)

[1.73.1\\
\\
\\
Apr 14, 2026](https://pypi.org/project/google-genai/1.73.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.73.0\\
\\
\\
Apr 13, 2026](https://pypi.org/project/google-genai/1.73.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.72.0\\
\\
\\
Apr 9, 2026](https://pypi.org/project/google-genai/1.72.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.71.0\\
\\
\\
Apr 8, 2026](https://pypi.org/project/google-genai/1.71.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.70.0\\
\\
\\
Apr 1, 2026](https://pypi.org/project/google-genai/1.70.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.69.0\\
\\
\\
Mar 28, 2026](https://pypi.org/project/google-genai/1.69.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.68.0\\
\\
\\
Mar 17, 2026](https://pypi.org/project/google-genai/1.68.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.67.0\\
\\
\\
Mar 12, 2026](https://pypi.org/project/google-genai/1.67.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.66.0\\
\\
\\
Mar 4, 2026](https://pypi.org/project/google-genai/1.66.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.65.0\\
\\
\\
Feb 25, 2026](https://pypi.org/project/google-genai/1.65.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.64.0\\
\\
\\
Feb 18, 2026](https://pypi.org/project/google-genai/1.64.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.63.0\\
\\
\\
Feb 11, 2026](https://pypi.org/project/google-genai/1.63.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.62.0\\
\\
\\
Feb 4, 2026](https://pypi.org/project/google-genai/1.62.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.61.0\\
\\
\\
Jan 30, 2026](https://pypi.org/project/google-genai/1.61.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.60.0\\
\\
\\
Jan 21, 2026](https://pypi.org/project/google-genai/1.60.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.59.0\\
\\
\\
Jan 15, 2026](https://pypi.org/project/google-genai/1.59.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.58.0\\
\\
\\
Jan 14, 2026](https://pypi.org/project/google-genai/1.58.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.57.0\\
\\
\\
Jan 7, 2026](https://pypi.org/project/google-genai/1.57.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.56.0\\
\\
\\
Dec 17, 2025](https://pypi.org/project/google-genai/1.56.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.55.0\\
\\
\\
Dec 10, 2025](https://pypi.org/project/google-genai/1.55.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.54.0\\
\\
\\
Dec 8, 2025](https://pypi.org/project/google-genai/1.54.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.53.0\\
\\
\\
Dec 3, 2025](https://pypi.org/project/google-genai/1.53.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.52.0\\
\\
\\
Nov 20, 2025](https://pypi.org/project/google-genai/1.52.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.51.0\\
\\
\\
Nov 18, 2025](https://pypi.org/project/google-genai/1.51.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.50.1\\
\\
\\
Nov 13, 2025](https://pypi.org/project/google-genai/1.50.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.50.0\\
\\
\\
Nov 12, 2025](https://pypi.org/project/google-genai/1.50.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.49.0\\
\\
\\
Nov 5, 2025](https://pypi.org/project/google-genai/1.49.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.48.0\\
\\
\\
Nov 3, 2025](https://pypi.org/project/google-genai/1.48.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.47.0\\
\\
\\
Oct 29, 2025](https://pypi.org/project/google-genai/1.47.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.46.0\\
\\
\\
Oct 21, 2025](https://pypi.org/project/google-genai/1.46.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.45.0\\
\\
\\
Oct 15, 2025](https://pypi.org/project/google-genai/1.45.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.44.0\\
\\
\\
Oct 14, 2025](https://pypi.org/project/google-genai/1.44.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.43.0\\
\\
\\
Oct 10, 2025](https://pypi.org/project/google-genai/1.43.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.42.0\\
\\
\\
Oct 8, 2025](https://pypi.org/project/google-genai/1.42.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.41.0\\
\\
\\
Oct 2, 2025](https://pypi.org/project/google-genai/1.41.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.40.0\\
\\
\\
Oct 1, 2025](https://pypi.org/project/google-genai/1.40.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.39.1\\
\\
\\
Sep 26, 2025](https://pypi.org/project/google-genai/1.39.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.39.0\\
\\
\\
Sep 25, 2025](https://pypi.org/project/google-genai/1.39.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.38.0\\
\\
\\
Sep 16, 2025](https://pypi.org/project/google-genai/1.38.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.37.0\\
\\
\\
Sep 16, 2025](https://pypi.org/project/google-genai/1.37.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.36.0\\
\\
\\
Sep 10, 2025](https://pypi.org/project/google-genai/1.36.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.35.0\\
\\
\\
Sep 9, 2025](https://pypi.org/project/google-genai/1.35.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.34.0\\
\\
\\
Sep 8, 2025](https://pypi.org/project/google-genai/1.34.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.33.0\\
\\
\\
Sep 3, 2025](https://pypi.org/project/google-genai/1.33.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.32.0\\
\\
\\
Aug 27, 2025](https://pypi.org/project/google-genai/1.32.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.31.0\\
\\
\\
Aug 18, 2025](https://pypi.org/project/google-genai/1.31.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.30.0\\
\\
\\
Aug 13, 2025](https://pypi.org/project/google-genai/1.30.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.29.0\\
\\
\\
Aug 6, 2025](https://pypi.org/project/google-genai/1.29.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.28.0\\
\\
\\
Jul 30, 2025](https://pypi.org/project/google-genai/1.28.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.27.0\\
\\
\\
Jul 23, 2025](https://pypi.org/project/google-genai/1.27.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.26.0\\
\\
\\
Jul 16, 2025](https://pypi.org/project/google-genai/1.26.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.25.0\\
\\
\\
Jul 9, 2025](https://pypi.org/project/google-genai/1.25.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.24.0\\
\\
\\
Jul 1, 2025](https://pypi.org/project/google-genai/1.24.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.23.0\\
\\
\\
Jun 27, 2025](https://pypi.org/project/google-genai/1.23.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.22.0\\
\\
\\
Jun 25, 2025](https://pypi.org/project/google-genai/1.22.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.21.1\\
\\
\\
Jun 19, 2025](https://pypi.org/project/google-genai/1.21.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.21.0\\
\\
\\
Jun 18, 2025](https://pypi.org/project/google-genai/1.21.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.20.0\\
\\
\\
Jun 11, 2025](https://pypi.org/project/google-genai/1.20.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.19.0\\
\\
\\
Jun 4, 2025](https://pypi.org/project/google-genai/1.19.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.18.0\\
\\
\\
May 30, 2025](https://pypi.org/project/google-genai/1.18.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.17.0\\
\\
\\
May 28, 2025](https://pypi.org/project/google-genai/1.17.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.16.1\\
\\
\\
May 19, 2025](https://pypi.org/project/google-genai/1.16.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.16.0\\
yanked\\
\\
May 19, 2025](https://pypi.org/project/google-genai/1.16.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.15.0\\
\\
\\
May 13, 2025](https://pypi.org/project/google-genai/1.15.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.14.0\\
\\
\\
May 7, 2025](https://pypi.org/project/google-genai/1.14.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.13.0\\
\\
\\
Apr 30, 2025](https://pypi.org/project/google-genai/1.13.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.12.1\\
\\
\\
Apr 24, 2025](https://pypi.org/project/google-genai/1.12.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.12.0\\
yanked\\
\\
Apr 24, 2025](https://pypi.org/project/google-genai/1.12.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.11.0\\
\\
\\
Apr 16, 2025](https://pypi.org/project/google-genai/1.11.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.10.0\\
\\
\\
Apr 8, 2025](https://pypi.org/project/google-genai/1.10.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.9.0\\
\\
\\
Mar 31, 2025](https://pypi.org/project/google-genai/1.9.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.8.0\\
\\
\\
Mar 26, 2025](https://pypi.org/project/google-genai/1.8.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.7.0\\
\\
\\
Mar 18, 2025](https://pypi.org/project/google-genai/1.7.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.6.0\\
yanked\\
\\
Mar 13, 2025](https://pypi.org/project/google-genai/1.6.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.5.0\\
\\
\\
Mar 6, 2025](https://pypi.org/project/google-genai/1.5.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.4.0\\
\\
\\
Mar 4, 2025](https://pypi.org/project/google-genai/1.4.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.3.0\\
\\
\\
Feb 24, 2025](https://pypi.org/project/google-genai/1.3.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.2.0\\
\\
\\
Feb 12, 2025](https://pypi.org/project/google-genai/1.2.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.1.0\\
\\
\\
Feb 10, 2025](https://pypi.org/project/google-genai/1.1.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.0.0\\
\\
\\
Feb 5, 2025](https://pypi.org/project/google-genai/1.0.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[1.0.0rc0\\
pre-release\\
\\
Feb 4, 2025](https://pypi.org/project/google-genai/1.0.0rc0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.8.0\\
\\
\\
Jan 30, 2025](https://pypi.org/project/google-genai/0.8.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.7.0\\
\\
\\
Jan 28, 2025](https://pypi.org/project/google-genai/0.7.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.6.0\\
\\
\\
Jan 21, 2025](https://pypi.org/project/google-genai/0.6.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.5.0\\
\\
\\
Jan 13, 2025](https://pypi.org/project/google-genai/0.5.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.4.0\\
\\
\\
Jan 8, 2025](https://pypi.org/project/google-genai/0.4.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.3.0\\
\\
\\
Dec 17, 2024](https://pypi.org/project/google-genai/0.3.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.2\\
\\
\\
Dec 12, 2024](https://pypi.org/project/google-genai/0.2.2/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.1\\
\\
\\
Dec 12, 2024](https://pypi.org/project/google-genai/0.2.1/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.2.0\\
\\
\\
Dec 11, 2024](https://pypi.org/project/google-genai/0.2.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.1.0\\
\\
\\
Dec 10, 2024](https://pypi.org/project/google-genai/0.1.0/)

![](https://pypi.org/static/images/white-cube.2351a86c.svg)

[0.0.1\\
\\
\\
Dec 10, 2024](https://pypi.org/project/google-genai/0.0.1/)

## Download files

Download the file for your platform. If you're not sure which to choose, learn more about [installing packages](https://packaging.python.org/tutorials/installing-packages/ "External link").

### Source Distribution

[google\_genai-1.73.1.tar.gz](https://files.pythonhosted.org/packages/3d/d8/40f5f107e5a2976bbac52d421f04d14fc221b55a8f05e66be44b2f739fe6/google_genai-1.73.1.tar.gz)
(531.0 kB
[view details](https://pypi.org/project/google-genai/#google_genai-1.73.1.tar.gz))


Uploaded Apr 14, 2026`Source`

### Built Distribution

Filter files by name, interpreter, ABI, and platform.

If you're not sure about the file name format, learn more about [wheel file names](https://packaging.python.org/en/latest/specifications/binary-distribution-format/ "External link").

Copy a direct link to the current filters [https://pypi.org/project/google-genai/#files](https://pypi.org/project/google-genai/#files)
Copy

Showing 1 of 1 file.

File name

InterpreterInterpreterpy3

ABIABInone

PlatformPlatformany

[google\_genai-1.73.1-py3-none-any.whl](https://files.pythonhosted.org/packages/65/af/508e0528015240d710c6763f7c89ff44fab9a94a80b4377e265d692cbfd6/google_genai-1.73.1-py3-none-any.whl)
(783.6 kB
[view details](https://pypi.org/project/google-genai/#google_genai-1.73.1-py3-none-any.whl))


Uploaded Apr 14, 2026`Python 3`

## File details

Details for the file `google_genai-1.73.1.tar.gz`.


### File metadata

- Download URL: [google\_genai-1.73.1.tar.gz](https://files.pythonhosted.org/packages/3d/d8/40f5f107e5a2976bbac52d421f04d14fc221b55a8f05e66be44b2f739fe6/google_genai-1.73.1.tar.gz)
- Upload date: Apr 14, 2026
- Size: 531.0 kB
- Tags: Source
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.2.0 CPython/3.11.2

### File hashes

| Algorithm | Hash digest |  |
| --- | --- | --- |
| SHA256 | `b637e3a3b9e2eccc46f27136d470165803de84eca52abfed2e7352081a4d5a15` | Copy |
| MD5 | `2281705e7d05e949f004ad24c04a2d4b` | Copy |
| BLAKE2b-256 | `3dd840f5f107e5a2976bbac52d421f04d14fc221b55a8f05e66be44b2f739fe6` | Copy |

Hashes for google\_genai-1.73.1.tar.gz

[See more details on using hashes here.](https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode "External link")

### Provenance

The following attestation bundles were made for `google_genai-1.73.1.tar.gz`:


Publisher: `google-cloud-sdk-py@oss-exit-gate-prod.iam.gserviceaccount.com`

Attestations:
_Values shown here reflect the state when the release was signed and may no longer be current._

- Statement:


  - Statement type: [`https://in-toto.io/Statement/v1`](https://in-toto.io/Statement/v1)
  - Predicate type: [`https://docs.pypi.org/attestations/publish/v1`](https://docs.pypi.org/attestations/publish/v1)
  - Subject name: `google_genai-1.73.1.tar.gz`
  - Subject digest: `b637e3a3b9e2eccc46f27136d470165803de84eca52abfed2e7352081a4d5a15`
  - Sigstore transparency entry: [1299122022](https://search.sigstore.dev/?logIndex=1299122022)
  - Sigstore integration time: Apr 14, 2026, 5:06:09 PM

Publication detail:
   - Token Issuer: `https://accounts.google.com`
  - Service Account: `google-cloud-sdk-py@oss-exit-gate-prod.iam.gserviceaccount.com`

## File details

Details for the file `google_genai-1.73.1-py3-none-any.whl`.


### File metadata

- Download URL: [google\_genai-1.73.1-py3-none-any.whl](https://files.pythonhosted.org/packages/65/af/508e0528015240d710c6763f7c89ff44fab9a94a80b4377e265d692cbfd6/google_genai-1.73.1-py3-none-any.whl)
- Upload date: Apr 14, 2026
- Size: 783.6 kB
- Tags: Python 3
- Uploaded using Trusted Publishing? Yes
- Uploaded via: twine/6.2.0 CPython/3.11.2

### File hashes

| Algorithm | Hash digest |  |
| --- | --- | --- |
| SHA256 | `af2d2287d25e42a187de19811ef33beb2e347c7e2bdb4dc8c467d78254e43a2c` | Copy |
| MD5 | `b1889d0c875f60a2221bc5ea4a86d083` | Copy |
| BLAKE2b-256 | `65af508e0528015240d710c6763f7c89ff44fab9a94a80b4377e265d692cbfd6` | Copy |

Hashes for google\_genai-1.73.1-py3-none-any.whl

[See more details on using hashes here.](https://pip.pypa.io/en/stable/topics/secure-installs/#hash-checking-mode "External link")

### Provenance

The following attestation bundles were made for `google_genai-1.73.1-py3-none-any.whl`:


Publisher: `google-cloud-sdk-py@oss-exit-gate-prod.iam.gserviceaccount.com`

Attestations:
_Values shown here reflect the state when the release was signed and may no longer be current._

- Statement:


  - Statement type: [`https://in-toto.io/Statement/v1`](https://in-toto.io/Statement/v1)
  - Predicate type: [`https://docs.pypi.org/attestations/publish/v1`](https://docs.pypi.org/attestations/publish/v1)
  - Subject name: `google_genai-1.73.1-py3-none-any.whl`
  - Subject digest: `af2d2287d25e42a187de19811ef33beb2e347c7e2bdb4dc8c467d78254e43a2c`
  - Sigstore transparency entry: [1299122099](https://search.sigstore.dev/?logIndex=1299122099)
  - Sigstore integration time: Apr 14, 2026, 5:06:10 PM

Publication detail:
   - Token Issuer: `https://accounts.google.com`
  - Service Account: `google-cloud-sdk-py@oss-exit-gate-prod.iam.gserviceaccount.com`

- English
- español
- français
- 日本語
- português (Brasil)
- українська
- Ελληνικά
- Deutsch
- 中文 (简体)
- 中文 (繁體)
- русский
- עברית
- Esperanto
- 한국어

Supported by

[![](https://pypi-camo.freetls.fastly.net/ed7074cadad1a06f56bc520ad9bd3e00d0704c5b/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f6177732d77686974652d6c6f676f2d7443615473387a432e706e67)AWS\\
Cloud computing and Security Sponsor](https://aws.amazon.com/) [![](https://pypi-camo.freetls.fastly.net/8855f7c063a3bdb5b0ce8d91bfc50cf851cc5c51/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f64617461646f672d77686974652d6c6f676f2d6668644c4e666c6f2e706e67)Datadog\\
Monitoring](https://www.datadoghq.com/) [![](https://pypi-camo.freetls.fastly.net/60f709d24f3e4d469f9adc77c65e2f5291a3d165/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f6465706f742d77686974652d6c6f676f2d7038506f476831302e706e67)Depot\\
Continuous Integration](https://depot.dev/) [![](https://pypi-camo.freetls.fastly.net/df6fe8829cbff2d7f668d98571df1fd011f36192/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f666173746c792d77686974652d6c6f676f2d65684d3077735f6f2e706e67)Fastly\\
CDN](https://www.fastly.com/) [![](https://pypi-camo.freetls.fastly.net/420cc8cf360bac879e24c923b2f50ba7d1314fb0/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f676f6f676c652d77686974652d6c6f676f2d616734424e3774332e706e67)Google\\
Download Analytics](https://careers.google.com/) [![](https://pypi-camo.freetls.fastly.net/d01053c02f3a626b73ffcb06b96367fdbbf9e230/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f70696e67646f6d2d77686974652d6c6f676f2d67355831547546362e706e67)Pingdom\\
Monitoring](https://www.pingdom.com/) [![](https://pypi-camo.freetls.fastly.net/67af7117035e2345bacb5a82e9aa8b5b3e70701d/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f73656e7472792d77686974652d6c6f676f2d4a2d6b64742d706e2e706e67)Sentry\\
Error logging](https://sentry.io/for/python/?utm_source=pypi&utm_medium=paid-community&utm_campaign=python-na-evergreen&utm_content=static-ad-pypi-sponsor-learnmore) [![](https://pypi-camo.freetls.fastly.net/b611884ff90435a0575dbab7d9b0d3e60f136466/68747470733a2f2f73746f726167652e676f6f676c65617069732e636f6d2f707970692d6173736574732f73706f6e736f726c6f676f732f737461747573706167652d77686974652d6c6f676f2d5467476c6a4a2d502e706e67)StatusPage\\
Status page](https://statuspage.io/)
