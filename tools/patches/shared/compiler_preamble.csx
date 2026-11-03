using System;
using System.IO;
using System.Linq;
using UndertaleModLib;
using UndertaleModLib.Models;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var context = new GlobalDecompileContext(Data);
var imports = new UndertaleModLib.Compiler.CodeImportGroup(Data, null, Data.ToolInfo.DecompilerSettings) { MainThreadAction = MainThreadAction };
string Read(string name) {
    var code = Data.Code.ByName(name);
    if (code == null) throw new Exception("Missing code: " + name);
    return new Underanalyzer.Decompiler.DecompileContext(context, code, Data.ToolInfo.DecompilerSettings).DecompileToString();
}
string ReplaceOnce(string source, string anchor, string replacement) {
    int at = source.IndexOf(anchor, StringComparison.Ordinal);
    if (at < 0 || source.IndexOf(anchor, at + anchor.Length, StringComparison.Ordinal) >= 0)
        throw new Exception("Patch anchor missing or ambiguous: " + anchor);
    return source.Substring(0, at) + replacement + source.Substring(at + anchor.Length);
}
void Queue(string name, string source) {
    File.WriteAllText(Path.Combine(@@work_cs@@, name + ".gml"), source);
    imports.QueueReplace(Data.Code.ByName(name), source);
}
