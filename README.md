# MCP Document Reader

A hands-on Model Context Protocol (MCP) server and client built with Python.

This project was developed step-by-step to understand how MCP works internally and how to build a real MCP server with tools, resources, prompts, structured outputs, validation, pagination, and a Python MCP client.

## 🚀 Features

- MCP server using Python
- MCP client using Python
- CRUD document operations
- Pydantic input validation
- Structured tool outputs
- Document search
- Pagination
- MCP resource templates
- MCP prompts
- Error handling
- Repository and service layers
- Path-safe document access
- MCP Inspector testing
- STDIO transport

## 🏗️ Architecture

```text
MCP Client
    ↓
MCP Protocol
    ↓
STDIO Transport
    ↓
MCP Server
    ↓
MCP Tools / Resources / Prompts
    ↓
Service Layer
    ↓
Repository Layer
    ↓
Local Documents