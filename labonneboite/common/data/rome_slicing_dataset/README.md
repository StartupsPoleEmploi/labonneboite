# About this data set

This data set was produced by @michelbl (Sept 2017) and a first integration attempt was made by @vermeer. The following issues should be addressed by the next attempt:

- verify that the general performance does not suffer too much due to the explosion of the number of ROME NAP mapping (x3)
- verify that the duration of a full reindexing stays reasonable for the same reason
- fix broken rome_mobilities logic
- fix broken tests
- give an early warning to the VAE team that this will break the job auto completion (suggest_job_labels) they are currently using, because instead of sending only ROME codes, it will send a mix of ROME codes and OGR codes due to the new ROME slicing logic

