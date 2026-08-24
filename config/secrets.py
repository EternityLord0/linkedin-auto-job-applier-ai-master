#  Copyright (c) 2026 Ajinkya Kardile. All rights reserved.
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see <https://opensource.org/licenses/MIT>.

from config.schema.secrets_model import SecretsModel

# ==========================================
# INSTANTIATE YOUR DATA HERE
# ==========================================
secrets_data = SecretsModel(
    username="your_email@example.com",
    password="your_password",
    use_AI=True,
    ai_provider="gemini",
    llm_api_url="",
    llm_api_key="YOUR_GEMINI_OR_OPENAI_API_KEY_HERE",
    llm_model="gemini-2.5-flash",
    llm_spec="openai",
    stream_output=False
)