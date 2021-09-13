#
# PyQt5 example for VLC Python bindings
# Copyright (C) 2009-2010 the VideoLAN team
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston MA 02110-1301, USA.
#
"""
A simple example for VLC python bindings using PyQt5.

Author: Saveliy Yusufov, Columbia University, sy2685@columbia.edu
Date: 25 December 2018
"""

import sys

from PyQt5 import QtWidgets

from pysaurus.interface.qtwebview.player import Player

PATHS = [
    r"I:\donnees\autres\p"
    r"\EuroGirlsOnGirls.21.04.15.Sybil.And.Agatha.Vega.XXX.1080p.MP4-WRB[rarbg]"
    r"\egog.21.04.15.sybil.and.agatha.vega.mp4",
    r"G:\donnees\autres\p\brownbunnies-sarai-minx8_2160p.mp4",
]
LAUNCHED = False
CURSOR = 0


def _next_path():
    global CURSOR
    path = PATHS[CURSOR % len(PATHS)]
    CURSOR += 1
    return path


def main():
    """Entry point for our simple vlc player"""
    app = QtWidgets.QApplication(sys.argv)
    player = Player(on_next=_next_path)
    player.show()
    app.exec_()


if __name__ == "__main__":
    main()
