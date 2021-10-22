---
layout: post
title: ""
categories: Miscellaneous
---
Sometimes, your post just stands for itself and doesn't need a title. And that's fine, too!

C# code example
```csharp
foreach (var selectable in _visibleSelectables)
{
    var screenPoint = camera.WorldToScreenPoint(selectable.transform.position);
    if (selectionRect != null && selectionRect.Value.Contains(screenPoint))
    {
        selectable.Select(true);
    }
}
```
