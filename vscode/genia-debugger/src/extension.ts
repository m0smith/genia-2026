import * as path from 'node:path';
import * as vscode from 'vscode';
import {
  GeniaDefinitionProvider,
  GeniaDocumentSymbolProvider,
  GeniaWorkspaceSymbolProvider,
} from './languageProviders';

export function activate(context: vscode.ExtensionContext): void {
  const factory = new GeniaDebugAdapterDescriptorFactory(context);
  const selector: vscode.DocumentSelector = [{ language: 'genia' }];

  context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('genia', factory));
  context.subscriptions.push(factory);

  context.subscriptions.push(vscode.languages.registerDocumentSymbolProvider(selector, new GeniaDocumentSymbolProvider()));
  context.subscriptions.push(vscode.languages.registerDefinitionProvider(selector, new GeniaDefinitionProvider()));
  context.subscriptions.push(vscode.languages.registerWorkspaceSymbolProvider(new GeniaWorkspaceSymbolProvider()));
}

export function deactivate(): void {
  // No-op.
}

class GeniaDebugAdapterDescriptorFactory implements vscode.DebugAdapterDescriptorFactory, vscode.Disposable {
  constructor(private readonly context: vscode.ExtensionContext) {}

  createDebugAdapterDescriptor(
    _session: vscode.DebugSession,
    _executable: vscode.DebugAdapterExecutable | undefined,
  ): vscode.ProviderResult<vscode.DebugAdapterDescriptor> {
    const adapterPath = path.join(this.context.extensionPath, 'out', 'geniaDebugAdapter.js');
    return new vscode.DebugAdapterExecutable('node', [adapterPath]);
  }

  dispose(): void {
    // No-op.
  }
}
