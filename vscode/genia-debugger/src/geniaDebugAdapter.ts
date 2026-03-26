import * as fs from 'node:fs';
import * as path from 'node:path';
import * as readline from 'node:readline';
import { spawn, ChildProcessWithoutNullStreams } from 'node:child_process';
import {
  ContinuedEvent,
  DebugSession,
  InitializedEvent,
  LoggingDebugSession,
  OutputEvent,
  Scope,
  Source,
  StackFrame,
  StoppedEvent,
  TerminatedEvent,
  Thread,
  Handles,
  Breakpoint,
} from '@vscode/debugadapter';
import { DebugProtocol } from '@vscode/debugprotocol';

interface GeniaLaunchRequestArguments extends DebugProtocol.LaunchRequestArguments {
  program: string;
  cwd?: string;
  runtimeExecutable?: string;
  runtimeArgs?: string[];
  stopOnEntry?: boolean;
}

type PendingResolver = (value: Record<string, unknown>) => void;

class GeniaDebugSession extends LoggingDebugSession {
  private static readonly THREAD_ID = 1;

  private runtime?: ChildProcessWithoutNullStreams;
  private runtimeReader?: readline.Interface;
  private readonly pendingByCommand = new Map<string, PendingResolver[]>();
  private readonly variableHandles = new Handles<{ frameId: number; scope: string }>();
  private configurationDone = false;

  public constructor() {
    super('genia-debug.txt');
    this.setDebuggerLinesStartAt1(true);
    this.setDebuggerColumnsStartAt1(true);
    this.setDebuggerPathFormat('path');
  }

  protected initializeRequest(
    response: DebugProtocol.InitializeResponse,
    _args: DebugProtocol.InitializeRequestArguments,
  ): void {
    response.body = {
      supportsConfigurationDoneRequest: true,
      supportsTerminateRequest: true,
    };
    this.sendResponse(response);
  }

  protected async launchRequest(
    response: DebugProtocol.LaunchResponse,
    args: GeniaLaunchRequestArguments,
  ): Promise<void> {
    try {
      const program = this.normalizeProgramPath(args.program);
      if (!fs.existsSync(program)) {
        throw new Error(`Program not found: ${program}`);
      }

      const runtimeExecutable = args.runtimeExecutable ?? 'python3';
      const runtimeArgs = Array.isArray(args.runtimeArgs) ? args.runtimeArgs : ['-m', 'genia.interpreter'];
      const spawnArgs = [...runtimeArgs, '--debug-stdio', program];
      const cwd = args.cwd ? path.resolve(args.cwd) : path.dirname(program);

      this.runtime = spawn(runtimeExecutable, spawnArgs, {
        cwd,
        stdio: 'pipe',
      });

      this.runtime.on('error', (err) => {
        this.sendEvent(new OutputEvent(`Genia runtime failed to start: ${err.message}\n`, 'stderr'));
        this.sendEvent(new TerminatedEvent());
      });

      this.runtime.on('exit', (code, signal) => {
        if (signal) {
          this.sendEvent(new OutputEvent(`Genia runtime exited due to signal ${signal}.\n`, 'stderr'));
        } else if (typeof code === 'number' && code !== 0) {
          this.sendEvent(new OutputEvent(`Genia runtime exited with code ${code}.\n`, 'stderr'));
        }
        this.sendEvent(new TerminatedEvent());
      });

      this.runtime.stderr.on('data', (chunk: Buffer) => {
        this.sendEvent(new OutputEvent(chunk.toString(), 'stderr'));
      });

      this.runtimeReader = readline.createInterface({ input: this.runtime.stdout });
      this.runtimeReader.on('line', (line: string) => this.onRuntimeLine(line));

      this.sendResponse(response);

      if (args.stopOnEntry === false) {
        const command = this.configurationDone ? Promise.resolve() : this.awaitConfigurationDone();
        void command.then(() => this.sendRuntimeCommandNoResponse('continue', {}));
      }
    } catch (err) {
      this.sendErrorResponse(response, {
        id: 1001,
        format: `Failed to launch Genia runtime: ${(err as Error).message}`,
      });
    }
  }

  protected setBreakPointsRequest(
    response: DebugProtocol.SetBreakpointsResponse,
    args: DebugProtocol.SetBreakpointsArguments,
  ): void {
    const sourcePath = this.normalizeSourcePath(args.source);
    const requested = args.breakpoints ?? [];
    const lines = args.lines ?? requested.map((bp) => bp.line ?? 1);
    const runtimeBreakpoints = lines.map((line) => ({ file: sourcePath, line }));

    void this.sendRuntimeCommand('setBreakpoints', { breakpoints: runtimeBreakpoints })
      .then((payload) => {
        const raw = Array.isArray(payload.breakpoints) ? payload.breakpoints : [];
        const verifiedSet = new Set(raw.map((entry) => this.breakpointKey(entry)));
        response.body = {
          breakpoints: lines.map((line) => {
            const key = `${sourcePath}:${line}`;
            return new Breakpoint(verifiedSet.size === 0 || verifiedSet.has(key), line, 0, new Source(path.basename(sourcePath), sourcePath));
          }),
        };
        this.sendResponse(response);
      })
      .catch((err) => {
        this.sendErrorResponse(response, { id: 1002, format: `setBreakpoints failed: ${(err as Error).message}` });
      });
  }

  protected configurationDoneRequest(response: DebugProtocol.ConfigurationDoneResponse): void {
    this.configurationDone = true;
    this.sendResponse(response);
  }

  protected threadsRequest(response: DebugProtocol.ThreadsResponse): void {
    response.body = {
      threads: [new Thread(GeniaDebugSession.THREAD_ID, 'Main Thread')],
    };
    this.sendResponse(response);
  }

  protected stackTraceRequest(
    response: DebugProtocol.StackTraceResponse,
    _args: DebugProtocol.StackTraceArguments,
  ): void {
    void this.sendRuntimeCommand('stackTrace', {})
      .then((payload) => {
        const frames = Array.isArray(payload.frames) ? payload.frames : [];
        const stackFrames = frames.map((frameData) => this.toStackFrame(frameData));
        response.body = {
          stackFrames,
          totalFrames: stackFrames.length,
        };
        this.sendResponse(response);
      })
      .catch((err) => {
        this.sendErrorResponse(response, { id: 1003, format: `stackTrace failed: ${(err as Error).message}` });
      });
  }

  protected scopesRequest(response: DebugProtocol.ScopesResponse, args: DebugProtocol.ScopesArguments): void {
    const frameId = args.frameId;
    void this.sendRuntimeCommand('scopes', { frameId })
      .then((payload) => {
        const names = Array.isArray(payload.scopes) ? payload.scopes.map((value) => String((value as { name?: string }).name ?? value)) : ['locals', 'globals'];
        const scopes = names.map((name) => {
          const handle = this.variableHandles.create({ frameId, scope: name.toLowerCase() });
          const title = name.charAt(0).toUpperCase() + name.slice(1);
          return new Scope(title, handle, false);
        });
        response.body = { scopes };
        this.sendResponse(response);
      })
      .catch((err) => {
        this.sendErrorResponse(response, { id: 1004, format: `scopes failed: ${(err as Error).message}` });
      });
  }

  protected variablesRequest(response: DebugProtocol.VariablesResponse, args: DebugProtocol.VariablesArguments): void {
    const handle = this.variableHandles.get(args.variablesReference);
    if (!handle) {
      response.body = { variables: [] };
      this.sendResponse(response);
      return;
    }

    void this.sendRuntimeCommand('variables', { frameId: handle.frameId, scope: handle.scope })
      .then((payload) => {
        const rawVars = Array.isArray(payload.variables) ? payload.variables : [];
        response.body = {
          variables: rawVars.map((item) => {
            const typed = item as { name?: string; value?: string; type?: string };
            return {
              name: String(typed.name ?? '?'),
              value: String(typed.value ?? 'nil'),
              type: typed.type,
              variablesReference: 0,
            };
          }),
        };
        this.sendResponse(response);
      })
      .catch((err) => {
        this.sendErrorResponse(response, { id: 1005, format: `variables failed: ${(err as Error).message}` });
      });
  }

  protected continueRequest(response: DebugProtocol.ContinueResponse): void {
    void this.sendRuntimeCommandNoResponse('continue', {})
      .then(() => {
        this.sendEvent(new ContinuedEvent(GeniaDebugSession.THREAD_ID));
        response.body = { allThreadsContinued: true };
        this.sendResponse(response);
      })
      .catch((err) => this.sendErrorResponse(response, { id: 1006, format: `continue failed: ${(err as Error).message}` }));
  }

  protected nextRequest(response: DebugProtocol.NextResponse): void {
    this.stepCommand(response, 'stepOver', 1007);
  }

  protected stepInRequest(response: DebugProtocol.StepInResponse): void {
    this.stepCommand(response, 'stepIn', 1008);
  }

  protected stepOutRequest(response: DebugProtocol.StepOutResponse): void {
    this.stepCommand(response, 'stepOut', 1009);
  }

  protected disconnectRequest(
    response: DebugProtocol.DisconnectResponse,
    _args: DebugProtocol.DisconnectArguments,
  ): void {
    void this.sendRuntimeCommandNoResponse('disconnect', {})
      .catch(() => {
        // Ignore disconnect races.
      })
      .finally(() => {
        this.runtimeReader?.close();
        this.runtime?.kill();
        this.sendResponse(response);
      });
  }

  private stepCommand(response: DebugProtocol.Response, command: string, errorId: number): void {
    void this.sendRuntimeCommandNoResponse(command, {})
      .then(() => {
        this.sendEvent(new ContinuedEvent(GeniaDebugSession.THREAD_ID));
        this.sendResponse(response);
      })
      .catch((err) => this.sendErrorResponse(response, { id: errorId, format: `${command} failed: ${(err as Error).message}` }));
  }

  private onRuntimeLine(line: string): void {
    const trimmed = line.trim();
    if (!trimmed) {
      return;
    }

    let message: Record<string, unknown>;
    try {
      message = JSON.parse(trimmed) as Record<string, unknown>;
    } catch {
      this.sendEvent(new OutputEvent(`${line}\n`, 'stdout'));
      return;
    }

    const responseTo = typeof message.responseTo === 'string' ? message.responseTo : undefined;
    if (responseTo) {
      this.resolvePending(responseTo, message);
      return;
    }

    const event = typeof message.event === 'string' ? message.event : undefined;
    switch (event) {
      case 'initialized':
        this.sendEvent(new InitializedEvent());
        break;
      case 'stopped': {
        const reason = typeof message.reason === 'string' ? message.reason : 'pause';
        this.sendEvent(new StoppedEvent(reason, GeniaDebugSession.THREAD_ID));
        break;
      }
      case 'terminated':
        this.sendEvent(new TerminatedEvent());
        break;
      case 'output': {
        const output = String(message.output ?? '');
        const category = String(message.category ?? 'console') as 'stdout' | 'stderr' | 'console';
        this.sendEvent(new OutputEvent(output, category));
        break;
      }
      case 'error': {
        const text = String(message.message ?? 'Unknown debug runtime error');
        this.sendEvent(new OutputEvent(`${text}\n`, 'stderr'));
        break;
      }
      default:
        this.sendEvent(new OutputEvent(`Unhandled runtime message: ${trimmed}\n`, 'console'));
    }
  }

  private sendRuntimeCommand(command: string, payload: Record<string, unknown>): Promise<Record<string, unknown>> {
    if (!this.runtime || !this.runtime.stdin.writable) {
      return Promise.reject(new Error('Genia runtime is not running'));
    }

    return new Promise<Record<string, unknown>>((resolve, reject) => {
      const queue = this.pendingByCommand.get(command) ?? [];
      queue.push(resolve);
      this.pendingByCommand.set(command, queue);

      const body = JSON.stringify({ command, ...payload });
      this.runtime!.stdin.write(`${body}\n`, (err) => {
        if (err) {
          this.dequeuePending(command, resolve);
          reject(err);
        }
      });
    });
  }

  private sendRuntimeCommandNoResponse(command: string, payload: Record<string, unknown>): Promise<void> {
    if (!this.runtime || !this.runtime.stdin.writable) {
      return Promise.reject(new Error('Genia runtime is not running'));
    }

    return new Promise<void>((resolve, reject) => {
      const body = JSON.stringify({ command, ...payload });
      this.runtime!.stdin.write(`${body}\n`, (err) => {
        if (err) {
          reject(err);
          return;
        }
        resolve();
      });
    });
  }

  private resolvePending(command: string, payload: Record<string, unknown>): void {
    const queue = this.pendingByCommand.get(command);
    if (!queue || queue.length === 0) {
      return;
    }
    const next = queue.shift();
    if (queue.length === 0) {
      this.pendingByCommand.delete(command);
    }
    next?.(payload);
  }

  private dequeuePending(command: string, resolver: PendingResolver): void {
    const queue = this.pendingByCommand.get(command);
    if (!queue) {
      return;
    }
    const idx = queue.indexOf(resolver);
    if (idx >= 0) {
      queue.splice(idx, 1);
    }
    if (queue.length === 0) {
      this.pendingByCommand.delete(command);
    }
  }

  private normalizeProgramPath(program: string): string {
    if (!program) {
      throw new Error('Missing required launch configuration field: program');
    }
    if (program.startsWith('file://')) {
      return path.normalize(decodeURIComponent(new URL(program).pathname));
    }
    return path.resolve(program);
  }

  private normalizeSourcePath(source?: DebugProtocol.Source): string {
    if (!source) {
      return '';
    }
    if (source.path) {
      return source.path.startsWith('file://')
        ? path.normalize(decodeURIComponent(new URL(source.path).pathname))
        : path.resolve(source.path);
    }
    return '';
  }

  private breakpointKey(entry: unknown): string {
    if (Array.isArray(entry) && entry.length >= 2) {
      return `${path.resolve(String(entry[0]))}:${Number(entry[1])}`;
    }
    if (typeof entry === 'object' && entry !== null) {
      const typed = entry as { file?: string; line?: number };
      return `${path.resolve(String(typed.file ?? ''))}:${Number(typed.line ?? 0)}`;
    }
    return '';
  }

  private toStackFrame(frameData: unknown): StackFrame {
    const frame = frameData as { id?: number; name?: string; file?: string; line?: number; column?: number };
    const frameId = Number(frame.id ?? 0);
    const filePath = String(frame.file ?? '');
    return new StackFrame(
      frameId,
      String(frame.name ?? '<frame>'),
      filePath ? new Source(path.basename(filePath), path.resolve(filePath)) : undefined,
      Number(frame.line ?? 1),
      Number(frame.column ?? 1),
    );
  }

  private awaitConfigurationDone(): Promise<void> {
    return new Promise<void>((resolve) => {
      const timer = setInterval(() => {
        if (this.configurationDone) {
          clearInterval(timer);
          resolve();
        }
      }, 25);
    });
  }
}

DebugSession.run(GeniaDebugSession);
