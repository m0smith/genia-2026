import * as path from 'node:path';
import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext): void {
  const factory = new GeniaDebugAdapterDescriptorFactory(context);
  context.subscriptions.push(vscode.debug.registerDebugAdapterDescriptorFactory('genia', factory));
  context.subscriptions.push(factory);
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
