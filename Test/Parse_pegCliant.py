import asyncio
import json
import websockets
from pygls.server import LanguageServer
from lsprotocol import types as lsp

# PEG パーサー (以前のコードと同じ)
class PEGParser:
    def __init__(self, grammar_json):
        self.grammar = self._load_grammar(grammar_json)
        self.text = ""

    def _load_grammar(self, filepath):
        with open(filepath, 'r') as f:
            return json.load(f)

    def parse(self, text):
        self.text = text
        errors = []
        if not text.endswith(";"):
            errors.append({
                "range": {"start": {"line": text.count('\n'), "character": len(text.split('\n')[-1])},
                          "end": {"line": text.count('\n'), "character": len(text.split('\n')[-1]) + 1}},
                "message": self.grammar.get("error_reporting", {}).get("missing_semicolon", "構文エラー: セミコロンがありません。")
            })
        return errors

# LSP サーバー (以前のコードと同じ)
peg_parser = None
ls = LanguageServer(name="peg-parser-lsp", version="0.1.0")

@ls.feature(lsp.TEXT_DOCUMENT_DID_OPEN)
def did_open(server: LanguageServer, params: lsp.DidOpenTextDocumentParams):
    global peg_parser
    peg_parser = PEGParser('peg_grammar.json')
    diagnostics = peg_parser.parse(params.textDocument.text)
    server.publish_diagnostics(params.textDocument.uri, _create_diagnostics(diagnostics))

@ls.feature(lsp.TEXT_DOCUMENT_DID_CHANGE)
def did_change(server: LanguageServer, params: lsp.DidChangeTextDocumentParams):
    diagnostics = peg_parser.parse(params.contentChanges[0].text)
    server.publish_diagnostics(params.textDocument.uri, _create_diagnostics(diagnostics))

def _create_diagnostics(errors):
    diagnostics = []
    for error in errors:
        range_ = lsp.Range(
            start=lsp.Position(line=error["range"]["start"]["line"], character=error["range"]["start"]["character"]),
            end=lsp.Position(line=error["range"]["end"]["line"], character=error["range"]["end"]["character"]),
        )
        diagnostic = lsp.Diagnostic(
            range=range_,
            message=error["message"],
            severity=lsp.DiagnosticSeverity.Error,
            source='peg-parser'
        )
        diagnostics.append(diagnostic)
    return diagnostics

# テストクライアント (以前のコードとほぼ同じ)
async def send_message(websocket, message):
    await websocket.send(json.dumps(message))

async def receive_message(websocket):
    try:
        return json.loads(await websocket.recv())
    except websockets.exceptions.ConnectionClosedOK:
        return None
    except Exception:
        return None

async def run_client():
    uri = "ws://localhost:8765"
    try:
        async with websockets.connect(uri) as websocket:
            print(f"Connected to LSP server at {uri}")

            # Initialize メッセージ
            initialize_message = {
                "jsonrpc": "2.0",
                "id": 0,
                "method": "initialize",
                "params": {
                    "processId": None,
                    "clientInfo": {"name": "TestClient", "version": "0.1.0"},
                    "rootUri": None,
                    "capabilities": {}
                }
            }
            await send_message(websocket, initialize_message)
            print("Initialize Response:", await receive_message(websocket))

            # Initialized 通知
            initialized_notification = {"jsonrpc": "2.0", "method": "initialized", "params": {}}
            await send_message(websocket, initialized_notification)

            # テキストドキュメントを開く
            did_open_notification = {
                "jsonrpc": "2.0",
                "method": "textDocument/didOpen",
                "params": {
                    "textDocument": {"uri": "file:///test.txt", "languageId": "testlang", "version": 1, "text": "test code"}
                }
            }
            await send_message(websocket, did_open_notification)

            # セミコロンなしのテキスト変更
            did_change_notification_no_semicolon = {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": "file:///test.txt", "version": 2},
                    "contentChanges": [{"text": "test code line 1\ntest code line 2"}]
                }
            }
            await send_message(websocket, did_change_notification_no_semicolon)
            await asyncio.sleep(0.1)
            response = await receive_message(websocket)
            print("Diagnostics (no semicolon):", response)

            # セミコロンありのテキスト変更
            did_change_notification_with_semicolon = {
                "jsonrpc": "2.0",
                "method": "textDocument/didChange",
                "params": {
                    "textDocument": {"uri": "file:///test.txt", "version": 3},
                    "contentChanges": [{"text": "test code line 1;\ntest code line 2;"}]
                }
            }
            await send_message(websocket, did_change_notification_with_semicolon)
            await asyncio.sleep(0.1)
            response = await receive_message(websocket)
            print("Diagnostics (with semicolon):", response)

            # Shutdown と Exit
            shutdown_message = {"jsonrpc": "2.0", "id": 1, "method": "shutdown", "params": None}
            await send_message(websocket, shutdown_message)
            print("Shutdown Response:", await receive_message(websocket))
            exit_notification = {"jsonrpc": "2.0", "method": "exit", "params": None}
            await send_message(websocket, exit_notification)

    except ConnectionRefusedError:
        print("Error: Could not connect to the LSP server. Make sure it's running.")
    except Exception as e:
        print(f"Client error: {e}")

# サーバーとクライアントを同時に実行
async def main():
    # サーバーを非同期タスクとして起動
    server_task = asyncio.create_task(ls.start_async(host="localhost", port=8765))
    await asyncio.sleep(0.1)  # サーバーが起動するのを少し待つ
    # クライアントを実行
    await run_client()
    # サーバータスクが完了するのを待つ (通常はクライアントが終了後にシャットダウンされる)
    await server_task

if __name__ == "__main__":
    # peg_grammar.json が存在することを確認
    try:
        with open('./Test/peg_grammar.json', 'r') as f:
            json.load(f)
    except FileNotFoundError:
        print("Error: peg_grammar.json not found. Please create this file in the same directory.")
    else:
        asyncio.run(main())