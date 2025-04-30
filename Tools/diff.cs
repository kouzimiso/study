using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
namespace ConfigSettingDiff
{
    // �w���vCSV�̂P���R�[�h��\���N���X
    public class HelpEntry
    {
        public string Group { get; set; } // �󕶎��̓O���[�o���Z�N�V����
        public string Key { get; set; }
        public string HelpText { get; set; }
        public string Default { get; set; }
    }

    // �t�H���_��r�̌��ʂ�ێ�����N���X
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

            // JSON �ݒ�t�@�C���̓ǂݍ���
            string jsonFilePath = args[0];
            Dictionary<string, object> pathMatchSetting;
            try
            {
                string jsonText = File.ReadAllText(jsonFilePath);
                pathMatchSetting = JsonConvert.DeserializeObject<Dictionary<string, object>>(jsonText);
            }
            catch (Exception ex)
            {
                Console.WriteLine("JSON�ݒ�t�@�C���̓ǂݍ��݂Ɏ��s���܂���: " + ex.Message);
                return;
            }

            string pathHelpFolder = args[1];
            string[] configFolders = args.Skip(2).ToArray();

            DiffResult diffResult = FolderSettingDiff(pathMatchSetting, pathHelpFolder, configFolders);

            // ���ʏo��
            File.WriteAllLines("result.csv", diffResult.CsvLines);
            if (!string.IsNullOrEmpty(diffResult.MismatchLogFile) && diffResult.MismatchLogLines.Count > 0)
            {
                File.WriteAllLines(diffResult.MismatchLogFile, diffResult.MismatchLogLines);
            }

            Console.WriteLine("��r�������������܂����Bresult.csv �� missmatch.log �����m�F���������B");
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

            // �e�t�H���_���̑Ώۃt�@�C�����𒊏o
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
                Console.WriteLine("[DEBUG] �ΏۂƂȂ�t�@�C����1����������܂���ł����B");
            }

            // CSV�̃w�b�_�[�s���쐬
            string header = "file_path,group,item,help,diff_result,default," +
                            string.Join(",", configFolders.Select((s, index) => "data" + (index + 1)));
            result.CsvLines.Add(header);

            // �e�t�@�C�������Ƃɔ�r
            foreach (var fileName in fileNames)
            {
                // �e�t�H���_�ɂ�����Ώۃt�@�C���̃p�X�i���݂��Ȃ���� null�j
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
                // �Ή�����w���v�t�@�C���́u�t�@�C�����{.csv�v�ɂȂ�
                string helpFile = Path.Combine(helpFolder, fileName + ".csv");

                List<string> fileDiffRows = FileSettingDiff(fileName, helpFile, filePaths);
                result.CsvLines.AddRange(fileDiffRows);
            }
            return result;
        }


        // �t�@�C���P�ʂ̐ݒ��r
        // fileName�F�Ώۂ̐ݒ�t�@�C�����i��r���ʏo�͗p�j  
        // helpFile�F�Ή�����w���vCSV�t�@�C���̃p�X  
        // configFilePaths�F�e�t�H���_���Ƃ̐ݒ�t�@�C���̃p�X�i���݂��Ȃ��ꍇ�� null�j
        static List<string> FileSettingDiff(string fileName, string helpFile, string[] configFilePaths)
        {
            // �w���vCSV�̓��e���p�[�X�i���݂��Ȃ���΋�j
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

            // �e�ݒ�t�@�C�����p�[�X���ăf�[�^�\���ɂ���
            // �\���F Dictionary<group, Dictionary<key, List<value>>>
            List<Dictionary<string, Dictionary<string, List<string>>>> configDataList = new List<Dictionary<string, Dictionary<string, List<string>>>>();
            foreach (var path in configFilePaths)
            {
                if (path != null)
                {
                    configDataList.Add(ParseConfigFile(path));
                }
                else
                {
                    // �t�@�C���������ꍇ�͋�̎�����p�ӂ��ăC���f�b�N�X�����킹��
                    configDataList.Add(new Dictionary<string, Dictionary<string, List<string>>>());
                }
            }

            // �S�ݒ�t�@�C���Ɍ����O���[�v�̃��j�I�����擾�i�O���[�o���� \"\"�j
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
            // �e�O���[�v�ɂ���
            foreach (var group in groups)
            {
                // �O���[�v���̑S�L�[���擾
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
                // �e�L�[���ƂɊe�ݒ�t�@�C���̒l�����o���A�����𔻒�
                foreach (var key in keys)
                {
                    List<string> values = new List<string>();
                    foreach (var data in configDataList)
                    {
                        if (data.ContainsKey(group) && data[group].ContainsKey(key))
                        {
                            // �����L�[����������ꍇ�̓Z�~�R������؂�ŘA��
                            values.Add(string.Join(";", data[group][key]));
                        }
                        else
                        {
                            values.Add("N/A");
                        }
                    }
                    // �l�̏W���i"N/A" �ȊO�j�̃��j�[�N���ō����L���𔻒�
                    var effectiveValues = values.Where(v => v != "N/A").Distinct().ToList();
                    string diffFlag = (effectiveValues.Count > 1) ? "diff" : "";
                    if (effectiveValues.Count == 0) diffFlag = "N/A";
                    // �w���v���ihelp text, default�l�j�̓w���vCSV����擾�i�L�[�� group|key �j
                    string dictKey = (group ?? "") + "|" + key;
                    string helpText = helpDict.ContainsKey(dictKey) ? helpDict[dictKey].HelpText : "";
                    string defaultVal = helpDict.ContainsKey(dictKey) ? helpDict[dictKey].Default : "";
                    // CSV�̂P�s���쐬�Ffile_path, group, item, help, result, default, �e�f�[�^�̒l�c
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

        // �ݒ�t�@�C���iINI�`���j���p�[�X����
        // �Z�N�V������ [group] �Ƃ��A�f�t�H���g�͋󕶎� \"\" �Ƃ���B�R�����g�s�i;�n�܂�j�͖����B
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
                // �R�����g�s�i�擪�� ;�j�͖���
                if (trimmed.StartsWith(";")) continue;
                // �Z�N�V��������F [group]
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

        // �w���vCSV���p�[�X����
        // �w�b�_�[�s��1�s�ڂƂ��ăX�L�b�v�B��؂�͊�{�̓J���}�Ƃ��邪�A�K�v�ɉ����ďC�����Ă��������B
        static List<HelpEntry> ParseHelpCsv(string path)
        {
            var list = new List<HelpEntry>();
            var lines = File.ReadAllLines(path);
            if (lines.Length == 0) return list;
            // 1�s�ڂ̓w�b�_�[�Ƃ݂Ȃ�
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

        // CSV�̃t�B�[���h�̑O��̃_�u���N�I�[�e�[�V��������������
        static string TrimCsv(string s)
        {
            s = s.Trim();
            if (s.StartsWith("\"") && s.EndsWith("\""))
                return s.Substring(1, s.Length - 2);
            return s;
        }

        // CSV�p�Ƀt�B�[���h���G�X�P�[�v����
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
