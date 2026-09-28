#!/usr/bin/env python3
# merge-mcp-config.py v2 - merge MCP servers into ~/.codely-cli/settings.json (CEO order P-2026-09-28-15)
# Usage: python merge-mcp-config.py <fragment.json> [toolsDir]
#   fragment.json = {"servers": {"<name>": {...config...}, ...}}
# Token substitution in all string values (fleet path adaptation):
#   %TOOLS%       -> toolsDir (default: ~\tools)
#   %TOOLS_NODE%  -> toolsDir\nodejs\node.exe
#   %PW_ENTRY%    -> toolsDir\nodejs\node_modules\@playwright\mcp\cli.js
# Additive only: never deletes existing servers; skips names already present
# unless the fragment config contains "force": true (then overwrite that server).
import json, os, sys

HOME = os.path.expanduser('~')
SETTINGS = os.path.join(HOME, '.codely-cli', 'settings.json')

def substitute(v, tokens):
    if isinstance(v, str):
        for k, t in tokens.items():
            v = v.replace(k, t)
        return v
    if isinstance(v, list):
        return [substitute(x, tokens) for x in v]
    if isinstance(v, dict):
        return {k: substitute(x, tokens) for k, x in v.items()}
    return v

def main():
    tools = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HOME, 'tools')
    tokens = {
        '%TOOLS%': tools,
        '%TOOLS_NODE%': os.path.join(tools, 'nodejs', 'node.exe'),
        '%PW_ENTRY%': os.path.join(tools, 'nodejs', 'node_modules', '@playwright', 'mcp', 'cli.js'),
        '%LOCALBIN%': os.path.join(HOME, '.local', 'bin'),
    }
    if len(sys.argv) < 2:
        print('USAGE merge-mcp-config.py <fragment.json> [toolsDir]'); sys.exit(2)
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        frag = json.load(f)
    servers = {k: substitute(v, tokens) for k, v in frag.get('servers', {}).items()}
    cfg = {}
    if os.path.exists(SETTINGS):
        with open(SETTINGS, 'r', encoding='utf-8-sig') as f:
            cfg = json.load(f)
    existing = cfg.get('mcpServers', {})
    added, skipped, forced = [], [], []
    for name, conf in servers.items():
        if name in existing:
            if conf.pop('force', False):
                existing[name] = conf; forced.append(name)
            else:
                skipped.append(name)
        else:
            existing[name] = conf; added.append(name)
    cfg['mcpServers'] = existing
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print('MERGE_OK added=' + ','.join(added) + ' skipped=' + ','.join(skipped) + ' forced=' + ','.join(forced))
    print('SERVERS_NOW=' + ','.join(sorted(existing.keys())))

if __name__ == '__main__':
    main()
