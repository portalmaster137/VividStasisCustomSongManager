
if (Data.Sprites.ByName("song_@@chart_id@@") != null) throw new Exception("Cover already registered");
var template = Data.Sprites.ByName("song_generic");
var texture = new UndertaleEmbeddedTexture { Name = new UndertaleString("Texture " + Data.EmbeddedTextures.Count) };
texture.TextureData.Image = UndertaleModLib.Util.GMImage.FromPng(File.ReadAllBytes(@@cover_cs@@), true);
Data.EmbeddedTextures.Add(texture);
var page = new UndertaleTexturePageItem {
    Name = new UndertaleString("PageItem " + Data.TexturePageItems.Count),
    SourceX = 0, SourceY = 0, SourceWidth = 100, SourceHeight = 100,
    TargetX = 0, TargetY = 0, TargetWidth = 100, TargetHeight = 100,
    BoundingWidth = 100, BoundingHeight = 100, TexturePage = texture
};
Data.TexturePageItems.Add(page);
var sprite = new UndertaleSprite {
    Name = Data.Strings.MakeString("song_@@chart_id@@"), Width = 100, Height = 100,
    MarginLeft = 0, MarginTop = 0, MarginRight = 99, MarginBottom = 99,
    OriginX = 0, OriginY = 0, SVersion = template.SVersion,
    IsSpecialType = template.IsSpecialType, SSpriteType = template.SSpriteType,
    GMS2PlaybackSpeed = template.GMS2PlaybackSpeed,
    GMS2PlaybackSpeedType = template.GMS2PlaybackSpeedType,
    SepMasks = template.SepMasks, BBoxMode = template.BBoxMode
};
sprite.Textures.Add(new UndertaleSprite.TextureEntry { Texture = page });
Data.Sprites.Add(sprite);
var coverGroup = Data.TextureGroupInfo.FirstOrDefault(g => g.Sprites.Any(r => r.Resource == template));
if (coverGroup == null) throw new Exception("Missing template texture group");
coverGroup.TexturePages.Add(new() { Resource = texture });
coverGroup.Sprites.Add(new() { Resource = sprite });
