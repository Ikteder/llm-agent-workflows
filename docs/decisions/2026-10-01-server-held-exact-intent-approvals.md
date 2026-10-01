# Decision: hold exact approved intent on the server

Date: 2026-10-01
Status: accepted

## Context

The application needs human review before its report tool writes files. A Boolean such as `approved=true`, a tool-name allow list, or a client-supplied copy of approved arguments is not enough. Those approaches do not prove that the reviewed arguments are the ones that execute, and they can permit replay after a retry or page refresh.

Current framework documentation consistently separates human approval from application authorization. Current issue evidence also shows real complexity around transformed arguments and resumed side effects.

## Decision

Keep the pending invocation in application memory and identify it with an opaque UUID. Bind a keyed digest to the session, tool name, complete validated arguments, project, and policy version. The approval endpoint changes only the server-held record. Execution requires the approval ID and consumes the record before the filesystem write.

The resumed request executes the stored invocation rather than rebuilding it from a second model response. This preserves exact reviewed intent even if future answer generation becomes nondeterministic.

## Consequences

- Argument mutation, cross-session use, stale policy use, and replay fail closed.
- A process restart invalidates pending and approved requests. This is deliberate for version 0.2 and safer than reconstructing authority from an audit log.
- The feature does not authenticate the approver. A network deployment must add its own identity, role, and transport controls.
- Approval state is intentionally single-process. Durable authorization storage is future work and must preserve the same exact-intent and single-use properties.

