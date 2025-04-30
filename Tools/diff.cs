using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
namespace ConfigSettingDiff
{
    // ヘルプCSVの１レコードを表すクラス
    public class HelpEntry
    {
        public string Group { get; set; } // 空文字はグローバルセクション
        public string Key { get; set; }
        public string HelpText { get; set; }
        public string Default { get; set; }
    }

    // フォルダ比較の結果を保持するクラス
    public class DiffResult
    {
        public List<string> CsvLines { get; set; }
        public List<string> MismatchLogLines { get; set; }
        public string MismatchLogFile { get; set; }
        public DiffResult()
        {
            CsvLines = new List<string>();
            MismatchLogLines = new List<string>();
        }
    }

    public class Program
    {
        public static void Main(string[] args)
        {
            if (args.Length < 3)
            {
                Console.WriteLine("Usage: ConfigDiff <json_setting> <help_folder> <config_folder1> <config_folder2> ...");
                return;
            }

            // JSON 設定ファイルの読み込み
            string jsonFilePath = args[0];
            Dictionary<string, object> pathMatchSetting;
            try
            {
                string jsonText = File.ReadAllText(jsonFilePath);
                pathMatchSetting = JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonText);
            }
            catch (Exception ex)
            {
                Console.WriteLine("JSON設定ファイルの読み込みに失敗しました: " + ex.Message);
                return;
            }

            string pathHelpFolder = args[1];
            string[] configFolders = args.Skip(2).ToArray();

            DiffResult diffResult = FolderSettingDiff(pathMatchSetting, pathHelpFolder, configFolders);

            // 結果出力
            File.WriteAllLines("result.csv", diffResult.CsvLines);
            if (!string.IsNullOrEmpty(diffResult.MismatchLogFile) && diffResult.MismatchLogLines.Count > 0)
            {
                File.WriteAllLines(diffResult.MismatchLogFile, diffResult.MismatchLogLines);
            }

            Console.WriteLine("比較処理が完了しました。result.csv と missmatch.log をご確認ください。");
        }
        public static DiffResult FolderSettingDiff(Dictionary<string, object> settings, string helpFolder, string[] configFolders)
        {
            DiffResult result = new DiffResult();
            string filter = settings.ContainsKey("filter") ? settings["filter"].ToString() : "*.*";
            List<string> ignoreList;
            if (settings.ContainsKey("ignore_string") && settings["ignore_string"] is JArray)
            {
                ignoreList = ((JArray)settings["ignore_string"]).ToObject<List<string>>();
                if (ignoreList == null)
                    ignoreList = new List<string>();
            }
            else
            {
                ignoreList = new List<string>();
            }
            string mismatchLogFile = settings.ContainsKey("") ? settings[""].ToString() : "";
            result.MismatchLogFile = mismatchLogFile;

            // 各フォルダ内の対象ファイル名を抽出
            HashSet<string> fileNames = new HashSet<string>();
            foreach (var folder in configFolders)
            {
                if (Directory.Exists(folder))
                {
                    var files = Directory.GetFiles(folder, filter)
                                    .Where(f => !ignoreList.Any(ignore => f.IndexOf(ignore, StringComparison.OrdinalIgnoreCase) >= 0));
                    Console.WriteLine("[DEBUG] Folder" +folder+" : Found "+ files.Count()+" file(s) with filter '"+filter+"'");
                    foreach (var file in files)
                    {
                        fileNames.Add(Path.GetFileName(file));
                    }
                }
                else
                {
                    Console.WriteLine("[DEBUG] Folder '"+folder+"' does not exist.");
                }
            }

            if (fileNames.Count == 0)
            {
                Console.WriteLine("[DEBUG] 対象となるファイルが1件も見つかりませんでした。");
            }

            // CSVのヘッダー行を作成
            string header = "file_path,group,item,help,diff_result,default," +
                            string.Join(",", configFolders.Select((s, index) => "data" + (index + 1)));
            result.CsvLines.Add(header);

            // 各ファイル名ごとに比較
            foreach (var fileName in fileNames)
            {
                // 各フォルダにおける対象ファイルのパス（存在しなければ null）
                string[] filePaths = new string[configFolders.Length];
                for (int i = 0; i < configFolders.Length; i++)
                {
                    string potential = Path.Combine(configFolders[i], fileName);
                    if (File.Exists(potential))
                    {
                        filePaths[i] = potential;
                    }
                    else
                    {
                        filePaths[i] = null;
                        result.MismatchLogLines.Add(string.Format("{0} is missing in folder {1}", fileName, configFolders[i]));
                    }
                }
                // 対応するヘルプファイルは「ファイル名＋.csv」になる
                string helpFile = Path.Combine(helpFolder, fileName + ".csv");

                List<string> fileDiffRows = FileSettingDiff(fileName, helpFile, filePaths);
                result.CsvLines.AddRange(fileDiffRows);
            }
            return result;
        }


        // ファイル単位の設定比較
        // fileName：対象の設定ファイル名（比較結果出力用）  
        // helpFile：対応するヘルプCSVファイルのパス  
        // configFilePaths：各フォルダごとの設定ファイルのパス（存在しない場合は null）
        static List<string> FileSettingDiff(string fileName, string helpFile, string[] configFilePaths)
        {
            // ヘルプCSVの内容をパース（存在しなければ空）
            var helpDict = new Dictionary<string, HelpEntry>(); // key: group + \"|\" + key
            if (File.Exists(helpFile))
            {
                var helpEntries = ParseHelpCsv(helpFile);
                foreach (var entry in helpEntries)
                {
                    string dictKey = (entry.Group ?? "") + "|" + entry.Key;
                    if (!helpDict.ContainsKey(dictKey))
                        helpDict[dictKey] = entry;
                }
            }

            // 各設定ファイルをパースしてデータ構造にする
            // 構造： Dictionary<group, Dictionary<key, List<value>>>
            List<Dictionary<string, Dictionary<string, List<string>>>> configDataList = new List<Dictionary<string, Dictionary<string, List<string>>>>();
            foreach (var path in configFilePaths)
            {
                if (path != null)
                {
                    configDataList.Add(ParseConfigFile(path));
                }
                else
                {
                    // ファイルが無い場合は空の辞書を用意してインデックスを合わせる
                    configDataList.Add(new Dictionary<string, Dictionary<string, List<string>>>());
                }
            }

            // 全設定ファイルに現れるグループのユニオンを取得（グローバルは \"\"）
            HashSet<string> groups = new HashSet<string>();
            foreach (var data in configDataList)
            {
                foreach (var grp in data.Keys)
                {
                    groups.Add(grp);
                }
            }
            if (groups.Count == 0)
                groups.Add("");

            List<string> rows = new List<string>();
            // 各グループについて
            foreach (var group in groups)
            {
                // グループ内の全キーを取得
                HashSet<string> keys = new HashSet<string>();
                foreach (var data in configDataList)
                {
                    if (data.ContainsKey(group))
                    {
                        foreach (var key in data[group].Keys)
                        {
                            keys.Add(key);
                        }
                    }
                }
                // 各キーごとに各設定ファイルの値を取り出し、差分を判定
                foreach (var key in keys)
                {
                    List<string> values = new List<string>();
                    foreach (var data in configDataList)
                    {
                        if (data.ContainsKey(group) && data[group].ContainsKey(key))
                        {
                            // 同じキーが複数ある場合はセミコロン区切りで連結
                            values.Add(string.Join(";", data[group][key]));
                        }
                        else
                        {
                            values.Add("N/A");
                        }
                    }
                    // 値の集合（"N/A" 以外）のユニーク数で差分有無を判定
                    var effectiveValues = values.Where(v => v != "N/A").Distinct().ToList();
                    string diffFlag = (effectiveValues.Count > 1) ? "diff" : "";
                    if (effectiveValues.Count == 0) diffFlag = "N/A";
                    // ヘルプ情報（help text, default値）はヘルプCSVから取得（キーは group|key ）
                    string dictKey = (group ?? "") + "|" + key;
                    string helpText = helpDict.ContainsKey(dictKey) ? helpDict[dictKey].HelpText : "";
                    string defaultVal = helpDict.ContainsKey(dictKey) ? helpDict[dictKey].Default : "";
                    // CSVの１行を作成：file_path, group, item, help, result, default, 各データの値…
                    string row = string.Format("{0},{1},{2},{3},{4},{5},{6}",
                                    fileName,
                                    group,
                                    key,
                                    EscapeCsv(helpText),
                                    diffFlag,
                                    EscapeCsv(defaultVal),
                                    string.Join(",", values.Select(v => EscapeCsv(v))));
                    rows.Add(row);
                }
            }
            return rows;
        }

        // 設定ファイル（INI形式）をパースする
        // セクションは [group] とし、デフォルトは空文字 \"\" とする。コメント行（;始まり）は無視。
        static Dictionary<string, Dictionary<string, List<string>>> ParseConfigFile(string path)
        {
            var result = new Dictionary<string, Dictionary<string, List<string>>>();
            string currentGroup = "";
            if (!result.ContainsKey(currentGroup))
                result[currentGroup] = new Dictionary<string, List<string>>();

            foreach (var line in File.ReadAllLines(path))
            {
                string trimmed = line.Trim();
                if (string.IsNullOrEmpty(trimmed)) continue;
                // コメント行（先頭が ;）は無視
                if (trimmed.StartsWith(";")) continue;
                // セクション判定： [group]
                if (trimmed.StartsWith("[") && trimmed.EndsWith("]"))
                {
                    currentGroup = trimmed.Substring(1, trimmed.Length - 2).Trim();
                    if (!result.ContainsKey(currentGroup))
                        result[currentGroup] = new Dictionary<string, List<string>>();
                    continue;
                }
                if (!trimmed.Contains("=")) continue;
                var parts = trimmed.Split(new char[] { '=' }, 2);
                string key = parts[0].Trim();
                string value = parts[1].Trim();
                if (!result[currentGroup].ContainsKey(key))
                    result[currentGroup][key] = new List<string>();
                result[currentGroup][key].Add(value);
            }
            return result;
        }

        // ヘルプCSVをパースする
        // ヘッダー行は1行目としてスキップ。区切りは基本はカンマとするが、必要に応じて修正してください。
        static List<HelpEntry> ParseHelpCsv(string path)
        {
            var list = new List<HelpEntry>();
            var lines = File.ReadAllLines(path);
            if (lines.Length == 0) return list;
            // 1行目はヘッダーとみなす
            for (int i = 1; i < lines.Length; i++)
            {
                if (string.IsNullOrWhiteSpace(lines[i])) continue;
                var parts = lines[i].Split(',');
                if (parts.Length < 4) continue;
                HelpEntry entry = new HelpEntry();
                entry.Group = TrimCsv(parts[0]);
                entry.Key = TrimCsv(parts[1]);
                entry.HelpText = TrimCsv(parts[2]);
                entry.Default = TrimCsv(parts[3]);
                list.Add(entry);
            }
            return list;
        }

        // CSVのフィールドの前後のダブルクオーテーションを除去する
        static string TrimCsv(string s)
        {
            s = s.Trim();
            if (s.StartsWith("\"") && s.EndsWith("\""))
                return s.Substring(1, s.Length - 2);
            return s;
        }

        // CSV用にフィールドをエスケープする
        static string EscapeCsv(string s)
        {
            if (s == null)
                return "";
            if (s.IndexOfAny(new char[] { ',', '\"', '\n' }) >= 0)
            {
                s = s.Replace("\"", "\"\"");
                return "\"" + s + "\"";
            }
            return s;
        }
    }
}
