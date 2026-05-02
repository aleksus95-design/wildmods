# Loading Key Art Replacement

This folder contains the safe rebuild workflow for the SCUM loading key art
override. It does not store extracted SCUM assets or rebuilt pak files.

## Latest Local Result

Output pak:

```text
C:\Users\aleks\Desktop\Новая папка (2)\zzzz_SCUM_LoadingKeyArt_WILDA_4K_P.pak
```

Source image used:

```text
C:\Users\aleks\Downloads\523097c9-ff12-4783-a1bf-55ada0518492.png
```

Original pak that was updated locally:

```text
C:\Users\aleks\Desktop\Новая папка (2)\zzzz_SCUM_LoadingKeyArt_WILDA_4K_P.pak
```

Backup created before replacement:

```text
C:\Users\aleks\Desktop\Новая папка (2)\backup_original\zzzz_SCUM_LoadingKeyArt_WILDA_4K_P.before_image_replace_20260502_223917.pak
```

Final pak SHA1:

```text
01E7292EBA6107D9C63F2163417999DB7F65541C
```

## Asset Details

Pak mount point:

```text
../../../SCUM/Content/ConZ_Files/Textures/
```

Files inside pak:

```text
SCUM_TheLongHaul_KeyArt.uasset
SCUM_TheLongHaul_KeyArt.uexp
```

Texture format:

```text
PF_B8G8R8A8
```

Texture size:

```text
3840x2160
```

The script preserves the Unreal texture asset structure and replaces only the
pixel block in `SCUM_TheLongHaul_KeyArt.uexp`.

## Rebuild Locally

Use the local extracted original texture pair and the replacement PNG:

```powershell
python .\loading-keyart\replace_keyart_texture.py
```

Then build the pak with UnrealPak using a response file that maps:

```text
SCUM_TheLongHaul_KeyArt.uasset -> ../../../SCUM/Content/ConZ_Files/Textures/SCUM_TheLongHaul_KeyArt.uasset
SCUM_TheLongHaul_KeyArt.uexp   -> ../../../SCUM/Content/ConZ_Files/Textures/SCUM_TheLongHaul_KeyArt.uexp
```

The actual local response file used in the latest build:

```text
D:\SCUM_LoadingKeyArt_Replace\loading_keyart_response.txt
```
