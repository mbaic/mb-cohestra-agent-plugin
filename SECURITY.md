# Security policy

## Report a vulnerability

Report a vulnerability privately. Use a [GitHub security advisory](https://github.com/mbaic/mb-cohestra-agent-plugin/security/advisories/new). Do not open a public issue or discussion.

Include these items:

- The affected version.
- The client and its version.
- The impact.
- Steps to reproduce.
- A proposed correction, when you have one.

The maintainer reads reports on a best-effort basis.

## Supported versions

Cohestra is a pre-1.0 product. Only the latest 0.x release gets security corrections. Update to the latest release before you report a defect.

## Trust model

A plugin changes what an AI client can do. Read the files before you install Cohestra.

- The package contains no hooks, no MCP server, no background service, and no telemetry code.
- The package contains no binary executable, install script, or credential collection.
- Agents are Markdown files. They tell a model what to do. They do not run code on their own.
- Some specialists have edit and execute tools. The client grants and limits these tools. Review each action that the client asks you to approve.
- Source code enters the model context when an agent reads it. Check the data policy of your organization before you use Cohestra on private code.
- The validation and packaging scripts read repository files and write local output. The optional `--online` flag of the validator fetches the public Agent Plugins schema.

## Secrets

Do not put secrets in issues, pull requests, logs, or eval fixtures. Remove tokens, keys, private URLs, and personal paths before you share a log.

## Scope

The behavior of the host client is outside the package boundary. This includes its permissions, sandbox, model providers, and data handling. Report host defects to the vendor of the client.
