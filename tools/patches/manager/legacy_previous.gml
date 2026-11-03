repeat (4) {
                        difficulty = (difficulty + maxd) % (maxd + 1);
                        if (custom_diffs[difficulty]) break;
                    }