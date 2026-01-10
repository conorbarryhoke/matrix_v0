python3 analyze_creature_families.py

1. ALL TO TRAINING (simple creatures with minimal features):
   - beast: 46 creatures
   - humanoid_simple: 17 creatures
   - goblinoid: 10 creatures
   - simple_flier: 3 creatures

2. ALL TO TRAINING (all giants - consistent simple pattern):
   - giant_cloud: 1 creatures
   - giant_fire: 2 creatures
   - giant_frost: 1 creatures
   - giant_hill: 1 creatures
   - giant_other: 31 creatures
   - giant_stone: 1 creatures
   - giant_storm: 1 creatures

3. SPLIT EVENLY (complex creatures with many features):

   dragon_young (10 creatures):
      TRAIN: Young Brass Dragon
      TEST: Young White Dragon
      TRAIN: Young Copper Dragon
      TEST: Young Black Dragon
      TRAIN: Young Bronze Dragon
      TEST: Young Green Dragon
      TRAIN: Young Blue Dragon
      TEST: Young Silver Dragon
      TRAIN: Young Red Dragon
      TEST: Young Gold Dragon

   dragon_adult (10 creatures):
      TRAIN: Adult Brass Dragon
      TEST: Adult White Dragon
      TRAIN: Adult Black Dragon
      TEST: Adult Copper Dragon
      TRAIN: Adult Green Dragon
      TEST: Adult Bronze Dragon
      TRAIN: Adult Blue Dragon
      TEST: Adult Silver Dragon
      TRAIN: Adult Red Dragon
      TEST: Adult Gold Dragon

   dragon_ancient (10 creatures):
      TRAIN: Ancient Brass Dragon
      TEST: Ancient White Dragon
      TRAIN: Ancient Copper Dragon
      TEST: Ancient Black Dragon
      TRAIN: Ancient Bronze Dragon
      TEST: Ancient Green Dragon
      TRAIN: Ancient Silver Dragon
      TEST: Ancient Blue Dragon
      TRAIN: Ancient Red Dragon
      TEST: Ancient Gold Dragon

   demon (6 creatures):
      TRAIN: Vrock
      TEST: Hezrou
      TRAIN: Glabrezu
      TEST: Nalfeshnee
      TRAIN: Marilith
      TEST: Balor

   devil (8 creatures):
      TRAIN: Bearded Devil
      TEST: Barbed Devil
      TRAIN: Chain Devil
      TEST: Bone Devil
      TRAIN: Horned Devil
      TEST: Erinyes
      TRAIN: Ice Devil
      TEST: Pit Fiend

   angel (3 creatures):
      TRAIN: Deva
      TEST: Planetar
      TRAIN: Solar