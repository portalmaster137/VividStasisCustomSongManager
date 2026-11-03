repeat (4) {
                        difficulty = (difficulty + 1) % (maxd + 1);
                        if (custom_diffs[difficulty]) break;
                    }