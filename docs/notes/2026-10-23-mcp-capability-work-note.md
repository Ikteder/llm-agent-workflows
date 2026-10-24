# MCP Capability Receipt Work Note

Date: 2026-10-23

The existing approval engine already prevented argument replacement, replay, cross-session use, expiry, stale policy use, unknown projects, and path escape. Its external-tool gap was definition identity: the approval HMAC had no capability digest, and consumption accepted only an approval ID plus local scope fields.

The implementation keeps the local path unchanged and adds optional external capability evidence. A first test assertion incorrectly rejected the word `description` in a safe section-digest key; it was corrected to assert that the raw description value is absent. The final integration behavior keeps a drifted approval available rather than consuming it, which supports recovery from a stale cache or transient wrong-server connection without silently widening authority.

The selected evidence visual is an authored SVG bar comparison because the relationship between 3/14 and 14/14 is central to the change. It is generated from raw JSON and parsed as XML during verification.

## Closure on 2026-10-24

The user requested completion, verified GitHub publication, and cancellation of this automation after this project. This is closure of the original seed `20261023`, not a new seeded project run. The primary dirty checkout remains untouched. Final review added fail-closed handling for malformed observations and local-to-external approval reuse, detached public approval previews from the stored authority, and documented adapter freshness and connection requirements. The final local source suite passed 42 tests on Python 3.14.8. The earlier Python 3.15 label in the experiment record was corrected from the environment's actual interpreter version.
