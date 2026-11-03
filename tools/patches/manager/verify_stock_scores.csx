var stockScores = Data.Code.ByName("gml_GlobalScript_load_highscores");
string savedScoresAssembly = stockScores.Disassemble(Data.Variables, Data.CodeLocals?.For(stockScores));
string originalScoresAssembly = File.ReadAllText(Path.Combine(@@work_cs@@, "stock_load_highscores.asm"));
if (!String.Equals(savedScoresAssembly, originalScoresAssembly, StringComparison.Ordinal))
    throw new Exception("Stock score-loader assembly changed; refusing to install");
if (savedScoresAssembly.Contains("pop.v.v builtin.score") || !savedScoresAssembly.Contains("pop.v.v self.score"))
    throw new Exception("Stock score factory does not write a struct score field");
File.WriteAllText(Path.Combine(@@work_cs@@, "verified_stock_load_highscores.asm"), savedScoresAssembly);
