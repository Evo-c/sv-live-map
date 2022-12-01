"""Subclass of NXReader with functions specifically for raids"""

from sv_live_map_core.nxreader import NXReader
from sv_live_map_core.sv_enums import StarLevel, StoryProgress
from sv_live_map_core.raid_enemy_table_array import RaidEnemyTableArray
from sv_live_map_core.raid_block import RaidBlock, process_raid_block
from sv_live_map_core.rng import SCXorshift32

class RaidReader(NXReader):
    """Subclass of NXReader with functions specifically for raids"""
    RAID_BINARY_SIZES = (0x3128, 0x3058, 0x4400, 0x5A78, 0x6690, 0x4FB0)
    # https://github.com/Manu098vm/SVResearches/blob/master/RAM%20Pointers/RAM%20Pointers.txt
    RAID_BLOCK_PTR = ("[[main+42FD560]+160]+40", 0xC98) # ty skylink!
    RAID_BINARY_EVENT_PTR = ("[[[[[main+42DA820]+30]+388]+300]+28]+414", 0x7530)
    SAVE_BLOCK_PTR = "[[[[[main+42F3130]+B0]]]+30]+8]"
    DIFFICULTY_FLAG_LOCATIONS = (0x2BEE0, 0x1F3C0, 0x1B600, 0x13E80)

    def __init__(self, ip_address = None, port = 6000):
        super().__init__(ip_address, port)
        self.raid_enemy_table_arrays: tuple[RaidEnemyTableArray, 7] = \
            self.read_raid_enemy_table_arrays()
        self.story_progress: StoryProgress = self.read_story_progess()

    @staticmethod
    def raid_binary_ptr(star_level: StarLevel) -> tuple[str, int]:
        """Get a pointer to the raid flatbuffer binary in memory"""
        return (
            f"[[[[[[[[main+42FD670]+C0]+E8]]+10]+4A8]+{0xD0 + star_level * 0xB0:X}]+1E8]",
            RaidReader.RAID_BINARY_SIZES[star_level]
        )

    def read_story_progess(self) -> StoryProgress:
        """Read and decrypt story progress from save blocks"""
        # each key remains constant and SCXorshift32(difficulty_{n}_key).next() can be precomputed
        # for the sake of showing how to decrypt it this is not done
        loc = self.DIFFICULTY_FLAG_LOCATIONS[3]
        difficulty_6_key = self.read_pointer_int(f"{self.SAVE_BLOCK_PTR}+{loc:X}", 4)
        difficulty_6_val = self.read_pointer_int(f"[{self.SAVE_BLOCK_PTR}+{loc+8:X}]", 1) \
            ^ SCXorshift32(difficulty_6_key).next()
        if difficulty_6_val == 2:
            return StoryProgress.SIX_STAR_UNLOCKED
        loc = self.DIFFICULTY_FLAG_LOCATIONS[2]
        difficulty_5_key = self.read_pointer_int(f"{self.SAVE_BLOCK_PTR}+{loc:X}", 4)
        difficulty_5_val = self.read_pointer_int(f"[{self.SAVE_BLOCK_PTR}+{loc+8:X}]", 1) \
            ^ SCXorshift32(difficulty_5_key).next()
        if difficulty_5_val == 2:
            return StoryProgress.FIVE_STAR_UNLOCKED
        loc = self.DIFFICULTY_FLAG_LOCATIONS[1]
        difficulty_4_key = self.read_pointer_int(f"{self.SAVE_BLOCK_PTR}+{loc:X}", 4)
        difficulty_4_val = self.read_pointer_int(f"[{self.SAVE_BLOCK_PTR}+{loc+8:X}]", 1) \
            ^ SCXorshift32(difficulty_4_key).next()
        if difficulty_4_val == 2:
            return StoryProgress.FOUR_STAR_UNLOCKED
        loc = self.DIFFICULTY_FLAG_LOCATIONS[0]
        difficulty_3_key = self.read_pointer_int(f"{self.SAVE_BLOCK_PTR}+{loc:X}", 4)
        difficulty_3_val = self.read_pointer_int(f"[{self.SAVE_BLOCK_PTR}+{loc+8:X}]", 1) \
            ^ SCXorshift32(difficulty_3_key).next()
        if difficulty_3_val == 2:
            return StoryProgress.THREE_STAR_UNLOCKED
        return StoryProgress.DEFAULT

    def read_raid_enemy_table_arrays(self) -> tuple[RaidEnemyTableArray, 7]:
        """Read all raid flatbuffer binaries from memory"""
        return (
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.ONE_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.TWO_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.THREE_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.FOUR_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.FIVE_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.raid_binary_ptr(StarLevel.SIX_STAR))
            ),
            RaidEnemyTableArray(
                self.read_pointer(*self.RAID_BINARY_EVENT_PTR)
            ),
        )

    def read_raid_block_data(self) -> RaidBlock:
        """Read raid block data from memory and process"""
        raid_block = process_raid_block(self.read_pointer(*self.RAID_BLOCK_PTR))
        raid_block.initialize_data(self.raid_enemy_table_arrays, self.story_progress)
        return raid_block