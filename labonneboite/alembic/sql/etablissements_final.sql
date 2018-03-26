# this script should only run in local development and after all migrations have completed

# generate random scores between 0 and 99
# static seeds 123 and 456 ensure the result is deterministic
UPDATE etablissements SET score=FLOOR(RAND(123)*(100));
UPDATE etablissements SET score_alternance=FLOOR(RAND(456)*(100));
