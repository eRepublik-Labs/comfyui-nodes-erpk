[Carl Franzen](https://venturebeat.com/author/carlfranzen)

Published

12:00 pm, PT, April 21, 2026


Updated

12:14 pm, PT, April 21, 2026


![Carl Franzen typing at a PC showing off the capabilities of ChatGPT Images 2.0. ](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1oLxFxfGFj9SctaWVV5dCq%2F4d7928375d881cfc6abc296dc0edfd8c%2FChatGPT_Image_Apr_21__2026__02_55_37_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=85)

Credit: VentureBeat made with ChatGPT Images 2.0.

[Add to Google Preferred Source](https://www.google.com/preferences/source?q=venturebeat.com "Add to Google Preferred Source")

It's been only a few months since OpenAI released its last big improvement to AI image generations in ChatGPT and through its application programming interface (API) — namely, a new image generation model known as [GPT-Image-1.5](https://venturebeat.com/technology/openais-gpt-image-1-5-challenges-google-at-enterprise-grade-visuals), released in December 2025, which brought about improved instruction following, colors, and lighting.

Now, after weeks of testing, the company that kicked off the generative AI boom is [unveiling a far more dramatic and even more impressive update](https://openai.com/index/introducing-chatgpt-images-2-0/): **ChatGPT Images 2.0**, which has been [available not-so-secretly for several weeks on LM Arena AI](https://www.chosun.com/english/industry-en/2026/04/20/FOWR7U6ZPRGFTDTEMH53T5Q5C4/), a third-party testing platform used by OpenAI and other major AI model providers to get early feedback, under the name "duct tape."

Throughout that time, it's already blown early users' minds with its capacity to generate long blocks of text or disparate text panels within the same image, its insanely realistic generation of user interfaces and screenshots from popular websites and platforms, its reproduction of real life figures like OpenAI co-founder and CEO Sam Altman, and its ability to perform web research and put the results into the image itself.

Now today, it's officially rolling out to ChatGPT users on all tiers, and OpenAI confirms it can also produce floor plans, image grids and sets of many smaller images, and character models from multiple angles, and apply almost all of these features to user-uploaded imagery as well.

![OpenAI ChatGPT Images 2.0 character sheet example.](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F5Jdd0Du8IxYmD2SNE9k1q8%2F2a8408181ce95f950dbd6bcaee6d0d13%2FCharacter_Card_Kenji.png%3Fw%3D1000%26q%3D100&w=3840&q=75)

OpenAI ChatGPT Images 2.0 character sheet example. Credit: OpenAI

The update, which encompasses the new `gpt-image-2` model for API users and a suite of "Thinking" features for ChatGPT subscribers, represents a fundamental shift in how the company views visual media. As the official release notes state, "Images are a language, not decoration. A good image does what a good sentence does—it selects, arranges, and reveals".

OpenAI did not release benchmarks to us ahead of time on ChatGPT Images 2.0, but it is safe to say the model is performing at the "state-of-the-art" based on all the outputs I've seen.

The move comes as the AI image model space has seen increasing competition, especially with the release of [Google's Nano Banana 2 image generation model](https://venturebeat.com/technology/googles-nano-banana-2-takes-aim-at-the-production-cost-problem-thats-kept-ai) (also known as Gemini 3 Pro Image or Gemini 3.1 Pro Image) in February 2026, which also offered dense text options "baked into" images similar to ChatGPT Images 2.0. But the latter's fidelity in reproducing user interfaces, screenshots, and multiple image packs at once seem to exceed even Google's latest image model's capabilities in my brief testing and anecdotal usage and observation of other users' images.

OpenAI spokespersons and researchers re-iterated the company's commitments to safety and tagging its image outputs with metadata as AI generated in the face of rising reports — including [one recently from _The New York Times_](https://www.nytimes.com/2026/04/17/business/media/artificial-intelligence-trump-social-media.html)— on AI user-generated characters (AI UGC) being used as the seed for realistic AI videos posted en masse on social media as part of political influence campaigns, including showing support for historically unpopular U.S. President Donald J. Trump with an army of fictitious people masquerading as "real Americans."

When VentureBeat asked in a closed press briefing directly about this story and GPT Images 2.0's potential for usage in deceptive campaigning or advertising/influence campaigns Adele Li, OpenAI's Product Lead for ChatGPT Images, responded:

_"We take safety and security incredibly seriously. That includes anything when it comes to political or election interference. And so while other platforms and companies may not have those safeguards, ChatGPT does, and we take monitoring and protection of our users, as well as the influence that our photos as they are created, incredibly seriously..in the last couple years, we've seen a lot more new entrants into the image generation space with different standards and philosophies as ChatGPT, but we've stayed steady through all that, and we're really proud of releasing this model as it relates to advanced capabilities, but doing so in a safe and protected way."_

OpenAI has also confirmed that it is deprecating GPT-Image-1.5 as the default model across its suite, though it will remain accessible via the API for legacy support. This transition signals OpenAI's confidence that the 2.0 model is a superior replacement for both casual and high-value creative tasks.

## **The reasoning era of AI image generation**

The most significant technical advancement in Images 2.0 is the integration of OpenAI’s "O-series" reasoning capabilities.

Historically, image models have operated as black boxes: you provide a prompt, and a single output is generated. Images 2.0 introduces an "agentic" approach.

When a user selects a "Thinking" model within ChatGPT, the system no longer simply "draws"; it researches, plans, and reasons through the structure of an image before the first pixel is rendered.

During a live press briefing, Li demonstrated this reasoning by uploading a complex PowerPoint file regarding internal product strategies.

Rather than merely creating a related image, the model synthesized the document's core data, identified the correct logos, and produced a professional poster that preserved the specific stylistic inputs of the original file.

In my brief testing — I was given access last night and tested it on a few generations this morning — ChatGPT Images 2.0 is the first image model from OpenAI and one of only two (Nano Banana 2 being the other) that can seemingly accurately reproduce a map of the extent of the Aztec, Maya, and Inca empires at their respective heights along with a fully legible legend, making it useful for educational or internal training purposes on global knowledge and geography.

![ChatGPT Images 2.0 example map of Aztec, Maya and Inca empires' territories](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1PGTc48NpkY1pT8mEaj6mx%2Fca29b2b173d448b4baea248ee23c0e0c%2FChatGPT_Image_Apr_21__2026__02_41_15_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=75)

Credit: VentureBeat made with ChatGPT Images 2.0

This reasoning capability also allows the model to search the web in real-time to ensure visual accuracy for current events or specific technical artifacts.

This is supported by a significantly more recent knowledge cutoff of December 2025, a major leap from previous iterations that struggled with modern context.

The underlying architecture has been "revamped from scratch," according to Research Lead Boyuan Chen. While Chen declined to confirm if the model uses a traditional diffusion or auto-regressive technique, he described it as a "generalist model" or a "GPT for images" that can handle 3D-style perspective shifts and complex spatial reasoning through simple text prompts.

## **Precision, multilingual support and a "wow" factor**

The product experience for Images 2.0 is defined by three major pillars: typography, linguistic diversity, and sequential consistency.

One of the most persistent "tells" of AI-generated imagery has been the inability to render legible text. OpenAI claims Images 2.0 marks a "step change" in this department. The model is now capable of producing readable typography even in dense compositions, such as scientific diagrams, menus, or infographic posters.

A look at the provided "Magazine Cover" sample (Open Scifi) illustrates this precision: every headline, volume number, and even the "Display until" date on the barcode is rendered with crisp, professional alignment that mirrors human-designed layouts.

![A sample magazine cover created with ChatGPT Images 2.0](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F3UAEvTLycvVwaX0rC6mXfE%2F54af20d9531047fe990a412cd5428322%2FMagazine_Cover.png%3Fw%3D1000%26q%3D100&w=3840&q=75)

A sample magazine cover created with ChatGPT Images 2.0. Credit: OpenAI

This capability extends into the "Thinking" mode, where the model can even generate three-page educational visuals—complete with quizzes—that maintain a consistent instructional flow.

OpenAI has also addressed a long-standing Western bias in AI imagery. Images 2.0 is described as a "polyglot" model with significant gains in non-Latin script rendering. Specifically, the model now supports high-fidelity text generation in **Japanese, Korean, Chinese, Hindi, and Bengali**.

In the "Global Language" diagram provided, which explains the water cycle, the model successfully renders complex Korean characters (Hangul) within an educational layout.

![OpenAI ChatGPT Images 2.0 sample diagram](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6te3pyWNxcEq4wPsdonwml%2F3ec8c8ce716f02f425c1c85741a2416c%2FJP_Global_Language.png%3Fw%3D1000%26q%3D100&w=3840&q=75)

OpenAI ChatGPT Images 2.0 sample diagram showcasing multilingual capabilities. Credit: OpenAI

The text is not just translated; it is "rendered correctly but with language that flows coherently," ensuring that labels and explanations feel natively integrated into the design.

For creators working on storyboards or brand campaigns, the most impactful new feature is the ability to generate up to **eight distinct images from a single prompt**. Crucially, these images maintain "character and object continuity" across the series.

Li noted that this solves a "cumbersome" workflow where users previously had to prompt one image at a time and manually stitch them together. This feature enables the creation of entire manga sequences, children's books, or a family of social media graphics that share the same visual DNA.

## **Licensing and availability**

OpenAI’s rollout strategy reflects a clear push toward professional and enterprise adoption. While the base model is available to all users—including those on the free tier—the advanced "Thinking" and "Pro" capabilities are reserved for paid tiers.

- **Free Users:** Have access to the base ImageGen 2.0 model for standard tasks.

- **Plus and Pro Users:** Can access "Thinking" capabilities, which include tool use, web search, and multi-image generation.

- **Pro Users:** Receive additional access to "ImageGen Pro" models for more advanced image generation.

- **API Developers:** Can integrate `gpt-image-2`, which supports resolutions up to 4K (currently in beta) and flexible aspect ratios ranging from a wide 3:1 to a tall 1:3.


[Pricing in the API](https://openai.com/api/pricing/) is as follows, echoing GPT-Image-1.5, the predecessor model, but actually shaving off $2 on the output side:

**Image**
$8.00 for inputs
$2.00 for cached inputs
$30.00 for outputs

**Text**
$5.00 for inputs
$1.25 for cached inputs
$10.00 for outputs

What is clear so far is that OpenAI is describing three practical layers of access, even if it has not published a precise tier-by-tier matrix.

The baseline is **ChatGPT Images 2.0**, which OpenAI's blog post states is available to all ChatGPT and Codex users and includes the core model improvements: better instruction following, stronger text rendering, multilingual gains, broader aspect ratios, and more polished, production-usable outputs.

Above that is **“thinking”**, which the release defines more concretely: when a thinking model is selected, the system can take more time, use the web, analyze uploaded materials, reason through layout before generating, and produce multiple distinct images at once, including up to eight coherent outputs with continuity.

In the briefing, Li also framed thinking and Pro as “juiced-up” versions of the base model with tool use, and said these advanced modes are slower, not faster, because they do more reasoning and search behind the scenes. What remains unclear is the exact feature boundary between **Thinking** and **Pro**.

The materials say Pro users get access to more advanced image generation, but they do not spell out whether that means higher quality, higher limits, higher resolution, more outputs, or some other advantage distinct from thinking itself.

For enterprise users, the safest way to think about the differences is not as three totally separate products, but as a spectrum from **fast default generation** to **slower, more agentic, more structured generation**.

If a team needs quick creative drafts, marketing concepts, simple graphics, or everyday image edits, the base Images 2.0 model appears to be the relevant default.

If the task involves factual grounding, transforming internal documents into explainers, creating multi-image sets, or maintaining consistency across a sequence of assets, the more important distinction is whether the organization has access to thinking-enabled outputs.

Until OpenAI provides a clearer Pro-versus-Thinking breakdown, enterprise buyers should treat “thinking” as the meaningful functional upgrade and treat “Pro” as a possibly higher-end access tier whose exact incremental benefits still need clarification before procurement or workflow planning.

## S **afety standards**

OpenAI’s says ChatGPT Images 2.0 offers a"multi-layered stack" of safety protocols, including:

1. **Provenance:** Adhering to industry standards for watermarking so that AI-generated images are identifiable.

2. **Model Safeguards:** Using advanced perception models to filter out harmful or abusive content for both adults and children.

3. **Active Monitoring:** Enforcing user policies through real-time reporting.


Li emphasized that while their philosophy is to "maximize user creativity," they maintain strict policies against election interference.

## **What it means for enterprise users**

The shift from Images 1.5 to 2.0 is more than a resolution bump. By integrating reasoning, OpenAI is attempting to solve the "intent gap" that has plagued AI art since its inception.

When you ask an AI for an "infographic about supply and demand," you aren't just looking for a picture; you are looking for a logical layout of information.

The "Interior Design" sample (Japandi Furnishing Concept) highlights this systemic thinking. The model didn't just generate a room; it created a cohesive floor plan, a color palette, a list of materials, and "inspiration" shots that all adhere to a singular aesthetic.

This is what OpenAI calls moving from a "tool" to a "visual system". However, this increased capability comes with a trade-off in speed.

For the professional user, this is likely a worthwhile exchange: waiting an extra minute for a "production-ready asset" is still significantly faster than the hours required for manual design.

As ChatGPT Images 2.0 rolls out, it marks the beginning of an era where AI doesn't just assist in making art, but in conducting "economically valuable creative tasks".

Whether it can truly replace the intentionality of a human designer remains to be seen, but with 2K resolution, multilingual fluency, and the ability to "think" before it acts, OpenAI has certainly closed the distance.

## More

[![nuneybits Vector art of Google logo morphing into research grap 58bdb7e1-2ede-42c5-9881-d2674c2d9475](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FXnHzMo0vBDWmcq26xBte3%2F4a3d68b62ae2c7ac004b7706cf2cebe5%2Fnuneybits_Vector_art_of_Google_logo_morphing_into_research_grap_58bdb7e1-2ede-42c5-9881-d2674c2d9475.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/googles-new-deep-research-and-deep-research-max-agents-can-search-the-web-and-your-private-data)

The release, built on Google's [Gemini 3.1 Pro model](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-pro/), marks an inflection point in the rapidly intensifying race to build AI systems that can autonomously conduct the kind of exhaustive, multi-source research that has traditionally consumed hours or days of human analyst time. It also represents Google's clearest bid yet to position its AI infrastructure as the backbone for enterprise research workflows in finance, life sciences, and market intelligence — industries where the stakes of getting information wrong are extraordinarily high.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 21, 2026


[![nuneybits Vector art of a retro CRT computer displaying color s d7afd7e6-cc20-434f-b18e-32f034a387ed-1](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F5DmzXzlni0pVWEsOQilzRl%2F7be8fdfb9d3f0d88f49cb8d3d8df28c7%2Fnuneybits_Vector_art_of_a_retro_CRT_computer_displaying_color_s_d7afd7e6-cc20-434f-b18e-32f034a387ed-1.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/anthropic-just-launched-claude-design-an-ai-tool-that-turns-prompts-into-prototypes-and-challenges-figma)

The simultaneous launches mark a watershed for Anthropic, whose ambitions now visibly extend from foundation model provider to full-stack product company — one that wants to own the arc from a rough idea to a shipped product. The timing is also significant: Anthropic hit roughly [$20 billion in annualized revenue](https://finance.yahoo.com/news/anthropic-tops-30-billion-run-221045473.html) in early March 2026, according to Bloomberg, up from $9 billion at the end of 2025 — and surpassed $30 billion by early April 2026. The company is in early talks with Goldman Sachs, JPMorgan, and Morgan Stanley about a potential IPO that could come as early as October 2026.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 17, 2026


[![nuneybits Vector art of Salesforce Tower bc4b6995-07bd-4746-97a9-9dfda2ab92d0](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F20o4KbpCNvhGDbjACvvc46%2F33584beeede6af5fbfc2d328076a0e64%2Fnuneybits_Vector_art_of_Salesforce_Tower_bc4b6995-07bd-4746-97a9-9dfda2ab92d0.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/salesforce-launches-headless-360-to-turn-its-entire-platform-into-infrastructure-for-ai-agents)

The announcement, made at the company's annual [TDX developer conference](https://www.salesforce.com/tdx/) in San Francisco, ships more than 100 new tools and skills immediately available to developers. It marks a decisive response to the existential question hanging over enterprise software: In a world where AI agents can reason, plan, and execute, does a company still need a CRM with a graphical interface?

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 16, 2026


[![Feminine robot with bun looks through microscope](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F2kuM1Fize1fBE3pybDQsvD%2Fae6248e28eafe454993a21e87632c189%2FChatGPT_Image_Apr_16__2026__03_01_33_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with OpenAI GPT-Image-1.5](https://venturebeat.com/technology/openai-debuts-gpt-rosalind-a-new-limited-access-model-for-life-sciences-and-broader-codex-plugin-on-github)

The journey from a laboratory hypothesis to a pharmacy shelf is one of the most grueling marathons in modern industry, typically spanning 10 to 15 years and billions of dollars in investment.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 16, 2026


[![Man using OpeanAI codex in B&W cyberspace](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FwlyUc6IcR6mIiA3AM9T06%2F56adbce4b13fc8f4926d0b14f5067436%2FChatGPT_Image_Apr_16__2026__12_59_06_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with GPT-Image-1.5](https://venturebeat.com/technology/openai-drastically-updates-codex-desktop-app-to-use-all-other-apps-on-your-computer-generate-images-preview-webpages)

OpenAI is releasing more than 90 new plugins. These connectors—including CircleCI, GitLab, and Microsoft Suite—allow the agent to gather context and take action.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 16, 2026


[![Anthropic vs. OpenAI vs. Google foot race on track with audience cheering and smiling man keeping time](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FSeh68p8wVtjmUzumzSTB9%2F82e03ea5925ffe574098a259daef121f%2FGemini_Generated_Image_a606wa606wa606wa.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Google Gemini 3.1 Pro Image](https://venturebeat.com/technology/anthropic-releases-claude-opus-4-7-narrowly-retaking-lead-for-most-powerful-generally-available-llm)

Opus 4.7 utilizes an updated tokenizer that improves text processing efficiency, though it can increase the token count of certain inputs by 1.0–1.35x.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 16, 2026


[![nuneybits Vector art of a glossy monitor displaying Adobe suite 0a74cb83-7204-43f9-93b9-57aedd832850](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F232aFndd9ByhThoweyPW9E%2Fcc7b863d6e9a8b1024da68bbcb559e11%2Fnuneybits_Vector_art_of_a_glossy_monitor_displaying_Adobe_suite_0a74cb83-7204-43f9-93b9-57aedd832850.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/adobes-new-firefly-ai-assistant-wants-to-run-photoshop-premiere-illustrator-and-more-from-one-prompt)

The announcements, which also include a new Color Mode for [Premiere Pro](https://www.adobe.com/products/premiere.html), the addition of [Kling 3.0 video models](https://higgsfield.ai/kling-3.0) to Firefly's growing roster of third-party AI engines, and [Frame.io Drive](http://frame.io/)— a virtual filesystem that lets distributed teams work with cloud-stored media as though it lived on their local machines — represent Adobe's clearest signal yet that it views agentic AI not as a feature upgrade but as a fundamental reshaping of how creative work gets done.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 15, 2026


[![nuneybits Vector art of a stack of invoices 8a53c753-9472-420d-8a66-873e33846084](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1BlLS9asVgj2WDV5j09DTX%2F7aa5369b05fb9ad458c16a4a1e481ba8%2Fnuneybits_Vector_art_of_a_stack_of_invoices_8a53c753-9472-420d-8a66-873e33846084.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/orchestration/traza-raises-usd2-1-million-led-by-base10-to-automate-procurement-workflows-with-ai)

For decades, procurement has been the back office that enterprise software forgot. Billions of dollars flow through vendor negotiations, purchase orders, and supplier communications every year at the largest manufacturers and construction companies in the country — and the vast majority of that work still runs on email threads, spreadsheets, and phone calls.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 15, 2026


[![nuneybits Vector art of the iconic Microsoft Windows logo on a d3fc862c-d081-4a53-86a0-8b31f591dd93](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F17szvygLbh5CP67yGHGlNG%2F7a78dac28a40f270d5d5ef636980f606%2Fnuneybits_Vector_art_of_the_iconic_Microsoft_Windows_logo_on_a__d3fc862c-d081-4a53-86a0-8b31f591dd93.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/microsoft-launches-mai-image-2-efficient-a-cheaper-and-faster-ai-image-model)

The new model is priced at $5 per million text input tokens and $19.50 per million image output tokens, a [roughly 41% reduction](https://microsoft.ai/news/mai-image-2e-flagship-quality-41-lower-cost/) from MAI-Image-2's pricing of $5 and $33, respectively, for those same tiers. Microsoft says the model runs 22% faster than its flagship sibling and achieves 4x greater throughput efficiency per GPU, as measured on NVIDIA H100 hardware at 1024×1024 resolution. The company also claims it outpaces competing hyperscaler models — specifically naming Google's [Gemini 3.1 Flash](https://blog.google/innovation-and-ai/models-and-research/gemini-models/gemini-3-1-flash-live/), [Gemini 3.1 Flash Image](https://deepmind.google/models/gemini-image/flash/), and [Gemini 3 Pro Image](https://deepmind.google/models/gemini-image/pro/) — by an average of 40% on p50 latency benchmarks.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 14, 2026


[![nuneybits Vector art of developer mopping code spill dbcceaac-fb6e-4e63-90cf-5774d34a0f44](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F5nAHuSU7TlSixVhQbV3Zpy%2Ff97f9591cd1d877db961dac2be53b6cc%2Fnuneybits_Vector_art_of_developer_mopping_code_spill_dbcceaac-fb6e-4e63-90cf-5774d34a0f44.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/43-of-ai-generated-code-changes-need-debugging-in-production-survey-finds)

The software industry is racing to write code with artificial intelligence. It is struggling, badly, to make sure that code holds up once it ships.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 14, 2026


[![Claude nerfed](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1jSNP91rl8Ww79tLt9WiLg%2Fd9a8da5cf84f328a95105adfec4ff688%2FGemini_Generated_Image_63c1cq63c1cq63c1.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with GPT-Image-1.5 and Google Gemini 3.1 Pro Image](https://venturebeat.com/technology/is-anthropic-nerfing-claude-users-increasingly-report-performance)

Anthropic has been dealing with surging demand; second, it has already changed how usage is rationed during busy periods.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 13, 2026


[![Llama exits Meta with box under Muse Spark sign](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6tTe1SOF6tLAWd3xvDNOml%2F749dbd15282f8ad2696467128825d7a6%2FDejected_llama_leaves_Muse_Spark_headquarters.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Llama exits Meta with box under Muse Spark sign. Credit: VentureBeat made with OpenAI GPT-Image-1.5](https://venturebeat.com/technology/goodbye-llama-meta-launches-new-proprietary-ai-model-muse-spark-first-since)

Meta reports that Muse Spark achieves its reasoning capabilities using over an order of magnitude less compute than Llama 4 Maverick, its previous mid-size flagship.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 8, 2026


[![SEO/AEO](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6mKfa09Ht7wzFiRIWUIcqc%2F0090650d90a363f1c858f4a671abbf76%2FAI_search.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
CleoP made with Midjourney](https://venturebeat.com/technology/llm-referred-traffic-converts-at-30-40-and-most-enterprises-arent-optimizing)

AI agents don't rank content — they cite it. Most enterprise content is already invisible in agent-driven queries, and the companies getting ahead aren't doing anything exotic.

[Taryn Plumb](https://venturebeat.com/author/taryn-plumb)
April 8, 2026


[![nuneybits Vector art of the Square payments system point of sal a0eb242e-be13-4204-9d6c-b1be02025525](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6zNqH1MY0JDez3yEqPyEHn%2Fd0336c111d8154186121d05f78707ff6%2Fnuneybits_Vector_art_of_the_Square_payments_system_point_of_sal_a0eb242e-be13-4204-9d6c-b1be02025525.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/data/block-introduces-managerbot-a-proactive-square-ai-agent-and-the-clearest)

In an exclusive interview with VentureBeat, [Willem Avé](https://squareup.com/us/en/the-bottom-line/about/willem-ave), Block's head of product at Square, described Managerbot as a decisive break from the company's earlier Square AI assistant, which functioned as a reactive chatbot that answered seller questions about sales, employees, and business performance.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 7, 2026


[![nuneybits Vector art of a retro CRT computer image in burnt ora f8676585-ba7c-4170-bb90-6ad2e8a2668e](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6SaGXxoA2WaaomE4o3ATIx%2Fe0ed70fe2b8554b83f11998884a52c0b%2Fnuneybits_Vector_art_of_a_retro_CRT_computer_image_in_burnt_ora_f8676585-ba7c-4170-bb90-6ad2e8a2668e.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/anthropic-says-its-most-powerful-ai-cyber-model-is-too-dangerous-to-release)

The launch partners include [Amazon Web Services](https://aws.amazon.com/), [Apple](https://www.apple.com/), [Broadcom](https://www.broadcom.com/), [Cisco](http://cisco.com/#tabs-69d6a56dd3-item-fdd67b2fb8-tab), [CrowdStrike](https://www.crowdstrike.com/en-us/), [Google](https://www.google.com/), [JPMorganChase](https://www.jpmorganchase.com/), [the Linux Foundation](https://www.linuxfoundation.org/), [Microsoft](https://microsoft.com/), [Nvidia](https://nvidia.com/), and [Palo Alto Networks](https://www.paloaltonetworks.com/). Anthropic says it has also extended access to more than 40 additional organizations that build or maintain critical software, and is committing up to $100 million in usage credits for Claude Mythos Preview across the effort, along with $4 million in direct donations to open-source security organizations.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 7, 2026


[![GLM-5.1 robot clocks in](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F77oM8cqy8fLWfF65ejw0eW%2F534038847f3f387f4d974ed91e77d77b%2FChatGPT_Image_Apr_7__2026__01_44_40_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
VentureBeat made with OpenAI GPT-Image-1.5](https://venturebeat.com/technology/ai-joins-the-8-hour-work-day-as-glm-ships-5-1-open-source-llm-beating-opus-4)

If a model can work for eight hours without human intervention, it fundamentally changes the software development lifecycle.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 7, 2026


[![Claude chef cuts off claws of red lobster](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FeUkPoLeb8EqcsOWG38sR7%2F90e6007c5bb7ca3224878c7f0cf77b60%2FGemini_Generated_Image_hxdsq2hxdsq2hxds.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Google Nano Banana Pro 2](https://venturebeat.com/technology/anthropic-cuts-off-the-ability-to-use-claude-subscriptions-with-openclaw-and)

To be clear, it will still be possible to use Claude models like Opus, Sonnet, and Haiku to power OpenClaw and similar external agents, but users will now need to opt into a pay-as-you-go or API.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 3, 2026


[![Vector art portrait of Jensen Huang image in Nvidia green and black minimalist no text image 1](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F2fleqnUY239c0tJFBLRGPF%2F123f498a5442eb1308cbeaee7fdd56c5%2FVector_art_portrait_of_Jensen_Huang_image_in_Nvidia_green_and_black_minimalist_no_text_image_1.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Nano-Banana-2](https://venturebeat.com/technology/nvidia-launches-enterprise-ai-agent-platform-with-adobe-salesforce-sap-among)

The Nvidia CEO unveiled the [Agent Toolkit](https://nvidianews.nvidia.com/news/ai-agents), an open-source platform for building autonomous AI agents, and then rattled off the names of the companies that will use it: [Adobe](https://www.adobe.com/), [Salesforce](https://www.salesforce.com/), [SAP](https://www.sap.com/index.html), [ServiceNow](https://www.servicenow.com/), [Siemens](https://www.siemens.com/), [CrowdStrike](https://www.crowdstrike.com/), [Atlassian](https://www.atlassian.com/), [Cadence](https://www.cadence.com/en_US/home.html), [Synopsys](https://www.synopsys.com/), [IQVIA](https://www.iqvia.com/), [Palantir](https://www.palantir.com/), [Box](https://www.box.com/home), [Cohesity](https://www.cohesity.com/), [Dassault Systèmes](https://www.3ds.com/), [Red Hat](https://www.redhat.com/en), [Cisco](https://www.cisco.com/) and [Amdocs](https://www.amdocs.com/). Seventeen enterprise software companies, touching virtually every industry and every Fortune 500 corporation, all agreeing to build their next generation of AI products on a shared foundation that Nvidia designed, Nvidia optimizes and Nvidia maintains.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 3, 2026


[![nuneybits Vector art of the iconic Microsoft Windows logo on a c7e8e82a-c8b6-4bb6-b555-19a4b7abcd08-1](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1MNM0JowRYE5e55Cwos47r%2Ff165200540aa49620bef1b7731908ac6%2Fnuneybits_Vector_art_of_the_iconic_Microsoft_Windows_logo_on_a__0d681fb6-874c-4a30-83b8-90efbe6996d5.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/microsoft-launches-3-new-ai-models-in-direct-shot-at-openai-and-google)

The trio of models — [MAI-Transcribe-1](https://microsoft.ai/news/state-of-the-art-speech-recognition-with-mai-transcribe-1/), [MAI-Voice-1](https://microsoft.ai/news/today-were-announcing-3-new-world-class-mai-models-available-in-foundry/), and [MAI-Image-2](https://msi-playground.microsoft.com/chat) — are available immediately through [Microsoft Foundry](https://azure.microsoft.com/en-us/products/ai-foundry) and a new [MAI Playground](https://msi-playground.microsoft.com/chat). They span three of the most commercially valuable modalities in enterprise AI: converting speech to text, generating realistic human voice, and creating images. Together, they represent the opening salvo from Microsoft's [superintelligence team](https://microsoft.ai/), which Suleyman formed just six months ago to pursue what he calls " [AI self-sufficiency](https://www.mitsloanme.com/article/microsoft-moves-toward-ai-self-sufficiency-amid-evolving-openai-ties/)."

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
April 3, 2026


[![Trinity Large looms over the city](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FBU6IEd1qLpLq0z4wTsSFU%2F45efac43ec6d50536095a1ad3e2791bd%2FGemini_Generated_Image_coxwn4coxwn4coxw.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Google Gemini 3.1 Pro Image](https://venturebeat.com/technology/arcees-new-open-source-trinity-large-thinking-is-the-rare-powerful-u-s-made)

As global labs pivot toward proprietary lock-in, Arcee has positioned Trinity as a sovereign infrastructure layer that developers can finally control and adapt for long-horizon agentic workflows.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
April 3, 2026


[![Woman's hand placing gems](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F1KjI96SJa9CT3g3xi3ldoE%2Fd0f64bee4c9285397f8a8458b0de4c9d%2FChatGPT_Image_Apr_2__2026__01_33_47_PM.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with GPT-Image-1.5](https://venturebeat.com/technology/google-releases-gemma-4-under-apache-2-0-and-that-license-change-may-matter)

As some Chinese AI labs (most notably Alibaba’s latest Qwen models, Qwen3.5 Omni and Qwen 3.6 Plus) have begun pulling back from fully open releases for their latest models, Google is moving in the opposite direction

[Sam Witteveen](https://venturebeat.com/author/sam-witteveen)
April 2, 2026


[![nuneybits Vector art of a laptop displaying an unmistakable Sla e2df2056-1841-4245-a4ea-4b79444c7d56](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6ibN7rf80EyoMcoQ2o6a6u%2F7e9042f231b585a6d6eb3cd58c50bca5%2Fnuneybits_Vector_art_of_a_laptop_displaying_an_unmistakable_Sla_e2df2056-1841-4245-a4ea-4b79444c7d56.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/orchestration/slack-adds-30-ai-features-to-slackbot-its-most-ambitious-update-since-the)

The announcement, timed to a keynote event that Salesforce CEO Marc Benioff is headlining Tuesday morning, arrives less than three months after Slackbot first became [generally available](https://www.salesforce.com/news/press-releases/2026/01/13/slackbot-announcement/) on January 13 to Business+ and Enterprise+ subscribers. In that short window, Slack says the feature is on track to become the fastest-adopted product in Salesforce's 27-year history, with some employees at customer organizations reporting they save up to 90 minutes per day. Inside Salesforce itself, teams claim savings of up to 20 hours per week, translating to more than $6.4 million in estimated productivity value.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
March 31, 2026


[![Claude bot tries to fix leaky fire hydrant](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2FK7d8cWOPYUVUoUmdWOpzB%2Fd269648e6f78ee428a297bb7c6905a4b%2FGemini_Generated_Image_io8kwlio8kwlio8k.png%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
VentureBeat made with Google Gemini 3.1 Pro Image](https://venturebeat.com/technology/claude-codes-source-code-appears-to-have-leaked-heres-what-we-know)

The leak provides competitors—from established giants to nimble rivals like Cursor—a literal blueprint for how to build a high-agency, reliable, and commercially viable AI agent.

[Carl Franzen](https://venturebeat.com/author/carlfranzen)
March 31, 2026


[![nuneybits Vector art of hands snapping glowing app pieces d8d5c36e-fbb8-4a03-b9b3-bd48c9a03e6e](https://venturebeat.com/_next/image?url=https%3A%2F%2Fimages.ctfassets.net%2Fjdtwqhzvc2n1%2F6GnLFT7vEip7kgNdhsy2mC%2F9bca69a98f8e59d1687dd9714e8186e2%2Fnuneybits_Vector_art_of_hands_snapping_glowing_app_pieces_d8d5c36e-fbb8-4a03-b9b3-bd48c9a03e6e.webp%3Fw%3D1000%26q%3D100&w=3840&q=50)\\
\\
Credit: VentureBeat made with Midjourney](https://venturebeat.com/technology/softr-launches-ai-native-platform-to-help-nontechnical-teams-build-business)

The company's new [AI Co-Builder](https://www.softr.io/ai-app-generator) lets non-technical users describe in plain language the software they need, and the platform generates a fully integrated system — database, user interface, permissions, and business logic included — connected and ready for real-world deployment immediately. The move marks a fundamental evolution for a company that spent five years building a no-code business before layering AI on top of what it describes as a proven infrastructure of constrained, pre-built building blocks.

[Michael Nuñez](https://venturebeat.com/author/michael_nunez)
March 31, 2026
