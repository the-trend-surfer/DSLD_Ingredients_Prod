"""
JSON Schema для 5-стовпчикової таблиці згідно вимог користувача
"""

TABLE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "nazva_ukr_orig": {
            "type": "string",
            "description": "Назва українською [Оригінальна назва]",
            "example": "АХЦЦ [AHCC]"
        },
        "dzherelo_syrovyny": {
            "type": "string",
            "description": "Джерело отримання біологічно активної речовини - частина рослини/організму/сировина",
            "example": "міцелій грибів шіїтаке (Lentinula edodes)"
        },
        "aktyvni_spoluky": {
            "type": "array",
            "description": "Тільки підтверджені активні речовини",
            "items": {
                "type": "string",
                "description": "Назва підтвердженої активної сполуки"
            },
            "example": ["альфа-глюкани", "бета-глюкани", "амінокислоти"]
        },
        "dobova_norma": {
            "type": "string",
            "description": "Конкретне значення або 'немає даних'",
            "example": "3 грами на добу"
        },
        "dzherela_tsytaty": {
            "type": "array",
            "description": "Джерела та цитати",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "quote": {"type": "string", "maxLength": 35},
                    "type": {"type": "string", "enum": ["PubMed", "EFSA", "FDA", "Journal"]}
                },
                "required": ["url", "quote", "type"]
            }
        }
    },
    "required": ["nazva_ukr_orig", "dzherelo_syrovyny", "aktyvni_spoluky", "dobova_norma", "dzherela_tsytaty"]
}