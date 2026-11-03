{
var sprite = Data.Sprites.ByName("song_@@cid@@");
if (sprite == null || sprite.Width != 100 || sprite.Height != 100 || sprite.Textures.Count != 1) throw new Exception("Invalid saved cover: @@cid@@");
var page = sprite.Textures[0].Texture;
if (page == null || page.SourceWidth != 100 || page.SourceHeight != 100 || page.TexturePage == null) throw new Exception("Invalid saved texture page");
using var output = new MemoryStream();
page.TexturePage.TextureData.Image.SavePng(output);
if (!output.ToArray().SequenceEqual(File.ReadAllBytes(@@cover@@))) throw new Exception("Saved cover differs: @@cid@@");
}
