"""Secret reference test vectors.

Ported from OpenClaw src/test-utils/secret-ref-test-vectors.ts

Test vectors for validating secret reference ID parsing.
Separated into valid and invalid sets for file-based and exec-based refs.
"""

# Valid file-based secret ref IDs (JSON Pointer style)
VALID_FILE_SECRET_REF_IDS = [
    "value",
    "/",
    "//",
    "/providers/openai/apiKey",
    "/providers//apiKey",
    "/~0/~1",
    "/" + ("/" * 256),
]

# Invalid file-based secret ref IDs
INVALID_FILE_SECRET_REF_IDS = [
    "",
    "providers/openai/apiKey",  # missing leading /
    "value/extra",  # trailing path segments
    "/providers/openai/apiKey~",  # invalid escape
    "/providers/openai/apiKey~2",  # invalid escape
    "/providers/openai/~)",
]

# Valid exec-based secret ref IDs
VALID_EXEC_SECRET_REF_IDS = [
    "vault/openai/api-key",
    "vault:secret/mykey",
    "providers/openai/apiKey",
    "aws/secret#json_key",
    "a..b/c",
    "a/.../b",
    "a/.well-known/key",
    "a/" + "b" * 254,
]

# Invalid exec-based secret ref IDs
INVALID_EXEC_SECRET_REF_IDS = [
    "",
    " ",
    "a/../b",  # path traversal
    "a/./b",  # self-reference
    "../b",  # relative traversal
    "./b",  # relative self-reference
    "a/..",  # trailing traversal
    "a/.",  # trailing self-reference
    "/absolute/path",  # absolute path
    "bad id",  # space in ID
    "a\\b",  # backslash
    "a" + "b" * 256,  # too long
]
