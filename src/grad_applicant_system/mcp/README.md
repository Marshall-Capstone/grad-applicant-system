# mcp

## Purpose

This folder contains the Model Context Protocol (MCP) layer for the Graduate Applicant System.

Its job is to expose selected system functionality as tools that can be called by an LLM or other MCP-compatible client.

---

## Belongs here

- MCP server setup
- MCP transport configuration
- MCP tool registration
- thin MCP tool handlers/wrappers
- schemas or tool definitions specific to MCP exposure

Examples:
- `server.py`
- `tools/list_applicants.py`
- `tools/get_applicant_by_email.py`

---

## Does not belong here

- direct business workflow logic
- large SQL implementations
- PDF parsing implementations
- UI code
- domain model definitions

Those belong in:
- `application/`
- `infrastructure/`
- `presentation/`
- `domain/`

---

## Design rule

Code in `mcp/` should stay thin.

An MCP tool should usually:
1. receive input from the client
2. call into an application use-case or service
3. return the result in MCP-friendly form

It should not become the main place where system logic lives.