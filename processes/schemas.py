"""
JSON Schemas for the scientific evidence collection system
"""

INGREDIENT_SCHEMA = {
    "type": "object",
    "properties": {
        "ingredient": {"type": "string"},
        "taxon": {
            "type": "object",
            "properties": {
                "uk": {"type": "string"},
                "lat": {"type": "string"},
                "rank": {"type": "string", "enum": ["species", "genus", "other"]}
            },
            "required": ["uk", "lat", "rank"]
        },
        "source_material": {
            "type": "object",
            "properties": {
                "kingdom": {
                    "type": "string",
                    "enum": ["Рослини", "Тварини", "Гриби", "Бактерії", "Людина", "Інше"]
                },
                "part_or_origin": {"type": "string"},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["kingdom", "part_or_origin"]
        },
        "active_compounds": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "evidence": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string", "format": "uri"},
                                "doi": {"type": ["string", "null"]},
                                "pmid": {"type": ["string", "null"]},
                                "quote_en": {"type": "string", "maxLength": 35},
                                "source_priority": {"type": "integer", "minimum": 1, "maximum": 4}
                            },
                            "required": ["url", "quote_en", "source_priority"]
                        },
                        "minItems": 1
                    }
                },
                "required": ["name", "evidence"]
            }
        },
        "daily_dose": {
            "type": "object",
            "properties": {
                "statement": {"type": ["string", "null"]},
                "unit": {
                    "type": ["string", "null"],
                    "enum": ["mg", "µg", "IU", "CFU", "g", "ml", "units", "other", None]
                },
                "context": {
                    "type": ["string", "null"],
                    "enum": ["adult", "pregnant", "pediatric", "general", None]
                },
                "evidence": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "url": {"type": "string", "format": "uri"},
                            "doi": {"type": ["string", "null"]},
                            "pmid": {"type": ["string", "null"]},
                            "quote_en": {"type": "string", "maxLength": 35},
                            "source_priority": {"type": "integer", "minimum": 1, "maximum": 4}
                        },
                        "required": ["url", "quote_en", "source_priority"]
                    }
                }
            }
        },
        "probiotic": {
            "type": "object",
            "properties": {
                "strain": {"type": ["string", "null"]},
                "cfu_formulation": {"type": ["string", "null"]}
            }
        },
        "class_overrides": {
            "type": "object",
            "properties": {
                "vitamin_form": {"type": ["string", "null"]},
                "mineral_form": {"type": ["string", "null"]},
                "enzyme_origin": {"type": ["string", "null"]}
            }
        },
        "result_status": {
            "type": "string",
            "enum": ["complete", "partial", "no_data"]
        },
        "log": {
            "type": "object",
            "properties": {
                "search_terms": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "time": {"type": "string", "format": "date-time"},
                "notes": {"type": "string"}
            },
            "required": ["search_terms", "time"]
        }
    },
    "required": [
        "ingredient", "taxon", "source_material", "active_compounds",
        "daily_dose", "result_status", "log"
    ]
}

NORMALIZER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "ingredient": {"type": "string"},
        "class": {
            "type": "string",
            "enum": ["plant", "animal", "vitamin", "mineral", "enzyme", "probiotic", "other"]
        },
        "taxon": {
            "type": "object",
            "properties": {
                "uk": {"type": "string"},
                "lat": {"type": "string"},
                "rank": {"type": "string", "enum": ["species", "genus", "other"]}
            },
            "required": ["uk", "lat", "rank"]
        },
        "source_material": {
            "type": "object",
            "properties": {
                "kingdom": {
                    "type": "string",
                    "enum": ["Рослини", "Тварини", "Гриби", "Бактерії", "Інше"]
                },
                "part_or_origin": {"type": "string"},
                "notes": {"type": ["string", "null"]}
            },
            "required": ["kingdom", "part_or_origin"]
        }
    },
    "required": ["ingredient", "class", "taxon", "source_material"]
}

SEARCHER_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "search_terms": {
            "type": "array",
            "items": {"type": "string"},
            "minItems": 8,
            "maxItems": 14
        },
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "domain": {"type": "string"},
                    "year": {"type": ["integer", "null"]},
                    "doi": {"type": ["string", "null"]},
                    "pmid": {"type": ["string", "null"]},
                    "why": {"type": "string"}
                },
                "required": ["title", "url", "domain", "why"]
            },
            "maxItems": 20
        }
    },
    "required": ["search_terms", "candidates"]
}

JUDGE_OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "accepted": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "source_priority": {"type": "integer", "minimum": 1, "maximum": 4},
                    "doi": {"type": ["string", "null"]},
                    "pmid": {"type": ["string", "null"]}
                },
                "required": ["title", "url", "source_priority"]
            }
        },
        "rejected": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "reason": {"type": "string"}
                },
                "required": ["url", "reason"]
            }
        }
    },
    "required": ["accepted", "rejected"]
}