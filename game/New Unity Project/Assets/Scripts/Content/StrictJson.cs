using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace MP1.Content
{
    /// <summary>
    /// Minimal strict JSON parser for Content Pack v1. JsonUtility cannot express what the contract requires
    /// (reject duplicate keys, tell null from missing, reject unknown fields), so this keeps the raw tree:
    /// objects are Dictionary&lt;string, object&gt;, arrays List&lt;object&gt;, integers long, other numbers double.
    /// </summary>
    public static class StrictJson
    {
        public class JsonException : Exception
        {
            public JsonException(string message, int position) : base($"{message} (vị trí {position})") { }
        }

        const int MaxDepth = 64;

        public static object Parse(string text)
        {
            if (text == null) throw new JsonException("Nội dung rỗng", 0);
            int i = 0;
            if (text.Length > 0 && text[0] == '﻿') i = 1; // UTF-8 BOM tolerated
            var value = ParseValue(text, ref i, 0);
            SkipWs(text, ref i);
            if (i != text.Length) throw new JsonException("Còn dữ liệu thừa sau JSON", i);
            return value;
        }

        static void SkipWs(string s, ref int i)
        {
            while (i < s.Length && (s[i] == ' ' || s[i] == '\t' || s[i] == '\n' || s[i] == '\r')) i++;
        }

        static object ParseValue(string s, ref int i, int depth)
        {
            if (depth > MaxDepth) throw new JsonException("JSON lồng quá sâu", i);
            SkipWs(s, ref i);
            if (i >= s.Length) throw new JsonException("JSON kết thúc đột ngột", i);
            char c = s[i];
            if (c == '{') return ParseObject(s, ref i, depth);
            if (c == '[') return ParseArray(s, ref i, depth);
            if (c == '"') return ParseString(s, ref i);
            if (c == 't') { Expect(s, ref i, "true"); return true; }
            if (c == 'f') { Expect(s, ref i, "false"); return false; }
            if (c == 'n') { Expect(s, ref i, "null"); return null; }
            if (c == '-' || (c >= '0' && c <= '9')) return ParseNumber(s, ref i);
            throw new JsonException($"Ký tự không hợp lệ '{c}'", i);
        }

        static void Expect(string s, ref int i, string word)
        {
            if (string.CompareOrdinal(s, i, word, 0, word.Length) != 0) throw new JsonException($"Mong đợi '{word}'", i);
            i += word.Length;
        }

        static Dictionary<string, object> ParseObject(string s, ref int i, int depth)
        {
            var obj = new Dictionary<string, object>(StringComparer.Ordinal);
            i++; SkipWs(s, ref i);
            if (i < s.Length && s[i] == '}') { i++; return obj; }
            while (true)
            {
                SkipWs(s, ref i);
                if (i >= s.Length || s[i] != '"') throw new JsonException("Mong đợi tên khóa", i);
                int keyPos = i;
                string key = ParseString(s, ref i);
                if (obj.ContainsKey(key)) throw new JsonException($"Khóa trùng '{key}'", keyPos);
                SkipWs(s, ref i);
                if (i >= s.Length || s[i] != ':') throw new JsonException("Mong đợi ':'", i);
                i++;
                obj[key] = ParseValue(s, ref i, depth + 1);
                SkipWs(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == '}') { i++; return obj; }
                throw new JsonException("Mong đợi ',' hoặc '}'", i);
            }
        }

        static List<object> ParseArray(string s, ref int i, int depth)
        {
            var list = new List<object>();
            i++; SkipWs(s, ref i);
            if (i < s.Length && s[i] == ']') { i++; return list; }
            while (true)
            {
                list.Add(ParseValue(s, ref i, depth + 1));
                SkipWs(s, ref i);
                if (i < s.Length && s[i] == ',') { i++; continue; }
                if (i < s.Length && s[i] == ']') { i++; return list; }
                throw new JsonException("Mong đợi ',' hoặc ']'", i);
            }
        }

        static string ParseString(string s, ref int i)
        {
            var sb = new StringBuilder();
            i++;
            while (i < s.Length)
            {
                char c = s[i++];
                if (c == '"') return sb.ToString();
                if (c < 0x20) throw new JsonException("Ký tự điều khiển trong chuỗi", i - 1);
                if (c != '\\') { sb.Append(c); continue; }
                if (i >= s.Length) break;
                char e = s[i++];
                switch (e)
                {
                    case '"': sb.Append('"'); break;
                    case '\\': sb.Append('\\'); break;
                    case '/': sb.Append('/'); break;
                    case 'b': sb.Append('\b'); break;
                    case 'f': sb.Append('\f'); break;
                    case 'n': sb.Append('\n'); break;
                    case 'r': sb.Append('\r'); break;
                    case 't': sb.Append('\t'); break;
                    case 'u':
                        if (i + 4 > s.Length || !int.TryParse(s.Substring(i, 4), NumberStyles.HexNumber, CultureInfo.InvariantCulture, out int code))
                            throw new JsonException("Mã \\u không hợp lệ", i);
                        sb.Append((char)code); i += 4; break;
                    default: throw new JsonException($"Escape không hợp lệ '\\{e}'", i - 1);
                }
            }
            throw new JsonException("Chuỗi chưa đóng", i);
        }

        static object ParseNumber(string s, ref int i)
        {
            int start = i;
            if (s[i] == '-') i++;
            if (i >= s.Length) throw new JsonException("Số không hợp lệ", start);
            if (s[i] == '0') i++;
            else if (s[i] >= '1' && s[i] <= '9') while (i < s.Length && char.IsDigit(s[i])) i++;
            else throw new JsonException("Số không hợp lệ", start);
            bool isInt = true;
            if (i < s.Length && s[i] == '.') { isInt = false; i++; int d = i; while (i < s.Length && char.IsDigit(s[i])) i++; if (i == d) throw new JsonException("Số không hợp lệ", start); }
            if (i < s.Length && (s[i] == 'e' || s[i] == 'E'))
            {
                isInt = false; i++;
                if (i < s.Length && (s[i] == '+' || s[i] == '-')) i++;
                int d = i; while (i < s.Length && char.IsDigit(s[i])) i++;
                if (i == d) throw new JsonException("Số mũ không hợp lệ", start);
            }
            string token = s.Substring(start, i - start);
            if (isInt && long.TryParse(token, NumberStyles.AllowLeadingSign, CultureInfo.InvariantCulture, out long l)) return l;
            return double.Parse(token, NumberStyles.Float, CultureInfo.InvariantCulture);
        }
    }
}
