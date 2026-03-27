import * as vscode from 'vscode';
import { findWordAtPosition, indexGeniaDocument, resolveDefinition } from './languageIndexer';

export class GeniaDocumentSymbolProvider implements vscode.DocumentSymbolProvider {
  provideDocumentSymbols(document: vscode.TextDocument): vscode.ProviderResult<vscode.DocumentSymbol[]> {
    const indexed = indexGeniaDocument(document.getText());
    return indexed.symbols.map((symbol) => {
      const range = toRange(symbol.range);
      const selectionRange = toRange(symbol.selectionRange);
      const kind = symbol.kind === 'function' ? vscode.SymbolKind.Function : vscode.SymbolKind.Variable;
      return new vscode.DocumentSymbol(symbol.name, symbol.detail ?? '', kind, range, selectionRange);
    });
  }
}

export class GeniaDefinitionProvider implements vscode.DefinitionProvider {
  provideDefinition(
    document: vscode.TextDocument,
    position: vscode.Position,
  ): vscode.ProviderResult<vscode.Definition | vscode.DefinitionLink[]> {
    const text = document.getText();
    const word = findWordAtPosition(text, position.line, position.character);
    if (!word) {
      return undefined;
    }

    const indexed = indexGeniaDocument(text);
    const target = resolveDefinition(indexed, word);
    if (!target) {
      return undefined;
    }

    return new vscode.Location(document.uri, toRange(target.selectionRange));
  }
}

export class GeniaWorkspaceSymbolProvider implements vscode.WorkspaceSymbolProvider {
  async provideWorkspaceSymbols(query: string, token: vscode.CancellationToken): Promise<vscode.SymbolInformation[]> {
    const normalizedQuery = query.trim().toLowerCase();
    const uris = await vscode.workspace.findFiles('**/*.genia', '**/node_modules/**', 200);
    const symbols: vscode.SymbolInformation[] = [];

    for (const uri of uris) {
      if (token.isCancellationRequested) {
        break;
      }

      const document = await vscode.workspace.openTextDocument(uri);
      const indexed = indexGeniaDocument(document.getText());

      for (const symbol of indexed.symbols) {
        if (normalizedQuery && !symbol.name.toLowerCase().includes(normalizedQuery)) {
          continue;
        }

        symbols.push(
          new vscode.SymbolInformation(
            symbol.name,
            symbol.kind === 'function' ? vscode.SymbolKind.Function : vscode.SymbolKind.Variable,
            symbol.detail ?? '',
            new vscode.Location(uri, toRange(symbol.selectionRange)),
          ),
        );
      }
    }

    return symbols;
  }
}

function toRange(range: { startLine: number; startCharacter: number; endLine: number; endCharacter: number }): vscode.Range {
  return new vscode.Range(
    new vscode.Position(range.startLine, range.startCharacter),
    new vscode.Position(range.endLine, range.endCharacter),
  );
}
