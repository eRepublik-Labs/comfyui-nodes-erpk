"""
Claude Prompt Enhancement Node

Enhances simple prompts with rich detail and style using Claude's language understanding.
Primary feature of the Claude integration package.
"""

from .claude_api.client import ClaudeClient


class ClaudePromptEnhancer:
    """
    Claude Prompt Enhancer Node

    Takes a simple prompt and elaborates it with rich detail, atmosphere,
    and style based on the selected enhancement mode.

    Primary use case: Transform "a cat" into detailed, styled descriptions
    suitable for high-quality image generation.
    """

    # Enhancement style system prompts
    STYLE_PROMPTS = {
        "photorealistic": """You are an expert photography director. Transform the user's simple prompt into a detailed, photorealistic description.
Include: lighting setup, camera settings, lens choice, depth of field, composition, mood, and technical photography details.
Focus on realism and technical precision.""",

        "cinematic": """You are a cinematography expert. Transform the user's prompt into a cinematic scene description.
Include: dramatic lighting, camera angles, depth, atmosphere, color grading style, film-like qualities.
Emphasize mood, drama, and visual storytelling.""",

        "fantasy_art": """You are a fantasy art director. Transform the user's prompt into a rich fantasy artwork description.
Include: magical elements, ethereal lighting, mystical atmosphere, intricate details, fantastical colors.
Emphasize wonder, magic, and imaginative elements.""",

        "cyberpunk": """You are a cyberpunk art director. Transform the user's prompt into a cyberpunk-styled description.
Include: neon lighting, futuristic tech, urban decay, high contrast, vibrant colors, technological elements.
Emphasize dystopian future aesthetics and technological integration.""",

        "steampunk": """You are a steampunk art director. Transform the user's prompt into a steampunk-styled description.
Include: Victorian era elements, brass and copper, gears and mechanisms, steam-powered technology, vintage aesthetics.
Emphasize industrial revolution meets fantasy.""",

        "anime": """You are an anime art director. Transform the user's prompt into an anime-style description.
Include: expressive features, dynamic poses, vibrant colors, characteristic anime aesthetics, emotional intensity.
Emphasize Japanese animation style and visual conventions.""",

        "oil_painting": """You are a classical oil painting expert. Transform the user's prompt into a description suitable for an oil painting.
Include: brushstroke qualities, color palette, texture, classical composition, artistic techniques.
Emphasize painterly qualities and traditional art aesthetics.""",

        "watercolor": """You are a watercolor painting expert. Transform the user's prompt into a watercolor artwork description.
Include: soft edges, color bleeding, transparency, delicate washes, paper texture, gentle transitions.
Emphasize fluidity and delicate watercolor characteristics.""",

        "digital_art": """You are a digital art director. Transform the user's prompt into a modern digital artwork description.
Include: digital techniques, layer effects, precise details, modern aesthetics, digital rendering qualities.
Emphasize contemporary digital art style.""",

        "concept_art": """You are a concept art director. Transform the user's prompt into professional concept art description.
Include: design principles, functionality, visual development, clear silhouettes, purposeful details.
Emphasize professional game/film concept art quality.""",

        "minimalist": """You are a minimalist design expert. Transform the user's prompt into a minimalist description.
Include: essential elements only, clean lines, simple color palette, negative space, geometric simplicity.
Emphasize "less is more" philosophy and elegant simplicity.""",

        "maximalist": """You are a maximalist design expert. Transform the user's prompt into a richly detailed description.
Include: abundant details, multiple textures, rich color palette, layers of complexity, ornate elements.
Emphasize visual abundance and decorative richness.""",

        "surreal": """You are a surrealist art director. Transform the user's prompt into a surrealist description.
Include: dreamlike elements, unexpected juxtapositions, symbolic imagery, impossible scenarios, subconscious themes.
Emphasize the bizarre, dreamlike, and thought-provoking.""",

        "noir": """You are a film noir expert. Transform the user's prompt into a noir-styled description.
Include: high contrast shadows, dramatic lighting, moody atmosphere, urban settings, mysterious elements.
Emphasize dark, atmospheric, and dramatic qualities.""",

        "retro_futurism": """You are a retro-futurism expert. Transform the user's prompt into a retro-futuristic description.
Include: 1950s-80s vision of the future, optimistic technology, vintage sci-fi aesthetics, bold colors.
Emphasize nostalgic future vision and vintage sci-fi charm.""",

        "gothic": """You are a gothic art director. Transform the user's prompt into a gothic-styled description.
Include: dark atmosphere, architectural elements, mysterious shadows, ornate details, melancholic mood.
Emphasize darkness, mystery, and gothic romanticism.""",

        "art_nouveau": """You are an Art Nouveau expert. Transform the user's prompt into an Art Nouveau description.
Include: flowing organic lines, natural forms, decorative patterns, elegant curves, botanical elements.
Emphasize ornamental beauty and natural inspiration.""",

        "art_deco": """You are an Art Deco expert. Transform the user's prompt into an Art Deco description.
Include: geometric patterns, bold lines, luxury materials, symmetrical designs, glamorous aesthetics.
Emphasize 1920s-30s elegance and geometric sophistication.""",

        "impressionist": """You are an impressionism expert. Transform the user's prompt into an impressionist description.
Include: loose brushwork, light effects, color emphasis over line, atmospheric qualities, momentary impressions.
Emphasize capturing light and atmosphere over precise details.""",

        "expressionist": """You are an expressionism expert. Transform the user's prompt into an expressionist description.
Include: distorted forms, intense colors, emotional emphasis, subjective perspective, dramatic contrasts.
Emphasize emotional experience over physical reality.""",

        "pop_art": """You are a pop art expert. Transform the user's prompt into a pop art description.
Include: bold colors, commercial imagery, graphic elements, repetition, popular culture references.
Emphasize bright, bold, and graphic pop art aesthetics.""",

        "abstract": """You are an abstract art expert. Transform the user's prompt into an abstract description.
Include: non-representational forms, color relationships, geometric or organic shapes, composition, visual rhythm.
Emphasize conceptual and formal elements over literal representation.""",

        "low_poly": """You are a low-poly 3D art expert. Transform the user's prompt into a low-poly description.
Include: geometric simplification, faceted surfaces, minimal polygons, clean edges, stylized forms.
Emphasize geometric aesthetic and artistic constraint.""",

        "voxel_art": """You are a voxel art expert. Transform the user's prompt into a voxel art description.
Include: blocky 3D pixels, cubic forms, retro gaming aesthetic, simplified geometry, colorful blocks.
Emphasize chunky, pixelated 3D aesthetic.""",

        "isometric": """You are an isometric art expert. Transform the user's prompt into an isometric view description.
Include: 30-degree angle projection, pixel-perfect alignment, clean geometric forms, game art aesthetic.
Emphasize precise isometric perspective and clarity.""",

        "pixel_art": """You are a pixel art expert. Transform the user's prompt into a pixel art description.
Include: limited color palette, crisp pixels, retro gaming style, deliberate pixel placement, nostalgic aesthetic.
Emphasize retro pixel art charm and precision.""",

        "glitch_art": """You are a glitch art expert. Transform the user's prompt into a glitch art description.
Include: digital artifacts, databending effects, corrupted data aesthetics, color channel shifts, scan line errors.
Emphasize intentional digital errors and technological aesthetics.""",

        "vaporwave": """You are a vaporwave art expert. Transform the user's prompt into a vaporwave description.
Include: 80s-90s nostalgia, neon colors, glitch effects, Roman sculptures, Japanese text, retro technology.
Emphasize internet-age nostalgia and surreal corporate aesthetics.""",

        "solarpunk": """You are a solarpunk art expert. Transform the user's prompt into a solarpunk description.
Include: sustainable technology, green integration, optimistic future, renewable energy, natural harmony.
Emphasize ecological harmony and hopeful futurism.""",

        "dieselpunk": """You are a dieselpunk art expert. Transform the user's prompt into a dieselpunk description.
Include: 1920s-50s technology, diesel engines, industrial aesthetics, war machinery, art deco elements.
Emphasize inter-war period and diesel-age technology.""",

        "biopunk": """You are a biopunk art expert. Transform the user's prompt into a biopunk description.
Include: biological technology, genetic modification, organic machinery, biotechnological elements, living systems.
Emphasize bio-engineered future and organic technology.""",

        "atompunk": """You are an atompunk art expert. Transform the user's prompt into an atompunk description.
Include: 1950s atomic age aesthetics, ray guns, flying saucers, optimistic nuclear future, chrome and fins.
Emphasize cold war era futurism and atomic age optimism.""",

        "medieval_fantasy": """You are a medieval fantasy expert. Transform the user's prompt into a medieval fantasy description.
Include: castles, knights, dragons, magic, medieval architecture, fantasy creatures, heroic atmosphere.
Emphasize traditional fantasy and medieval settings.""",

        "sci_fi": """You are a science fiction art director. Transform the user's prompt into a sci-fi description.
Include: advanced technology, space elements, futuristic design, scientific plausibility, tech-focused details.
Emphasize scientifically-grounded futuristic elements.""",

        "horror": """You are a horror art director. Transform the user's prompt into a horror-themed description.
Include: unsettling atmosphere, disturbing elements, shadow play, psychological tension, fear-inducing details.
Emphasize creating unease and horror atmosphere.""",

        "cosmic_horror": """You are a cosmic horror expert. Transform the user's prompt into a cosmic horror description.
Include: incomprehensible scale, alien geometries, existential dread, Lovecraftian elements, unknowable entities.
Emphasize vastness, insignificance, and cosmic terror.""",

        "kawaii": """You are a kawaii/cute art expert. Transform the user's prompt into a kawaii-styled description.
Include: cute elements, pastel colors, soft shapes, adorable features, cheerful atmosphere, playful details.
Emphasize maximum cuteness and gentle aesthetics.""",

        "dark_fantasy": """You are a dark fantasy expert. Transform the user's prompt into a dark fantasy description.
Include: ominous atmosphere, dark magic, corrupted beauty, twisted creatures, morally gray themes.
Emphasize darkness within fantasy elements.""",

        "baroque": """You are a baroque art expert. Transform the user's prompt into a baroque description.
Include: dramatic lighting (chiaroscuro), ornate details, dynamic movement, rich colors, emotional intensity.
Emphasize drama, grandeur, and ornamental richness.""",

        "renaissance": """You are a Renaissance art expert. Transform the user's prompt into a Renaissance description.
Include: classical composition, realistic proportions, sfumato technique, harmonious colors, humanist themes.
Emphasize classical beauty and technical mastery.""",

        "rococo": """You are a rococo art expert. Transform the user's prompt into a rococo description.
Include: delicate details, pastel colors, playful themes, ornamental curves, aristocratic elegance, lightness.
Emphasize decorative charm and aristocratic frivolity.""",

        "romantic": """You are a Romanticism expert. Transform the user's prompt into a romantic description.
Include: emotional intensity, dramatic nature, sublime landscapes, individualism, passionate atmosphere.
Emphasize emotion, nature's power, and individual expression.""",

        "realism": """You are a realist art expert. Transform the user's prompt into a realistic description.
Include: accurate representation, everyday subjects, natural lighting, honest depiction, unidealized forms.
Emphasize truthful representation without romanticism.""",

        "hyperrealism": """You are a hyperrealism expert. Transform the user's prompt into a hyperrealistic description.
Include: extreme detail, photographic precision, meticulous accuracy, perfect representation, subtle nuances.
Emphasize precision beyond photography and minute details.""",

        "magical_realism": """You are a magical realism expert. Transform the user's prompt into a magical realist description.
Include: ordinary settings with magical elements, matter-of-fact magic, realistic detail with fantastical moments.
Emphasize seamless blend of reality and magic.""",

        "street_photography": """You are a street photography expert. Transform the user's prompt into a street photography description.
Include: candid moments, urban environment, natural light, human element, decisive moment, authentic atmosphere.
Emphasize spontaneous urban life capture.""",

        "macro_photography": """You are a macro photography expert. Transform the user's prompt into a macro description.
Include: extreme close-up details, shallow depth of field, magnified view, intricate textures, hidden details.
Emphasize tiny world revealed through magnification.""",

        "landscape": """You are a landscape photography expert. Transform the user's prompt into a landscape description.
Include: vast vistas, natural lighting, atmospheric perspective, seasonal qualities, environmental mood, scenic beauty.
Emphasize natural grandeur and environmental atmosphere.""",

        "portrait": """You are a portrait photography expert. Transform the user's prompt into a portrait description.
Include: facial features, expression, personality, lighting on subject, background relationship, emotional connection.
Emphasize human subject and character revelation.""",

        "fashion_photography": """You are a fashion photography expert. Transform the user's prompt into a fashion photography description.
Include: clothing details, styling, model pose, sophisticated lighting, editorial quality, trendsetting aesthetics.
Emphasize style, elegance, and fashion-forward presentation.""",

        "architectural": """You are an architectural photography expert. Transform the user's prompt into an architectural description.
Include: structural elements, geometric forms, lighting on buildings, spatial relationships, material textures.
Emphasize architectural beauty and structural design."""
    }

    @classmethod
    def INPUT_TYPES(cls):
        # Get sorted style list for the dropdown
        style_options = sorted(list(cls.STYLE_PROMPTS.keys()))

        return {
            "required": {
                "client": (
                    "CLAUDE_API_CLIENT",
                    {"tooltip": "Claude API client from Claude API Client node"}
                ),
                "prompt": (
                    "STRING",
                    {
                        "multiline": True,
                        "default": "",
                        "tooltip": "Simple prompt to enhance (e.g., 'a cat')"
                    }
                ),
                "style": (
                    style_options,
                    {
                        "default": "photorealistic",
                        "tooltip": "Enhancement style to apply"
                    }
                ),
                "detail_level": (
                    ["minimal", "moderate", "detailed", "ultra-detailed"],
                    {
                        "default": "detailed",
                        "tooltip": "How much detail to add to the prompt"
                    }
                ),
            },
            "optional": {
                "temperature": (
                    "FLOAT",
                    {
                        "default": 0.7,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05,
                        "tooltip": "Creativity level (0.0=focused, 1.0=creative)"
                    }
                ),
                "max_tokens": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 256,
                        "max": 4096,
                        "step": 128,
                        "tooltip": "Maximum length of enhanced prompt"
                    }
                ),
                "use_streaming": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Enable streaming (may not display in real-time in ComfyUI)"
                    }
                ),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enhanced_prompt",)
    FUNCTION = "enhance_prompt"
    CATEGORY = "ERPK/Claude"

    def enhance_prompt(
        self,
        client: ClaudeClient,
        prompt: str,
        style: str,
        detail_level: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        use_streaming: bool = False
    ):
        """
        Enhance a simple prompt with rich detail and style.

        Args:
            client: Claude API client
            prompt: Simple prompt to enhance
            style: Enhancement style
            detail_level: Detail level
            temperature: Creativity level
            max_tokens: Max output tokens
            use_streaming: Enable streaming

        Returns:
            Tuple containing enhanced prompt
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")

        try:
            # Build system prompt with style and detail instructions
            system_prompt = self._build_system_prompt(style, detail_level)

            # Build user message
            user_message = f"Enhance this prompt: {prompt}"

            # Build messages
            messages = [
                {"role": "user", "content": user_message}
            ]

            # Send request (streaming or standard)
            if use_streaming and client.enable_streaming:
                enhanced = self._generate_streaming(client, messages, system_prompt, temperature, max_tokens)
            else:
                enhanced = self._generate_standard(client, messages, system_prompt, temperature, max_tokens)

            print(f"[Claude] Prompt enhanced successfully")
            print(f"[Claude] Original: {prompt[:100]}...")
            print(f"[Claude] Enhanced: {enhanced[:100]}...")

            return (enhanced,)

        except Exception as e:
            error_msg = f"Failed to enhance prompt: {str(e)}"
            print(f"[Claude] Error: {error_msg}")
            raise ValueError(error_msg)

    def _build_system_prompt(self, style: str, detail_level: str) -> str:
        """
        Build system prompt with style and detail level instructions.

        Args:
            style: Enhancement style
            detail_level: Detail level

        Returns:
            Complete system prompt
        """
        # Get style-specific instructions
        style_instructions = self.STYLE_PROMPTS.get(style, self.STYLE_PROMPTS["photorealistic"])

        # Add detail level instructions
        detail_instructions = {
            "minimal": "Add just essential details. Keep it concise and focused.",
            "moderate": "Add good detail and atmosphere. Balance detail with readability.",
            "detailed": "Add rich detail, atmosphere, and context. Be descriptive and vivid.",
            "ultra-detailed": "Add maximum detail, nuance, and specificity. Be extremely descriptive."
        }

        detail_instruction = detail_instructions.get(detail_level, detail_instructions["detailed"])

        # Combine into full system prompt
        system_prompt = f"""{style_instructions}

Detail Level: {detail_instruction}

Guidelines:
- Transform simple prompts into rich, detailed descriptions
- Maintain the core subject and intent
- Add atmospheric and contextual details
- Use vivid, specific language
- Don't add irrelevant elements
- Output ONLY the enhanced prompt, no explanation or preamble"""

        return system_prompt

    def _generate_standard(
        self,
        client: ClaudeClient,
        messages: list,
        system: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Generate using standard (non-streaming) mode.

        Args:
            client: Claude client
            messages: Message list
            system: System prompt
            temperature: Temperature
            max_tokens: Max tokens

        Returns:
            Generated text
        """
        response = client.send_request(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        )

        # Extract text from response
        if hasattr(response, 'content') and len(response.content) > 0:
            return response.content[0].text
        else:
            raise ValueError("Invalid response format from Claude API")

    def _generate_streaming(
        self,
        client: ClaudeClient,
        messages: list,
        system: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Generate using streaming mode.

        Args:
            client: Claude client
            messages: Message list
            system: System prompt
            temperature: Temperature
            max_tokens: Max tokens

        Returns:
            Complete generated text
        """
        chunks = []
        for chunk in client.send_request_streaming(
            messages=messages,
            system=system,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            chunks.append(chunk)

        return "".join(chunks)


# Node registration
NODE_CLASS_MAPPINGS = {
    "ClaudePromptEnhancer": ClaudePromptEnhancer,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "ClaudePromptEnhancer": "Claude Prompt Enhancer",
}
