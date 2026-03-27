export type GeniaSymbolKind = 'function' | 'variable';

export interface IndexedRange {
  startLine: number;
  startCharacter: number;
  endLine: number;
  endCharacter: number;
}

export interface IndexedSymbol {
  kind: GeniaSymbolKind;
  name: string;
  parameters: string[];
  detail?: string;
  range: IndexedRange;
  selectionRange: IndexedRange;
}

export interface IndexedDocument {
  symbols: IndexedSymbol[];
  byName: Map<string, IndexedSymbol[]>;
}

const IDENTIFIER = /[A-Za-z_][A-Za-z0-9_]*/y;

export function indexGeniaDocument(text: string): IndexedDocument {
  const lines = text.split(/\r?\n/);
  const symbols: IndexedSymbol[] = [];

  let line = 0;
  while (line < lines.length) {
    const currentLine = stripComment(lines[line]);
    const match = currentLine.match(/^(\s*)([A-Za-z_][A-Za-z0-9_]*)\b/);

    if (!match) {
      line += 1;
      continue;
    }

    const indent = match[1].length;
    if (indent > 0) {
      line += 1;
      continue;
    }

    const name = match[2];
    const nameColumn = match[1].length;

    const functionHeader = collectFunctionHeader(lines, line, name);
    if (functionHeader) {
      const endLine = findDefinitionEnd(lines, line, functionHeader.headerEndLine, functionHeader.bodyToken);
      const endCharacter = lines[endLine]?.length ?? 0;
      symbols.push({
        kind: 'function',
        name,
        parameters: functionHeader.parameters,
        detail: `(${functionHeader.parameters.join(', ')})`,
        range: { startLine: line, startCharacter: 0, endLine, endCharacter },
        selectionRange: {
          startLine: line,
          startCharacter: nameColumn,
          endLine: line,
          endCharacter: nameColumn + name.length,
        },
      });
      line = endLine + 1;
      continue;
    }

    const assignment = stripComment(lines[line]).match(/^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(?![=])/);
    if (assignment) {
      const endLine = findAssignmentEnd(lines, line);
      symbols.push({
        kind: 'variable',
        name,
        parameters: [],
        range: { startLine: line, startCharacter: 0, endLine, endCharacter: lines[endLine]?.length ?? 0 },
        selectionRange: {
          startLine: line,
          startCharacter: nameColumn,
          endLine: line,
          endCharacter: nameColumn + name.length,
        },
      });
      line = endLine + 1;
      continue;
    }

    line += 1;
  }

  const byName = new Map<string, IndexedSymbol[]>();
  for (const symbol of symbols) {
    const bucket = byName.get(symbol.name) ?? [];
    bucket.push(symbol);
    byName.set(symbol.name, bucket);
  }

  return { symbols, byName };
}

export function findWordAtPosition(text: string, lineNumber: number, character: number): string | undefined {
  const lines = text.split(/\r?\n/);
  const line = lines[lineNumber] ?? '';
  if (line.length === 0) {
    return undefined;
  }

  let left = Math.min(character, line.length - 1);
  let right = left;

  const isWord = (ch: string): boolean => /[A-Za-z0-9_]/.test(ch);
  if (!isWord(line[left])) {
    if (left > 0 && isWord(line[left - 1])) {
      left -= 1;
      right = left;
    } else {
      return undefined;
    }
  }

  while (left > 0 && isWord(line[left - 1])) {
    left -= 1;
  }
  while (right + 1 < line.length && isWord(line[right + 1])) {
    right += 1;
  }

  const word = line.slice(left, right + 1);
  IDENTIFIER.lastIndex = 0;
  if (!IDENTIFIER.test(word)) {
    return undefined;
  }
  return word;
}

export function resolveDefinition(indexed: IndexedDocument, identifier: string): IndexedSymbol | undefined {
  return indexed.byName.get(identifier)?.[0];
}

function collectFunctionHeader(
  lines: string[],
  startLine: number,
  name: string,
): { parameters: string[]; bodyToken: '=' | '{'; headerEndLine: number } | undefined {
  const firstLine = stripComment(lines[startLine]);
  const headerStart = firstLine.match(new RegExp(`^${name}\\s*\\(`));
  if (!headerStart) {
    return undefined;
  }

  let line = startLine;
  let parenDepth = 0;
  let seenParen = false;
  let paramsBuffer = '';

  while (line < lines.length) {
    const segment = stripComment(lines[line]);
    for (let idx = 0; idx < segment.length; idx += 1) {
      const ch = segment[idx];
      if (!seenParen) {
        if (ch === '(') {
          seenParen = true;
          parenDepth = 1;
        }
        continue;
      }

      if (ch === '(') {
        parenDepth += 1;
      } else if (ch === ')') {
        parenDepth -= 1;
        if (parenDepth === 0) {
          const tail = segment.slice(idx + 1).trimStart();
          if (tail.startsWith('=') || tail.startsWith('{')) {
            return {
              parameters: parseParameters(paramsBuffer),
              bodyToken: tail[0] as '=' | '{',
              headerEndLine: line,
            };
          }

          const token = findBodyToken(lines, line + 1);
          if (token) {
            return {
              parameters: parseParameters(paramsBuffer),
              bodyToken: token.token,
              headerEndLine: token.line,
            };
          }
          return undefined;
        }
      }

      if (seenParen && parenDepth > 0) {
        paramsBuffer += ch;
      }
    }

    if (seenParen && parenDepth > 0) {
      paramsBuffer += '\n';
    }

    line += 1;
  }

  return undefined;
}

function parseParameters(raw: string): string[] {
  return raw
    .split(',')
    .map((entry) => entry.trim())
    .filter((entry) => /^[A-Za-z_][A-Za-z0-9_]*$/.test(entry));
}

function findBodyToken(lines: string[], fromLine: number): { token: '=' | '{'; line: number } | undefined {
  for (let line = fromLine; line < lines.length; line += 1) {
    const trimmed = stripComment(lines[line]).trim();
    if (!trimmed) {
      continue;
    }
    if (trimmed.startsWith('=') || trimmed.startsWith('{')) {
      return { token: trimmed[0] as '=' | '{', line };
    }
    return undefined;
  }
  return undefined;
}

function findDefinitionEnd(lines: string[], startLine: number, headerEndLine: number, bodyToken: '=' | '{'): number {
  if (bodyToken === '{') {
    return findMatchingBraceEnd(lines, headerEndLine) ?? headerEndLine;
  }

  return findAssignmentEnd(lines, headerEndLine);
}

function findAssignmentEnd(lines: string[], startLine: number): number {
  const baseIndent = leadingWhitespace(lines[startLine]);
  let endLine = startLine;

  for (let line = startLine + 1; line < lines.length; line += 1) {
    const raw = lines[line];
    const trimmed = stripComment(raw).trim();
    if (trimmed.length === 0) {
      endLine = line;
      continue;
    }

    const indent = leadingWhitespace(raw);
    if (indent > baseIndent) {
      endLine = line;
      continue;
    }

    break;
  }

  return endLine;
}

function findMatchingBraceEnd(lines: string[], startLine: number): number | undefined {
  let depth = 0;
  let sawOpening = false;

  for (let line = startLine; line < lines.length; line += 1) {
    const text = stripComment(lines[line]);
    for (const ch of text) {
      if (ch === '{') {
        depth += 1;
        sawOpening = true;
      } else if (ch === '}') {
        depth -= 1;
        if (sawOpening && depth === 0) {
          return line;
        }
      }
    }
  }

  return undefined;
}

function stripComment(line: string): string {
  const hash = line.indexOf('#');
  return hash >= 0 ? line.slice(0, hash) : line;
}

function leadingWhitespace(line: string): number {
  const match = line.match(/^\s*/);
  return match ? match[0].length : 0;
}
