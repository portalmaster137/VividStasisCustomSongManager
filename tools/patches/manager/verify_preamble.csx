using System;
using System.IO;
using System.Linq;
using UndertaleModLib;
using UndertaleModLib.Decompiler;
EnsureDataLoaded();
var context = new GlobalDecompileContext(Data);
string Read(string name) {
    var code = Data.Code.ByName(name);
    if (code == null) throw new Exception("Missing saved code " + name);
    return new Underanalyzer.Decompiler.DecompileContext(context, code, Data.ToolInfo.DecompilerSettings).DecompileToString();
}
