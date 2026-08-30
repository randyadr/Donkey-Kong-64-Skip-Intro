#include "modding.h"

typedef unsigned char u8;
typedef int s32;

/* DK64 Recompiled / DK64 US runtime globals. */
#define DK64_GAME_MODE_COPY      (*(volatile u8*)0x80755314u)
#define DK64_GAME_MODE           (*(volatile u8*)0x80755318u)
#define DK64_NEXT_MAP            (*(volatile s32*)0x807444E4u)
#define DK64_NEXT_EXIT           (*(volatile s32*)0x807444E8u)
#define DK64_TRANSITION_STATE    (*(volatile u8*)0x807444ECu)

#define GAME_MODE_MAIN_MENU 5u
#define MAP_MAIN_MENU       0x50
#define TRANSITION_LOAD_MAP 6u

/*
 * DK64 Recompiled fires recomp_on_init() after its earliest platform/boot
 * splash setup and immediately before entering the normal frame loop.
 *
 * Do not call initMapChange() from a frontend hook here.  Instead queue the
 * exact state the base frame loop already consumes: transition state 6 makes
 * the loop invoke its normal map loader with next_map/next_exit.
 */
RECOMP_CALLBACK("*", recomp_on_init)
void dk64_skip_intro_on_init(void) {
    /* Fill every part of the transition request before arming it. */
    DK64_NEXT_MAP = MAP_MAIN_MENU;
    DK64_NEXT_EXIT = 0;
    DK64_GAME_MODE_COPY = GAME_MODE_MAIN_MENU;
    DK64_GAME_MODE = GAME_MODE_MAIN_MENU;

    /* Write this last. The base loop sees state 6 and performs the load. */
    DK64_TRANSITION_STATE = TRANSITION_LOAD_MAP;
}
