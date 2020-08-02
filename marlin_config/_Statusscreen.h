/**
 * Marlin 3D Printer Firmware
 * Copyright (c) 2020 MarlinFirmware [https://github.com/MarlinFirmware/Marlin]
 *
 * Based on Sprinter and grbl.
 * Copyright (c) 2011 Camiel Gubbels / Erik van der Zalm
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 *
 */

/**
 * Custom Status Screen bitmap
 *
 * Place this file in the root with your configuration files
 * and enable CUSTOM_STATUS_SCREEN_IMAGE in Configuration.h.
 *
 * Use the Marlin Bitmap Converter to make your own:
 * https://marlinfw.org/tools/u8glib/converter.html
 */

//
// Status Screen Logo bitmap
//
/**
 * Made with Marlin Bitmap Converter
 * https://marlinfw.org/tools/u8glib/converter.html
 *
 * This bitmap from the file 'christine_small.png'
 */
#pragma once

#define STATUS_LOGO_WIDTH 32

const unsigned char status_logo_bmp[] PROGMEM = {
  B00000000,B00011111,B11100000,B00000000, // ...........########.............
  B00000000,B11110000,B00111100,B00000000, // ........####......####..........
  B00000001,B10000000,B00000110,B00000000, // .......##............##.........
  B00000110,B00000000,B00000001,B10000000, // .....##................##.......
  B00001100,B00000000,B00000000,B11000000, // ....##..................##......
  B00001000,B00000000,B00000000,B01000000, // ....#....................#......
  B00010000,B00000000,B00000000,B00100000, // ...#......................#.....
  B00110000,B00000000,B10000000,B00110000, // ..##............#.........##....
  B00100000,B00000001,B11000000,B00010000, // ..#............###.........#....
  B00100000,B00000011,B01100000,B00010000, // ..#...........##.##........#....
  B01000000,B00000110,B00110000,B00001000, // .#...........##...##........#...
  B01000000,B00001100,B00011000,B00001000, // .#..........##.....##.......#...
  B01000000,B00111000,B00001100,B00001000, // .#........###.......##......#...
  B01000000,B11100000,B00000110,B00001000, // .#......###..........##.....#...
  B11011111,B10000000,B00000001,B11101100, // ##.######..............####.##..
  B11111100,B00000000,B00000000,B11111100, // ######..................######..
  B11101000,B00000000,B00000000,B01011100, // ###.#....................#.###..
  B11011001,B11100000,B00111100,B01101100, // ##.##..####.......####...##.##..
  B11011000,B11111000,B01111000,B01101100, // ##.##...#####....####....##.##..
  B11001000,B01110000,B00111000,B01001100, // ##..#....###......###....#..##..
  B11101000,B00000000,B00000000,B01011100, // ###.#....................#.###..
  B10111000,B00000000,B00000000,B01110100, // #.###....................###.#..
  B10001100,B00000011,B00000000,B11000100, // #...##........##........##...#..
  B10000100,B00011111,B11100000,B10000100, // #....#.....########.....#....#..
  B10000100,B00100000,B00110000,B10000100, // #....#....#.......##....#....#..
  B10000100,B00000000,B00000000,B10000100, // #....#..................#....#..
  B10000010,B00000000,B00000001,B00000100, // #.....#................#.....#..
  B11000011,B00000000,B00000011,B00001100, // ##....##..............##....##..
  B00111111,B10000000,B00000111,B11110000, // ..#######............#######....
  B00000001,B11000000,B00001110,B00000000, // .......###..........###.........
  B00000000,B00110000,B01110000,B00000000, // ..........##.....###............
  B00000000,B00001111,B11000000,B00000000  // ............######..............
};

//
// Use default bitmaps
//
#define STATUS_HOTEND_ANIM
#define STATUS_BED_ANIM
#define STATUS_HEATERS_XSPACE   20
#if HOTENDS < 2
  #define STATUS_HEATERS_X      48
  #define STATUS_BED_X          72
#else
  #define STATUS_HEATERS_X      40
  #define STATUS_BED_X          80
#endif
