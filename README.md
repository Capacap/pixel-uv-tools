# Pixel UV Tools for Blender
Tools for creating pixel-perfect UVs in Blender

## W.I.P
Add-on is operational but documentation is in progress.

## Move UVs by Pixels
Moves the UVs of selected faces by a given amount of pixels.

- **Texture Size** - The width and height of the texture. Defaults to 256.
- **Delta X** - The amount of pixels to move by on the x-axis. Defaults to 0.
- **Delta Y** - The amount of pixels to move by on the y-axis. Defaults to 0.

## Scale UVs by Pixels
Scales the UVs of selected faces by a given amount of pixels.

- **Texture Size** - The width and height of the texture. Defaults to 256.
- **Delta X** - The amount of pixels to scale by on the x-axis. Defaults to 0.
- **Delta Y** - The amount of pixels to scale by on the y-axis. Defaults to 0.

## Snap UVs to Pixels
Snaps the UVs of selected faces to the nearest pixel-corners.

- **Texture Size** - The width and height of the texture. Defaults to 256.

## Snap UV Island Bounds to Pixels
Snaps the corners of each selected UV island's bounding box to the nearest pixel-corners.

- **Texture Size** - The width and height of the texture. Defaults to 256.

## Smart Follow Quads
Automatically preforms a "Follow Active Quads" operation on each selected UV island, using the most suitable quad of each island.

- **Edge Length Mode** - The edge-length mode of the Follow Active Quads operation. Defaults to 'Even'.

## Pack Islands Pixel Margin
Preforms a "Pack Islands" operation on the UVs of selected faces where the margin is specified in pixels.

- **Texture Size** - The width and height of the texture. Defaults to 256.
- **Pixel Margin** - The amount of pixels to use as margin around each UV island. Defaults to 2.
- **UDIM Source** - UDIM Source of the Pack Islands operation. Defaults to 'Closest UDIM'.
- **Rotate** - Allow or disallow rotation of UV islands. Defaults to True.
- **Rotation Method** - Rotation method of the Pack Islands operation. Defaults to 'Cardinal'.
- **Scale** - Allow or disallow scaling of UV islands. Defaults to True.
- **Merge Overlapping** - Merge Overlapping setting of the Pack Islands operation. Defaults to False.
- **Lock Pinned Islands** - Lock pinned islands setting of the Pack Islands operation. Defaults to False.
- **Pin Method** - Pin method of the Pack Islands operation. Defaults to 'All'
- **Shape Method** - Shape method of the Pack Islands operation. Defaults to 'Bounding Box'

## Regular Polygon Projection
Projects the UVs of selected faces over the sides and caps of a regular-polygon cylinder. When set to 4 verticies this projection behaves similarly to 'Cube Projection' but with without the inverted UVs on the back sides.

- **Verticies** - The amount of verticies on the regular polygon. Defaults to 4.
- **Cap Penalty** - Dissuades faces from projecting over the caps of the regular-polygon cylinder. Defaults to 0.
- **Use Seams** - Create UV islands from edges marked as seams. If disabled seams will be automatically generated based on face normals. Defaults to False.

## Tips and Tricks

The reccommended workflow is as follows:
1. Project the UVs using any method of your choice.
2. Run 'Pack Islands Pixel Margin' to pack your uv islands.
3. Run 'Snap UV Island Bounds to Pixels' to make your uv islands align nicely to the pixel grid.
4. On hard-surface models run 'Snap UVs to Pixels', consider running this operator at double the texture size to preserve smaller uvs that would otherwise get squished.

---

![pixel-uv-tools-example01](https://github.com/Capacap/pixel-uv-tools/blob/main/pixel-uv-tools-example01.png)
![pixel-uv-tools-example02](https://github.com/Capacap/pixel-uv-tools/blob/main/pixel-uv-tools-example02.png)
