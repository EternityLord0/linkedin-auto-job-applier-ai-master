#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

import os
from config.schema.secrets_model import SecretsModel

# ==========================================
# INSTANTIATE YOUR DATA HERE
# ==========================================
_gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or ""

secrets_data = SecretsModel(
    username="",
    password="",
    use_AI=True,
    ai_provider="gemini",
    llm_api_url="",
    llm_api_key=_gemini_key or "YOUR_API_KEY",
    llm_model="gemini-2.5-flash",
    llm_spec="openai",
    stream_output=False
)