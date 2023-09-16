using System;
using System.Diagnostics;
using System.IO;
using System.Text;

class Program
{
    static void Main()
    {
        // CSVファイルへの出力パス
        string exportFilePath = "SharedMemoryList.csv";

        // CSVファイルを書き込むストリームを作成
        using (StreamWriter writer = new StreamWriter(exportFilePath))
        {
            // CSVヘッダを書き込む
            writer.WriteLine("プロセス名,プロセスID,共有メモリアドレス");

            Process[] processes = Process.GetProcesses();

            foreach (Process process in processes)
            {
                IntPtr hProcess = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, false, process.Id);

                if (hProcess != IntPtr.Zero)
                {
                    // 共有メモリのアドレスを指定してデータを読み取ります（例: 0x00400000）
                    IntPtr baseAddress = new IntPtr(0x00400000);
                    byte[] buffer = new byte[1024]; // データを読み取るためのバッファ

                    int bytesRead;
                    if (ReadProcessMemory(hProcess, baseAddress, buffer, buffer.Length, out bytesRead))
                    {
                        string data = Encoding.ASCII.GetString(buffer, 0, bytesRead);
                        writer.WriteLine($"{process.ProcessName},{process.Id},{baseAddress}");
                    }

                    CloseHandle(hProcess);
                }
            }
        }

        Console.WriteLine($"エクスポートが完了しました。ファイル: {exportFilePath}");
    }

    // 以前と同様の OpenProcess、ReadProcessMemory、CloseHandle のインポートおよび定義
    // ...

    const int PROCESS_VM_READ = 0x0010;
    const int PROCESS_QUERY_INFORMATION = 0x0400;
}
