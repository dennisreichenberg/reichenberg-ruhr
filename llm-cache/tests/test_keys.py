from llm_cache.keys import chat_key, embedding_key, last_user_message, semantic_bucket


def test_chat_key_is_deterministic_and_field_sensitive() -> None:
    p1 = {
        "model": "llama3",
        "messages": [{"role": "user", "content": "hi"}],
        "temperature": 0.0,
        "stream": False,
    }
    p2 = dict(p1)
    # cache-irrelevant fields must not affect the key
    p2["user"] = "alice"
    p2["stream"] = True
    assert chat_key(p1) == chat_key(p2)

    p3 = dict(p1)
    p3["temperature"] = 0.7
    assert chat_key(p1) != chat_key(p3)


def test_embedding_key() -> None:
    a = {"model": "nomic", "input": "hello"}
    b = {"model": "nomic", "input": "hello"}
    c = {"model": "nomic", "input": "world"}
    assert embedding_key(a) == embedding_key(b)
    assert embedding_key(a) != embedding_key(c)


def test_last_user_message_string() -> None:
    payload = {
        "messages": [
            {"role": "system", "content": "be terse"},
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "tell me a joke"},
        ]
    }
    assert last_user_message(payload) == "tell me a joke"


def test_last_user_message_parts() -> None:
    payload = {
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {"type": "image_url", "image_url": {"url": "..."}},
                    {"type": "text", "text": "this"},
                ],
            }
        ]
    }
    assert last_user_message(payload) == "describe this"


def test_last_user_message_none() -> None:
    assert last_user_message({}) is None
    assert last_user_message({"messages": [{"role": "system", "content": "x"}]}) is None


def test_semantic_bucket_is_per_model() -> None:
    assert semantic_bucket("a") != semantic_bucket("b")
    assert semantic_bucket("a") == semantic_bucket("a")
