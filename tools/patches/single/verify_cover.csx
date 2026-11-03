
var jacket = Data.Sprites.ByName("song_@@value@@");
if (jacket == null || jacket.Width != 100 || jacket.Height != 100 || jacket.Textures.Count != 1)
    throw new Exception("Invalid cover sprite");
var coverPage = jacket.Textures[0].Texture;
if (coverPage == null || coverPage.TexturePage == null || coverPage.SourceWidth != 100 || coverPage.SourceHeight != 100)
    throw new Exception("Invalid cover texture reference");
var coverBytes = new MemoryStream();
coverPage.TexturePage.TextureData.Image.SavePng(coverBytes);
if (!coverBytes.ToArray().SequenceEqual(File.ReadAllBytes(@@cover_cs@@)))
    throw new Exception("Cover PNG differs after save");
coverBytes.Dispose();
