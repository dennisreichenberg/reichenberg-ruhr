"""Tests for the YAML-driven cost estimation."""

from llm_usage.pricing import PricingTable


def test_packaged_table_loads():
    table = PricingTable.load()
    # gpt-4o is in the shipped defaults.
    assert table.rate_for("gpt-4o")[0] > 0


def test_local_backend_is_free():
    table = PricingTable.load()
    assert table.estimate("qwen2.5-coder:7b", 1000, 1000, backend="ollama") == 0.0
    assert table.estimate("vllm/whatever", 1000, 1000, backend="vllm") == 0.0


def test_provider_prefix_is_stripped():
    table = PricingTable({"models": {"gpt-4o": {"input": 2.5, "output": 10.0}}})
    assert table.rate_for("openai/gpt-4o") == (2.5, 10.0)


def test_estimate_per_million_tokens():
    table = PricingTable({"models": {"gpt-4o": {"input": 2.5, "output": 10.0}}})
    # 1M prompt tokens -> $2.50, 1M completion -> $10.00
    assert table.estimate("gpt-4o", 1_000_000, 0) == 2.5
    assert table.estimate("gpt-4o", 0, 1_000_000) == 10.0
    assert table.estimate("gpt-4o", 1000, 1000) == round((2.5 + 10.0) / 1000, 6)


def test_unknown_model_falls_back_to_default():
    table = PricingTable({"default": {"input": 1.0, "output": 1.0}})
    assert table.rate_for("totally-unknown") == (1.0, 1.0)


def test_bare_number_entry():
    table = PricingTable({"models": {"flat": 5.0}})
    assert table.rate_for("flat") == (5.0, 5.0)
