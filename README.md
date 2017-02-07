# dungeon_generator
Example dungeon generator for Goldsmiths MScCGE tools and middleware project.

This project in based on the version, provided by Andy Thomasson: https://github.com/andy-thomason/dungeon_generator

The dungeon is built, using corridors, rooms, intersections and corridor-stairs. Every tile is picked randomly, with weighted coefficients.

The main algorithm, on which I focused is the tile substitution.
As you can see after you randomly place for example 100 tiles, some of the tiles require wall, doorway or substitution with another tile. For example, 4-way intersection with only 2 ways occupied we can substitute it with 2-way tile.

Here’s the screenshot of the version before calling substitution algorithm:
![Alt text](/before.png?raw=true "Before")

After:
![Alt text](/after.png?raw=true "After")

Also, the simple aabb-collision detection algorithm was implemented by me.

At the end the opened connections are being filled with the rooms and locked with the walls from the outside. The number of open entrances is the parameter.

![Alt text](/result.png?raw=true "Result")
