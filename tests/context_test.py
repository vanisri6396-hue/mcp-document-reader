from context.manager import ContextManager


def test_message_limiting():
    manager = ContextManager(
        max_messages=5,
        max_context_tokens=1000,
        max_tool_result_chars=500,
        response_token_reserve=100,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Original user request",
        }
    )

    for index in range(10):
        manager.add_and_manage(
            {
                "role": "assistant",
                "content": f"Message {index}",
            }
        )

    assert manager.message_count() <= 5

    messages = manager.get_messages()

    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Original user request"


def test_original_user_request_is_preserved():
    manager = ContextManager(
        max_messages=4,
        max_context_tokens=1000,
        max_tool_result_chars=500,
        response_token_reserve=100,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Important original task",
        }
    )

    for index in range(10):
        manager.add_and_manage(
            {
                "role": "assistant",
                "content": f"Assistant message {index}",
            }
        )

    messages = manager.get_messages()

    assert messages[0]["content"] == "Important original task"


def test_tool_call_and_result_are_preserved_together():
    manager = ContextManager(
        max_messages=6,
        max_context_tokens=2000,
        max_tool_result_chars=500,
        response_token_reserve=100,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Find information.",
        }
    )

    manager.add_and_manage(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "search_documents",
                        "arguments": '{"query":"MCP"}',
                    },
                }
            ],
        }
    )

    manager.add_tool_result(
        tool_name="search_documents",
        tool_call_id="call_1",
        content='{"documents":["report.txt"]}',
    )

    messages = manager.get_messages()

    assistant_tool_calls = [
        message
        for message in messages
        if (
            message.get("role") == "assistant"
            and message.get("tool_calls")
        )
    ]

    tool_results = [
        message
        for message in messages
        if message.get("role") == "tool"
    ]

    assert len(assistant_tool_calls) == len(tool_results)


def test_tool_result_optimization():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=2000,
        max_tool_result_chars=100,
        response_token_reserve=100,
    )

    large_result = "A" * 1000

    optimized = manager.optimize_tool_result(
        large_result
    )

    assert len(optimized) > 0
    assert "truncated" in optimized.lower()
    assert "Original length" in optimized

    assert manager.truncated_tool_results == 1


def test_small_tool_result_is_not_truncated():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=2000,
        max_tool_result_chars=100,
        response_token_reserve=100,
    )

    small_result = "Small result."

    optimized = manager.optimize_tool_result(
        small_result
    )

    assert optimized == small_result
    assert manager.truncated_tool_results == 0


def test_token_estimation():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=2000,
        max_tool_result_chars=500,
        response_token_reserve=100,
    )

    text = "A" * 400

    estimated_tokens = manager.estimate_tokens_from_text(
        text
    )

    assert estimated_tokens == 100


def test_context_budget():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=1000,
        max_tool_result_chars=500,
        response_token_reserve=200,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Test context.",
        }
    )

    assert manager.usable_context_tokens == 800

    assert manager.remaining_tokens() >= 0


def test_context_statistics():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=2000,
        max_tool_result_chars=500,
        response_token_reserve=200,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Test request.",
        }
    )

    stats = manager.get_stats()

    assert stats.message_count == 1
    assert stats.estimated_tokens > 0
    assert stats.max_messages == 20
    assert stats.max_context_tokens == 2000
    assert stats.remaining_tokens >= 0


def test_add_tool_result():
    manager = ContextManager(
        max_messages=20,
        max_context_tokens=2000,
        max_tool_result_chars=500,
        response_token_reserve=200,
    )

    manager.add_message(
        {
            "role": "user",
            "content": "Read the document.",
        }
    )

    manager.add_and_manage(
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_document",
                        "arguments": (
                            '{"doc_id":"report.txt"}'
                        ),
                    },
                }
            ],
        }
    )

    manager.add_tool_result(
        tool_name="read_document",
        tool_call_id="call_1",
        content="Document contents.",
    )

    messages = manager.get_messages()

    assert messages[-1]["role"] == "tool"
    assert messages[-1]["name"] == "read_document"
    assert messages[-1]["tool_call_id"] == "call_1"
    assert messages[-1]["content"] == "Document contents."


def test_clear():
    manager = ContextManager()

    manager.add_message(
        {
            "role": "user",
            "content": "Test",
        }
    )

    manager.clear()

    assert manager.message_count() == 0
    assert manager.truncated_tool_results == 0


def test_invalid_configuration():
    try:
        ContextManager(max_messages=1)
        assert False
    except ValueError:
        pass

    try:
        ContextManager(max_context_tokens=50)
        assert False
    except ValueError:
        pass

    try:
        ContextManager(max_tool_result_chars=50)
        assert False
    except ValueError:
        pass


def run_tests():
    tests = [
        test_message_limiting,
        test_original_user_request_is_preserved,
        test_tool_call_and_result_are_preserved_together,
        test_tool_result_optimization,
        test_small_tool_result_is_not_truncated,
        test_token_estimation,
        test_context_budget,
        test_context_statistics,
        test_add_tool_result,
        test_clear,
        test_invalid_configuration,
    ]

    passed = 0
    failed = 0

    print("\n" + "=" * 70)
    print("LEVEL 7.9 CONTEXT MANAGEMENT TEST SUITE")
    print("=" * 70)

    for test in tests:

        try:
            test()

            print(f"PASS: {test.__name__}")
            passed += 1

        except Exception as error:

            print(f"FAIL: {test.__name__}")
            print(f"      {error}")

            failed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    print(f"PASSED : {passed}")
    print(f"FAILED : {failed}")
    print(f"TOTAL  : {len(tests)}")

    if failed == 0:
        print("\nCONTEXT MANAGEMENT STATUS: PASS")
        print("All Level 7.9 tests passed successfully.")
    else:
        print("\nCONTEXT MANAGEMENT STATUS: FAIL")
        print("Some Level 7.9 tests failed.")

    return failed == 0


if __name__ == "__main__":
    success = run_tests()

    if not success:
        raise SystemExit(1)