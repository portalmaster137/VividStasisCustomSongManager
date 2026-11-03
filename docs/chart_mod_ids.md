# Chart mod and easing IDs

These IDs are specific to the supplied game build. They were derived from the extracted GML without executing the game. [The JSON catalog](../analysis/chart_format/mod_ids.json) includes every registration, source filename and line, expanded literal-loop iteration, effective name/ID map, and any ambiguities. [The generator](../analysis/chart_format/generate_mod_ids.py) reproduces it.

Global IDs are assigned from zero by `addGlobalMod`. The high bit selects chart-specific IDs, whose names depend on the selected gimmick object. The base gimmick initializes its extra-mod registration index to 1; `addExtraMod` assigns `index | 0x80`. Thus ordinary object-specific registration starts at `0x81`, not `0x80`. All cataloged derived gimmicks directly inherit from `obj_base_gimmick` according to the extracted object metadata.

Duplicate names are not treated as two simultaneously valid names: the game stores name→ID in a struct, so a later registration overwrites the earlier value. Full registration history remains in JSON, while the effective reverse map omits shadowed registrations. This is a static interpretation of source assignment order, not runtime observation.

## Global IDs

| ID | Hex | Name |
| --- | --- | --- |
| 0 | `0x00` | `unknown` |
| 1 | `0x01` | `prx` |
| 2 | `0x02` | `prxb` |
| 3 | `0x03` | `prxc` |
| 4 | `0x04` | `pry` |
| 5 | `0x05` | `pryb` |
| 6 | `0x06` | `pryc` |
| 7 | `0x07` | `prsx` |
| 8 | `0x08` | `pra` |
| 9 | `0x09` | `przm` |
| 10 | `0x0A` | `przmb` |
| 11 | `0x0B` | `przx` |
| 12 | `0x0C` | `przy` |
| 13 | `0x0D` | `prrx` |
| 14 | `0x0E` | `prry` |
| 15 | `0x0F` | `prrz` |
| 16 | `0x10` | `prrzb` |
| 17 | `0x11` | `shxs` |
| 18 | `0x12` | `shxp` |
| 19 | `0x13` | `shxa` |
| 20 | `0x14` | `shys` |
| 21 | `0x15` | `shyp` |
| 22 | `0x16` | `shya` |
| 23 | `0x17` | `scrollspeed` |
| 24 | `0x18` | `noterot` |
| 25 | `0x19` | `velocity` |
| 26 | `0x1A` | `spinradius` |
| 27 | `0x1B` | `spiny` |
| 28 | `0x1C` | `spinx` |
| 29 | `0x1D` | `driven` |
| 30 | `0x1E` | `beat` |
| 31 | `0x1F` | `wave` |
| 32 | `0x20` | `hom` |
| 33 | `0x21` | `boost_distance` |
| 34 | `0x22` | `boost_time` |
| 35 | `0x23` | `yoffset` |
| 36 | `0x24` | `notealp` |
| 37 | `0x25` | `przmc` |
| 38 | `0x26` | `prxd` |
| 39 | `0x27` | `pryd` |
| 40 | `0x28` | `prct` |
| 41 | `0x29` | `prcb` |
| 42 | `0x2A` | `prcl` |
| 43 | `0x2B` | `prcr` |
| 44 | `0x2C` | `prvib` |
| 45 | `0x2D` | `shct` |
| 46 | `0x2E` | `shft` |
| 47 | `0x2F` | `shcb` |
| 48 | `0x30` | `shfb` |
| 49 | `0x31` | `shcl` |
| 50 | `0x32` | `shfl` |
| 51 | `0x33` | `shcr` |
| 52 | `0x34` | `shfr` |
| 53 | `0x35` | `scrollind0` |
| 54 | `0x36` | `scrollind1` |
| 55 | `0x37` | `scrollind2` |
| 56 | `0x38` | `scrollind3` |
| 57 | `0x39` | `scrollind4` |
| 58 | `0x3A` | `scrollind5` |
| 59 | `0x3B` | `scrollind6` |
| 60 | `0x3C` | `drawdist` |
| 61 | `0x3D` | `pburstleft` |
| 62 | `0x3E` | `pburstright` |
| 63 | `0x3F` | `particlexpower` |
| 64 | `0x40` | `particleypower` |
| 65 | `0x41` | `uialpha` |
| 66 | `0x42` | `fx_contrast` |
| 67 | `0x43` | `fx_chroma_distort` |
| 68 | `0x44` | `fx_film` |
| 69 | `0x45` | `fx_glow` |
| 70 | `0x46` | `fx_particleglow` |
| 71 | `0x47` | `pburstspeed` |
| 72 | `0x48` | `freeze` |
| 73 | `0x49` | `drawuntil` |

## Easing IDs

| ID | Name |
| --- | --- |
| 1 | `linear` |
| 2 | `outElastic` |
| 3 | `inExpo` |
| 4 | `outExpo` |
| 5 | `inOutExpo` |
| 6 | `inQuad` |
| 7 | `outQuad` |
| 8 | `inOutQuad` |
| 9 | `inCubic` |
| 10 | `outCubic` |
| 11 | `inOutCubic` |
| 12 | `outBack` |
| 13 | `inSine` |
| 14 | `outSine` |
| 15 | `inOutSine` |
| 16 | `outQuart` |
| 17 | `inOutCirc` |
| 18 | `inCirc` |
| 19 | `outCirc` |

## Object-specific IDs

Object names are values of the chart mods configuration object field. Objects with no registrations are included to distinguish an empty mapping from an unexamined one. Nonliteral/runtime control flow is not evaluated; any unresolved situations are listed explicitly.

### `obj_00_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_00_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `blipzoom` | 46 |
| 130 | `0x82` | `blipalpha` | 47 |
| 131 | `0x83` | `satal` | 48 |
| 132 | `0x84` | `satx` | 49 |
| 133 | `0x85` | `saty` | 50 |

### `obj_00_gimmick_old`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_00_gimmick_old_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `blipzoom` | 179 |
| 130 | `0x82` | `blipalpha` | 180 |
| 131 | `0x83` | `satal` | 181 |
| 132 | `0x84` | `satx` | 182 |
| 133 | `0x85` | `saty` | 183 |

### `obj___gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj___gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 104 |
| 130 | `0x82` | `glitchoffset` | 105 |
| 131 | `0x83` | `fish` | 106 |
| 132 | `0x84` | `vig` | 107 |
| 133 | `0x85` | `bloom` | 108 |
| 134 | `0x86` | `gray` | 109 |
| 135 | `0x87` | `posx` | 110 |
| 136 | `0x88` | `posy` | 111 |
| 137 | `0x89` | `cover1` | 112 |
| 138 | `0x8A` | `cover2` | 113 |
| 139 | `0x8B` | `cover3` | 114 |
| 140 | `0x8C` | `twx1` | 117 |
| 141 | `0x8D` | `twy1` | 118 |
| 142 | `0x8E` | `twa1` | 119 |
| 143 | `0x8F` | `twr1` | 120 |
| 144 | `0x90` | `twx2` | 117 |
| 145 | `0x91` | `twy2` | 118 |
| 146 | `0x92` | `twa2` | 119 |
| 147 | `0x93` | `twr2` | 120 |
| 148 | `0x94` | `twx3` | 117 |
| 149 | `0x95` | `twy3` | 118 |
| 150 | `0x96` | `twa3` | 119 |
| 151 | `0x97` | `twr3` | 120 |
| 152 | `0x98` | `twx4` | 117 |
| 153 | `0x99` | `twy4` | 118 |
| 154 | `0x9A` | `twa4` | 119 |
| 155 | `0x9B` | `twr4` | 120 |
| 156 | `0x9C` | `sina` | 122 |
| 157 | `0x9D` | `sinp` | 123 |
| 158 | `0x9E` | `sino` | 124 |
| 159 | `0x9F` | `cosa` | 125 |
| 160 | `0xA0` | `cosp` | 126 |
| 161 | `0xA1` | `coso` | 127 |
| 162 | `0xA2` | `tana` | 128 |
| 163 | `0xA3` | `tanp` | 129 |
| 164 | `0xA4` | `tano` | 130 |
| 165 | `0xA5` | `static` | 131 |
| 166 | `0xA6` | `uialpha` | 132 |
| 167 | `0xA7` | `spinradiusx` | 133 |
| 168 | `0xA8` | `spinradiusz` | 134 |
| 169 | `0xA9` | `fakezy` | 135 |
| 170 | `0xAA` | `fakezyb` | 136 |
| 171 | `0xAB` | `float` | 137 |
| 172 | `0xAC` | `wiggly` | 138 |

### `obj_aleph_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_aleph_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 4 |
| 130 | `0x82` | `uialpha` | 5 |
| 131 | `0x83` | `scorealph` | 6 |
| 132 | `0x84` | `bgalph` | 7 |
| 133 | `0x85` | `noteoverlayalp` | 8 |
| 134 | `0x86` | `sg_endblip` | 9 |
| 135 | `0x87` | `glitchoffset` | 10 |
| 136 | `0x88` | `uhnoise` | 11 |
| 137 | `0x89` | `abberationxamp` | 12 |
| 138 | `0x8A` | `abberationyamp` | 13 |
| 139 | `0x8B` | `fish` | 14 |
| 140 | `0x8C` | `static` | 15 |
| 141 | `0x8D` | `sg_endblip_destroy` | 16 |
| 142 | `0x8E` | `sn_bg_alpha` | 17 |
| 143 | `0x8F` | `sn_bg_fxamp` | 18 |
| 144 | `0x90` | `sn_bg_animspd` | 19 |
| 145 | `0x91` | `yoffset` | 20 |

### `obj_angelstar_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_angelstar_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `uialpha` | 8 |
| 130 | `0x82` | `cover1` | 9 |
| 131 | `0x83` | `cover2` | 10 |
| 132 | `0x84` | `cover3` | 11 |
| 133 | `0x85` | `wflash` | 12 |
| 134 | `0x86` | `rainbow` | 13 |
| 135 | `0x87` | `sides` | 14 |
| 136 | `0x88` | `notealp` | 25 |
| 137 | `0x89` | `video` | 26 |
| 138 | `0x8A` | `noteoverlayalp` | 27 |
| 139 | `0x8B` | `shadermode` | 28 |
| 140 | `0x8C` | `scorealph` | 29 |
| 141 | `0x8D` | `bgalph` | 30 |
| 142 | `0x8E` | `gray` | 31 |
| 143 | `0x8F` | `barrel` | 32 |
| 144 | `0x90` | `barrel2` | 33 |
| 145 | `0x91` | `hdistort` | 34 |
| 156 | `0x9C` | `fish` | 45 |
| 147 | `0x93` | `vig` | 36 |
| 148 | `0x94` | `abx` | 37 |
| 149 | `0x95` | `aby` | 38 |
| 150 | `0x96` | `aberamp` | 39 |
| 151 | `0x97` | `glitchamp` | 40 |
| 152 | `0x98` | `glitchoffset` | 41 |
| 153 | `0x99` | `uhnoise` | 42 |
| 154 | `0x9A` | `abberationxamp` | 43 |
| 155 | `0x9B` | `abberationyamp` | 44 |
| 157 | `0x9D` | `static` | 46 |
| 158 | `0x9E` | `fx_hue_hue` | 47 |
| 159 | `0x9F` | `fx_hue_saturation` | 48 |
| 160 | `0xA0` | `fx_edge` | 49 |
| 161 | `0xA1` | `fx_posterize` | 50 |
| 162 | `0xA2` | `fx_twirl` | 51 |
| 163 | `0xA3` | `fx_posterize_vis` | 52 |
| 164 | `0xA4` | `fx_underwater` | 53 |
| 165 | `0xA5` | `bloom` | 54 |
| 166 | `0xA6` | `angelstar_checker_alpha` | 55 |
| 167 | `0xA7` | `angelstar_checker_set` | 56 |
| 168 | `0xA8` | `fx_zoom` | 57 |
| 169 | `0xA9` | `fx_red` | 58 |
| 170 | `0xAA` | `recolor` | 59 |
| 171 | `0xAB` | `holdoverlayalpha` | 63 |

Shadowed registrations are retained in the JSON catalog and omitted from this effective mapping.

### `obj_astellion_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_astellion_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `gray` | 4 |
| 130 | `0x82` | `barrel` | 5 |
| 131 | `0x83` | `barrel2` | 6 |
| 132 | `0x84` | `hdistort` | 7 |
| 133 | `0x85` | `fish` | 8 |
| 134 | `0x86` | `vig` | 9 |
| 135 | `0x87` | `abx` | 10 |
| 136 | `0x88` | `aby` | 11 |
| 137 | `0x89` | `aberamp` | 12 |
| 138 | `0x8A` | `uialpha` | 13 |
| 139 | `0x8B` | `cover1` | 14 |
| 140 | `0x8C` | `cover2` | 15 |
| 141 | `0x8D` | `cover3` | 16 |
| 142 | `0x8E` | `wflash` | 17 |
| 143 | `0x8F` | `rainbow` | 18 |
| 144 | `0x90` | `sides` | 19 |
| 145 | `0x91` | `notealp` | 44 |
| 146 | `0x92` | `video` | 45 |
| 147 | `0x93` | `noteoverlayalp` | 46 |
| 148 | `0x94` | `astbars` | 47 |
| 149 | `0x95` | `bgalph` | 51 |
| 150 | `0x96` | `fxdist1` | 52 |
| 151 | `0x97` | `fxdist2` | 53 |
| 152 | `0x98` | `parttimer` | 54 |

### `obj_base_gimmick`

Parent: `None`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_base_gimmick_Create_0.gml).

No extra-mod registrations.

### `obj_convergence_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_convergence_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 9 |
| 130 | `0x82` | `uialpha` | 10 |
| 131 | `0x83` | `scorealph` | 11 |
| 132 | `0x84` | `bgalph` | 12 |
| 133 | `0x85` | `noteoverlayalp` | 13 |
| 134 | `0x86` | `sg_endblip` | 14 |
| 135 | `0x87` | `supernova_dialogue` | 15 |
| 136 | `0x88` | `supernova_cg_xscale` | 16 |
| 137 | `0x89` | `supernova_cg_alpha` | 17 |
| 138 | `0x8A` | `glitchoffset` | 18 |
| 139 | `0x8B` | `uhnoise` | 19 |
| 140 | `0x8C` | `abberationxamp` | 20 |
| 141 | `0x8D` | `abberationyamp` | 21 |
| 142 | `0x8E` | `fish` | 22 |
| 143 | `0x8F` | `static` | 23 |
| 144 | `0x90` | `supernova_cg_frame` | 24 |
| 145 | `0x91` | `sg_endblip_destroy` | 25 |
| 146 | `0x92` | `sn_bg_alpha` | 26 |
| 147 | `0x93` | `sn_bg2_alpha` | 27 |
| 148 | `0x94` | `sn_bg_fxamp` | 28 |
| 149 | `0x95` | `sn_bg_animspd` | 29 |
| 150 | `0x96` | `setup_co` | 30 |

### `obj_credits_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_credits_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `lyricIndex` | 7 |

### `obj_credits_gimmick_encore`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_credits_gimmick_encore_Create_0.gml).

No extra-mod registrations.

### `obj_distortedfate_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_distortedfate_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `df_sideline` | 3 |
| 130 | `0x82` | `df_whitebg` | 4 |
| 131 | `0x83` | `df_grid_alpha` | 5 |
| 132 | `0x84` | `df_grid_top` | 6 |
| 133 | `0x85` | `df_grid_bottom` | 7 |
| 134 | `0x86` | `df_sideline2` | 8 |
| 135 | `0x87` | `gray` | 21 |
| 136 | `0x88` | `barrel` | 22 |
| 137 | `0x89` | `barrel2` | 23 |
| 138 | `0x8A` | `hdistort` | 24 |
| 139 | `0x8B` | `fish` | 25 |
| 140 | `0x8C` | `vig` | 26 |
| 141 | `0x8D` | `abx` | 27 |
| 142 | `0x8E` | `aby` | 28 |
| 143 | `0x8F` | `aberamp` | 29 |
| 144 | `0x90` | `uialpha` | 30 |
| 145 | `0x91` | `cover1` | 31 |
| 146 | `0x92` | `cover2` | 32 |
| 147 | `0x93` | `cover3` | 33 |
| 148 | `0x94` | `wflash` | 34 |
| 149 | `0x95` | `rainbow` | 35 |
| 150 | `0x96` | `sides` | 36 |
| 151 | `0x97` | `notealp` | 47 |
| 152 | `0x98` | `video` | 48 |
| 153 | `0x99` | `noteoverlayalp` | 49 |
| 154 | `0x9A` | `df_countdown` | 50 |
| 155 | `0x9B` | `lr_slash` | 51 |
| 156 | `0x9C` | `lr_slash_color` | 59 |
| 157 | `0x9D` | `lr_sides_blue` | 63 |
| 158 | `0x9E` | `lr_sides_red` | 74 |
| 159 | `0x9F` | `lr_sides_rev_blue` | 87 |
| 160 | `0xA0` | `lr_sides_rev_red` | 98 |
| 161 | `0xA1` | `lr_mountain_bg` | 111 |

### `obj_dracula_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_dracula_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `cover1` | 12 |
| 130 | `0x82` | `cover2` | 13 |
| 131 | `0x83` | `cover3` | 14 |
| 132 | `0x84` | `uialpha` | 15 |
| 133 | `0x85` | `vib` | 16 |
| 134 | `0x86` | `jart` | 17 |
| 135 | `0x87` | `jdesat` | 18 |
| 136 | `0x88` | `seedspeed` | 19 |
| 137 | `0x89` | `wflash` | 20 |
| 138 | `0x8A` | `posx` | 21 |
| 139 | `0x8B` | `posy` | 22 |

### `obj_extendnova_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_extendnova_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 9 |
| 130 | `0x82` | `uialpha` | 10 |
| 131 | `0x83` | `scorealph` | 11 |
| 132 | `0x84` | `bgalph` | 12 |
| 133 | `0x85` | `noteoverlayalp` | 13 |
| 134 | `0x86` | `sg_endblip` | 14 |
| 135 | `0x87` | `supernova_dialogue` | 15 |
| 136 | `0x88` | `supernova_cg_xscale` | 16 |
| 137 | `0x89` | `supernova_cg_alpha` | 17 |
| 138 | `0x8A` | `glitchoffset` | 18 |
| 139 | `0x8B` | `uhnoise` | 19 |
| 140 | `0x8C` | `abberationxamp` | 20 |
| 141 | `0x8D` | `abberationyamp` | 21 |
| 142 | `0x8E` | `fish` | 22 |
| 143 | `0x8F` | `static` | 23 |
| 144 | `0x90` | `supernova_cg_frame` | 24 |
| 145 | `0x91` | `sg_endblip_destroy` | 25 |
| 146 | `0x92` | `sn_bg_alpha` | 26 |
| 147 | `0x93` | `sn_bg_fxamp` | 27 |
| 148 | `0x94` | `sn_bg_animspd` | 28 |
| 149 | `0x95` | `setup_co` | 29 |
| 150 | `0x96` | `setup_co_en_s1` | 30 |
| 151 | `0x97` | `setup_co_en_s2` | 34 |
| 152 | `0x98` | `setup_co_en_s3` | 38 |
| 153 | `0x99` | `setup_co_en_s4` | 42 |
| 154 | `0x9A` | `setup_co_en_s5` | 46 |
| 155 | `0x9B` | `setup_co_en_s6` | 50 |
| 156 | `0x9C` | `setup_co_en_s7` | 54 |
| 157 | `0x9D` | `setup_co_en_s8` | 58 |
| 158 | `0x9E` | `en_whiteoverlay` | 62 |
| 159 | `0x9F` | `en_voidparticles` | 63 |
| 160 | `0xA0` | `en_slash_sat` | 64 |
| 161 | `0xA1` | `en_posterize_vis` | 86 |
| 162 | `0xA2` | `en_posterize` | 87 |
| 163 | `0xA3` | `en_chorus_bg_alpha` | 88 |
| 164 | `0xA4` | `en_evildawn_hpbar_amount` | 89 |
| 165 | `0xA5` | `en_gun_dawn` | 90 |
| 166 | `0xA6` | `en_evildawn_hpbar_alpha` | 109 |
| 167 | `0xA7` | `en_evildawn_hpbar_shake` | 110 |
| 168 | `0xA8` | `en_enddrop_bg_alpha` | 111 |
| 169 | `0xA9` | `fx_edge` | 112 |

### `obj_firstbreath_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_firstbreath_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `df_sideline` | 8 |
| 130 | `0x82` | `df_whitebg` | 9 |
| 131 | `0x83` | `df_grid_alpha` | 10 |
| 132 | `0x84` | `df_grid_top` | 11 |
| 133 | `0x85` | `df_grid_bottom` | 12 |
| 134 | `0x86` | `df_sideline2` | 13 |
| 135 | `0x87` | `gray` | 26 |
| 136 | `0x88` | `barrel` | 27 |
| 137 | `0x89` | `barrel2` | 28 |
| 138 | `0x8A` | `hdistort` | 29 |
| 139 | `0x8B` | `fish` | 30 |
| 140 | `0x8C` | `vig` | 31 |
| 141 | `0x8D` | `abx` | 32 |
| 142 | `0x8E` | `aby` | 33 |
| 143 | `0x8F` | `aberamp` | 34 |
| 144 | `0x90` | `uialpha` | 35 |
| 145 | `0x91` | `cover1` | 36 |
| 146 | `0x92` | `cover2` | 37 |
| 147 | `0x93` | `cover3` | 38 |
| 148 | `0x94` | `wflash` | 39 |
| 149 | `0x95` | `rainbow` | 40 |
| 150 | `0x96` | `sides` | 41 |
| 151 | `0x97` | `notealp` | 42 |
| 152 | `0x98` | `video` | 43 |
| 153 | `0x99` | `noteoverlayalp` | 44 |
| 154 | `0x9A` | `df_countdown` | 45 |
| 155 | `0x9B` | `lr_slash` | 46 |
| 156 | `0x9C` | `lr_slash_color` | 57 |
| 157 | `0x9D` | `lr_sides_blue` | 73 |
| 158 | `0x9E` | `lr_sides_red` | 86 |
| 159 | `0x9F` | `lr_sides_rev_blue` | 101 |
| 160 | `0xA0` | `lr_sides_rev_red` | 102 |
| 161 | `0xA1` | `lr_mountain_bg` | 117 |
| 162 | `0xA2` | `setup_co` | 118 |
| 163 | `0xA3` | `glitchamp` | 119 |
| 164 | `0xA4` | `supernova_cg_alpha` | 120 |
| 165 | `0xA5` | `supernova_cg_xscale` | 121 |
| 166 | `0xA6` | `supernova_cg_frame` | 122 |
| 167 | `0xA7` | `glitchoffset` | 123 |
| 168 | `0xA8` | `uhnoise` | 124 |
| 169 | `0xA9` | `abberationxamp` | 125 |
| 170 | `0xAA` | `abberationyamp` | 126 |
| 171 | `0xAB` | `sn_bg_alpha` | 127 |
| 172 | `0xAC` | `sn_bg_fxamp` | 128 |
| 173 | `0xAD` | `sn_bg_animspd` | 129 |

### `obj_lastwish_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_lastwish_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `uialpha` | 2 |
| 130 | `0x82` | `bgalph` | 3 |
| 131 | `0x83` | `film` | 4 |
| 132 | `0x84` | `glow` | 5 |
| 133 | `0x85` | `filmsat` | 6 |
| 134 | `0x86` | `lwcover` | 7 |
| 135 | `0x87` | `lwflickerspd` | 8 |
| 136 | `0x88` | `lwjitterintensity` | 9 |
| 137 | `0x89` | `lwchroma` | 10 |
| 138 | `0x8A` | `lwtext` | 11 |

### `obj_libertia_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_libertia_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 9 |
| 130 | `0x82` | `uialpha` | 10 |
| 131 | `0x83` | `scorealph` | 11 |
| 132 | `0x84` | `bgalph` | 12 |
| 133 | `0x85` | `noteoverlayalp` | 13 |
| 134 | `0x86` | `sg_endblip` | 14 |
| 135 | `0x87` | `supernova_dialogue` | 22 |
| 136 | `0x88` | `supernova_cg_xscale` | 23 |
| 137 | `0x89` | `supernova_cg_alpha` | 24 |
| 138 | `0x8A` | `glitchoffset` | 25 |
| 139 | `0x8B` | `uhnoise` | 26 |
| 140 | `0x8C` | `abberationxamp` | 27 |
| 141 | `0x8D` | `abberationyamp` | 28 |
| 142 | `0x8E` | `fish` | 29 |
| 143 | `0x8F` | `static` | 30 |
| 144 | `0x90` | `supernova_cg_frame` | 31 |
| 145 | `0x91` | `sg_endblip_destroy` | 32 |
| 146 | `0x92` | `sn_bg_alpha` | 36 |
| 147 | `0x93` | `sn_bg_fxamp` | 37 |
| 148 | `0x94` | `sn_bg_animspd` | 38 |
| 149 | `0x95` | `setup_co` | 39 |

### `obj_marenol_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_marenol_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 33 |
| 130 | `0x82` | `glitchoffset` | 34 |
| 131 | `0x83` | `fish` | 35 |
| 132 | `0x84` | `posx` | 36 |
| 133 | `0x85` | `posy` | 37 |
| 134 | `0x86` | `cover1` | 38 |
| 135 | `0x87` | `cover2` | 39 |
| 136 | `0x88` | `cover3` | 40 |
| 137 | `0x89` | `twx1` | 43 |
| 138 | `0x8A` | `twy1` | 44 |
| 139 | `0x8B` | `twa1` | 45 |
| 140 | `0x8C` | `twr1` | 46 |
| 141 | `0x8D` | `twx2` | 43 |
| 142 | `0x8E` | `twy2` | 44 |
| 143 | `0x8F` | `twa2` | 45 |
| 144 | `0x90` | `twr2` | 46 |
| 145 | `0x91` | `twx3` | 43 |
| 146 | `0x92` | `twy3` | 44 |
| 147 | `0x93` | `twa3` | 45 |
| 148 | `0x94` | `twr3` | 46 |
| 149 | `0x95` | `twx4` | 43 |
| 150 | `0x96` | `twy4` | 44 |
| 151 | `0x97` | `twa4` | 45 |
| 152 | `0x98` | `twr4` | 46 |
| 153 | `0x99` | `sina` | 48 |
| 154 | `0x9A` | `sinp` | 49 |
| 155 | `0x9B` | `sino` | 50 |
| 156 | `0x9C` | `cosa` | 51 |
| 157 | `0x9D` | `cosp` | 52 |
| 158 | `0x9E` | `coso` | 53 |
| 159 | `0x9F` | `tana` | 54 |
| 160 | `0xA0` | `tanp` | 55 |
| 161 | `0xA1` | `tano` | 56 |
| 162 | `0xA2` | `static` | 57 |
| 163 | `0xA3` | `vibx` | 58 |
| 164 | `0xA4` | `viby` | 59 |
| 165 | `0xA5` | `uialpha` | 60 |
| 166 | `0xA6` | `flicker` | 61 |

### `obj_memories_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_memories_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 11 |
| 130 | `0x82` | `uialpha` | 12 |
| 131 | `0x83` | `scorealph` | 13 |
| 132 | `0x84` | `bgalph` | 14 |
| 133 | `0x85` | `noteoverlayalp` | 15 |
| 134 | `0x86` | `sg_endblip` | 16 |
| 135 | `0x87` | `supernova_dialogue` | 17 |
| 136 | `0x88` | `supernova_cg_xscale` | 18 |
| 137 | `0x89` | `supernova_cg_alpha` | 19 |
| 138 | `0x8A` | `glitchoffset` | 20 |
| 139 | `0x8B` | `uhnoise` | 21 |
| 140 | `0x8C` | `abberationxamp` | 22 |
| 141 | `0x8D` | `abberationyamp` | 23 |
| 142 | `0x8E` | `fish` | 24 |
| 143 | `0x8F` | `static` | 25 |
| 144 | `0x90` | `supernova_cg_frame` | 26 |
| 145 | `0x91` | `sg_endblip_destroy` | 27 |
| 146 | `0x92` | `sn_bg_alpha` | 28 |
| 147 | `0x93` | `sn_bg_fxamp` | 29 |
| 148 | `0x94` | `sn_bg_animspd` | 30 |
| 149 | `0x95` | `setup_co` | 31 |

### `obj_multigrode_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_multigrode_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 4 |
| 130 | `0x82` | `uialpha` | 5 |
| 131 | `0x83` | `scorealph` | 6 |
| 132 | `0x84` | `bgalph` | 7 |
| 133 | `0x85` | `noteoverlayalp` | 8 |
| 134 | `0x86` | `sg_endblip` | 9 |
| 135 | `0x87` | `glitchoffset` | 10 |
| 136 | `0x88` | `uhnoise` | 11 |
| 137 | `0x89` | `abberationxamp` | 12 |
| 138 | `0x8A` | `abberationyamp` | 13 |
| 139 | `0x8B` | `fish` | 14 |
| 140 | `0x8C` | `static` | 15 |
| 141 | `0x8D` | `sg_endblip_destroy` | 16 |
| 142 | `0x8E` | `sn_bg_alpha` | 17 |
| 143 | `0x8F` | `sn_bg_fxamp` | 18 |
| 144 | `0x90` | `sn_bg_animspd` | 19 |
| 145 | `0x91` | `yoffset` | 20 |
| 146 | `0x92` | `dialogue_size` | 21 |
| 147 | `0x93` | `text_alpha` | 22 |
| 148 | `0x94` | `dialogue_id` | 23 |
| 149 | `0x95` | `fruitmemoryx` | 24 |
| 150 | `0x96` | `refreshdialogue` | 25 |

### `obj_pictured_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_pictured_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `c_flash` | 28 |
| 130 | `0x82` | `c_shader` | 29 |
| 131 | `0x83` | `uialpha` | 30 |
| 132 | `0x84` | `scorealph` | 31 |
| 133 | `0x85` | `bgalph` | 32 |
| 134 | `0x86` | `noteoverlayalp` | 33 |
| 135 | `0x87` | `holdoverlayalpha` | 34 |
| 136 | `0x88` | `1_pinkbg_vis` | 35 |
| 137 | `0x89` | `1_speech` | 36 |
| 138 | `0x8A` | `1_glitch` | 37 |
| 139 | `0x8B` | `2_boost` | 38 |
| 140 | `0x8C` | `2_dialbox_size` | 39 |
| 141 | `0x8D` | `2_dialbox_circles` | 40 |
| 142 | `0x8E` | `2_bg_pics` | 41 |
| 143 | `0x8F` | `2_dialbox_pulsar` | 42 |
| 144 | `0x90` | `2_dialbox_speech` | 43 |
| 145 | `0x91` | `2_bg_pinkbg_vis` | 44 |
| 146 | `0x92` | `3_pinkbg_alph` | 45 |
| 147 | `0x93` | `3_noteblack` | 46 |
| 148 | `0x94` | `4_plusbg_vis` | 47 |
| 149 | `0x95` | `4_plusbg_pulse` | 48 |
| 150 | `0x96` | `4_square_alph` | 49 |
| 151 | `0x97` | `4_square_rotspd` | 50 |
| 152 | `0x98` | `4_square_scale` | 51 |
| 153 | `0x99` | `5_video_toggle` | 52 |
| 154 | `0x9A` | `5_video_alph` | 53 |
| 155 | `0x9B` | `5_bord_alph` | 54 |
| 156 | `0x9C` | `5_abber` | 55 |
| 157 | `0x9D` | `6_glitch` | 56 |
| 158 | `0x9E` | `6_video_toggle` | 57 |
| 159 | `0x9F` | `6_video_alph` | 58 |
| 160 | `0xA0` | `6_red_layer_alph` | 59 |
| 161 | `0xA1` | `6_static_alph` | 60 |
| 162 | `0xA2` | `7_bg_vis` | 61 |
| 163 | `0xA3` | `7_note_vfx` | 62 |
| 164 | `0xA4` | `7_static_alph` | 63 |

### `obj_plaudite_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_plaudite_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 8 |
| 130 | `0x82` | `uialpha` | 9 |
| 131 | `0x83` | `scorealph` | 10 |
| 132 | `0x84` | `bgalph` | 11 |
| 133 | `0x85` | `noteoverlayalp` | 12 |
| 134 | `0x86` | `sg_endblip` | 13 |
| 135 | `0x87` | `supernova_dialogue` | 14 |
| 136 | `0x88` | `supernova_cg_xscale` | 15 |
| 137 | `0x89` | `supernova_cg_alpha` | 16 |
| 138 | `0x8A` | `glitchoffset` | 17 |
| 139 | `0x8B` | `uhnoise` | 18 |
| 140 | `0x8C` | `abberationxamp` | 19 |
| 141 | `0x8D` | `abberationyamp` | 20 |
| 142 | `0x8E` | `fish` | 21 |
| 143 | `0x8F` | `static` | 22 |
| 144 | `0x90` | `supernova_cg_frame` | 23 |
| 145 | `0x91` | `sg_endblip_destroy` | 24 |
| 146 | `0x92` | `sn_bg_alpha` | 25 |
| 147 | `0x93` | `sn_bg_fxamp` | 26 |
| 148 | `0x94` | `sn_bg_animspd` | 27 |
| 149 | `0x95` | `setup_co` | 28 |
| 150 | `0x96` | `setup_co_sect4` | 29 |
| 151 | `0x97` | `setup_co_sect6` | 33 |
| 152 | `0x98` | `setup_co_sect8` | 37 |
| 153 | `0x99` | `setup_co_sect12` | 41 |
| 154 | `0x9A` | `setup_co_sect14` | 45 |
| 155 | `0x9B` | `setup_co_end` | 49 |
| 156 | `0x9C` | `plaudite_jacket` | 53 |
| 157 | `0x9D` | `plaudite_sect2bg` | 54 |
| 158 | `0x9E` | `plaudite_sect5bg` | 55 |
| 159 | `0x9F` | `plaudite_sect7bg` | 56 |
| 160 | `0xA0` | `unraveling_sidething` | 57 |
| 161 | `0xA1` | `astellion_sidething` | 68 |
| 162 | `0xA2` | `astellion_particles` | 85 |
| 163 | `0xA3` | `supernova_bg_visible` | 86 |
| 164 | `0xA4` | `libertia_bg_visible` | 87 |
| 165 | `0xA5` | `stopmotion_bg_visible` | 88 |
| 166 | `0xA6` | `convergence_bg_visible` | 89 |
| 167 | `0xA7` | `plaudite_finaldropbg` | 90 |
| 168 | `0xA8` | `plaudite_finaldropwhitebg` | 91 |
| 169 | `0xA9` | `plaudite_slash_saturday` | 92 |
| 170 | `0xAA` | `plaudite_slash_dawn` | 100 |
| 171 | `0xAB` | `plaudite_ending_event` | 108 |
| 172 | `0xAC` | `plaudite_red_particle` | 134 |
| 173 | `0xAD` | `plaudite_pburst` | 135 |
| 174 | `0xAE` | `plaudite_disable_jacket` | 149 |
| 175 | `0xAF` | `plaudite_slash_neutral` | 150 |
| 176 | `0xB0` | `plaudite_finaldropbg2` | 157 |
| 177 | `0xB1` | `holdoverlayalpha` | 158 |
| 178 | `0xB2` | `setup_co_sect1` | 159 |
| 179 | `0xB3` | `hide_combo` | 182 |

### `obj_ram_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_ram_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 61 |
| 130 | `0x82` | `glitchoffset` | 62 |
| 131 | `0x83` | `fish` | 63 |
| 132 | `0x84` | `vig` | 64 |
| 133 | `0x85` | `bloom` | 65 |
| 134 | `0x86` | `gray` | 66 |
| 135 | `0x87` | `posx` | 67 |
| 136 | `0x88` | `posy` | 68 |
| 137 | `0x89` | `cover1` | 69 |
| 138 | `0x8A` | `cover2` | 70 |
| 139 | `0x8B` | `cover3` | 71 |
| 140 | `0x8C` | `twx1` | 74 |
| 141 | `0x8D` | `twy1` | 75 |
| 142 | `0x8E` | `twa1` | 76 |
| 143 | `0x8F` | `twr1` | 77 |
| 144 | `0x90` | `twx2` | 74 |
| 145 | `0x91` | `twy2` | 75 |
| 146 | `0x92` | `twa2` | 76 |
| 147 | `0x93` | `twr2` | 77 |
| 148 | `0x94` | `twx3` | 74 |
| 149 | `0x95` | `twy3` | 75 |
| 150 | `0x96` | `twa3` | 76 |
| 151 | `0x97` | `twr3` | 77 |
| 152 | `0x98` | `twx4` | 74 |
| 153 | `0x99` | `twy4` | 75 |
| 154 | `0x9A` | `twa4` | 76 |
| 155 | `0x9B` | `twr4` | 77 |
| 156 | `0x9C` | `sina` | 79 |
| 157 | `0x9D` | `sinp` | 80 |
| 158 | `0x9E` | `sino` | 81 |
| 159 | `0x9F` | `cosa` | 82 |
| 160 | `0xA0` | `cosp` | 83 |
| 161 | `0xA1` | `coso` | 84 |
| 162 | `0xA2` | `tana` | 85 |
| 163 | `0xA3` | `tanp` | 86 |
| 164 | `0xA4` | `tano` | 87 |
| 165 | `0xA5` | `static` | 88 |
| 166 | `0xA6` | `uialpha` | 89 |
| 167 | `0xA7` | `spinradiusx` | 90 |
| 168 | `0xA8` | `spinradiusz` | 91 |
| 169 | `0xA9` | `fakezy` | 92 |
| 170 | `0xAA` | `fakezyb` | 93 |
| 171 | `0xAB` | `float` | 94 |
| 172 | `0xAC` | `wiggly` | 95 |
| 173 | `0xAD` | `imgx1` | 98 |
| 174 | `0xAE` | `imgy1` | 99 |
| 175 | `0xAF` | `imgzm1` | 100 |
| 176 | `0xB0` | `imgzmb1` | 101 |
| 177 | `0xB1` | `imgzmx1` | 102 |
| 178 | `0xB2` | `imgzmy1` | 103 |
| 179 | `0xB3` | `imgrz1` | 104 |
| 180 | `0xB4` | `imga1` | 105 |
| 181 | `0xB5` | `imgx2` | 98 |
| 182 | `0xB6` | `imgy2` | 99 |
| 183 | `0xB7` | `imgzm2` | 100 |
| 184 | `0xB8` | `imgzmb2` | 101 |
| 185 | `0xB9` | `imgzmx2` | 102 |
| 186 | `0xBA` | `imgzmy2` | 103 |
| 187 | `0xBB` | `imgrz2` | 104 |
| 188 | `0xBC` | `imga2` | 105 |
| 189 | `0xBD` | `imgx3` | 98 |
| 190 | `0xBE` | `imgy3` | 99 |
| 191 | `0xBF` | `imgzm3` | 100 |
| 192 | `0xC0` | `imgzmb3` | 101 |
| 193 | `0xC1` | `imgzmx3` | 102 |
| 194 | `0xC2` | `imgzmy3` | 103 |
| 195 | `0xC3` | `imgrz3` | 104 |
| 196 | `0xC4` | `imga3` | 105 |
| 197 | `0xC5` | `imgx4` | 98 |
| 198 | `0xC6` | `imgy4` | 99 |
| 199 | `0xC7` | `imgzm4` | 100 |
| 200 | `0xC8` | `imgzmb4` | 101 |
| 201 | `0xC9` | `imgzmx4` | 102 |
| 202 | `0xCA` | `imgzmy4` | 103 |
| 203 | `0xCB` | `imgrz4` | 104 |
| 204 | `0xCC` | `imga4` | 105 |
| 205 | `0xCD` | `imgx5` | 98 |
| 206 | `0xCE` | `imgy5` | 99 |
| 207 | `0xCF` | `imgzm5` | 100 |
| 208 | `0xD0` | `imgzmb5` | 101 |
| 209 | `0xD1` | `imgzmx5` | 102 |
| 210 | `0xD2` | `imgzmy5` | 103 |
| 211 | `0xD3` | `imgrz5` | 104 |
| 212 | `0xD4` | `imga5` | 105 |
| 213 | `0xD5` | `imgx6` | 98 |
| 214 | `0xD6` | `imgy6` | 99 |
| 215 | `0xD7` | `imgzm6` | 100 |
| 216 | `0xD8` | `imgzmb6` | 101 |
| 217 | `0xD9` | `imgzmx6` | 102 |
| 218 | `0xDA` | `imgzmy6` | 103 |
| 219 | `0xDB` | `imgrz6` | 104 |
| 220 | `0xDC` | `imga6` | 105 |
| 221 | `0xDD` | `imgx7` | 98 |
| 222 | `0xDE` | `imgy7` | 99 |
| 223 | `0xDF` | `imgzm7` | 100 |
| 224 | `0xE0` | `imgzmb7` | 101 |
| 225 | `0xE1` | `imgzmx7` | 102 |
| 226 | `0xE2` | `imgzmy7` | 103 |
| 227 | `0xE3` | `imgrz7` | 104 |
| 228 | `0xE4` | `imga7` | 105 |
| 229 | `0xE5` | `planea` | 107 |
| 230 | `0xE6` | `rotdir` | 108 |
| 231 | `0xE7` | `texta` | 109 |

### `obj_scarletdeath_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_scarletdeath_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `uialpha` | 8 |
| 130 | `0x82` | `cover1` | 9 |
| 131 | `0x83` | `cover2` | 10 |
| 132 | `0x84` | `cover3` | 11 |
| 133 | `0x85` | `wflash` | 12 |
| 134 | `0x86` | `rainbow` | 13 |
| 135 | `0x87` | `sides` | 14 |
| 136 | `0x88` | `notealp` | 15 |
| 137 | `0x89` | `video` | 16 |
| 138 | `0x8A` | `noteoverlayalp` | 17 |
| 139 | `0x8B` | `shadermode` | 18 |
| 140 | `0x8C` | `scorealph` | 19 |
| 141 | `0x8D` | `bgalph` | 20 |
| 142 | `0x8E` | `gray` | 21 |
| 143 | `0x8F` | `barrel` | 22 |
| 144 | `0x90` | `barrel2` | 23 |
| 145 | `0x91` | `hdistort` | 24 |
| 156 | `0x9C` | `fish` | 35 |
| 147 | `0x93` | `vig` | 26 |
| 148 | `0x94` | `abx` | 27 |
| 149 | `0x95` | `aby` | 28 |
| 150 | `0x96` | `aberamp` | 29 |
| 151 | `0x97` | `glitchamp` | 30 |
| 152 | `0x98` | `glitchoffset` | 31 |
| 153 | `0x99` | `uhnoise` | 32 |
| 154 | `0x9A` | `abberationxamp` | 33 |
| 155 | `0x9B` | `abberationyamp` | 34 |
| 157 | `0x9D` | `static` | 36 |
| 158 | `0x9E` | `fx_hue_hue` | 37 |
| 159 | `0x9F` | `fx_hue_saturation` | 38 |
| 160 | `0xA0` | `fx_edge` | 39 |
| 161 | `0xA1` | `fx_posterize` | 40 |
| 162 | `0xA2` | `fx_twirl` | 41 |
| 163 | `0xA3` | `fx_posterize_vis` | 42 |
| 164 | `0xA4` | `fx_underwater` | 43 |
| 165 | `0xA5` | `bloom` | 44 |
| 166 | `0xA6` | `angelstar_checker_alpha` | 45 |
| 167 | `0xA7` | `angelstar_checker_set` | 46 |
| 168 | `0xA8` | `fx_zoom` | 47 |
| 169 | `0xA9` | `fx_red` | 48 |
| 170 | `0xAA` | `heartattack1` | 49 |
| 171 | `0xAB` | `heartattack2` | 57 |
| 172 | `0xAC` | `heartattack3` | 65 |
| 173 | `0xAD` | `heartattack4` | 73 |
| 174 | `0xAE` | `heartattack5` | 81 |
| 175 | `0xAF` | `heartattack6` | 89 |

Shadowed registrations are retained in the JSON catalog and omitted from this effective mapping.

### `obj_sekaisen_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_sekaisen_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `gray` | 6 |
| 130 | `0x82` | `barrel` | 7 |
| 131 | `0x83` | `barrel2` | 8 |
| 132 | `0x84` | `hdistort` | 9 |
| 133 | `0x85` | `fish` | 10 |
| 134 | `0x86` | `vig` | 11 |
| 135 | `0x87` | `abx` | 12 |
| 136 | `0x88` | `aby` | 13 |
| 137 | `0x89` | `aberamp` | 14 |
| 138 | `0x8A` | `uialpha` | 15 |
| 139 | `0x8B` | `cover1` | 16 |
| 140 | `0x8C` | `cover2` | 17 |
| 141 | `0x8D` | `cover3` | 18 |
| 142 | `0x8E` | `wflash` | 19 |
| 143 | `0x8F` | `rainbow` | 20 |
| 144 | `0x90` | `sides` | 21 |
| 145 | `0x91` | `notealp` | 22 |
| 146 | `0x92` | `video` | 23 |
| 147 | `0x93` | `noteoverlayalp` | 24 |
| 148 | `0x94` | `starspawner_timer` | 25 |
| 149 | `0x95` | `starspd_low` | 26 |
| 150 | `0x96` | `starspd_high` | 27 |
| 151 | `0x97` | `starspd_multiplier` | 28 |
| 152 | `0x98` | `sekaisen_jacket` | 29 |
| 153 | `0x99` | `sekaisen_arrow_point` | 30 |
| 154 | `0x9A` | `sekaisen_target_point` | 31 |
| 155 | `0x9B` | `track_alpha` | 32 |
| 156 | `0x9C` | `en_whiteoverlay` | 33 |
| 157 | `0x9D` | `eo_endsat1` | 34 |
| 158 | `0x9E` | `eo_endsat2` | 35 |
| 159 | `0x9F` | `eo_endsat3` | 36 |
| 160 | `0xA0` | `eo_endsat4` | 37 |
| 161 | `0xA1` | `eo_endcg` | 38 |
| 162 | `0xA2` | `bgalph` | 39 |
| 163 | `0xA3` | `hide_combo` | 40 |

### `obj_self_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_self_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 13 |
| 130 | `0x82` | `uialpha` | 14 |
| 131 | `0x83` | `scorealph` | 15 |
| 132 | `0x84` | `holdoverlayalpha` | 16 |
| 133 | `0x85` | `bgalph` | 17 |
| 134 | `0x86` | `noteoverlayalp` | 18 |
| 135 | `0x87` | `sg_endblip` | 19 |
| 136 | `0x88` | `glitchoffset` | 20 |
| 137 | `0x89` | `uhnoise` | 21 |
| 138 | `0x8A` | `abberationxamp` | 22 |
| 139 | `0x8B` | `abberationyamp` | 23 |
| 140 | `0x8C` | `fish` | 24 |
| 141 | `0x8D` | `static` | 25 |
| 142 | `0x8E` | `sg_endblip_destroy` | 26 |
| 143 | `0x8F` | `sn_bg_alpha` | 27 |
| 144 | `0x90` | `sn_bg_fxamp` | 28 |
| 145 | `0x91` | `sn_bg_animspd` | 29 |
| 146 | `0x92` | `yoffset` | 30 |
| 147 | `0x93` | `scrollind0` | 31 |
| 148 | `0x94` | `scrollind1` | 32 |
| 149 | `0x95` | `scrollind2` | 33 |
| 150 | `0x96` | `scrollind3` | 34 |
| 151 | `0x97` | `scrollind4` | 35 |
| 152 | `0x98` | `scrollind5` | 36 |
| 153 | `0x99` | `scrollind6` | 37 |
| 154 | `0x9A` | `stopmotionnoteskin` | 38 |
| 155 | `0x9B` | `storycheck1` | 39 |
| 156 | `0x9C` | `storycheck2` | 43 |
| 157 | `0x9D` | `sm_bg_enable` | 62 |
| 158 | `0x9E` | `sm_bg_fade_alpha` | 63 |
| 159 | `0x9F` | `temporaryshadercreate` | 64 |
| 160 | `0xA0` | `temporaryshaderdestroy` | 68 |
| 161 | `0xA1` | `sm_leftbg_frameset` | 69 |
| 162 | `0xA2` | `sm_rightbg_frameset` | 70 |
| 163 | `0xA3` | `sm_pushcommand` | 71 |
| 164 | `0xA4` | `sm_killcommand` | 72 |
| 165 | `0xA5` | `sm_bar_show` | 73 |
| 166 | `0xA6` | `sm_bar_progress` | 74 |
| 167 | `0xA7` | `sm_cyclecount` | 75 |
| 168 | `0xA8` | `self_satcolor` | 76 |
| 169 | `0xA9` | `self_satalpha` | 77 |
| 170 | `0xAA` | `self_satframe` | 78 |
| 171 | `0xAB` | `self_tsukicolor` | 79 |
| 172 | `0xAC` | `self_tsukialpha` | 80 |
| 173 | `0xAD` | `self_tsukiframe` | 81 |
| 174 | `0xAE` | `self_destsg` | 82 |
| 175 | `0xAF` | `self_gravebg` | 86 |
| 176 | `0xB0` | `self_gravefg` | 87 |

### `obj_starcrashers_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_starcrashers_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `gray` | 14 |
| 130 | `0x82` | `barrel` | 15 |
| 131 | `0x83` | `barrel2` | 16 |
| 132 | `0x84` | `hdistort` | 17 |
| 133 | `0x85` | `fish` | 18 |
| 134 | `0x86` | `vig` | 19 |
| 135 | `0x87` | `abx` | 20 |
| 136 | `0x88` | `aby` | 21 |
| 137 | `0x89` | `aberamp` | 22 |
| 138 | `0x8A` | `uialpha` | 23 |
| 139 | `0x8B` | `cover1` | 24 |
| 140 | `0x8C` | `cover2` | 25 |
| 141 | `0x8D` | `cover3` | 26 |
| 142 | `0x8E` | `wflash` | 27 |
| 143 | `0x8F` | `rainbow` | 28 |
| 144 | `0x90` | `sides` | 29 |
| 145 | `0x91` | `notealp` | 30 |
| 146 | `0x92` | `video` | 31 |
| 147 | `0x93` | `noteoverlayalp` | 32 |
| 148 | `0x94` | `stargaze_mask_sat_alpha` | 33 |
| 149 | `0x95` | `stargaze_mask_tsuki_alpha` | 34 |
| 150 | `0x96` | `stargaze_mask_star_alpha` | 35 |
| 151 | `0x97` | `starspawner_timer` | 36 |
| 152 | `0x98` | `starspd_low` | 37 |
| 153 | `0x99` | `starspd_high` | 38 |
| 154 | `0x9A` | `starspd_multiplier` | 39 |
| 155 | `0x9B` | `spawn_star_mask` | 40 |
| 156 | `0x9C` | `intro_gradient_alpha` | 45 |
| 157 | `0x9D` | `missinglink_bg_alpha` | 46 |
| 158 | `0x9E` | `turningpoint_bg_alpha` | 47 |
| 159 | `0x9F` | `frostedmemories_bg_alpha` | 48 |
| 160 | `0xA0` | `red_bg_alpha` | 49 |
| 161 | `0xA1` | `black_bg_alpha` | 50 |
| 162 | `0xA2` | `laser_spawn` | 51 |
| 163 | `0xA3` | `spawn_centerrect_red` | 58 |
| 164 | `0xA4` | `spawn_centerrect_black` | 66 |
| 165 | `0xA5` | `lasthours_checker_alpha` | 74 |
| 166 | `0xA6` | `lasthours_checker_chance` | 75 |
| 167 | `0xA7` | `lasthours_checker_set` | 76 |
| 168 | `0xA8` | `terminaljourney_bg_alpha` | 77 |
| 169 | `0xA9` | `star_set_random_alpha` | 78 |
| 170 | `0xAA` | `buildup_cutin_alpha` | 79 |
| 171 | `0xAB` | `buildup_cutin_frame` | 80 |
| 172 | `0xAC` | `chorus_town_alpha` | 81 |
| 173 | `0xAD` | `chorus_backgroundchecker_alpha` | 82 |
| 174 | `0xAE` | `chorus_firework` | 83 |
| 175 | `0xAF` | `chorus_satalli_alpha` | 89 |
| 176 | `0xB0` | `chorus_greenleft_overlay` | 90 |
| 177 | `0xB1` | `chorus_satalli_bg_alpha` | 91 |
| 178 | `0xB2` | `chorus_satalli_alli_particles` | 92 |
| 179 | `0xB3` | `chorus_satalli_sat_particles` | 102 |
| 180 | `0xB4` | `end_libertia_bg_alpha` | 116 |
| 181 | `0xB5` | `whitefade_alpha` | 117 |
| 182 | `0xB6` | `end_gravescene1_alpha` | 118 |
| 183 | `0xB7` | `blackfade_alpha` | 119 |
| 184 | `0xB8` | `end_gravescene2_alpha` | 120 |
| 185 | `0xB9` | `ending_coroutine` | 121 |

### `obj_stargazers_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_stargazers_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `gray` | 11 |
| 130 | `0x82` | `barrel` | 12 |
| 131 | `0x83` | `barrel2` | 13 |
| 132 | `0x84` | `hdistort` | 14 |
| 133 | `0x85` | `fish` | 15 |
| 134 | `0x86` | `vig` | 16 |
| 135 | `0x87` | `abx` | 17 |
| 136 | `0x88` | `aby` | 18 |
| 137 | `0x89` | `aberamp` | 19 |
| 138 | `0x8A` | `uialpha` | 20 |
| 139 | `0x8B` | `cover1` | 21 |
| 140 | `0x8C` | `cover2` | 22 |
| 141 | `0x8D` | `cover3` | 23 |
| 142 | `0x8E` | `wflash` | 24 |
| 143 | `0x8F` | `rainbow` | 25 |
| 144 | `0x90` | `sides` | 26 |
| 145 | `0x91` | `notealp` | 31 |
| 146 | `0x92` | `video` | 32 |
| 147 | `0x93` | `noteoverlayalp` | 33 |
| 148 | `0x94` | `bgalph` | 34 |
| 149 | `0x95` | `holdoverlayalpha` | 35 |
| 150 | `0x96` | `scorealph` | 36 |
| 151 | `0x97` | `sg_lanelines0` | 37 |
| 152 | `0x98` | `sg_lanelines1` | 38 |
| 153 | `0x99` | `sg_lanelines2` | 39 |
| 154 | `0x9A` | `sg_judgeline` | 40 |
| 155 | `0x9B` | `sg_starspawner` | 41 |
| 156 | `0x9C` | `starspd_low` | 42 |
| 157 | `0x9D` | `starspd_high` | 43 |
| 158 | `0x9E` | `star_pause` | 44 |
| 159 | `0x9F` | `starspawn` | 45 |
| 160 | `0xA0` | `sg_endblip` | 57 |
| 161 | `0xA1` | `sg_bg_alpha` | 64 |
| 162 | `0xA2` | `sg_bg_speed` | 65 |

### `obj_stopmotion_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_stopmotion_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 24 |
| 130 | `0x82` | `uialpha` | 25 |
| 131 | `0x83` | `scorealph` | 26 |
| 132 | `0x84` | `holdoverlayalpha` | 27 |
| 133 | `0x85` | `bgalph` | 28 |
| 134 | `0x86` | `noteoverlayalp` | 29 |
| 135 | `0x87` | `sg_endblip` | 30 |
| 136 | `0x88` | `glitchoffset` | 31 |
| 137 | `0x89` | `uhnoise` | 32 |
| 138 | `0x8A` | `abberationxamp` | 33 |
| 139 | `0x8B` | `abberationyamp` | 34 |
| 140 | `0x8C` | `fish` | 35 |
| 141 | `0x8D` | `static` | 36 |
| 142 | `0x8E` | `sg_endblip_destroy` | 37 |
| 143 | `0x8F` | `sn_bg_alpha` | 38 |
| 144 | `0x90` | `sn_bg_fxamp` | 39 |
| 145 | `0x91` | `sn_bg_animspd` | 40 |
| 146 | `0x92` | `yoffset` | 41 |
| 147 | `0x93` | `scrollind0` | 42 |
| 148 | `0x94` | `scrollind1` | 43 |
| 149 | `0x95` | `scrollind2` | 44 |
| 150 | `0x96` | `scrollind3` | 45 |
| 151 | `0x97` | `scrollind4` | 46 |
| 152 | `0x98` | `scrollind5` | 47 |
| 153 | `0x99` | `scrollind6` | 48 |
| 154 | `0x9A` | `stopmotionnoteskin` | 49 |
| 155 | `0x9B` | `storycheck1` | 50 |
| 156 | `0x9C` | `storycheck2` | 58 |
| 157 | `0x9D` | `sm_bg_enable` | 74 |
| 158 | `0x9E` | `sm_bg_fade_alpha` | 75 |
| 159 | `0x9F` | `temporaryshadercreate` | 76 |
| 160 | `0xA0` | `temporaryshaderdestroy` | 80 |
| 161 | `0xA1` | `sm_leftbg_frameset` | 84 |
| 162 | `0xA2` | `sm_rightbg_frameset` | 88 |
| 163 | `0xA3` | `sm_pushcommand` | 92 |
| 164 | `0xA4` | `sm_killcommand` | 103 |
| 165 | `0xA5` | `sm_bar_show` | 107 |
| 166 | `0xA6` | `sm_bar_progress` | 108 |
| 167 | `0xA7` | `sm_cyclecount` | 109 |

### `obj_supernova_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_supernova_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 9 |
| 130 | `0x82` | `uialpha` | 10 |
| 131 | `0x83` | `scorealph` | 11 |
| 132 | `0x84` | `bgalph` | 12 |
| 133 | `0x85` | `noteoverlayalp` | 13 |
| 134 | `0x86` | `sg_endblip` | 14 |
| 135 | `0x87` | `supernova_dialogue` | 22 |
| 136 | `0x88` | `supernova_cg_xscale` | 23 |
| 137 | `0x89` | `supernova_cg_alpha` | 24 |
| 138 | `0x8A` | `glitchoffset` | 25 |
| 139 | `0x8B` | `uhnoise` | 26 |
| 140 | `0x8C` | `abberationxamp` | 27 |
| 141 | `0x8D` | `abberationyamp` | 28 |
| 142 | `0x8E` | `fish` | 29 |
| 143 | `0x8F` | `static` | 30 |
| 144 | `0x90` | `supernova_cg_frame` | 31 |
| 145 | `0x91` | `sg_endblip_destroy` | 32 |
| 146 | `0x92` | `sn_bg_alpha` | 36 |
| 147 | `0x93` | `sn_bg_fxamp` | 37 |
| 148 | `0x94` | `sn_bg_animspd` | 38 |
| 149 | `0x95` | `setup_co` | 39 |

### `obj_times_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_times_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 14 |
| 130 | `0x82` | `static` | 15 |
| 131 | `0x83` | `wflash` | 16 |
| 132 | `0x84` | `tx` | 17 |
| 133 | `0x85` | `tx2` | 18 |
| 134 | `0x86` | `tx3` | 19 |
| 135 | `0x87` | `txj` | 20 |
| 136 | `0x88` | `ty` | 21 |
| 137 | `0x89` | `ty2` | 22 |
| 138 | `0x8A` | `ty3` | 23 |
| 139 | `0x8B` | `tyj` | 24 |
| 140 | `0x8C` | `trz` | 25 |
| 141 | `0x8D` | `trz2` | 26 |
| 142 | `0x8E` | `tz` | 27 |
| 143 | `0x8F` | `tzx` | 28 |
| 144 | `0x90` | `tzy` | 29 |
| 145 | `0x91` | `tspl` | 30 |
| 146 | `0x92` | `sepx` | 31 |
| 147 | `0x93` | `sepy` | 32 |
| 148 | `0x94` | `spinang` | 33 |
| 149 | `0x95` | `spinrad` | 34 |
| 150 | `0x96` | `siny` | 35 |
| 151 | `0x97` | `vib` | 36 |
| 152 | `0x98` | `hid1` | 39 |
| 153 | `0x99` | `hid2` | 39 |
| 154 | `0x9A` | `hid3` | 39 |
| 155 | `0x9B` | `hid4` | 39 |
| 156 | `0x9C` | `hid5` | 39 |

### `obj_tutorial_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_tutorial_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `glitchamp` | 4 |
| 130 | `0x82` | `uialpha` | 5 |
| 131 | `0x83` | `cover1` | 6 |
| 132 | `0x84` | `scorealph` | 7 |
| 133 | `0x85` | `bgalph` | 8 |
| 134 | `0x86` | `noteoverlayalp` | 9 |
| 135 | `0x87` | `sg_endblip` | 10 |
| 136 | `0x88` | `glitchoffset` | 11 |
| 137 | `0x89` | `uhnoise` | 12 |
| 138 | `0x8A` | `abberationxamp` | 13 |
| 139 | `0x8B` | `abberationyamp` | 14 |
| 140 | `0x8C` | `fish` | 15 |
| 141 | `0x8D` | `static` | 16 |
| 142 | `0x8E` | `sg_endblip_destroy` | 17 |
| 143 | `0x8F` | `sn_bg_alpha` | 18 |
| 144 | `0x90` | `sn_bg_fxamp` | 19 |
| 145 | `0x91` | `sn_bg_animspd` | 20 |
| 146 | `0x92` | `yoffset` | 21 |
| 147 | `0x93` | `tutorialX` | 22 |
| 148 | `0x94` | `tutorialA` | 23 |
| 149 | `0x95` | `tutorialIndex` | 24 |

### `obj_unraveling_gimmick`

Parent: `obj_base_gimmick`. [Create event](../extraction/main/CodeEntries/gml_Object_obj_unraveling_gimmick_Create_0.gml).

| ID | Hex | Name | Source line |
| --- | --- | --- | --- |
| 129 | `0x81` | `gray` | 11 |
| 130 | `0x82` | `barrel` | 12 |
| 131 | `0x83` | `barrel2` | 13 |
| 132 | `0x84` | `hdistort` | 14 |
| 133 | `0x85` | `fish` | 15 |
| 134 | `0x86` | `vig` | 16 |
| 135 | `0x87` | `abx` | 17 |
| 136 | `0x88` | `aby` | 18 |
| 137 | `0x89` | `aberamp` | 19 |
| 138 | `0x8A` | `uialpha` | 20 |
| 139 | `0x8B` | `cover1` | 21 |
| 140 | `0x8C` | `cover2` | 22 |
| 141 | `0x8D` | `cover3` | 23 |
| 142 | `0x8E` | `wflash` | 24 |
| 143 | `0x8F` | `rainbow` | 25 |
| 144 | `0x90` | `sides` | 26 |
| 145 | `0x91` | `notealp` | 40 |
| 146 | `0x92` | `video` | 41 |
| 147 | `0x93` | `noteoverlayalp` | 42 |
