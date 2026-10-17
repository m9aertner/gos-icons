# @m9aertner/gos-icons

Gate Operating System (GOS) specific icons in the style of [Phosphor Icons](https://phosphoricons.com) ("regular" weight, 256 x 256 grid), as icon font and as SVG. Complements `@phosphor-icons/web` (font) and `@phosphor-icons/core` (SVG), does not replace them.

Picture, design notes, build and release steps: <https://github.com/m9aertner/gos-icons>

## Icons

| Name | Meaning |
| --- | --- |
| `arrow-square-through` | Passes through the square, in and out in one step. In GOS: container remains on truck (ROT) |

## Icon font

Load both stylesheets in your global stylesheet, Phosphor first. `@phosphor-icons/web/regular` provides the `ph` base class; this package swaps in its own glyph font for its icons.

```scss
@use 'sass:meta';
@include meta.load-css('@phosphor-icons/web/regular');
@include meta.load-css('@m9aertner/gos-icons/regular');
```

```html
<i class="ph ph-arrow-square-through"></i>
<p-button icon="ph ph-arrow-square-through" />
```

Size comes from `font-size`, colour from `color`, as for every other `ph` icon. Only the "regular" weight exists; there are no ligatures.

## SVG

Same single-path format as `@phosphor-icons/core/regular/*.svg`:

```ts
import arrowSquareThroughSvg from '@m9aertner/gos-icons/regular/arrow-square-through.svg';
```
