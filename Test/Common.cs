using System;
using System.Diagnostics;
using System.IO;
using System.Text;

class Program
{
    static void Main()
    {
        // CSV�t�@�C���ւ̏o�̓p�X
        string exportFilePath = "SharedMemoryList.csv";

        // CSV�t�@�C�����������ރX�g���[�����쐬
        using (StreamWriter writer = new StreamWriter(exportFilePath))
        {
            // CSV�w�b�_����������
            writer.WriteLine("�v���Z�X��,�v���Z�XID,���L�������A�h���X");

            Process[] processes = Process.GetProcesses();

            foreach (Process process in processes)
            {
                IntPtr hProcess = OpenProcess(PROCESS_VM_READ | PROCESS_QUERY_INFORMATION, false, process.Id);

                if (hProcess != IntPtr.Zero)
                {
                    // ���L�������̃A�h���X���w�肵�ăf�[�^��ǂݎ��܂��i��: 0x00400000�j
                    IntPtr baseAddress = new IntPtr(0x00400000);
                    byte[] buffer = new byte[1024]; // �f�[�^��ǂݎ�邽�߂̃o�b�t�@

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

        Console.WriteLine($"�G�N�X�|�[�g���������܂����B�t�@�C��: {exportFilePath}");
    }

    // �ȑO�Ɠ��l�� OpenProcess�AReadProcessMemory�ACloseHandle �̃C���|�[�g����ђ�`
    // ...

    const int PROCESS_VM_READ = 0x0010;
    const int PROCESS_QUERY_INFORMATION = 0x0400;
}
