30 / 04 / 2024
- Added alternate to pure pursuit
- Added support if pure pursuit returns no intersections: Continue towards f(x + 1), or f(x - 1) in case of direction
- Added pursuit towards points following the heading
![Photo of pure pursuit working](images/image.png)
- Added images
- Removed pure pursuit due to too many errors
- Optimised curve following


29 / 04 / 2024
- Added everything so far
- Added support for moving backwards
- fixed issue of going forward due to low precision
- added matplotlib for plotting