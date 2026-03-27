import test from 'node:test';
import assert from 'node:assert/strict';
import { findWordAtPosition, indexGeniaDocument, resolveDefinition } from './languageIndexer';

test('indexer finds top-level functions and assignments', () => {
  const source = `add(a, b) = a + b
value = 1
  nested(x) = x
`;

  const indexed = indexGeniaDocument(source);
  assert.equal(indexed.symbols.length, 2);
  assert.equal(indexed.symbols[0]?.kind, 'function');
  assert.equal(indexed.symbols[0]?.name, 'add');
  assert.deepEqual(indexed.symbols[0]?.parameters, ['a', 'b']);
  assert.equal(indexed.symbols[1]?.kind, 'variable');
  assert.equal(indexed.symbols[1]?.name, 'value');
});

test('indexer finds multiline function definitions', () => {
  const source = `fact(
  n
) =
  if(n == 0, 1, n * fact(n - 1))
next = 42
`;

  const indexed = indexGeniaDocument(source);
  const fact = indexed.symbols.find((symbol) => symbol.name === 'fact');
  assert.ok(fact);
  assert.equal(fact.kind, 'function');
  assert.deepEqual(fact.parameters, ['n']);
  assert.equal(fact.range.startLine, 0);
  assert.equal(fact.range.endLine, 3);
});

test('definition resolution finds same-file function definition', () => {
  const source = `sum(a, b) = a + b
x = sum(1, 2)
`;

  const indexed = indexGeniaDocument(source);
  const callLine = 1;
  const characterInName = source.split(/\r?\n/)[callLine].indexOf('sum') + 1;
  const word = findWordAtPosition(source, callLine, characterInName);
  assert.equal(word, 'sum');

  const resolved = resolveDefinition(indexed, word!);
  assert.ok(resolved);
  assert.equal(resolved.name, 'sum');
  assert.equal(resolved.selectionRange.startLine, 0);
});

test('malformed code does not crash indexing', () => {
  const source = `broken(
  x,
# comment only
name =
foo( =
`;

  assert.doesNotThrow(() => indexGeniaDocument(source));
  const indexed = indexGeniaDocument(source);
  assert.ok(Array.isArray(indexed.symbols));
});
