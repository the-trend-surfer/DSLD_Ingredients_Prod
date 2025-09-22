"""
Stage 0: Normalizer Process
Нормалізація назви інгредієнта, визначення таксономії та категорії
"""
import json
import jsonschema
import google.generativeai as genai
from typing import Dict, Any, Optional, List
from modules.multi_ai_client import multi_ai_client
from processes.schemas import NORMALIZER_OUTPUT_SCHEMA
from config import Config

class IngredientNormalizer:
    """Normalizer agent for ingredient classification and taxonomy"""

    def __init__(self):
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self) -> str:
        return """You are a supplement ingredient translator and classifier.

TASK: Translate ingredient name and return ONLY valid JSON.

CRITICAL FORMAT FOR "taxon.uk": "Українська назва (English original)"

{
  "ingredient": "normalized ingredient name",
  "class": "plant|animal|vitamin|mineral|enzyme|probiotic|other",
  "taxon": {
    "uk": "Українська назва (English original)",
    "lat": "Scientific name if available",
    "rank": "species|genus|other"
  },
  "source_material": {
    "kingdom": "Рослини|Тварини|Гриби|Бактерії|Інше",
    "part_or_origin": "root|leaf|whole|extract|synthetic"
  }
}

EXAMPLES:
AHCC -> {"ingredient": "AHCC", "class": "other", "taxon": {"uk": "АХЦЦ (AHCC)", "lat": "Lentinula edodes extract", "rank": "other"}, "source_material": {"kingdom": "Гриби", "part_or_origin": "extract"}}

Vitamin C -> {"ingredient": "Vitamin C", "class": "vitamin", "taxon": {"uk": "Вітамін С (Vitamin C)", "lat": "Ascorbic acid", "rank": "other"}, "source_material": {"kingdom": "Інше", "part_or_origin": "synthetic"}}

Ginkgo Biloba -> {"ingredient": "Ginkgo Biloba", "class": "plant", "taxon": {"uk": "Гінкго білоба (Ginkgo Biloba)", "lat": "Ginkgo biloba", "rank": "species"}, "source_material": {"kingdom": "Рослини", "part_or_origin": "leaf"}}

RULES:
- CRITICAL: "taxon.uk" MUST be "Українська (English)" format
- Return ONLY the JSON object, no other text
- Use EXACT field names: "ingredient", "class", "taxon", "source_material"
- All required fields must be present"""

    def normalize(self, ingredient_name: str, synonyms: Optional[List[str]] = None,
                  kingdom_hint: Optional[str] = None) -> Dict[str, Any]:
        """
        Normalize ingredient name and determine taxonomy

        Args:
            ingredient_name: Raw ingredient name
            synonyms: List of synonyms if available
            kingdom_hint: Kingdom hint from Google Sheets column D

        Returns:
            Normalized ingredient data matching NORMALIZER_OUTPUT_SCHEMA
        """
        try:
            # STEP 1: Create basic Ukrainian translation
            print(f"[NORMALIZE] Step 1: Creating Ukrainian translation for {ingredient_name}")
            translation = {
                'name_ua': f"{ingredient_name}",  # Будемо використовувати AI для перекладу
                'name_lat': '',
                'category': 'інше'
            }

            # STEP 2: Classify ingredient using AI
            print(f"[NORMALIZE] Step 2: Classifying {ingredient_name}")

            all_names = [ingredient_name]
            if synonyms:
                all_names.extend(synonyms)

            context = f"""Ingredient: {ingredient_name}
All names: {', '.join(all_names)}
Kingdom hint: {kingdom_hint or 'unknown'}
Ukrainian name: {translation['name_ua']}
Latin name: {translation['name_lat']}
Category: {translation['category']}

Classify this ingredient and return ONLY the JSON object."""

            # Call AI with classification
            response = self._call_ai_simple(context)

            # Parse JSON response
            normalized_data = self._extract_and_validate_json(response, ingredient_name)

            if normalized_data:
                # STEP 3: Use translated names instead of AI classification names
                normalized_data['taxon']['uk'] = translation['name_ua']
                if translation['name_lat']:
                    normalized_data['taxon']['lat'] = translation['name_lat']

                # Map category to class if not already correct
                category_map = {
                    'рослина': 'plant',
                    'тварина': 'animal',
                    'вітамін': 'vitamin',
                    'мінерал': 'mineral',
                    'фермент': 'enzyme',
                    'пробіотик': 'probiotic',
                    'інше': 'other'
                }

                if translation['category'] in category_map:
                    normalized_data['class'] = category_map[translation['category']]

                print(f"[OK] Normalized: {normalized_data['ingredient']} ({normalized_data['class']}) → {translation['name_ua']}")
                return normalized_data
            else:
                return self._create_fallback_result_with_translation(ingredient_name, translation)

        except Exception as e:
            # Безпечний вивід помилки без Unicode символів
            error_msg = str(e).encode('ascii', 'ignore').decode('ascii')
            print(f"[ERROR] Normalizer error for {ingredient_name}: {error_msg}")
            return self._create_fallback_result(ingredient_name)

    def _call_ai_simple(self, context: str) -> str:
        """Call AI with simple, direct approach using normalizer system prompt"""
        try:
            # Try each model with the normalizer's system prompt
            for model_type in ['claude', 'openai', 'gemini']:
                if model_type in multi_ai_client.available_models:
                    try:
                        print(f"[INFO] Trying {model_type} for normalization...")

                        if model_type == 'claude':
                            response = self._call_claude_with_system_prompt(context)
                        elif model_type == 'openai':
                            response = self._call_openai_with_system_prompt(context)
                        elif model_type == 'gemini':
                            response = self._call_gemini_with_system_prompt(context)

                        if response and '{' in response and '}' in response:
                            print(f"[OK] {model_type} returned JSON response")
                            return response

                    except Exception as e:
                        print(f"[ERROR] {model_type} failed: {e}")
                        continue

            # If all models fail, return empty
            print(f"[ERROR] All models failed for normalization")
            return ""

        except Exception as e:
            print(f"[ERROR] AI call failed: {e}")
            return ""

    def _call_claude_with_system_prompt(self, context: str) -> str:
        """Call Claude with normalizer system prompt"""
        try:
            client = multi_ai_client.clients['claude']
            model = Config.MODELS['claude']['primary']

            response = client.messages.create(
                model=model,
                max_tokens=800,
                temperature=0.1,
                system=self.system_prompt,
                messages=[
                    {"role": "user", "content": context}
                ]
            )

            return response.content[0].text.strip()

        except Exception as e:
            # Try fallback model
            try:
                fallback_model = Config.MODELS['claude']['fallback']
                response = client.messages.create(
                    model=fallback_model,
                    max_tokens=800,
                    temperature=0.1,
                    system=self.system_prompt,
                    messages=[
                        {"role": "user", "content": context}
                    ]
                )
                return response.content[0].text.strip()
            except Exception as e2:
                raise Exception(f"Claude failed: {e}")

    def _call_openai_with_system_prompt(self, context: str) -> str:
        """Call OpenAI with normalizer system prompt"""
        try:
            client = multi_ai_client.clients['openai']
            model = Config.MODELS['openai']['primary']

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=800,
                temperature=0.1
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Try fallback model
            try:
                fallback_model = Config.MODELS['openai']['fallback']
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=800,
                    temperature=0.1
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                raise Exception(f"OpenAI failed: {e}")

    def _call_gemini_with_system_prompt(self, context: str) -> str:
        """Call Gemini with normalizer system prompt"""
        try:
            model_name = multi_ai_client.clients['gemini']
            model = genai.GenerativeModel(model_name)

            # Combine system prompt with context for Gemini
            full_prompt = f"{self.system_prompt}\n\n{context}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=800,
                    temperature=0.1
                )
            )

            return response.text.strip()

        except Exception as e:
            # Try fallback model
            try:
                fallback_model = Config.MODELS['gemini']['fallback']
                model = genai.GenerativeModel(fallback_model)

                full_prompt = f"{self.system_prompt}\n\n{context}"

                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=800,
                        temperature=0.1
                    )
                )
                return response.text.strip()
            except Exception as e2:
                raise Exception(f"Gemini failed: {e}")

    def _extract_and_validate_json(self, response: str, ingredient_name: str) -> Optional[Dict[str, Any]]:
        """Extract and validate JSON from AI response"""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1

            if start_idx == -1 or end_idx == -1:
                print(f"[ERROR] No JSON found in response")
                return None

            json_str = response[start_idx:end_idx]
            normalized_data = json.loads(json_str)

            # Validate against schema
            jsonschema.validate(normalized_data, NORMALIZER_OUTPUT_SCHEMA)

            return normalized_data

        except (json.JSONDecodeError, ValueError, jsonschema.ValidationError) as e:
            print(f"[ERROR] JSON validation failed for {ingredient_name}: {e}")
            return None

    def _create_fallback_result(self, ingredient_name: str) -> Dict[str, Any]:
        """Create fallback result when normalization fails"""
        # Create basic fallback translation
        translation = {
            'name_ua': ingredient_name,
            'name_lat': '',
            'category': 'інше'
        }
        return self._create_fallback_result_with_translation(ingredient_name, translation)

    def _create_fallback_result_with_translation(self, ingredient_name: str, translation: Dict[str, str]) -> Dict[str, Any]:
        """Create fallback result using translation data"""

        # Map category to class and kingdom
        category_map = {
            'рослина': ('plant', 'Рослини'),
            'тварина': ('animal', 'Тварини'),
            'вітамін': ('vitamin', 'Інше'),
            'мінерал': ('mineral', 'Інше'),
            'фермент': ('enzyme', 'Інше'),
            'пробіотик': ('probiotic', 'Бактерії'),
            'інше': ('other', 'Невідомо')
        }

        ingredient_class, kingdom = category_map.get(translation['category'], ('other', 'Невідомо'))

        return {
            "ingredient": ingredient_name,
            "class": ingredient_class,
            "taxon": {
                "uk": translation['name_ua'],
                "lat": translation['name_lat'] or "Невідомо",
                "rank": "other"
            },
            "source_material": {
                "kingdom": kingdom,
                "part_or_origin": "невідомо"
            }
        }

    def _create_basic_fallback_result(self, ingredient_name: str) -> Dict[str, Any]:
        """Create basic fallback result when translation also fails"""
        # Guess basic classification
        name_lower = ingredient_name.lower()

        if any(word in name_lower for word in ['vitamin', 'acid', 'folate', 'cobalamin']):
            ingredient_class = "vitamin"
            kingdom = "Інше"
        elif any(word in name_lower for word in ['zinc', 'iron', 'calcium', 'magnesium']):
            ingredient_class = "mineral"
            kingdom = "Інше"
        elif any(word in name_lower for word in ['lactobacillus', 'bifidobacterium', 'probiotic']):
            ingredient_class = "probiotic"
            kingdom = "Бактерії"
        else:
            ingredient_class = "other"
            kingdom = "Невідомо"

        return {
            "ingredient": ingredient_name,
            "class": ingredient_class,
            "taxon": {
                "uk": ingredient_name,
                "lat": "Невідомо",
                "rank": "other"
            },
            "source_material": {
                "kingdom": kingdom,
                "part_or_origin": "невідомо"
            }
        }

# Global instance
normalizer = IngredientNormalizer()