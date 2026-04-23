[Skip to content](https://developers.openai.com/api/reference/resources/images/methods/edit#_top)

[API Reference](https://developers.openai.com/api/reference)

[Images](https://developers.openai.com/api/reference/resources/images)

Copy Markdown

Open in **ChatGPT**

* * *

**Copy Markdown**

**View as Markdown**

# Create image edit

POST/images/edits

Creates an edited or extended image given one or more source images and a prompt. This endpoint supports GPT Image models (`gpt-image-1.5`, `gpt-image-1`, `gpt-image-1-mini`, and `chatgpt-image-latest`) and `dall-e-2`.

##### Body ParametersJSONExpand Collapse

images: array of object {file\_id, image\_url}

Input image references to edit.
For GPT image models, you can provide up to 16 images.

file\_id: optional string

The File API ID of an uploaded image to use as input.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20images%20%3E%20(schema)%20%3E%20(items)%20%3E%20(property)%20file_id)

image\_url: optional string

A fully qualified URL or base64-encoded data URL.

maxLength20971520

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20images%20%3E%20(schema)%20%3E%20(items)%20%3E%20(property)%20image_url)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20images%20%3E%20(schema))

prompt: string

A text description of the desired image edit.

minLength1

maxLength32000

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20prompt%20%3E%20(schema))

background: optional "transparent"or"opaque"or"auto"

Background behavior for generated image output.

One of the following:

"transparent"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20background%20%3E%20(schema)%20%3E%20(member)%200)

"opaque"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20background%20%3E%20(schema)%20%3E%20(member)%201)

"auto"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20background%20%3E%20(schema)%20%3E%20(member)%202)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20background%20%3E%20(schema))

input\_fidelity: optional "high"or"low"

Controls fidelity to the original input image(s).

One of the following:

"high"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20input_fidelity%20%3E%20(schema)%20%3E%20(member)%200)

"low"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20input_fidelity%20%3E%20(schema)%20%3E%20(member)%201)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20input_fidelity%20%3E%20(schema))

mask: optional object {file\_id, image\_url}

Reference an input image by either URL or uploaded file ID.
Provide exactly one of `image_url` or `file_id`.

file\_id: optional string

The File API ID of an uploaded image to use as input.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20mask%20%3E%20(schema)%20%3E%20(property)%20file_id)

image\_url: optional string

A fully qualified URL or base64-encoded data URL.

maxLength20971520

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20mask%20%3E%20(schema)%20%3E%20(property)%20image_url)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20mask%20%3E%20(schema))

model: optional stringor"gpt-image-1.5"or"gpt-image-1"or"gpt-image-1-mini"or"chatgpt-image-latest"

The model to use for image editing.

One of the following:

string

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%200)

"gpt-image-1.5"or"gpt-image-1"or"gpt-image-1-mini"or"chatgpt-image-latest"

The model to use for image editing.

One of the following:

"gpt-image-1.5"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%201%20%3E%20(member)%200)

"gpt-image-1"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%201%20%3E%20(member)%201)

"gpt-image-1-mini"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%201%20%3E%20(member)%202)

"chatgpt-image-latest"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%201%20%3E%20(member)%203)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema)%20%3E%20(variant)%201)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20model%20%3E%20(schema))

moderation: optional "low"or"auto"

Moderation level for GPT image models.

One of the following:

"low"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20moderation%20%3E%20(schema)%20%3E%20(member)%200)

"auto"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20moderation%20%3E%20(schema)%20%3E%20(member)%201)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20moderation%20%3E%20(schema))

n: optional number

The number of edited images to generate.

minimum1

maximum10

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20n%20%3E%20(schema))

output\_compression: optional number

Compression level for `jpeg` or `webp` output.

minimum0

maximum100

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20output_compression%20%3E%20(schema))

output\_format: optional "png"or"jpeg"or"webp"

Output image format. Supported for GPT image models.

One of the following:

"png"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20output_format%20%3E%20(schema)%20%3E%20(member)%200)

"jpeg"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20output_format%20%3E%20(schema)%20%3E%20(member)%201)

"webp"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20output_format%20%3E%20(schema)%20%3E%20(member)%202)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20output_format%20%3E%20(schema))

partial\_images: optional number

The number of partial images to generate. This parameter is used for
streaming responses that return partial images. Value must be between 0 and 3.
When set to 0, the response will be a single image sent in one streaming event.

Note that the final image may be sent before the full number of partial images
are generated if the full image is generated more quickly.

maximum3

minimum0

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20partial_images%20%3E%20(schema))

quality: optional "low"or"medium"or"high"or"auto"

Output quality for GPT image models.

One of the following:

"low"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20quality%20%3E%20(schema)%20%3E%20(member)%200)

"medium"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20quality%20%3E%20(schema)%20%3E%20(member)%201)

"high"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20quality%20%3E%20(schema)%20%3E%20(member)%202)

"auto"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20quality%20%3E%20(schema)%20%3E%20(member)%203)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20quality%20%3E%20(schema))

size: optional "auto"or"1024x1024"or"1536x1024"or"1024x1536"

Requested output image size.

One of the following:

"auto"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20size%20%3E%20(schema)%20%3E%20(member)%200)

"1024x1024"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20size%20%3E%20(schema)%20%3E%20(member)%201)

"1536x1024"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20size%20%3E%20(schema)%20%3E%20(member)%202)

"1024x1536"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20size%20%3E%20(schema)%20%3E%20(member)%203)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20size%20%3E%20(schema))

stream: optional boolean

Stream partial image results as events.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20stream%20%3E%20(schema))

user: optional string

A unique identifier representing your end-user, which can help OpenAI
monitor and detect abuse.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(method)%20edit%20%3E%20(params)%200.non_streaming%20%3E%20(param)%20user%20%3E%20(schema))

##### ReturnsExpand Collapse

ImagesResponseobject {created, background, data, 4 more}

The response from the image generation endpoint.

created: number

The Unix timestamp (in seconds) of when the image was created.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20created)

background: optional "transparent"or"opaque"

The background parameter used for the image generation. Either `transparent` or `opaque`.

One of the following:

"transparent"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20background%20%3E%20(member)%200)

"opaque"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20background%20%3E%20(member)%201)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20background)

data: optional array of [Image](https://developers.openai.com/api/reference/resources/images#(resource)%20images%20%3E%20(model)%20image%20%3E%20(schema)) { b64\_json, revised\_prompt, url }

The list of generated images.

b64\_json: optional string

The base64-encoded JSON of the generated image. Returned by default for the GPT image models, and only present if `response_format` is set to `b64_json` for `dall-e-2` and `dall-e-3`.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20image%20%3E%20(schema)%20%3E%20(property)%20b64_json)

revised\_prompt: optional string

For `dall-e-3` only, the revised prompt that was used to generate the image.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20image%20%3E%20(schema)%20%3E%20(property)%20revised_prompt)

url: optional string

When using `dall-e-2` or `dall-e-3`, the URL of the generated image if `response_format` is set to `url` (default value). Unsupported for the GPT image models.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20image%20%3E%20(schema)%20%3E%20(property)%20url)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20data)

output\_format: optional "png"or"webp"or"jpeg"

The output format of the image generation. Either `png`, `webp`, or `jpeg`.

One of the following:

"png"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20output_format%20%3E%20(member)%200)

"webp"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20output_format%20%3E%20(member)%201)

"jpeg"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20output_format%20%3E%20(member)%202)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20output_format)

quality: optional "low"or"medium"or"high"

The quality of the image generated. Either `low`, `medium`, or `high`.

One of the following:

"low"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20quality%20%3E%20(member)%200)

"medium"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20quality%20%3E%20(member)%201)

"high"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20quality%20%3E%20(member)%202)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20quality)

size: optional "1024x1024"or"1024x1536"or"1536x1024"

The size of the image generated. Either `1024x1024`, `1024x1536`, or `1536x1024`.

One of the following:

"1024x1024"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20size%20%3E%20(member)%200)

"1024x1536"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20size%20%3E%20(member)%201)

"1536x1024"

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20size%20%3E%20(member)%202)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20size)

usage: optional object {input\_tokens, input\_tokens\_details, output\_tokens, 2 more}

For `gpt-image-1` only, the token usage information for the image generation.

input\_tokens: number

The number of tokens (images and text) in the input prompt.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20input_tokens)

input\_tokens\_details: object {image\_tokens, text\_tokens}

The input tokens detailed information for the image generation.

image\_tokens: number

The number of image tokens in the input prompt.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20input_tokens_details%20%3E%20(property)%20image_tokens)

text\_tokens: number

The number of text tokens in the input prompt.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20input_tokens_details%20%3E%20(property)%20text_tokens)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20input_tokens_details)

output\_tokens: number

The number of output tokens generated by the model.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20output_tokens)

total\_tokens: number

The total number of tokens (images and text) used for the image generation.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20total_tokens)

output\_tokens\_details: optional object {image\_tokens, text\_tokens}

The output token details for the image generation.

image\_tokens: number

The number of image output tokens generated by the model.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20output_tokens_details%20%3E%20(property)%20image_tokens)

text\_tokens: number

The number of text output tokens generated by the model.

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20output_tokens_details%20%3E%20(property)%20text_tokens)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage%20%3E%20(property)%20output_tokens_details)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema)%20%3E%20(property)%20usage)

[Link to this property](https://developers.openai.com/api/reference/resources/images/methods/edit#(resource)%20images%20%3E%20(model)%20images_response%20%3E%20(schema))

Edit imageStreaming

### Create image edit

HTTP

HTTP

HTTP

TypeScript

TypeScript

Python

Python

Java

Java

Go

Go

Ruby

Ruby

```
curl -s -D >(grep -i x-request-id >&2) \
  -o >(jq -r '.data[0].b64_json' | base64 --decode > gift-basket.png) \
  -X POST "https://api.openai.com/v1/images/edits" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F "model=gpt-image-1.5" \
  -F "image[]=@body-lotion.png" \
  -F "image[]=@bath-bomb.png" \
  -F "image[]=@incense-kit.png" \
  -F "image[]=@soap.png" \
  -F 'prompt=Create a lovely gift basket with these four items in it'
```

### Create image edit

HTTP

HTTP

HTTP

TypeScript

TypeScript

Python

Python

Java

Java

Go

Go

Ruby

Ruby

```
curl -s -N -X POST "https://api.openai.com/v1/images/edits" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -F "model=gpt-image-1.5" \
  -F "image[]=@body-lotion.png" \
  -F "image[]=@bath-bomb.png" \
  -F "image[]=@incense-kit.png" \
  -F "image[]=@soap.png" \
  -F 'prompt=Create a lovely gift basket with these four items in it' \
  -F "stream=true"
```

```
event: image_edit.partial_image
data: {"type":"image_edit.partial_image","b64_json":"...","partial_image_index":0}

event: image_edit.completed
data: {"type":"image_edit.completed","b64_json":"...","usage":{"total_tokens":100,"input_tokens":50,"output_tokens":50,"input_tokens_details":{"text_tokens":10,"image_tokens":40}}}
```

##### Returns Examples

200 example

```
{
  "created": 0,
  "background": "transparent",
  "data": [\
    {\
      "b64_json": "b64_json",\
      "revised_prompt": "revised_prompt",\
      "url": "url"\
    }\
  ],
  "output_format": "png",
  "quality": "low",
  "size": "1024x1024",
  "usage": {
    "input_tokens": 0,
    "input_tokens_details": {
      "image_tokens": 0,
      "text_tokens": 0
    },
    "output_tokens": 0,
    "total_tokens": 0,
    "output_tokens_details": {
      "image_tokens": 0,
      "text_tokens": 0
    }
  }
}
```
