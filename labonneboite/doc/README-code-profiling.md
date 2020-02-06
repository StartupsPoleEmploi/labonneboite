## Profiling

You will need to install a kgrind file visualizer for profiling. Kgrind files store the detailed results of a profiling.
- For Mac OS install and use QCacheGrind: `brew update && brew install qcachegrind`
- For other OSes: install and use [KCacheGrind](https://kcachegrind.github.io/html/Home.html)

### Profiling `create_index.py`

Here is how to profile the `create_index.py` script and its (long) reindexing of all elasticsearch data. This script is the first we had to do some profiling on, but the idea is that all techniques below should be easily reusable for future profilings of other parts of the code.

### Notes

- Part of this script heavily relies on parallel computing (using `multiprocessing` library). However profiling and parallel computing do not go very well together. Profiling the main process will give zero information about what happens inside each parallel job. This is why we also profile from within each job.

### Profiling the full script in local

Reminder: the local database has only a small part of the data .i.e data of only 1 of 96 departements, namely the departement 57. Thus profiling on this dataset is not exactly relevant. Let's still explain the details though.
- `make create-index-from-scratch-with-profiling`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, however you cannot see there the profiling from within any of the parrallel jobs.

![](https://www.evernote.com/l/ABKrdnXchbJNA6D_tl_PtEYUUezIhiz5DUcB/image.png)

- `qcachegrind labonneboite/scripts/profiling_results/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.

![](https://www.evernote.com/l/ABLptykQ5cNP7LzMtHOsC9wMVPdnK-wYErYB/image.png)

### Profiling the full script in staging

*Warning: in order to do this, you need to have ssh access to our staging server.*

The full dataset (all 96 departements) is in staging which makes it a very good environment to run the full profiling to get a big picture.
- `make create-index-from-scratch-with-profiling-on-staging`

Visualize the results (for Mac OS):
- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_run.kgrind`
  - you will visualize the big picture of the profiling, and as you have the full dataset, you will get the correct big picture about the time ratio between high-level methods:

![](https://www.evernote.com/l/ABIF2kbcoFtJCqDkThppsj98o8K1B7B__LUB/image.png)

- `qcachegrind labonneboite/scripts/profiling_results/staging/create_index_dpt57.kgrind`
  - you will visualize the profiling from within the single job reindexing data of departement 57.

![](https://www.evernote.com/l/ABKoq_-DZw1GlqbPyISsH_-MbQbxVyy9WoAB/image.png)

### Profiling a single job in local

Former profiling methods are good to get a big picture however they take quite some time to compute, and sometimes you want a quick profiling in local in order to quickly see the result of some changes. Here is how to do that:
- `make create-index-from-scratch-with-profiling-single-job`

This variant disables parallel computation, skips all tasks but office reindexing, and runs only a single job (departement 57). This makes the result very fast and easy to profile:
- `qcachegrind labonneboite/scripts/profiling_results/create_index_run.kgrind`

![](https://www.evernote.com/l/ABJT1VAV0_xI26HSnAHBP5a7JRSar7CnMjcB/image.png)

### Surgical profiling line by line

Profiling techniques above can give you a good idea of the performance big picture, but sometimes you really want to dig deeper into very specific and critical methods. For example above we really want to investigate what happens within the `get_scores_by_rome` method which seems critical for performance.

Let's do a line by line profiling using https://github.com/rkern/line_profiler.

Simply add a `@profile` decorator to any method you would like to profile line by line e.g.

```
@profile
def get_scores_by_rome(office, office_to_update=None):
```

You can perfectly profile methods in other parts of the code than `create_index.py`.

Here is an example of output:

![](https://www.evernote.com/l/ABJdN3iVDEJFgLeH2HgHyYOVMjOYK0a30e4B/image.png)
