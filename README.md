# Pixel UV Tools for Blender

A Blender addon for pixel-perfect UV editing. Every operator is reachable from the 3D Viewport's UV menu, so packing, snapping, and unwrapping pixel-aligned UVs never requires opening the UV editor. The same operators are also available from the UV Editor.

## Installation

1. Download this repository as a zip, or clone it and zip the `pixel_uv_tools` folder.
2. In Blender, open `Edit > Preferences > Add-ons > Install from Disk...` and select the zip.
3. Enable *Pixel UV Tools* in the add-on list.

Operators appear under `UV > Pixel UV Tools` in both the 3D Viewport (Edit Mode, `U`) and the UV Editor.

## Recommended workflow

For a typical pixel-art model:

1. Select the mesh faces you want to unwrap.
2. Run **Pixel Unwrap (Centerline)** for symmetric meshes, or **Pixel Unwrap (Active Edge)** for flat surfaces where a specific edge should define the UV baseline.
3. If you re-edit the mesh or add islands later, run **Pixel Pack Islands** to re-pack to the pixel grid.
4. For fine adjustments use **Pixel Move UVs**, **Pixel Scale UVs**, or the snap operators.

Every operator takes a **Texture Size** (or **Resolution**) parameter that defines the pixel grid. Set it to the resolution of your target texture.

## Operators

### Transform UVs

**Pixel Move UVs**

Translates the UVs of selected faces by an integer number of pixels. When invoked without arguments it enters an interactive drag mode where 20 screen-pixels of mouse movement equals one texture pixel. Confirm with LMB or Enter, cancel with RMB or Esc.

- *Texture Size*: width and height of the target texture. Default 256.
- *Delta X*, *Delta Y*: pixels to move on each axis. Default 0.

**Pixel Scale UVs**

Rounds the bounding-box size of the selection to an integer pixel count, then adds a pixel delta on each axis. Scales around the selection centroid.

- *Texture Size*: default 256.
- *Delta X*, *Delta Y*: additional pixels to add to the bounding-box width and height. Default 1.

### Snap and pack

**Pixel Snap UVs**

Snaps every UV vertex of selected faces to the nearest pixel corner. Best for hard-surface meshes. Tip: run it at twice the target resolution to preserve features smaller than a pixel, then snap again at the real resolution.

- *Texture Size*: default 256.

**Pixel Snap Islands**

For each selected UV island, rounds the bounding box to an even pixel count and centers the box on a pixel corner. Keeps island proportions pixel-perfect without squashing small details.

- *Resolution*: default 256.

**Pixel Pack Islands**

Packs islands, snaps their dimensions to the pixel grid, re-packs to close the gaps created by snapping, then snaps island positions to pixel corners. A drop-in replacement for Blender's Pack Islands when the target is a fixed-resolution texture.

- *Texture Resolution*: default 256.
- *Pixel Margin*: margin between islands in pixels. Default 2.
- *UDIM Source*: forwarded to Pack Islands. Default Closest UDIM.
- *Rotate*, *Scale*, *Merge Overlapping*, *Lock Pinned Islands*, *Pin Method*, *Shape Method*: forwarded to Pack Islands. See Blender's Pack Islands documentation for details.

### Unwrap

**Pixel Unwrap (Active Edge)**

Pins the active edge along the U axis using its 3D length, then runs an angle-based unwrap over the selected faces. Use this when a specific edge should become horizontal in UV space. If no faces are selected, the operator selects faces reachable from the active edge through non-seam edges.

**Pixel Unwrap (Centerline)**

Pins vertices on the `X = 0` plane to a vertical line in UV space, runs an angle-based unwrap on each seam-delimited island, packs the result, and snaps everything to the pixel grid. Designed for symmetric meshes (characters, weapons) where the silhouette's center should land on a texel boundary.

- *Texture Size*: default 256.
- *Packing Margin*: pixels between islands. Default 2.
- *Shape Method*: shape metric used by the packing step. Default Bounding Box.
- *Centerline Adjustment*: `Pixel Corner` places the centerline on a texel boundary, `Pixel Center` offsets by half a pixel so the centerline runs through texel centers. Default Pixel Corner.

### Utility operators

**Pixel Move Islands** and **Pixel Scale Islands** are registered but not shown in the UV menu. They are used internally by Pixel Pack Islands and can be invoked by name through `F3` search if you need them directly.

---

![example 1](https://github.com/Capacap/pixel-uv-tools/blob/main/pixel-uv-tools-example01.png)
![example 2](https://github.com/Capacap/pixel-uv-tools/blob/main/pixel-uv-tools-example02.png)
