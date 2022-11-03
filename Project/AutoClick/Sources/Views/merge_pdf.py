from pathlib import Path
import PyPDF2


def merge_pdf_files(folder_path, file_name, reverse):
    # フォルダ内のPDFファイル一覧
    pdf_dir = Path(folder_path)
    pdf_files = sorted(pdf_dir.glob("*.pdf"), reverse=reverse)

    # １つのPDFファイルにまとめる
    pdf_writer = PyPDF2.PdfFileWriter()
    for pdf_file in pdf_files:
        pdf_reader = PyPDF2.PdfFileReader(str(pdf_file))
        for i in range(pdf_reader.getNumPages()):
            pdf_writer.addPage(pdf_reader.getPage(i))

    # 保存
    with open(file_name, "wb") as f:
        pdf_writer.write(f)


if __name__ == "__main__":
    # テスト
    merge_pdf_files("./pdf_files", "test.pdf", False)
