"""
Multi-AI client for working with OpenAI, Claude, and Gemini
"""
import openai
import anthropic
import google.generativeai as genai
import time
from config import Config

class MultiAIClient:
    """Multi-AI client with automatic fallback and model selection"""

    def __init__(self):
        self.clients = {}
        self.available_models = []
        self.setup_clients()

    def setup_clients(self):
        """Initialize all available AI clients"""

        # Setup OpenAI
        if Config.OPENAI_API_KEY:
            try:
                self.clients['openai'] = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
                self.available_models.append('openai')
                print("[OK] OpenAI client initialized")
            except Exception as e:
                print(f"[ERROR] OpenAI setup failed: {e}")

        # Setup Claude
        if Config.CLAUDE_API_KEY:
            try:
                self.clients['claude'] = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)
                self.available_models.append('claude')
                print("[OK] Claude client initialized")
            except Exception as e:
                print(f"[ERROR] Claude setup failed: {e}")

        # Setup Gemini
        if Config.GEMINI_API_KEY:
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)

                # Test available Gemini models
                available_gemini_models = [
                    "gemini-2.5-flash-lite",
                    "gemini-1.5-flash",
                    "gemini-1.5-pro",
                    "models/gemini-pro"
                ]

                working_model = None
                for model_name in available_gemini_models:
                    try:
                        test_model = genai.GenerativeModel(model_name)
                        response = test_model.generate_content("Test",
                            generation_config=genai.types.GenerationConfig(
                                max_output_tokens=10,
                                temperature=0.7
                            )
                        )
                        if response.text:
                            working_model = model_name
                            break
                    except Exception as e:
                        continue

                if working_model:
                    self.clients['gemini'] = working_model
                    self.available_models.append('gemini')
                    print(f"[OK] Gemini client initialized: {working_model}")
                else:
                    print("[ERROR] No working Gemini models found")

            except Exception as e:
                print(f"[ERROR] Gemini setup failed: {e}")

        print(f"[INFO] Available AI models: {', '.join(self.available_models)}")

    def get_system_prompt(self):
        """Get the system prompt for evidence collection"""
        return """Ти - спеціаліст з наукового аналізу інгредієнтів харчових добавок.

ЗАВДАННЯ: Проаналізуй наукові дані про інгредієнт та надай структуровану довідку українською мовою.

ФОРМАТ ВІДПОВІДІ:
**НАЗВА:** [українська назва] ([латинська назва])

**ДЖЕРЕЛО ОТРИМАННЯ:** [вид українською] ([латинська назва]); [частина рослини/тварини]

**АКТИВНІ СПОЛУКИ:** [перелік з концентраціями, якщо відомі]

**НАУКОВІ ДОСЛІДЖЕННЯ:**
- [короткий опис дослідження з роком]
- [ефекти та дозування]

**РІВЕНЬ ДОКАЗІВ:** [Level 1-4]

**ДЖЕРЕЛА:**
1. [точна назва джерела, рік]
2. [URL або DOI]

ОБОВ'ЯЗКОВІ ПРАВИЛА:
- Тільки перевірені наукові факти
- Заборонено вигадувати дослідження
- Якщо немає даних - пиши "немає достовірних даних"
- Обов'язково вказуй джерела
- Дотримуйся українського формату"""

    def fetch_evidence_with_best_model(self, ingredient, synonyms=None, search_results=None):
        """Fetch evidence using the best available model with fallback"""

        # Prepare context
        context = f"Інгредієнт: {ingredient}\n"
        if synonyms:
            context += f"Синоніми: {', '.join(synonyms)}\n"

        if search_results:
            context += "\nДоступні джерела:\n"
            for i, result in enumerate(search_results[:5], 1):
                context += f"{i}. {result.get('title', 'No title')}\n"
                context += f"   URL: {result.get('url', 'No URL')}\n"
                context += f"   Опис: {result.get('snippet', 'No description')[:200]}...\n\n"

        context += f"\nПроаналізуй наукову інформацію про {ingredient} базуючись на наданих джерелах."

        # Try models in priority order
        for model_type in Config.MODEL_PRIORITY:
            if model_type in self.available_models:
                try:
                    print(f"[INFO] Trying {model_type} for {ingredient}...")

                    if model_type == 'claude':
                        result = self._call_claude(context)
                    elif model_type == 'openai':
                        result = self._call_openai(context)
                    elif model_type == 'gemini':
                        result = self._call_gemini(context)

                    if result and "немає достовірних даних" not in result:
                        print(f"[OK] {model_type} успішно відповів для {ingredient}")
                        return result

                except Exception as e:
                    print(f"[ERROR] {model_type} failed for {ingredient}: {e}")
                    continue

        # If all models failed, return template
        print(f"[ERROR] All models failed for {ingredient}")
        return self._generate_no_data_template(ingredient)

    def _call_claude(self, context):
        """Call Claude API"""
        try:
            client = self.clients['claude']
            model = Config.MODELS['claude']['primary']

            response = client.messages.create(
                model=model,
                max_tokens=1500,
                temperature=0.7,
                system=self.get_system_prompt(),
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
                    max_tokens=1500,
                    temperature=0.7,
                    system=self.get_system_prompt(),
                    messages=[
                        {"role": "user", "content": context}
                    ]
                )
                return response.content[0].text.strip()
            except Exception as e2:
                raise Exception(f"Claude primary and fallback failed: {e}, {e2}")

    def _call_openai(self, context):
        """Call OpenAI API"""
        try:
            client = self.clients['openai']
            model = Config.MODELS['openai']['primary']

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": context}
                ],
                max_tokens=1500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            # Try fallback model
            try:
                fallback_model = Config.MODELS['openai']['fallback']
                response = client.chat.completions.create(
                    model=fallback_model,
                    messages=[
                        {"role": "system", "content": self.get_system_prompt()},
                        {"role": "user", "content": context}
                    ],
                    max_tokens=1500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e2:
                raise Exception(f"OpenAI primary and fallback failed: {e}, {e2}")

    def _call_gemini(self, context):
        """Call Gemini API"""
        try:
            model_name = self.clients['gemini']
            model = genai.GenerativeModel(model_name)

            # Combine system prompt with context for Gemini
            full_prompt = f"{self.get_system_prompt()}\n\n{context}"

            response = model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1500,
                    temperature=0.7
                )
            )

            return response.text.strip()

        except Exception as e:
            # Try fallback model
            try:
                fallback_model = Config.MODELS['gemini']['fallback']
                model = genai.GenerativeModel(fallback_model)

                full_prompt = f"{self.get_system_prompt()}\n\n{context}"

                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=1500,
                        temperature=0.7
                    )
                )
                return response.text.strip()
            except Exception as e2:
                raise Exception(f"Gemini primary and fallback failed: {e}, {e2}")

    def _generate_no_data_template(self, ingredient):
        """Generate template when no data is available"""
        return f"""**НАЗВА:** {ingredient}

**ДЖЕРЕЛО ОТРИМАННЯ:** немає достовірних даних

**АКТИВНІ СПОЛУКИ:** немає достовірних даних

**НАУКОВІ ДОСЛІДЖЕННЯ:**
- немає достовірних наукових досліджень у доступних джерелах

**РІВЕНЬ ДОКАЗІВ:** Level 4 (недостатньо даних)

**ДЖЕРЕЛА:**
1. Інформація не знайдена в перевірених наукових базах даних
2. Потребує додаткового дослідження"""

    def test_all_models(self):
        """Test all available models with a simple query"""
        print("[TEST] Testing all available AI models...")
        test_ingredient = "Vitamin C"

        for model_type in self.available_models:
            try:
                print(f"\n[TEST] Testing {model_type}...")

                if model_type == 'claude':
                    result = self._call_claude(f"Інгредієнт: {test_ingredient}\nКоротко опиши цей інгредієнт.")
                elif model_type == 'openai':
                    result = self._call_openai(f"Інгредієнт: {test_ingredient}\nКоротко опиши цей інгредієнт.")
                elif model_type == 'gemini':
                    result = self._call_gemini(f"Інгредієнт: {test_ingredient}\nКоротко опиши цей інгредієнт.")

                if result:
                    print(f"[OK] {model_type} working: {result[:100]}...")
                else:
                    print(f"[ERROR] {model_type} returned empty response")

            except Exception as e:
                print(f"[ERROR] {model_type} test failed: {e}")

        print("\n[COMPLETE] Model testing completed!")

# Global instance
multi_ai_client = MultiAIClient()