import json
from pathlib import Path

import jsonschema

from trace.models.mock import MockModel


def load_schema():
    with Path("schemas/trace-per-turn-response.schema.json").open("r", encoding="utf-8") as f:
        return json.load(f)


def test_mock_per_turn_schema_valid():
    schema = load_schema()
    model = MockModel(mode="per_turn", perfect=True)
    resp = model.generate("irrelevant")
    obj = json.loads(resp)
    jsonschema.validate(instance=obj, schema=schema)

